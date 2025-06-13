from tkinter import messagebox

import customtkinter as ctk

from src.database import SecureDB


class UserManagerDialog(ctk.CTkToplevel):
    """Диалоговое окно управления пользователями"""
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.title("Управление пользователями")
        self.geometry("500x400")
        self._setup_ui()
        
    def _setup_ui(self):
        """Инициализация интерфейса"""
        self.grid_columnconfigure(0, weight=1)
        
        # Поля ввода
        ctk.CTkLabel(self, text="Создание нового пользователя").grid(row=0, column=0, pady=10)
        
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Логин")
        self.username_entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Пароль", show="*")
        self.password_entry.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        self.role_var = ctk.StringVar(value="user")
        ctk.CTkRadioButton(self, text="Обычный пользователь", variable=self.role_var, value="user").grid(row=3, column=0, sticky="w", padx=20)
        ctk.CTkRadioButton(self, text="Администратор", variable=self.role_var, value="admin").grid(row=4, column=0, sticky="w", padx=20)
        
        # Кнопки
        self.create_btn = ctk.CTkButton(self, text="Создать", command=self._create_user)
        self.create_btn.grid(row=5, column=0, pady=20, padx=20, sticky="ew")
        
    def _create_user(self):
        """Обработчик создания пользователя"""
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
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать пользователя: {str(e)}")
