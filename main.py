import sys
import logging
import customtkinter as ctk
from pathlib import Path
from src.database import SecureDB
from src.logger import configure_logging
from gui.auth import AuthDialog
from gui.main_window import IncidentTracker

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
        app = IncidentTracker(root, db, user_info)
        app.pack(fill="both", expand=True)
        logging.debug("IncidentTracker успешно инициализирован")
    except Exception:
        logging.exception("Ошибка при инициализации IncidentTracker")

    root.mainloop()

if __name__ == "__main__":
    ensure_data_dir()
    configure_logging()
    db = SecureDB("data/incidents.db")

    # Сначала окно авторизации
    auth_root = ctk.CTk()
    auth_root.geometry("300x200+200+200")
    auth_root.title("Авторизация")

    def on_auth_success(user_info):
        logging.info("Авторизация прошла успешно, закрываем окно авторизации.")
        auth_root.withdraw()
        start_main_app(user_info)

    auth_dialog = AuthDialog(auth_root, db, on_auth_success)
    auth_dialog.pack(fill="both", expand=True)
    auth_root.mainloop()
