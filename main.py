import customtkinter as ctk
import serial
import serial.tools.list_ports
from pynput.keyboard import Controller
import threading
import sys
import queue
import time

# =====================
# Serial2Keyboard PRO
# Thread-safe + stable version
# =====================

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class Serial2KeyboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Serial2Keyboard PRO")
        self.geometry("700x500")
        self.resizable(False, False)

        # State
        self.is_running = False
        self.serial_conn = None
        self.current_key = None

        # Thread-safe communication
        self.serial_queue = queue.Queue()
        self.worker_thread = None
        self.reader_thread = None

        # Keyboard controller
        self.keyboard = Controller()

        self.build_ui()
        self.after(100, self.process_queue)

    # ---------------- UI ----------------
    def build_ui(self):
        self.title_label = ctk.CTkLabel(self, text="Serial2Keyboard PRO", font=("Segoe UI", 22, "bold"))
        self.title_label.pack(pady=15)

        self.frame = ctk.CTkFrame(self)
        self.frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.port_var = ctk.StringVar(value="Select Port")
        self.baud_var = ctk.StringVar(value="115200")

        self.port_menu = ctk.CTkOptionMenu(self.frame, variable=self.port_var, values=self.get_ports())
        self.port_menu.grid(row=0, column=1, padx=10, pady=10)

        self.baud_menu = ctk.CTkOptionMenu(self.frame, variable=self.baud_var,
                                           values=["9600", "57600", "115200"])
        self.baud_menu.grid(row=1, column=1, padx=10, pady=10)

        ctk.CTkLabel(self.frame, text="Port:").grid(row=0, column=0)
        ctk.CTkLabel(self.frame, text="Baud:").grid(row=1, column=0)

        self.btn = ctk.CTkButton(self, text="Start", command=self.toggle)
        self.btn.pack(pady=10)

        self.status = ctk.CTkLabel(self, text="Idle")
        self.status.pack(pady=5)

    # ---------------- Ports ----------------
    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports] if ports else ["No Ports"]

    # ---------------- Control ----------------
    def toggle(self):
        if not self.is_running:
            self.start()
        else:
            self.stop()

    def start(self):
        port = self.port_var.get()
        baud = self.baud_var.get()

        if port == "Select Port" or port == "No Ports":
            self.set_status("Select valid port", "red")
            return

        try:
            self.serial_conn = serial.Serial(port, int(baud), timeout=0.1)
        except Exception as e:
            self.set_status(f"Serial error: {e}", "red")
            return

        self.is_running = True
        self.btn.configure(text="Stop")
        self.set_status(f"Listening on {port}", "green")

        self.reader_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.reader_thread.start()

    def stop(self):
        self.is_running = False
        self.btn.configure(text="Start")
        self.set_status("Stopped", "white")

        if self.current_key:
            self.keyboard.release(self.current_key)
            self.current_key = None

        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
        except:
            pass

    # ---------------- Serial Reader (Thread) ----------------
    def read_serial(self):
        while self.is_running:
            try:
                if self.serial_conn.in_waiting:
                    data = self.serial_conn.readline().decode().strip()
                    self.serial_queue.put(data)
            except Exception as e:
                self.serial_queue.put(f"__ERROR__:{e}")
                break

            time.sleep(0.01)

    # ---------------- Queue Processor (Main Thread) ----------------
    def process_queue(self):
        try:
            while not self.serial_queue.empty():
                data = self.serial_queue.get()

                if data.startswith("__ERROR__"):
                    self.set_status(data, "red")
                    self.stop()
                    return

                self.handle_key(data)

        except Exception as e:
            self.set_status(str(e), "red")

        self.after(50, self.process_queue)

    # ---------------- Key Handling ----------------
    def handle_key(self, data):
        if self.current_key:
            self.keyboard.release(self.current_key)
            self.current_key = None

        mapping = {
            "W": "w",
            "A": "a",
            "S": "s",
            "D": "d",
            " ": " "
        }

        key = mapping.get(data)
        if key:
            self.keyboard.press(key)
            self.current_key = key

    # ---------------- UI Safe Update ----------------
    def set_status(self, text, color="white"):
        self.after(0, lambda: self.status.configure(text=text, text_color=color))

    # ---------------- Exit ----------------
    def on_close(self):
        self.stop()
        self.destroy()
        sys.exit()


# NOTE: If you get "Permission denied" on serial port (Linux/Mint), run:
# sudo usermod -a -G dialout $USER
# then reboot

if __name__ == "__main__":
    app = Serial2KeyboardApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

