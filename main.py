import customtkinter as ctk
import serial
import serial.tools.list_ports
from pynput.keyboard import Controller
import threading
import sys

#test
# --- UI Configuration ---
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class Serial2KeyboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Serial2Keyboard")
        self.geometry("450x380")
        self.resizable(False, False)

        # Variables
        self.is_running = False
        self.serial_conn = None
        self.current_key = None
        self.thread = None
        
        # Initialize the cross-platform keyboard controller
        self.keyboard = Controller()

        self.build_ui()

    def build_ui(self):
        # Header
        self.title_label = ctk.CTkLabel(self, text="Serial2Keyboard", font=("Segoe UI", 24, "bold"))
        self.title_label.pack(pady=(25, 2))

        self.subtitle_label = ctk.CTkLabel(self, text="by E21 Academy", font=("Segoe UI", 12, "italic"), text_color="gray")
        self.subtitle_label.pack(pady=(0, 20))

        # Controls Frame
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=10, padx=40, fill="both", expand=True)

        # Configure columns to have equal weight so content meets perfectly in the center
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        # Port Selection - Aligned East (Right)
        self.port_label = ctk.CTkLabel(self.frame, text="Select Port:")
        self.port_label.grid(row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="e")
        
        # Aligned West (Left)
        self.port_var = ctk.StringVar(value="Select Port")
        self.port_dropdown = ctk.CTkOptionMenu(self.frame, variable=self.port_var, values=self.get_ports())
        self.port_dropdown.grid(row=0, column=1, padx=(10, 20), pady=(20, 10), sticky="w")

        # Baudrate Selection - Aligned East (Right)
        self.baud_label = ctk.CTkLabel(self.frame, text="Select Baudrate:")
        self.baud_label.grid(row=1, column=0, padx=(20, 10), pady=(10, 20), sticky="e")

        # Aligned West (Left)
        self.baud_var = ctk.StringVar(value="115200")
        self.baud_dropdown = ctk.CTkOptionMenu(self.frame, variable=self.baud_var, values=["9600", "57600", "115200"])
        self.baud_dropdown.grid(row=1, column=1, padx=(10, 20), pady=(10, 20), sticky="w")

        # Start/Stop Button
        self.toggle_btn = ctk.CTkButton(self, text="Start Listening", command=self.toggle_listening, fg_color="green", hover_color="darkgreen")
        self.toggle_btn.pack(pady=(15, 10))

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="Status: Disconnected", font=("Segoe UI", 12))
        self.status_label.pack(pady=(0, 20))

    def get_ports(self):
        # Auto-detects COM ports on Windows, /dev/tty on Mac/Linux
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        return port_list if port_list else ["No Ports Found"]

    def toggle_listening(self):
        if not self.is_running:
            port = self.port_var.get()
            baud = self.baud_var.get()
            
            if port == "Select Port" or port == "No Ports Found":
                self.status_label.configure(text="Status: Please select a valid port.", text_color="red")
                return

            self.is_running = True
            self.toggle_btn.configure(text="Stop Listening", fg_color="red", hover_color="darkred")
            self.port_dropdown.configure(state="disabled")
            self.baud_dropdown.configure(state="disabled")
            
            self.thread = threading.Thread(target=self.serial_loop, args=(port, baud), daemon=True)
            self.thread.start()
        else:
            self.stop_listening()

    def stop_listening(self):
        self.is_running = False
        self.toggle_btn.configure(text="Start Listening", fg_color="green", hover_color="darkgreen")
        self.port_dropdown.configure(state="normal")
        self.baud_dropdown.configure(state="normal")
        self.status_label.configure(text="Status: Disconnected", text_color="white")
        
        self.port_dropdown.configure(values=self.get_ports())

        if self.current_key:
            self.keyboard.release(self.current_key)
            self.current_key = None

    def serial_loop(self, port, baud):
        try:
            self.serial_conn = serial.Serial(port, int(baud), timeout=0.1) 
            self.status_label.configure(text=f"Status: Listening on {port}...", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Status: Error - Port likely in use or requires permissions.", text_color="red")
            self.stop_listening()
            return

        while self.is_running:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode('utf-8').replace('\r', '').replace('\n', '')

                    # 1. Release previous key
                    if self.current_key:
                        self.keyboard.release(self.current_key)
                        self.current_key = None

                    # 2. Press new key
                    if data == 'W':
                        self.keyboard.press('w')
                        self.current_key = 'w'
                    elif data == 'S':
                        self.keyboard.press('s')
                        self.current_key = 's'
                    elif data == 'A':
                        self.keyboard.press('a')
                        self.current_key = 'a'
                    elif data == 'D':
                        self.keyboard.press('d')
                        self.current_key = 'd'
                    elif data == ' ':
                        self.keyboard.press(' ')
                        self.current_key = ' '
            except Exception:
                break

        # Cleanup
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def on_closing(self):
        self.stop_listening()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = Serial2KeyboardApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
