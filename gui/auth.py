import logging
from tkinter import messagebox

import customtkinter as ctk


class AuthDialog(ctk.CTkFrame):
    def __init__(self, master, db, on_success):
        super().__init__(master)
        self.db = db
        self.on_success = on_success

        self.label = ctk.CTkLabel(self, text="Вход")
        self.label.pack(pady=10)

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Имя пользователя")
        self.username_entry.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Пароль", show="*")
        self.password_entry.pack(pady=5)

        self.login_btn = ctk.CTkButton(self, text="Войти", command=self._login)
        self.login_btn.pack(pady=10)

        self.username_entry.focus()

        master.resizable(False, False)

    def _login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user = self.db.get_user(username, password)

        if user:
            logging.info("Успешный вход")
            self.on_success(user)
            self.db.log_change(
                username=username,
                таблица="Система",
                действие=f"Успешный вход",
                поле="Статус",
                старое_значение="Завершено",
                новое_значение="Активен"
            )
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
