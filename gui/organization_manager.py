from tkinter import ttk
import customtkinter as ctk

from src.database import SecureDB


class OrganizationManager(ctk.CTkFrame):
    def __init__(self, master, db: SecureDB, user_info: dict):
        super().__init__(master)
        self.db = db
        self.user = user_info
        self.selected_org_id = None
        self._setup_ui()
        self._load_organizations()
        self._update_ui_permissions()
        self._start_auto_refresh()

    def _setup_ui(self):
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Название")
        self.name_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.address_entry = ctk.CTkEntry(self, placeholder_text="Адрес")
        self.address_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.phone_entry = ctk.CTkEntry(self, placeholder_text="Контактный телефон")
        self.phone_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.add_button = ctk.CTkButton(self, text="Добавить", command=self._add_organization)
        self.add_button.grid(row=0, column=3, padx=5, pady=5)

        self.edit_button = ctk.CTkButton(self, text="Редактировать", command=self._edit_organization)
        self.edit_button.grid(row=1, column=2, padx=5, pady=5)

        self.delete_button = ctk.CTkButton(self, text="Удалить", fg_color="red", command=self._delete_organization)
        self.delete_button.grid(row=1, column=3, padx=5, pady=5)

        self.tree = ttk.Treeview(self, columns=("Название", "Адрес", "Телефон"), show="headings")
        self.tree.heading("Название", text="Название")
        self.tree.heading("Адрес", text="Адрес")
        self.tree.heading("Телефон", text="Телефон")
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
        readonly = "normal" if is_admin else "disabled"

        self.edit_button.configure(state=readonly)
        self.delete_button.configure(state=readonly)

        self.name_entry.configure(state="normal")
        self.address_entry.configure(state="normal")
        self.phone_entry.configure(state="normal")

    def _start_auto_refresh(self):
        self._load_organizations()
        self.after(10000, self._start_auto_refresh)

    def _load_organizations(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for org in self.db.get_organizations():
            self.tree.insert("", "end", iid=org[0], values=org[1:])

    def _on_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.selected_org_id = int(selected[0])
            values = self.tree.item(selected[0])['values']
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, values[0])
            self.address_entry.delete(0, "end")
            self.address_entry.insert(0, values[1])
            self.phone_entry.delete(0, "end")
            self.phone_entry.insert(0, "+" + str(values[2]))

    def _add_organization(self):
        name = self.name_entry.get().strip()
        address = self.address_entry.get().strip()
        phone = self.phone_entry.get().strip()
        if name:
            self.db.add_organization(name, address, phone)
            self.db.log_change(
                username=self.user['username'],
                таблица="Организации",
                действие="Добавление",
                поле="Все",
                старое_значение="",
                новое_значение=str({
                    'название': name,
                    'адрес': address,
                    'телефон': phone
                })
            )
            self._load_organizations()

    def _edit_organization(self):
        if self.selected_org_id:
            name = self.name_entry.get().strip()
            address = self.address_entry.get().strip()
            phone = self.phone_entry.get().strip()

            old_org = self.db.get_organization_by_id(self.selected_org_id)
            if not old_org:
                return

            old_data = {
                'название': old_org[1],
                'адрес': old_org[2],
                'телефон': str(old_org[3])
            }

            new_data = {
                'название': name,
                'адрес': address,
                'телефон': phone
            }

            changes = [k for k in old_data if old_data[k] != new_data[k]]
            if changes:
                self.db.update_organization(self.selected_org_id, name, address, phone)
                self.db.log_change(
                    username=self.user['username'],
                    таблица="Организации",
                    действие="Редактирование",
                    поле="; ".join(changes),
                    старое_значение=str(old_data),
                    новое_значение=str(new_data)
                )
                self._load_organizations()

    def _delete_organization(self):
        if self.selected_org_id:
            org = self.db.get_organization_by_id(self.selected_org_id)
            if org:
                old_data = {
                    'название': org[1],
                    'адрес': org[2],
                    'телефон': str(org[3])
                }
                self.db.delete_organization(self.selected_org_id)
                self.db.log_change(
                    username=self.user['username'],
                    таблица="Организации",
                    действие="Удаление",
                    поле="Все",
                    старое_значение=str(old_data),
                    новое_значение=""
                )
                self._load_organizations()
                self.selected_org_id = None
