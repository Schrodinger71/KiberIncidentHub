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
        if user_info["role"] == "admin":
            gradient_start = "#4b0000"
            gradient_end = "#8b0000"
            frame_color = "#3b1e1e"
        else:  # role == 'user'
            gradient_start = "#005f73"
            gradient_end = "#0a9396"
            frame_color = "#023047"

        # Градиентный фон
        self.gradient = GradientFrame(self, gradient_start, gradient_end, width=400, height=320, highlightthickness=0)
        self.gradient.pack(fill="both", expand=True)

        self.inner_frame = ctk.CTkFrame(self.gradient, fg_color=frame_color, width=360, height=280)
        self.inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        master.title(f"Главное меню — {user_info['username']}")
        master.geometry("400x320+700+300")
        master.resizable(False, False)
        master.configure(bg="#0f2027")

        # Шрифты
        self.title_font = ctk.CTkFont(size=22, weight="bold")
        self.button_font = ctk.CTkFont(size=14, weight="bold")

        # Заголовок с лёгкой тенью (через дубликат)
        self.shadow_label = ctk.CTkLabel(
            self.inner_frame,
            text=f"Добро пожаловать, {user_info['username']}!",
            font=self.title_font,
            text_color="#111111"
        )
        self.shadow_label.place(relx=0.5, rely=0.1, anchor="center")

        self.title_label = ctk.CTkLabel(
            self.inner_frame,
            text=f"Добро пожаловать, {user_info['username']}!",
            font=self.title_font,
            text_color="#FFFFFF"
        )
        self.title_label.place(relx=0.5, rely=0.1, anchor="center")

        # Кнопки с иконками (пример с emoji)
        self.incident_btn = ctk.CTkButton(
            self.inner_frame,
            text="🛠 Управление инцидентами",
            fg_color="#4a90e2",
            hover_color="#357ABD",
            text_color="white",
            command=self.open_incident_tracker,
            height=50,
            width=320,
            corner_radius=15,
            font=self.button_font
        )
        self.incident_btn.place(relx=0.5, rely=0.35, anchor="center")

        self.user_btn = ctk.CTkButton(
            self.inner_frame,
            text="👥 Управление пользователями",
            fg_color="#226fc6",
            hover_color="#2D6DAC",
            text_color="white",
            command=self._open_user_manager,
            height=50,
            width=320,
            corner_radius=15,
            font=self.button_font,
            state="normal" if self.user_info['role'] == 'admin' else "disabled"
        )
        self.user_btn.place(relx=0.5, rely=0.55, anchor="center")

        self.logout_btn = ctk.CTkButton(
            self.inner_frame,
            text="🚪 Выйти",
            fg_color="#d9534f",
            hover_color="#c9302c",
            text_color="white",
            command=self.logout,
            height=40,
            corner_radius=15,
            font=self.button_font
        )
        self.logout_btn.place(relx=0.5, rely=0.75, anchor="center")

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

    def logout(self):
        if self.incident_window and self.incident_window.winfo_exists():
            self.incident_window.destroy()
        self.on_logout()
