from tkinter import messagebox
import customtkinter as ctk
from src.database import SecureDB


class IncidentTracker(ctk.CTkFrame):
    def __init__(self, master, db: SecureDB, user_info: dict):
        super().__init__(master)
        self.db = db
        self.user = user_info
        master.title(f"Инциденты (пользователь: {self.user['username']})")
        self.selected_incident_id = None
        self._setup_ui()
        self._load_reference_data()
        self._load_incidents()

    def _setup_ui(self):
        self.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.entry_name = ctk.CTkEntry(self, placeholder_text="Название инцидента")
        self.entry_name.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.status_var = ctk.StringVar()
        self.status_combo = ctk.CTkComboBox(self, variable=self.status_var)
        self.status_combo.grid(row=0, column=1, padx=5, pady=5)

        self.org_var = ctk.StringVar()
        self.org_combo = ctk.CTkComboBox(self, variable=self.org_var)
        self.org_combo.grid(row=0, column=2, padx=5, pady=5)

        self.resp_var = ctk.StringVar()
        self.resp_combo = ctk.CTkComboBox(self, variable=self.resp_var)
        self.resp_combo.grid(row=0, column=3, padx=5, pady=5)

        self.add_button = ctk.CTkButton(self, text="Добавить", command=self._add_incident)
        self.add_button.grid(row=0, column=4, padx=5, pady=5)

        self.edit_button = ctk.CTkButton(self, text="Редактировать", command=self._edit_incident)
        self.edit_button.grid(row=0, column=5, padx=5, pady=5)

        self.delete_button = ctk.CTkButton(self, text="Удалить", fg_color="red", command=self._delete_incident)
        self.delete_button.grid(row=1, column=5, padx=5, pady=5)

        self.search_entry = ctk.CTkEntry(self, placeholder_text="Поиск по названию")
        self.search_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.search_button = ctk.CTkButton(self, text="Поиск", command=self._search_incidents)
        self.search_button.grid(row=1, column=2, padx=5, pady=5)

        self.reset_button = ctk.CTkButton(self, text="Сброс", command=self._load_incidents)
        self.reset_button.grid(row=1, column=3, padx=5, pady=5)

        self.incident_listbox = ctk.CTkScrollableFrame(self, width=700, height=300)
        self.incident_listbox.grid(row=2, column=0, columnspan=6, padx=10, pady=10, sticky="nsew")

    def _load_reference_data(self):
        self.statuses = self.db.get_statuses()
        self.organizations = self.db.get_organizations()
        self.responsibles = self.db.get_responsibles()

        self.status_combo.configure(values=[s[1] for s in self.statuses])
        if self.statuses: self.status_var.set(self.statuses[0][1])

        self.org_combo.configure(values=[o[1] for o in self.organizations])
        if self.organizations: self.org_var.set(self.organizations[0][1])

        self.resp_combo.configure(values=[r[1] for r in self.responsibles])
        if self.responsibles: self.resp_var.set(self.responsibles[0][1])

    def _load_incidents(self, search_term: str = None):
        self._clear_listbox()
        incidents = self.db.get_incidents()
        if search_term:
            incidents = [i for i in incidents if search_term.lower() in i[1].lower()]

        self.incident_widgets = []
        for inc in incidents:
            inc_id, name, date, status_id, org_id, resp_id = inc
            status_name = next((s[1] for s in self.statuses if s[0] == status_id), "Неизвестно")
            org_name = next((o[1] for o in self.organizations if o[0] == org_id), "Неизвестно")
            resp_name = next((r[1] for r in self.responsibles if r[0] == resp_id), "Неизвестно")

            text = f"ID:{inc_id} | {name} | {status_name} | {org_name} | {resp_name}"
            label = ctk.CTkButton(self.incident_listbox, text=text, anchor="w", command=lambda i=inc: self._select_incident(i))
            label.pack(fill="x", pady=2, padx=2)
            self.incident_widgets.append(label)

    def _clear_listbox(self):
        for widget in self.incident_listbox.winfo_children():
            widget.destroy()
        self.selected_incident_id = None

    def _add_incident(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Введите название инцидента")
            return

        status_id = next((s[0] for s in self.statuses if s[1] == self.status_var.get()), None)
        org_id = next((o[0] for o in self.organizations if o[1] == self.org_var.get()), None)
        resp_id = next((r[0] for r in self.responsibles if r[1] == self.resp_var.get()), None)

        self.db.add_incident(название=name, статус_id=status_id, организация_id=org_id, ответственный_id=resp_id)
        messagebox.showinfo("Успех", f"Инцидент '{name}' добавлен")
        self.entry_name.delete(0, 'end')
        self._load_incidents()

    def _select_incident(self, incident_data):
        inc_id, name, _, status_id, org_id, resp_id = incident_data
        self.selected_incident_id = inc_id
        self.entry_name.delete(0, 'end')
        self.entry_name.insert(0, name)
        self.status_var.set(next((s[1] for s in self.statuses if s[0] == status_id), ""))
        self.org_var.set(next((o[1] for o in self.organizations if o[0] == org_id), ""))
        self.resp_var.set(next((r[1] for r in self.responsibles if r[0] == resp_id), ""))

    def _edit_incident(self):
        if not self.selected_incident_id:
            messagebox.showwarning("Выбор", "Выберите инцидент для редактирования")
            return

        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Название не может быть пустым")
            return

        status_id = next((s[0] for s in self.statuses if s[1] == self.status_var.get()), None)
        org_id = next((o[0] for o in self.organizations if o[1] == self.org_var.get()), None)
        resp_id = next((r[0] for r in self.responsibles if r[1] == self.resp_var.get()), None)

        self.db.update_incident(id=self.selected_incident_id, название=name, статус_id=status_id, организация_id=org_id, ответственный_id=resp_id)
        messagebox.showinfo("Готово", "Инцидент обновлён")
        self._load_incidents()

    def _delete_incident(self):
        if not self.selected_incident_id:
            messagebox.showwarning("Выбор", "Сначала выберите инцидент")
            return

        if messagebox.askyesno("Удаление", "Удалить выбранный инцидент?"):
            self.db.delete_incident(self.selected_incident_id)
            self.selected_incident_id = None
            self._load_incidents()
            self.db.log_change(
                username=self.user['username'],
                таблица="Инциденты",
                действие=f"Удалён инцидент с ID {self.selected_incident_id}",
                поле=None,
                старое_значение=None,
                новое_значение=None
            )

    def _search_incidents(self):
        term = self.search_entry.get().strip()
        self._load_incidents(search_term=term)
