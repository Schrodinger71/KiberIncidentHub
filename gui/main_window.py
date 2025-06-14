import logging
from tkinter import messagebox

import customtkinter as ctk

from gui.history_window import HistoryViewer
from gui.incident_tracker import IncidentTracker
from gui.user_manager_window import UserManagerDialogEmbed


class GradientFrame(ctk.CTkCanvas):
    def __init__(self, master, color1, color2, **kwargs):
        kwargs.setdefault('bg', master["bg"])
        kwargs.setdefault('highlightthickness', 0)
        super().__init__(master, **kwargs)
        self.color1 = color1
        self.color2 = color2
        self.bind("<Configure>", self._draw_gradient)

    def _draw_gradient(self, event=None):
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        limit = height
        (r1, g1, b1) = self.winfo_rgb(self.color1)
        (r2, g2, b2) = self.winfo_rgb(self.color2)
        r_ratio = float(r2 - r1) / limit
        g_ratio = float(g2 - g1) / limit
        b_ratio = float(b2 - b1) / limit
        for i in range(limit):
            nr = int(r1 + (r_ratio * i)) >> 8
            ng = int(g1 + (g_ratio * i)) >> 8
            nb = int(b1 + (b_ratio * i)) >> 8
            color = f"#{nr:02x}{ng:02x}{nb:02x}"
            self.create_line(0, i, width, i, tags=("gradient",), fill=color)
        self.lower("gradient")


class MainWindow(ctk.CTkFrame):
    def __init__(self, master, db, user_info, on_logout):
        super().__init__(master)
        self.db = db
        self.user_info = user_info
        self.on_logout = on_logout

        # Цвета по ролям
        role_colors = {
            "admin": {
                "gradient_start": "#4b0000",
                "gradient_end": "#8b0000",
                "frame_color": "#3b1e1e"
            },
            "user": {
                "gradient_start": "#005f73",
                "gradient_end": "#0a9396",
                "frame_color": "#023047"
            }
        }
        colors = role_colors[user_info["role"]]

        # Градиентный фон
        self.gradient = GradientFrame(self, colors["gradient_start"], colors["gradient_end"], 
                                      width=800, height=620, highlightthickness=0)
        self.gradient.pack(fill="both", expand=True)

        # Основной контейнер
        self.inner_frame = ctk.CTkFrame(self.gradient, fg_color=colors["frame_color"], width=760, height=580)
        self.inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        master.title(f"Главное меню — {user_info['username']}")
        master.geometry("1100x620+300+100")
        master.resizable(True, True)
        master.configure(bg="#0f2027")

        self.title_font = ctk.CTkFont(size=22, weight="bold")
        self.button_font = ctk.CTkFont(size=14, weight="bold")

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
        self.tabview.pack(pady=(10, 10))

        # Описание вкладок
        self.tabs_config = [
            {"text": "🛠 Управление инцидентами", "admin_only": False, "creator": self.create_incident_tab},
            {"text": "🏷 Статусы инцидентов", "admin_only": False, "creator": self.create_statuses_tab},
            {"text": "🏢 Организации", "admin_only": False, "creator": self.create_organizations_tab},
            {"text": "👔 Ответственные", "admin_only": False, "creator": self.create_responsibles_tab},
            {"text": "👥 Пользователи", "admin_only": True, "creator": self.create_users_tab},
            {"text": "🛡 Меры реагирования", "admin_only": True, "creator": self.create_measures_tab},
            {"text": "📜 Журнал изменений", "admin_only": True, "creator": self.create_history_tab},
        ]

        self.tabs = {}  # сохраняем вкладки

        # Создаем вкладки и наполняем
        for tab_conf in self.tabs_config:
            tab_name = tab_conf["text"]
            tab = self.tabview.add(tab_name)
            self.tabs[tab_name] = tab

            if tab_conf["admin_only"] and self.user_info["role"] != "admin":
                # Для не-админа - показываем заглушку
                label = ctk.CTkLabel(tab, text="Доступ к этой вкладке разрешён только администраторам.",
                                     font=ctk.CTkFont(size=16), text_color="#888888")
                label.pack(expand=True, fill="both", pady=100)
            else:
                # Админ или обычная вкладка - вызываем функцию создания содержимого
                tab_conf["creator"](tab)

        # Создаем кнопку выхода
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

        # Обработка попытки переключения на вкладки с admin_only при не-админе
        self.last_selected_tab = self.tabview.get()
        if self.user_info["role"] != "admin":
            self.check_tab_change()

    def check_tab_change(self):
        current_tab = self.tabview.get()
        if current_tab != self.last_selected_tab:
            # Найдем вкладку в конфиге
            for tab_conf in self.tabs_config:
                if tab_conf["text"] == current_tab and tab_conf["admin_only"]:
                    # Вернуть назад
                    self.tabview.set(self.tabs_config[0]["text"])
                    messagebox.showwarning("Доступ запрещён", "Доступ к этой вкладке разрешён только администраторам.")
                    break
            self.last_selected_tab = self.tabview.get()
        self.after(100, self.check_tab_change)

    # Методы для создания содержимого вкладок для админа/пользователя
    def create_incident_tab(self, tab):
        self.incident_tracker = IncidentTracker(tab, self.db, self.user_info)
        self.incident_tracker.pack(fill="both", expand=True)

    def create_statuses_tab(self, tab):
        # Здесь добавь UI для статусов
        pass

    def create_organizations_tab(self, tab):
        # Здесь добавь UI для организаций
        pass

    def create_responsibles_tab(self, tab):
        # Здесь добавь UI для ответственных
        pass

    def create_users_tab(self, tab):
        self.user_manager = UserManagerDialogEmbed(tab, self.db, self.user_info)
        self.user_manager.pack(fill="both", expand=True)

    def create_measures_tab(self, tab):
        # Здесь добавь UI для мер реагирования
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
            старое_значение="None",
            новое_значение="None"
        )
        self.on_logout()
