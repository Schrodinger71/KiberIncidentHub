import customtkinter as ctk
from gui.incident_tracker import IncidentTracker


class MainWindow(ctk.CTkFrame):
    def __init__(self, master, db, user_info):
        super().__init__(master)
        self.db = db
        self.user_info = user_info
        master.title(f"Главное меню (пользователь: {user_info['username']})")
        master.geometry("400x200+100+100")

        self.incident_btn = ctk.CTkButton(self, text="Управление инцидентами", command=self.open_incident_tracker)
        self.incident_btn.pack(pady=20, padx=20)

        self.incident_window = None

    def open_incident_tracker(self):
        if self.incident_window is None or not self.incident_window.winfo_exists():
            self.incident_window = ctk.CTkToplevel(self)
            self.incident_window.geometry("800x600+150+150")
            self.incident_window.title("Управление инцидентами")
            tracker = IncidentTracker(self.incident_window, self.db, self.user_info)
            tracker.pack(fill="both", expand=True)
        else:
            self.incident_window.lift()
