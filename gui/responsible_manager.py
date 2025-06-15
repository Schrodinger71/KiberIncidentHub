from tkinter import ttk

import customtkinter as ctk


class ResponsibleManager(ctk.CTkFrame):
    def __init__(self, master, db, user_info, organizations):
        super().__init__(master)
        self.db = db
        self.user = user_info
        self.organizations = organizations  # список организаций (id, название)
        self.selected_resp_id = None
        self._setup_ui()
        self._load_responsibles()
        self._update_ui_permissions()
        self._start_auto_refresh()

    def _setup_ui(self):
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Имя")
        self.name_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.position_entry = ctk.CTkEntry(self, placeholder_text="Должность")
        self.position_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email")
        self.email_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # CTkComboBox для выбора организации
        self.org_var = ctk.StringVar()
        org_names = [org[1] for org in self.organizations]
        self.org_combobox = ctk.CTkComboBox(self, variable=self.org_var, values=org_names, state="readonly")
        self.org_combobox.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        if org_names:
            self.org_combobox.set(org_names[0])

        self.add_button = ctk.CTkButton(self, text="Добавить", command=self._add_responsible)
        self.add_button.grid(row=1, column=0, padx=5, pady=5)

        self.edit_button = ctk.CTkButton(self, text="Редактировать", command=self._edit_responsible)
        self.edit_button.grid(row=1, column=1, padx=5, pady=5)

        self.delete_button = ctk.CTkButton(self, text="Удалить", fg_color="red", command=self._delete_responsible)
        self.delete_button.grid(row=1, column=2, padx=5, pady=5)

        self.tree = ttk.Treeview(self, columns=("Имя", "Должность", "Email", "Организация"), show="headings")
        for col in ("Имя", "Должность", "Email", "Организация"):
            self.tree.heading(col, text=col)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

        # Стиль таблицы
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        fieldbackground="#2b2b2b",
                        rowheight=25)
        style.map("Treeview", background=[('selected', '#444444')])

    def _update_ui_permissions(self):
        is_admin = self.user['role'] == 'admin'
        state_edit = "normal" if is_admin else "disabled"

        self.edit_button.configure(state=state_edit)
        self.delete_button.configure(state=state_edit)

        # Все могут вводить данные
        self.name_entry.configure(state="normal")
        self.position_entry.configure(state="normal")
        self.email_entry.configure(state="normal")
        self.org_combobox.configure(state="readonly")
        self.organizations = self.db.get_organizations()
        org_names = [org[1] for org in self.organizations]
        self.org_combobox.configure(values=org_names)

        # Если текущий выбранный элемент отсутствует — установить первый
        if org_names:
            current_value = self.org_var.get()
            if current_value not in org_names:
                self.org_var.set(org_names[0])

    def _start_auto_refresh(self):
        self._update_ui_permissions()
        self._load_responsibles()
        self.after(10000, self._start_auto_refresh)

    def _load_responsibles(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        responsibles = self.db.get_responsibles()
        for resp in responsibles:
            # resp = (id, имя, должность, email, орг_id)
            org_name = next((org[1] for org in self.organizations if org[0] == resp[4]), "Неизвестно")
            self.tree.insert("", "end", iid=resp[0], values=(resp[1], resp[2] or "-", resp[3] or "-", org_name))

    def _on_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.selected_resp_id = int(selected[0])
            values = self.tree.item(selected[0])['values']
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, values[0])
            self.position_entry.delete(0, "end")
            self.position_entry.insert(0, values[1] if values[1] != "-" else "")
            self.email_entry.delete(0, "end")
            self.email_entry.insert(0, values[2] if values[2] != "-" else "")
            # Выбрать организацию в комбобоксе
            if values[3] in self.org_combobox.cget("values"):
                self.org_combobox.set(values[3])
            else:
                self.org_combobox.set("")

    def _add_responsible(self):
        имя = self.name_entry.get().strip()
        должность = self.position_entry.get().strip() or None
        email = self.email_entry.get().strip() or None
        org_name = self.org_var.get()
        организация_id = next((org[0] for org in self.organizations if org[1] == org_name), None)

        if имя:
            self.db.add_responsible(имя, должность, email, организация_id)
            self.db.log_change(
                username=self.user['username'],
                таблица="Ответственные",
                действие="Добавление",
                поле="Все",
                старое_значение="",
                новое_значение=str({
                    'имя': имя,
                    'должность': должность,
                    'email': email,
                    'организация_id': организация_id
                })
            )
            self._load_responsibles()

    def _edit_responsible(self):
        if not self.selected_resp_id:
            return

        имя = self.name_entry.get().strip()
        должность = self.position_entry.get().strip() or None
        email = self.email_entry.get().strip() or None
        org_name = self.org_var.get()
        организация_id = next((org[0] for org in self.organizations if org[1] == org_name), None)

        old_resp = self.db.get_responsible_by_id(self.selected_resp_id)
        if not old_resp:
            return

        old_data = {
            'имя': old_resp[1],
            'должность': old_resp[2],
            'email': old_resp[3],
            'организация_id': old_resp[4]
        }
        new_data = {
            'имя': имя,
            'должность': должность,
            'email': email,
            'организация_id': организация_id
        }
        changes = [k for k in old_data if old_data[k] != new_data[k]]
        if changes:
            self.db.update_responsible(self.selected_resp_id, имя, должность, email, организация_id)
            self.db.log_change(
                username=self.user['username'],
                таблица="Ответственные",
                действие="Редактирование",
                поле="; ".join(changes),
                старое_значение=str(old_data),
                новое_значение=str(new_data)
            )
            self._load_responsibles()

    def _delete_responsible(self):
        if not self.selected_resp_id:
            return
        old_resp = self.db.get_responsible_by_id(self.selected_resp_id)
        if old_resp:
            old_data = {
                'имя': old_resp[1],
                'должность': old_resp[2],
                'email': old_resp[3],
                'организация_id': old_resp[4]
            }
            self.db.delete_responsible(self.selected_resp_id)
            self.db.log_change(
                username=self.user['username'],
                таблица="Ответственные",
                действие="Удаление",
                поле="Все",
                старое_значение=str(old_data),
                новое_значение=""
            )
            self._load_responsibles()
            self.selected_resp_id = None
