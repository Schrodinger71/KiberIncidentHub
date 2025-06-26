import customtkinter as ctk
from src.database import SecureDB

class StatusManager(ctk.CTkFrame):
    def __init__(self, master, db: SecureDB, user_info: dict):
        super().__init__(master)
        self.db = db
        self.user_info = user_info
        self._setup_ui()
        self._load_statuses()

    def _setup_ui(self):
        self.entry_status = ctk.CTkEntry(self, placeholder_text="Новый статус")
        self.entry_status.pack(pady=5, padx=10, fill="x")

        self.add_button = ctk.CTkButton(self, text="Добавить", command=self._add_status)
        self.add_button.pack(pady=5, padx=10)

        self.status_list = ctk.CTkScrollableFrame(self)
        self.status_list.pack(fill="both", expand=True, padx=10, pady=10)

    def _load_statuses(self):
        for widget in self.status_list.winfo_children():
            widget.destroy()

        statuses = self.db.get_statuses()
        for status_id, status_text in statuses:
            row_frame = ctk.CTkFrame(self.status_list)
            row_frame.pack(fill="x", padx=5, pady=2)

            label = ctk.CTkLabel(row_frame, text=status_text, anchor="w")
            label.pack(side="left", fill="x", expand=True)

            delete_button = ctk.CTkButton(row_frame, text="Удалить", width=70,
                                          command=lambda sid=status_id, text=status_text: self._delete_status(sid, text))
            delete_button.pack(side="right", padx=5)

    def _add_status(self):
        new_status = self.entry_status.get().strip()
        if new_status:
            self.db.add_status(new_status)
            self.db.log_change(
                username=self.user_info["username"],
                таблица="СтатусыИнцидентов",
                действие=f"Добавлен новый статус: {new_status}",
                поле="статус",
                старое_значение="None",
                новое_значение=new_status
            )
            self.entry_status.delete(0, "end")
            self._load_statuses()

    def _delete_status(self, status_id: int, status_text: str):
        self.db.delete_status(status_id)
        self.db.log_change(
            username=self.user_info["username"],
            таблица="СтатусыИнцидентов",
            действие=f"Удалён статус: {status_text}",
            поле="статус",
            старое_значение=status_text,
            новое_значение="None"
        )
        self._load_statuses()
