from tkinter import messagebox

import customtkinter as ctk

from gui.incident_tracker import IncidentTracker
from gui.user_manager_window import UserManagerDialog


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
        self.incident_window = None

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
                                   width=400, height=520, highlightthickness=0)
        self.gradient.pack(fill="both", expand=True)

        self.inner_frame = ctk.CTkFrame(self.gradient, fg_color=colors["frame_color"], 
                                      width=360, height=480)
        self.inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        master.title(f"Главное меню — {user_info['username']}")
        master.geometry("400x520+700+300")
        master.resizable(False, False)
        master.configure(bg="#0f2027")

        # Шрифты
        self.title_font = ctk.CTkFont(size=22, weight="bold")
        self.button_font = ctk.CTkFont(size=14, weight="bold")

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self.inner_frame,
            text=f"Добро пожаловать, {user_info['username']}!",
            font=self.title_font,
            text_color="#FFFFFF"
        )
        self.title_label.place(relx=0.5, rely=0.08, anchor="center")

        # Основные кнопки
        button_options = {
            "height": 45,
            "width": 300,
            "corner_radius": 12,
            "font": self.button_font,
            "anchor": "center"
        }

        # Список всех кнопок (и для админа, и для пользователя)
        buttons = [
            {
                "text": "🛠 Управление инцидентами",
                "fg_color": "#4a90e2",
                "hover_color": "#357ABD",
                "command": self.open_incident_tracker,
                "rely": 0.22,
                "admin_only": False
            },
            {
                "text": "🏷 Статусы инцидентов",
                "fg_color": "#5bc0de",
                "hover_color": "#46b8da",
                "command": self.open_statuses_manager,
                "rely": 0.32,
                "admin_only": False
            },
            {
                "text": "🏢 Организации",
                "fg_color": "#5cb85c",
                "hover_color": "#4cae4c",
                "command": self.open_organizations_manager,
                "rely": 0.42,
                "admin_only": False
            },
            {
                "text": "👔 Ответственные",
                "fg_color": "#f0ad4e",
                "hover_color": "#eea236",
                "command": self.open_responsibles_manager,
                "rely": 0.52,
                "admin_only": False
            },
            {
                "text": "👥 Пользователи",
                "fg_color": "#226fc6",
                "hover_color": "#2D6DAC",
                "command": self._open_user_manager,
                "rely": 0.62,
                "admin_only": True
            },
            {
                "text": "🛡 Меры реагирования",
                "fg_color": "#d9534f",
                "hover_color": "#c9302c",
                "command": self.open_measures_manager,
                "rely": 0.72,
                "admin_only": True
            },
            {
                "text": "📜 Журнал изменений",
                "fg_color": "#777777",
                "hover_color": "#5e5e5e",
                "command": self.open_history_viewer,
                "rely": 0.82,
                "admin_only": True
            }
        ]

        # Создаем кнопки
        for btn in buttons:
            button = ctk.CTkButton(
                self.inner_frame,
                text=btn["text"],
                fg_color=btn["fg_color"],
                hover_color=btn["hover_color"],
                text_color="white",
                command=btn["command"],
                state="normal" if (user_info["role"] == "admin" or not btn["admin_only"]) else "disabled",
                **{k: v for k, v in button_options.items() if k != "anchor"}
            )
            if user_info["role"] != "admin" and btn["admin_only"]:
                button.configure(text=btn["text"] + "(Доступ закрыт)")
            button.configure(fg_color="#555555" if user_info["role"] != "admin" and btn["admin_only"] else btn["fg_color"])
            button.place(relx=0.5, rely=btn["rely"], anchor="center")


        # Кнопка выхода
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
        self.logout_btn.place(relx=0.5, rely=0.92, anchor="center")


    def open_incident_tracker(self):
        """Открывает окно управления инцидентами"""
        if self.incident_window is None or not self.incident_window.winfo_exists():
            self.incident_window = ctk.CTkToplevel(self)
            self.incident_window.geometry("800x600+150+150")
            self.incident_window.title("Управление инцидентами")
            tracker = IncidentTracker(self.incident_window, self.db, self.user_info)
            tracker.pack(fill="both", expand=True)
        else:
            self.incident_window.lift()

    def _open_user_manager(self):
        """Открывает окно управления пользователями"""
        if self.user_info['role'] != 'admin':
            messagebox.showwarning("Доступ запрещен", "Требуются права администратора")
            return
        UserManagerDialog(self, self.db, self.user_info)

    def open_statuses_manager(self):
        """Открывает окно управления статусами инцидентов"""
        status_window = ctk.CTkToplevel(self)
        status_window.title("Управление статусами инцидентов")
        status_window.geometry("600x400")
        
        # Здесь реализация интерфейса для работы с таблицей СтатусыИнцидентов
        # ...

    def open_organizations_manager(self):
        """Окно управления организациями"""
        org_window = ctk.CTkToplevel(self)
        org_window.title("Управление организациями")
        org_window.geometry("800x600")
        
        # Реализация работы с таблицей Организации
        # ...

    def open_responsibles_manager(self):
        """Окно управления ответственными лицами"""
        resp_window = ctk.CTkToplevel(self)
        resp_window.title("Управление ответственными")
        resp_window.geometry("900x700")
        
        # Работа с таблицей Ответственные + связь с Организациями
        # ...

    def open_measures_manager(self):
        """Окно управления мерами реагирования"""
        measures_window = ctk.CTkToplevel(self)
        measures_window.title("Меры реагирования")
        measures_window.geometry("600x500")
        
        # Управление таблицей МерыРеагирования
        # ...

    def open_history_viewer(self):
        """Просмотр истории изменений"""
        history_window = ctk.CTkToplevel(self)
        history_window.title("История изменений")
        history_window.geometry("1000x800")
        
        # Отображение данных из ИсторияИзменений
        # ...

    def logout(self):
        if self.incident_window and self.incident_window.winfo_exists():
            self.incident_window.destroy()
        self.on_logout()
