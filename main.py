# Copyright 2025 Schrodinger71
# Licensed under the Apache License, Version 2.0 (see LICENSE file)

import logging
import sys
from pathlib import Path
import tkinter.messagebox as mb

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

        # Проверка окружения
        self._check_environment()
        self._ensure_data_dir()
        configure_logging()

        # Строка подключения к SQL Server
        connection_string = env_cfg.POSTGRES_CONNECTION_STRING
        if not connection_string:
            error_msg = "Отсутствует строка подключения к POSTGRES_CONNECTION_STRING:\nPOSTGRES_CONNECTION_STRING"
            mb.showerror("Ошибка конфигурации", error_msg)
            sys.exit(1)

        # Инициализация БД
        self.db = SecureDB(connection_string)
        self.db._start_auto_backup(self)

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
            "POSTGRES_CONNECTION_STRING"
        ]

        missing_vars = [var for var in required_vars if not hasattr(env_cfg, var)]
        if missing_vars:
            error_msg = "Отсутствуют обязательные переменные:\n" + "\n".join(missing_vars)
            mb.showerror("Ошибка конфигурации", error_msg)
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
        except Exception:
            pass
        mb.showerror(
            "Фатальная ошибка",
            f"Приложение завершено с ошибкой:\n{str(e)}"
        )
        sys.exit(1)

        """
        Пример .env
        DB_ENCRYPTION_KEY=a4F_CKss9tTFrC6HBaJ5vRSWwm9wOdWkZTMfkgNgnSc=
        LOG_HMAC_KEY=LKtq1dOWAOeJd6FODT7Zra1ZD-pywb8NtfKiPnhLgrM=
        PASSWORD_HMAC_KEY=X93Y5Ks1cO5eiZL-jPx4tvY0U84mApKRD8P4f5v4f4M=
        POSTGRES_CONNECTION_STRING=host=192.168.10.65 port=5432 dbname=IncidentDB user=postgres password=your_password
        TRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=IncidentDB;UID=sa;PWD=your_password

        """