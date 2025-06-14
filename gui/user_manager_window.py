import logging
from tkinter import font as tkfont
from tkinter import messagebox, ttk

import customtkinter as ctk


class UserManagerDialog(ctk.CTkToplevel):
    def __init__(self, master, db, user_info):
        super().__init__(master)
        self.db = db
        self.title("Управление пользователями")
        self.geometry("700x650")
        self._setup_ui()
        self._load_users()
        self.user_info = user_info

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # ====== Фрейм создания пользователя ======
        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form_frame, text="Создать нового пользователя", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=(10, 5))

        self.username_entry = ctk.CTkEntry(form_frame, placeholder_text="Логин")
        self.username_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.password_entry = ctk.CTkEntry(form_frame, placeholder_text="Пароль", show="*")
        self.password_entry.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.role_var = ctk.StringVar(value="user")
        roles_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        roles_frame.grid(row=3, column=0, pady=5, sticky="w", padx=10)
        ctk.CTkRadioButton(roles_frame, text="Обычный пользователь", variable=self.role_var, value="user").pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(roles_frame, text="Администратор", variable=self.role_var, value="admin").pack(side="left")

        self.create_btn = ctk.CTkButton(form_frame, text="Создать", command=self._create_user)
        self.create_btn.grid(row=4, column=0, pady=10, padx=10, sticky="ew")

        # ====== Разделитель ======
        ctk.CTkLabel(self, text="Список пользователей\n(двойной клик для редактирования)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=1, column=0, pady=(10, 5))

        # ====== Таблица пользователей ======
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)



        style = ttk.Style()
        style.theme_use("clam")

        tree_font = tkfont.Font(family="Segoe UI", size=12)

        style.configure("Treeview",
                        font=tree_font,
                        background="#2b2b2b",     # Тёмный фон строк
                        foreground="white",        # Белый текст
                        fieldbackground="#2b2b2b", # Тёмный фон для пустых областей
                        rowheight=36,
                        bordercolor="#2b2b2b",
                        borderwidth=0)

        style.configure("Treeview.Heading",
                        font=("Segoe UI", 13, "bold"),
                        background="#444",
                        foreground="white")

        style.map("Treeview",
                background=[("selected", "#555")],      # Фон выбранной строки
                foreground=[("selected", "white")])     # Текст выбранной строки (белый)

        self.tree = ttk.Treeview(table_frame, columns=("username", "role"), show="headings", height=8)
        self.tree.heading("username", text="Логин")
        self.tree.heading("role", text="Роль")
        self.tree.column("username", anchor="w", width=200)
        self.tree.column("role", anchor="center", width=100)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
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