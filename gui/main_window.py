# Copyright 2025 Schrodinger71
# Licensed under the Apache License, Version 2.0 (see LICENSE file)

import logging

import customtkinter as ctk

from gui.history_window import HistoryViewer
from gui.incident_tracker import IncidentTracker
from gui.organization_manager import OrganizationManager
from gui.profile import ProfileWindow
from gui.responsible_manager import ResponsibleManager
from gui.user_manager_window import UserManagerDialogEmbed


class MainWindow(ctk.CTkFrame):
    def __init__(self, master, db, user_info, on_logout):
        super().__init__(master)
        self.db = db
        self.user_info = user_info
        self.on_logout = on_logout

        role_colors = {
            "admin": {
                "bg": "#650606"
            },
            "user": {
                "bg": "#023047"
            }
        }
        colors = role_colors[user_info["role"]]

        master.title(f"Главное меню — {user_info['username']}")
        master.geometry("1150x620+300+100")
        master.resizable(True, True)

        # Цвет фона
        self.configure(fg_color=colors["bg"])
        self.pack(fill="both", expand=True)

        self.title_font = ctk.CTkFont(size=22, weight="bold")
        self.button_font = ctk.CTkFont(size=14, weight="bold")

        # Основной контейнер
        self.inner_frame = ctk.CTkFrame(self, fg_color=colors["bg"], width=760, height=580)
        self.inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self.inner_frame,
            text=f"Добро пожаловать, {user_info['username']}! Ваша роль {user_info['role']}.",
            font=self.title_font,
            text_color="#FFFFFF"
        )
        self.title_label.pack(pady=(15, 5))

        # Вкладки
        self.tabview = ctk.CTkTabview(self.inner_frame, width=720, height=460)
        self.tabview.pack(pady=(5, 5))

        self.tabs_config = [
            {"text": "👤 Профиль", "admin_only": False, "creator": self.create_profile_tab},
            {"text": "🛠 Управление инцидентами", "admin_only": False, "creator": self.create_incident_tab},
            {"text": "🏷 Статусы инцидентов", "admin_only": False, "creator": self.create_statuses_tab},
            {"text": "🏢 Организации", "admin_only": False, "creator": self.create_organizations_tab},
            {"text": "👔 Ответственные", "admin_only": False, "creator": self.create_responsibles_tab},
            {"text": "👥 Пользователи", "admin_only": True, "creator": self.create_users_tab},
            {"text": "🛡 Меры реагирования", "admin_only": True, "creator": self.create_measures_tab},
            {"text": "📜 Журнал изменений", "admin_only": True, "creator": self.create_history_tab},
        ]

        self.tabs = {}

        for tab_conf in self.tabs_config:
            tab_name = tab_conf["text"]
            tab = self.tabview.add(tab_name)
            self.tabs[tab_name] = tab

            if tab_conf["admin_only"] and self.user_info["role"] != "admin":
                label = ctk.CTkLabel(tab, text="Доступ к этой вкладке разрешён только администраторам.",
                                     font=ctk.CTkFont(size=16), text_color="#888888")
                label.pack(expand=True, fill="both", pady=100)
            else:
                tab_conf["creator"](tab)

        self.logout_btn = ctk.CTkButton(
            self.inner_frame,
            text="🚪 Выйти",
            fg_color="#a20505",
            hover_color="#685b5a",
            text_color="white",
            command=self.logout,
            height=40,
            width=200,
            corner_radius=10,
            font=self.button_font
        )
        self.logout_btn.pack(pady=(10, 10), side="bottom")

        self.last_selected_tab = self.tabview.get()

    # Методы создания вкладок
    def create_profile_tab(self, tab):
        self.profile = ProfileWindow(tab, self.db, self.user_info)
        self.profile.pack(fill="both", expand=True)

    def create_incident_tab(self, tab):
        self.incident_tracker = IncidentTracker(tab, self.db, self.user_info)
        self.incident_tracker.pack(fill="both", expand=True)

    def create_statuses_tab(self, tab):
        pass

    def create_organizations_tab(self, tab):
        org_manager = OrganizationManager(tab, self.db, self.user_info)
        org_manager.pack(fill="both", expand=True)

    def create_responsibles_tab(self, tab):
        organizations = self.db.get_organizations()
        self.user_manager = ResponsibleManager(tab, self.db, self.user_info, organizations)
        self.user_manager.pack(fill="both", expand=True)

    def create_users_tab(self, tab):
        self.user_manager = UserManagerDialogEmbed(tab, self.db, self.user_info)
        self.user_manager.pack(fill="both", expand=True)

    def create_measures_tab(self, tab):
        pass

    def create_history_tab(self, tab):
        self.history_viewer = HistoryViewer(tab, self.db, self.user_info)
        self.history_viewer.pack(fill="both", expand=True)

    def logout(self):
        logging.info(f"Пользователь {self.user_info['username']} вышел из системы.")
        self.db.log_change(
            username=self.user_info['username'],
            таблица="Система",
            действие="Выход из системы",
            поле="Статус",
            старое_значение="Активен",
            новое_значение="Завершено"
        )
        self.on_logout()
