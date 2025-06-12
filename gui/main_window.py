import customtkinter as ctk
from src.database import SecureDB

class IncidentTracker(ctk.CTkFrame):
    def __init__(self, master, db: SecureDB, user_info: dict):
        super().__init__(master)
        self.db = db
        self.user = user_info
        master.title(f"Инциденты (пользователь: {self.user['username']})")
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(self, placeholder_text="Название инцидента")
        self.entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.add_button = ctk.CTkButton(self, text="Добавить", command=self._add_incident)
        self.add_button.grid(row=0, column=1, padx=10, pady=10)
    
    def _add_incident(self):
        incident_name = self.entry.get()
        print(f"Добавлен инцидент: {incident_name}")
