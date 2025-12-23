# Copyright 2025 Schrodinger71
# Licensed under the Apache License, Version 2.0 (see LICENSE file)

import logging
import sys
from pathlib import Path

import customtkinter as ctk

from config import env_cfg
from gui.auth import AuthDialog
from gui.main_window import MainWindow
from src.database import SecureDB
from src.logger import configure_logging


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._initialize_app()
        self._setup_ui()
        
    def _initialize_app(self):
        """Инициализация приложения"""
        self.title("KiberIncidentHub")
        self.geometry("800x600+700+300")
        self.protocol("WM_DELETE_WINDOW", self._on_app_close)
        
        # Настройка окружения
        self._check_environment()
        self._ensure_data_dir()
        configure_logging()
        
        """
        # Локальный SQL Server
        SQL_SERVER_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=IncidentDB;UID=sa;PWD=your_password

        # SQL Server на конкретном порту
        SQL_SERVER_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=IncidentDB;UID=sa;PWD=your_password

        # SQL Server с Windows Authentication
        SQL_SERVER_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=IncidentDB;Trusted_Connection=yes;

        # Удалённый SQL Server
        SQL_SERVER_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=your-server-name.database.windows.net;DATABASE=IncidentDB;UID=your_username;PWD=your_password


        # Ключи шифрования (обязательные)
        DB_ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
        LOG_HMAC_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
        PASSWORD_HMAC_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
        # Строка подключения к SQL Server (обязательная)
        SQL_SERVER_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=IncidentDB;UID=sa;PWD=your_password

        """
        # Подключение к SQL Server
        # Строка подключения берётся из конфигурации или переменной окружения
        connection_string = env_cfg.get('SQL_SERVER_CONNECTION_STRING')
        if not connection_string:
            error_msg = "Отсутствует строка подключения к SQL Server: SQL_SERVER_CONNECTION_STRING"
            ctk.CTkMessagebox(
                title="Ошибка конфигурации",
                message=error_msg,
                icon="cancel"
            )
            sys.exit(1)

        # Инициализация БД с подключением к SQL Server
        self.db = SecureDB(connection_string)
        self.db._start_auto_backup(self) # Запускаем автобэкап БД

        self.current_frame = None
        
    def _setup_ui(self):
        """Начальная настройка интерфейса"""
        self.show_auth()

    def _check_environment(self):
        """Проверка обязательных переменных окружения"""
        required_vars = [
            "DB_ENCRYPTION_KEY",
            "LOG_HMAC_KEY", 
            "PASSWORD_HMAC_KEY",
            "SQL_SERVER_CONNECTION_STRING"  # Добавляем обязательную переменную для SQL Server
        ]
        
        missing_vars = [var for var in required_vars if not hasattr(env_cfg, var)]
        if missing_vars:
            error_msg = "Отсутствуют обязательные переменные:\n" + "\n".join(missing_vars)
            ctk.CTkMessagebox(
                title="Ошибка конфигурации",
                message=error_msg,
                icon="cancel"
            )
            sys.exit(1)

    def _ensure_data_dir(self):
        """Создание директории для данных"""
        Path("data").mkdir(exist_ok=True)

    def show_auth(self):
        """Показать окно авторизации"""
        self._clear_frame()
        self.geometry("300x200+700+300")
        self.title("Авторизация")

        def on_success(user_info):
            logging.info(f"Успешная авторизация: {user_info['username']}")
            self.show_main(user_info)

        self.current_frame = AuthDialog(self, self.db, on_success)
        self.current_frame.pack(fill="both", expand=True)

    def show_main(self, user_info):
        """Показать главное окно"""
        self._clear_frame()
        self.geometry("1150x620+300+100")
        self.title(f"KiberIncidentHub - {user_info['username']}")

        self.current_frame = MainWindow(self, self.db, user_info, self.show_auth)
        self.current_frame.pack(fill="both", expand=True)

    def _clear_frame(self):
        """Очистка текущего фрейма"""
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

    def _on_app_close(self):
        """Обработчик закрытия приложения"""
        logging.info("Завершение работы приложения")
        
        # Логирование выхода, если есть активный пользователь
        if hasattr(self, 'current_frame') and hasattr(self.current_frame, 'user_info'):
            try:
                self.db.log_change(
                    username=self.current_frame.user_info['username'],
                    таблица="Система",
                    действие="Выход из системы",
                    поле="Статус",
                    старое_значение="Активен",
                    новое_значение="Завершено"
                )
            except Exception as e:
                logging.error(f"Ошибка логирования выхода: {e}")

        # Закрываем соединение с SQL Server
        self.db.close()

        self.destroy()
        sys.exit()

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        logging.critical(f"Критическая ошибка: {e}", exc_info=True)
        try:
            app.db.close()
        except:
            pass
        ctk.CTkMessagebox(
            title="Фатальная ошибка",
            message=f"Приложение завершено с ошибкой:\n{str(e)}",
            icon="cancel"
        )
        sys.exit(1)
