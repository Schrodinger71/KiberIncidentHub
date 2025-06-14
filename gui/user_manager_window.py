import logging
from tkinter import font as tkfont
from tkinter import messagebox, ttk

import customtkinter as ctk


class UserManagerDialogEmbed(ctk.CTkFrame):
    def __init__(self, master, db, user_info):
        super().__init__(master)
        self.db = db
        self.user_info = user_info
        self._setup_ui()
        self._load_users()

    def _setup_ui(self):
        self.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        # ====== Форма создания пользователя ======
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Логин")
        self.username_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Пароль", show="*")
        self.password_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.role_var = ctk.StringVar(value="user")
        self.role_combo = ctk.CTkComboBox(self, variable=self.role_var, values=["user", "admin"])
        self.role_combo.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.create_btn = ctk.CTkButton(self, text="Создать", command=self._create_user)
        self.create_btn.grid(row=0, column=3, padx=5, pady=5)

        self.refresh_btn = ctk.CTkButton(self, text="Обновить", command=self._load_users)
        self.refresh_btn.grid(row=0, column=4, padx=5, pady=5)

        # ====== Заголовок ======
        ctk.CTkLabel(self, text="Пользователи (двойной клик — редактирование)",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=1, column=0, columnspan=6, padx=10, pady=(5, 5))

        # ====== Таблица пользователей ======
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=2, column=0, columnspan=6, padx=10, pady=10, sticky="nsew")
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)

        # Treeview
        self.tree = ttk.Treeview(self.table_frame, columns=("username", "role"), show="headings")
        self.tree.heading("username", text="Логин")
        self.tree.heading("role", text="Роль")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # ====== Стили Treeview ======
        tree_font = tkfont.nametofont("TkDefaultFont").copy()
        tree_font.configure(size=14, family="Segoe UI")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        font=tree_font,
                        rowheight=36,
                        background="#2b2b2b",
                        foreground="white",
                        fieldbackground="#2b2b2b",
                        bordercolor="#2b2b2b",
                        borderwidth=0)

        style.configure("Treeview.Heading",
                        font=("Segoe UI", 16, "bold"),
                        background="#444",
                        foreground="white")

        style.map("Treeview",
                  background=[("selected", "#555")],
                  foreground=[("selected", "white")])

        self.tree = ttk.Treeview(self.table_frame, columns=("username", "role"), show="headings", height=8)
        self.tree.heading("username", text="Логин")
        self.tree.heading("role", text="Роль")
        self.tree.column("username", anchor="center", width=200)
        self.tree.column("role", anchor="center", width=100)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self._on_edit_user)

        # ====== Кнопка удаления ======
        self.delete_btn = ctk.CTkButton(self, text="Удалить выбранного", command=self._delete_selected_user)
        self.delete_btn.grid(row=3, column=0, pady=10, padx=20, sticky="ew")

    def _create_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = self.role_var.get()

        if not username or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля")
            return

        try:
            self.db.add_user(username, password, role)
            messagebox.showinfo("Успех", f"Пользователь {username} создан")
            self.username_entry.delete(0, 'end')
            self.password_entry.delete(0, 'end')
            self._load_users()
            self.db.log_change(
                username=self.user_info["username"],
                таблица="users",
                действие=f"Создание пользователя {username} с ролью {role}",
                поле="Все",
                старое_значение="None",
                новое_значение="None"
            )
            logging.info(f"Создание пользователя {username} с ролью {role}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать пользователя: {str(e)}")

    def _load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        users = self.db.get_all_users()
        for user in users:
            self.tree.insert("", "end", values=(user["username"], user["role"]))

    def _delete_selected_user(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите пользователя для удаления")
            return

        username = self.tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Подтверждение", f"Удалить пользователя {username}?"):
            try:
                self.db.delete_user(username)
                self._load_users()
                self.db.log_change(
                    username=self.user_info["username"],
                    таблица="users",
                    действие=f"Удаление пользователя {username}",
                    поле="Все",
                    старое_значение="Существовал",
                    новое_значение="Удалён"
                )
                logging.info(f"Удаление пользователя {username}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _on_edit_user(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        username, current_role = self.tree.item(selected[0])["values"]

        def save_changes():
            new_password = password_entry.get()
            new_role = role_var.get()

            try:
                if new_password:
                    self.db.change_user_password(username, new_password)
                    self.db.log_change(
                        username=self.user_info["username"],
                        таблица="users",
                        действие=f"Изменение пароля пользователя {username}",
                        поле="password",
                        старое_значение="Старый пароль скрыт",
                        новое_значение="Новый пароль скрыт"
                    )
                    logging.info(f"Изменение пароля пользователя {username}")

                if new_role != current_role:
                    self.db.change_user_role(username, new_role)
                    self.db.log_change(
                        username=self.user_info["username"],
                        таблица="users",
                        действие=f"Изменение роли пользователя {username}",
                        поле="role",
                        старое_значение=current_role,
                        новое_значение=new_role
                    )
                    logging.info(f"Изменение роли пользователя {username}: {current_role} -> {new_role}")

                messagebox.showinfo("Готово", f"Данные пользователя {username} обновлены")
                self._load_users()
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"Редактировать: {username}")
        edit_win.geometry("300x200")

        ctk.CTkLabel(edit_win, text="Новый пароль (необязательно)").pack(pady=(10, 5))
        password_entry = ctk.CTkEntry(edit_win, show="*")
        password_entry.pack(pady=5)

        role_var = ctk.StringVar(value=current_role)
        ctk.CTkRadioButton(edit_win, text="Обычный пользователь", variable=role_var, value="user").pack(anchor="w", padx=20)
        ctk.CTkRadioButton(edit_win, text="Администратор", variable=role_var, value="admin").pack(anchor="w", padx=20)

        ctk.CTkButton(edit_win, text="Сохранить", command=save_changes).pack(pady=15)