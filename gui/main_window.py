import customtkinter as ctk
from tkinter import messagebox
from src.database import SecureDB

class IncidentTracker(ctk.CTkFrame):
    def __init__(self, master, db: SecureDB, user_info: dict):
        super().__init__(master)
        self.db = db
        self.user = user_info
        master.title(f"Инциденты (пользователь: {self.user['username']})")
        self._setup_ui()
        self._load_reference_data()
        self._load_incidents()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Название инцидента
        self.entry_name = ctk.CTkEntry(self, placeholder_text="Название инцидента")
        self.entry_name.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Статус (Combobox)
        self.status_var = ctk.StringVar()
        self.status_combo = ctk.CTkComboBox(self, variable=self.status_var)
        self.status_combo.grid(row=0, column=1, padx=10, pady=10)

        # Организация (Combobox)
        self.org_var = ctk.StringVar()
        self.org_combo = ctk.CTkComboBox(self, variable=self.org_var)
        self.org_combo.grid(row=0, column=2, padx=10, pady=10)

        # Ответственный (Combobox)
        self.resp_var = ctk.StringVar()
        self.resp_combo = ctk.CTkComboBox(self, variable=self.resp_var)
        self.resp_combo.grid(row=0, column=3, padx=10, pady=10)

        # Кнопка Добавить
        self.add_button = ctk.CTkButton(self, text="Добавить инцидент", command=self._add_incident)
        self.add_button.grid(row=0, column=4, padx=10, pady=10)

        # Список инцидентов - простой текст (можно заменить на более сложный виджет)
        self.incident_list = ctk.CTkTextbox(self, width=700, height=300)
        self.incident_list.grid(row=1, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")
        self.incident_list.configure(state="disabled")

    def _load_reference_data(self):
        # Загрузить статусы, организации, ответственных из базы
        self.statuses = self.db.get_statuses()  # [(id, статус), ...]
        self.organizations = self.db.get_organizations()  # [(id, название, ...), ...]
        self.responsibles = self.db.get_responsibles()  # [(id, имя, ...), ...]

        # Заполнить combobox статусами
        status_names = [s[1] for s in self.statuses]
        self.status_combo.configure(values=status_names)
        if status_names:
            self.status_var.set(status_names[0])

        # Заполнить организации
        org_names = [o[1] for o in self.organizations]
        self.org_combo.configure(values=org_names)
        if org_names:
            self.org_var.set(org_names[0])

        # Заполнить ответственных
        resp_names = [r[1] for r in self.responsibles]
        self.resp_combo.configure(values=resp_names)
        if resp_names:
            self.resp_var.set(resp_names[0])

    def _load_incidents(self):
        # Загрузить инциденты из базы и вывести в текстовое поле
        incidents = self.db.get_incidents()
        self.incident_list.configure(state="normal")
        self.incident_list.delete("1.0", "end")
        for inc in incidents:
            inc_id, name, date, status_id, org_id, resp_id = inc

            status_name = next((s[1] for s in self.statuses if s[0] == status_id), "Неизвестно")
            org_name = next((o[1] for o in self.organizations if o[0] == org_id), "Неизвестно")
            resp_name = next((r[1] for r in self.responsibles if r[0] == resp_id), "Неизвестно")

            line = f"ID:{inc_id} | {name} | Статус: {status_name} | Организация: {org_name} | Ответственный: {resp_name}\n"
            self.incident_list.insert("end", line)
        self.incident_list.configure(state="disabled")

    def _add_incident(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Введите название инцидента")
            return

        # Найти id выбранного статуса
        status_id = next((s[0] for s in self.statuses if s[1] == self.status_var.get()), None)
        org_id = next((o[0] for o in self.organizations if o[1] == self.org_var.get()), None)
        resp_id = next((r[0] for r in self.responsibles if r[1] == self.resp_var.get()), None)

        self.db.add_incident(название=name, статус_id=status_id, организация_id=org_id, ответственный_id=resp_id)

        messagebox.showinfo("Успех", f"Инцидент '{name}' добавлен")
        self.entry_name.delete(0, 'end')
        self._load_incidents()
