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


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Инциденты")
        self.geometry("800x600+700+300")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        ensure_data_dir()
        configure_logging()
        self.db = SecureDB("data/incidents.db")

        self.current_frame = None
        self.show_auth()

    def show_auth(self):
        self.clear_frame()
        self.geometry("300x200+700+300")
        self.title("Авторизация")

        def on_success(user_info):
            logging.info(f"Авторизация успешна: {user_info['username']}")
            self.show_main(user_info)

        self.current_frame = AuthDialog(self, self.db, on_success)
        self.current_frame.pack(fill="both", expand=True)

    def show_main(self, user_info):
        self.clear_frame()
        self.geometry("800x600+700+300")
        self.title(f"Инциденты (пользователь: {user_info['username']})")

        self.current_frame = MainWindow(self, self.db, user_info, self.show_auth)
        self.current_frame.pack(fill="both", expand=True)

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

    def on_close(self):
        logging.info("Приложение закрывается.")
        self.destroy()
        sys.exit()


if __name__ == "__main__":
    app = App()
    app.mainloop()
