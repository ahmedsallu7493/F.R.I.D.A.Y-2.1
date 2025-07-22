import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import psutil
import json
import os

CHAT_LOG_FILE = r"Fronted/File/chat.data"
CHAT_DATA_FILE = r"Data/chat.data"
mic_status=r"Fronted/File/Mic.data"

class FridayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("F.R.I.D.A.Y - AI Assistant")
        self.fullscreen = True
        self.root.attributes('-fullscreen', True)

        self.bg_img_orig = Image.open("Fronted/Graphics/bg.jpg")
        self.mic_on = False

        self.create_top_bar()
        self.create_content_area()
        self.load_icons()
        self.update_background()

        self.root.bind('<Configure>', lambda e: self.update_background())
        self.status_label_after()
        self.root.after(3000, self.poll_mic_and_input)
        self.root.after(1000, self.poll_chat_data_and_update)  # Start periodic check

    def create_top_bar(self):
        tf = self.top_frame = tk.Frame(self.root, bg="black", height=60)
        tf.grid(row=0, column=0, sticky="ew")
        tf.grid_propagate(False)
        for i in range(9):
            tf.columnconfigure(i, weight=(1 if i == 4 else 0))

        self.icons = {}
        self.btn_refs = {}

        for name, col in [
            ("home", 0), ("chat", 1), ("mic", 2), ("settings", 3),
            ("min", 5), ("restore", 6), ("close", 7)
        ]:
            self.btn_refs[name] = tk.Button(tf, bg="black", bd=0)
            self.btn_refs[name].grid(row=0, column=col, padx=8, pady=10)

        self.status_lbl = tk.Label(tf, fg="white", bg="black", font=("Segoe UI", 10))
        self.status_lbl.grid(row=0, column=8, sticky="e", padx=8)

    def load_icons(self):
        icons_info = {
            "home": "Fronted/Graphics/Home.png",
            "chat": "Fronted/Graphics/chat.png",
            "mic_on": "Fronted/Graphics/Mic On.png",
            "mic_off": "Fronted/Graphics/Mic Off.png",
            "settings": "Fronted/Graphics/Setting.png",
            "min": "Fronted/Graphics/Minimizes2.png",
            "restore": "Fronted/Graphics/restoredown.png",
            "close": "Fronted/Graphics/close.png",
        }

        for name, path in icons_info.items():
            img = Image.open(path).resize((32, 32), Image.Resampling.LANCZOS)
            self.icons[name] = ImageTk.PhotoImage(img)
            if name in self.btn_refs:
                self.btn_refs[name].config(image=self.icons[name])

        self.btn_refs["mic"].config(command=self.toggle_mic)
        self.btn_refs["min"].config(command=lambda: self.root.iconify())
        self.btn_refs["restore"].config(command=self.toggle_fullscreen)
        self.btn_refs["close"].config(command=self.root.quit)
        
        # Chat button toggles chat display visibility
        self.btn_refs["chat"].config(command=self.toggle_chat_display)
        self.btn_refs["settings"].config(command=lambda: [self.hide_chat_display(), messagebox.showinfo("Settings", "Settings clicked")])
        self.btn_refs["home"].config(command=lambda: [self.hide_chat_display(), messagebox.showinfo("Home", "Home clicked")])

    def create_content_area(self):
        self.bg_lbl = tk.Label(self.root)
        self.bg_lbl.grid(row=1, column=0, sticky="nsew")

        self.content = tk.Frame(self.bg_lbl, bg="white", bd=2, relief="ridge")
        # Initially hidden
        self.content.place_forget()

        self.chat_display = tk.Text(self.content, wrap="word", font=("Segoe UI", 12),
                                    state="disabled", bg="#f0f0f0", height=15, width=70)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)

    def toggle_chat_display(self):
        if self.content.winfo_ismapped():
            self.hide_chat_display()
        else:
            self.show_chat_display()

    def show_chat_display(self):
        self.content.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
        self.show_chat_history()

    def hide_chat_display(self):
        self.content.place_forget()

    def show_chat_history(self):
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", "end")

        user_name = os.getenv("USER_NAME", "User")
        assistant_name = os.getenv("ASSISTANT_NAME", "Assistant")

        if os.path.exists(CHAT_LOG_FILE):
            try:
                with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for msg in data:
                            role = msg.get("role", "")
                            content = msg.get("content", "")
                            if role == "user":
                                self.chat_display.insert("end", f"{user_name}: {content}\n\n")
                            elif role == "assistant":
                                self.chat_display.insert("end", f"{assistant_name}: {content}\n\n")
            except Exception as e:
                self.chat_display.insert("end", f"Error reading chat: {e}\n")

        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    def toggle_mic(self):
        self.mic_on = not self.mic_on
        icon = "mic_on" if self.mic_on else "mic_off"
        self.btn_refs["mic"].config(image=self.icons[icon])

        msg = "Microphone turned ON" if self.mic_on else "Microphone turned OFF"
        messagebox.showinfo("Mic", msg)

    def poll_mic_and_input(self):
        if not self.mic_on:
            self.prompt_for_input()
        self.root.after(8000, self.poll_mic_and_input)

    def prompt_for_input(self):
        user_input = simpledialog.askstring("Input Required", "Microphone is OFF.\nPlease type your message:")
        if user_input:
            self.handle_text_input(user_input)

    def handle_text_input(self, user_input):
        print(f"[INPUT RECEIVED]: {user_input}")
        # Add your processing logic here

    def update_background(self):
        w, h = self.root.winfo_width(), self.root.winfo_height() - 60
        if w > 10 and h > 10:
            img = self.bg_img_orig.resize((w, h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.bg_lbl.config(image=photo)
            self.bg_lbl.image = photo

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.root.attributes('-fullscreen', False)
            self.root.geometry("1000x600")
        else:
            self.root.attributes('-fullscreen', True)
        self.fullscreen = not self.fullscreen

    def status_label_after(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        self.status_lbl.config(text=f"CPU: {cpu}% | RAM: {ram}%")
        self.root.after(1000, self.status_label_after)

    # === New methods for chat.data checking and updating chat log ===
    def poll_chat_data_and_update(self):
        if self.is_chat_data_true():
            self.update_chat_autoservice()
            if self.content.winfo_ismapped():
                self.show_chat_history()  # refresh chat window if open
        self.root.after(999999999, self.poll_chat_data_and_update)

    def is_chat_data_true(self):
        if os.path.exists(CHAT_DATA_FILE):
            try:
                with open(CHAT_DATA_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip().lower()
                    if content == "true":
                        return True
            except Exception as e:
                print(f"Error reading {CHAT_DATA_FILE}: {e}")
        return False

    def update_chat_autoservice(self):
        if not os.path.exists(CHAT_LOG_FILE):
            chat_history = []
        else:
            try:
                with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
                    chat_history = json.load(f)
            except Exception as e:
                print(f"Error reading {CHAT_LOG_FILE}: {e}")
                chat_history = []

        # Append an auto-response message
        chat_history.append({
            "role": "assistant",
            "content": "Auto-response: chat.data is true, updating chat service."
        })

        try:
            with open(CHAT_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(chat_history, f, indent=4)
        except Exception as e:
            print(f"Error writing {CHAT_LOG_FILE}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FridayApp(root)
    root.mainloop()
