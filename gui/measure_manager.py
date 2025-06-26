import customtkinter as ctk
from src.database import SecureDB

class MeasureManager(ctk.CTkFrame):
    def __init__(self, master, db: SecureDB, user_info: dict):
        super().__init__(master)
        self.db = db
        self.user_info = user_info
        self._setup_ui()
        self._load_measures()

    def _setup_ui(self):
        self.entry_measure = ctk.CTkEntry(self, placeholder_text="Описание меры реагирования")
        self.entry_measure.pack(pady=5, padx=10, fill="x")

        self.add_button = ctk.CTkButton(self, text="Добавить", command=self._add_measure)
        self.add_button.pack(pady=5, padx=10)

        self.measure_list = ctk.CTkScrollableFrame(self)
        self.measure_list.pack(fill="both", expand=True, padx=10, pady=10)

    def _load_measures(self):
        for widget in self.measure_list.winfo_children():
            widget.destroy()

        measures = self.db.get_response_measures()
        for measure_id, measure_text in measures:
            row_frame = ctk.CTkFrame(self.measure_list)
            row_frame.pack(fill="x", padx=5, pady=2)

            label = ctk.CTkLabel(row_frame, text=measure_text, anchor="w")
            label.pack(side="left", fill="x", expand=True)

            delete_button = ctk.CTkButton(row_frame, text="Удалить", width=70,
                                          command=lambda mid=measure_id, text=measure_text: self._delete_measure(mid, text))
            delete_button.pack(side="right", padx=5)

    def _add_measure(self):
        new_measure = self.entry_measure.get().strip()
        if new_measure:
            self.db.add_response_measure(new_measure)
            self.db.log_change(
                username=self.user_info["username"],
                таблица="МерыРеагирования",
                действие=f"Добавлена новая мера реагирования: {new_measure}",
                поле="описание",
                старое_значение="None",
                новое_значение=new_measure
            )
            self.entry_measure.delete(0, "end")
            self._load_measures()

    def _delete_measure(self, measure_id: int, measure_text: str):
        self.db.delete_response_measure(measure_id)
        self.db.log_change(
            username=self.user_info["username"],
            таблица="МерыРеагирования",
            действие=f"Удалена мера реагирования: {measure_text}",
            поле="описание",
            старое_значение=measure_text,
            новое_значение="None"
        )
        self._load_measures()
