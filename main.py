import customtkinter as ctk
import serial
import serial.tools.list_ports
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button as MouseButton
import threading
import sys
import time

# --- Special Keys & Actions ---
SPECIAL_KEYS = {
    "Space": Key.space, "Ctrl": Key.ctrl_l, "Shift": Key.shift,
    "Enter": Key.enter, "Esc": Key.esc, "Alt": Key.alt_l, "Tab": Key.tab,
    "Up Arrow": Key.up, "Down Arrow": Key.down, "Left Arrow": Key.left, "Right Arrow": Key.right
}

MOUSE_ACTIONS = [
    "Mouse L-Click", "Mouse R-Click", "Mouse M-Click", 
    "Mouse Up", "Mouse Down", "Mouse Left", "Mouse Right"
]

STANDARD_KEYS = [chr(i) for i in range(97, 123)] + [str(i) for i in range(10)]
ALL_ACTIONS = list(SPECIAL_KEYS.keys()) + MOUSE_ACTIONS + STANDARD_KEYS
SERIAL_CHARS = [chr(i) for i in range(65, 91)] # A-Z

# --- UI Configuration ---
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class Serial2KeyboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Serial2Key | Input Mapper")
        self.geometry("850x550")
        self.minsize(800, 500)

        # App Grid Layout: 1 row, 2 columns (Sidebar + Main Content)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Variables
        self.is_running = False
        self.serial_conn = None
        self.last_data = 'I'
        self.thread = None
        self.mouse_speed = 8 
        
        # Default Mappings
        self.key_map = {
            'W': 'w', 'S': 's', 'A': 'a', 'D': 'd',
            'Z': 'Space', 'E': 'e', 'Q': 'q'
        }
        
        # Controllers
        self.keyboard = KeyboardController()
        self.mouse = MouseController()

        self.build_ui()

    def build_ui(self):
        # ==========================================
        # LEFT SIDEBAR: Connection & Status
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.brand_label = ctk.CTkLabel(self.sidebar, text="Serial2Key", font=("Segoe UI", 24, "bold"))
        self.brand_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.port_var = ctk.StringVar(value="Select Port")
        self.port_dropdown = ctk.CTkOptionMenu(self.sidebar, variable=self.port_var, values=self.get_ports(), width=180)
        self.port_dropdown.grid(row=1, column=0, padx=20, pady=10)

        self.baud_var = ctk.StringVar(value="115200")
        self.baud_dropdown = ctk.CTkOptionMenu(self.sidebar, variable=self.baud_var, values=["9600", "57600", "115200"], width=180)
        self.baud_dropdown.grid(row=2, column=0, padx=20, pady=10)

        self.toggle_btn = ctk.CTkButton(self.sidebar, text="START LISTENING", font=("Segoe UI", 13, "bold"),
                                        command=self.toggle_listening, fg_color="#2E7D32", hover_color="#1B5E20", height=40)
        self.toggle_btn.grid(row=3, column=0, padx=20, pady=20)

        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=6, column=0, padx=20, pady=20, sticky="s")
        
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color="gray", font=("Segoe UI", 18))
        self.status_dot.pack(side="left", padx=(0, 5))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Disconnected", font=("Segoe UI", 13))
        self.status_label.pack(side="left")

        # ==========================================
        # RIGHT MAIN PANEL: Mappings & Config
        # ==========================================
        self.main_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.main_panel.grid_rowconfigure(2, weight=1) 

        self.map_title = ctk.CTkLabel(self.main_panel, text="Input Bindings", font=("Segoe UI", 28, "bold"))
        self.map_title.grid(row=0, column=0, sticky="w", pady=(0, 20))

        self.add_frame = ctk.CTkFrame(self.main_panel, corner_radius=10)
        self.add_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20), ipadx=10, ipady=10)
        self.add_frame.grid_columnconfigure(5, weight=1)

        self.add_label = ctk.CTkLabel(self.add_frame, text="Create New Binding:", font=("Segoe UI", 14))
        self.add_label.grid(row=0, column=0, padx=(15, 10), pady=15)

        self.add_serial_var = ctk.StringVar(value="W")
        self.add_serial_drop = ctk.CTkOptionMenu(self.add_frame, variable=self.add_serial_var, values=SERIAL_CHARS, width=80)
        self.add_serial_drop.grid(row=0, column=1, padx=5, pady=15)
        
        self.arrow_label = ctk.CTkLabel(self.add_frame, text="➔", font=("Segoe UI", 16))
        self.arrow_label.grid(row=0, column=2, padx=5)

        self.add_action_var = ctk.StringVar(value="Mouse Up")
        self.add_action_drop = ctk.CTkOptionMenu(self.add_frame, variable=self.add_action_var, values=ALL_ACTIONS, width=140)
        self.add_action_drop.grid(row=0, column=3, padx=5, pady=15)

        self.add_btn = ctk.CTkButton(self.add_frame, text="+ Add Binding", command=self.add_mapping, width=100)
        self.add_btn.grid(row=0, column=4, padx=(15, 15), pady=15)

        self.error_label = ctk.CTkLabel(self.add_frame, text="", text_color="#FF5252", font=("Segoe UI", 12, "bold"))
        self.error_label.grid(row=1, column=0, columnspan=5, sticky="w", padx=15, pady=(0, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_panel, fg_color="transparent")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew")
        
        self.refresh_mapping_list()

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports] if ports else ["No Ports Found"]

    # --- Mapping UI Logic ---
    def add_mapping(self):
        serial_char = self.add_serial_var.get()
        action = self.add_action_var.get()

        if serial_char in self.key_map:
            self.error_label.configure(text=f"⚠️ Serial Key '{serial_char}' is already mapped! Delete it below first.")
            return

        self.error_label.configure(text="")
        self.key_map[serial_char] = action
        self.refresh_mapping_list()

    def delete_mapping(self, serial_char):
        if serial_char in self.key_map:
            del self.key_map[serial_char]
            self.error_label.configure(text="") 
            self.refresh_mapping_list()

    def refresh_mapping_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for s_char, action in self.key_map.items():
            row_frame = ctk.CTkFrame(self.scroll_frame, corner_radius=8, fg_color=("gray85", "gray16"))
            row_frame.pack(fill="x", pady=5, padx=5)
            
            info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=10)
            
            s_label = ctk.CTkLabel(info_frame, text=s_char, font=("Segoe UI", 16, "bold"), text_color="#3B82F6", width=30)
            s_label.pack(side="left")
            
            arrow = ctk.CTkLabel(info_frame, text="triggers", font=("Segoe UI", 12), text_color="gray")
            arrow.pack(side="left", padx=15)
            
            a_label = ctk.CTkLabel(info_frame, text=action, font=("Segoe UI", 14, "bold"))
            a_label.pack(side="left")

            del_btn = ctk.CTkButton(row_frame, text="✕ Remove", width=70, height=28, 
                                    fg_color="transparent", border_width=1, border_color="#C62828", 
                                    text_color="#C62828", hover_color="#421010",
                                    command=lambda c=s_char: self.delete_mapping(c))
            del_btn.pack(side="right", padx=15)

    # --- Action Execution Logic ---
    def press_action(self, action):
        if action in SPECIAL_KEYS:
            self.keyboard.press(SPECIAL_KEYS[action])
        elif action == "Mouse L-Click":
            self.mouse.press(MouseButton.left)
        elif action == "Mouse R-Click":
            self.mouse.press(MouseButton.right)
        elif action == "Mouse M-Click":
            self.mouse.press(MouseButton.middle)
        elif action not in MOUSE_ACTIONS: 
            self.keyboard.press(action)

    def release_action(self, action):
        if action in SPECIAL_KEYS:
            self.keyboard.release(SPECIAL_KEYS[action])
        elif action == "Mouse L-Click":
            self.mouse.release(MouseButton.left)
        elif action == "Mouse R-Click":
            self.mouse.release(MouseButton.right)
        elif action == "Mouse M-Click":
            self.mouse.release(MouseButton.middle)
        elif action not in MOUSE_ACTIONS: 
            self.keyboard.release(action)

    def handle_continuous_mouse(self, action):
        if action == "Mouse Up":
            self.mouse.move(0, -self.mouse_speed)
        elif action == "Mouse Down":
            self.mouse.move(0, self.mouse_speed)
        elif action == "Mouse Left":
            self.mouse.move(-self.mouse_speed, 0)
        elif action == "Mouse Right":
            self.mouse.move(self.mouse_speed, 0)

    # --- Core Serial Loop ---
    def toggle_listening(self):
        if not self.is_running:
            port = self.port_var.get()
            baud = self.baud_var.get()
            
            if port in ("Select Port", "No Ports Found"):
                self.status_dot.configure(text_color="#FF5252")
                self.status_label.configure(text="Invalid Port")
                return

            self.is_running = True
            self.toggle_btn.configure(text="STOP LISTENING", fg_color="#C62828", hover_color="#B71C1C")
            self.port_dropdown.configure(state="disabled")
            self.baud_dropdown.configure(state="disabled")
            
            self.thread = threading.Thread(target=self.serial_loop, args=(port, baud), daemon=True)
            self.thread.start()
        else:
            self.stop_listening()

    def stop_listening(self):
        self.is_running = False
        self.toggle_btn.configure(text="START LISTENING", fg_color="#2E7D32", hover_color="#1B5E20")
        self.port_dropdown.configure(state="normal")
        self.baud_dropdown.configure(state="normal")
        
        self.status_dot.configure(text_color="gray")
        self.status_label.configure(text="Disconnected")
        self.port_dropdown.configure(values=self.get_ports())

        if self.last_data in self.key_map:
            self.release_action(self.key_map[self.last_data])
        self.last_data = 'I'

    def serial_loop(self, port, baud):
        try:
            # Reverted timeout back to 0.1 to match your old stable code behavior
            self.serial_conn = serial.Serial(port, int(baud), timeout=0.1) 
            self.status_dot.configure(text_color="#4CAF50")
            self.status_label.configure(text=f"Active on {port}")
        except Exception as e:
            self.status_dot.configure(text_color="#FF5252")
            self.status_label.configure(text="Port Error / In Use")
            self.stop_listening()
            return

        while self.is_running:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode('utf-8').strip()
                    
                    # FIX: We removed the check that prevented identical consecutive strings.
                    # Now it mimics your old code: releases the old key, then immediately presses the new one.
                    if data:
                        if self.last_data in self.key_map:
                            self.release_action(self.key_map[self.last_data])
                        
                        if data in self.key_map:
                            self.press_action(self.key_map[data])
                            
                        self.last_data = data

                # Keep continuous actions (like mouse moving) running smoothly
                if self.last_data in self.key_map:
                    self.handle_continuous_mouse(self.key_map[self.last_data])

                time.sleep(0.01)

            except Exception:
                break

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
