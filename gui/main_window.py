import customtkinter as ctk

from gui.incident_tracker import IncidentTracker


class MainWindow(ctk.CTkFrame):
    def __init__(self, master, db, user_info, on_logout):
        super().__init__(master)
        self.db = db
        self.user_info = user_info
        self.on_logout = on_logout
        self.incident_window = None

        # Настройка интерфейса в зависимости от роли
        self.configure_role_style(user_info["role"])

        master.title(f"Главное меню (пользователь: {user_info['username']})")
        master.geometry("400x250+700+300")

        self.info_label = ctk.CTkLabel(
            self,
            text=f"Добро пожаловать, {user_info['username']}!",
            font=("Arial", 16),
            text_color=self.text_color
        )
        self.info_label.pack(pady=10)

        self.incident_btn = ctk.CTkButton(
            self,
            text="Управление инцидентами",
            fg_color=self.button_color,
            hover_color=self.button_hover_color,
            text_color="white",
            command=self.open_incident_tracker
        )
        self.incident_btn.pack(pady=20, padx=20)

        self.logout_btn = ctk.CTkButton(
            self,
            text="Выйти",
            fg_color="red",
            hover_color="darkred",
            text_color="white",
            command=self.logout
        )
        self.logout_btn.pack(pady=10)

    def configure_role_style(self, role):
        if role == "admin":
            self.configure(fg_color="#1e1e2f")
            self.button_color = "#8d252c"  # синий
            self.button_hover_color = "#b4130b"
            self.text_color = "#FFFFFF"
        else:  # role == "user"
            self.configure(fg_color="#1e1e2f")
            self.button_color = "#1d2577"  # зелёный
            self.button_hover_color = "#01459C"
            self.text_color = "#FFFFFF"

    def open_incident_tracker(self):
        if self.incident_window is None or not self.incident_window.winfo_exists():
            self.incident_window = ctk.CTkToplevel(self)
            self.incident_window.geometry("800x600+150+150")
            self.incident_window.title("Управление инцидентами")
            tracker = IncidentTracker(self.incident_window, self.db, self.user_info)
            tracker.pack(fill="both", expand=True)
        else:
            self.incident_window.lift()

    def logout(self):
        if self.incident_window and self.incident_window.winfo_exists():
            self.incident_window.destroy()
        self.on_logout()
