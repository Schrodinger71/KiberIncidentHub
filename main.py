import logging
import sys
from pathlib import Path

import customtkinter as ctk

from gui.auth import AuthDialog
from gui.main_window import MainWindow
from src.database import SecureDB
from src.logger import configure_logging


def ensure_data_dir():
    Path("data").mkdir(exist_ok=True)

def start_main_app(user_info):
    logging.info(f"Вошёл: {user_info['username']} с ролью {user_info['role']}")

    root = ctk.CTk()
    root.geometry("800x600+100+100")
    root.title(f"Инциденты (пользователь: {user_info['username']})")

    def on_close():
        logging.info("Главное окно закрыто, завершаем программу.")
        root.update_idletasks()
        root.destroy()
        sys.exit()

    root.protocol("WM_DELETE_WINDOW", on_close)

    try:
        app = MainWindow(root, db, user_info)
        app.pack(fill="both", expand=True)
        logging.debug("MainWindow успешно инициализирован")
    except Exception:
        logging.exception("Ошибка при инициализации MainWindow")

    root.mainloop()

def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x+100}+{y+100}")

if __name__ == "__main__":
    ensure_data_dir()
    configure_logging()
    db = SecureDB("data/incidents.db")

    # Окно авторизации
    auth_root = ctk.CTk()
    center_window(auth_root, 300, 200)
    auth_root.title("Авторизация")

    def on_auth_success(user_info):
        logging.info("Авторизация прошла успешно, закрываем окно авторизации.")
        auth_root.withdraw()
        start_main_app(user_info)

    auth_dialog = AuthDialog(auth_root, db, on_auth_success)
    auth_dialog.pack(fill="both", expand=True)
    auth_root.mainloop()
