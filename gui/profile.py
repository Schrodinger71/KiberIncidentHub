import customtkinter as ctk
import datetime

class ProfileWindow(ctk.CTkFrame):
    """Окно профиля пользователя с отображением имени, роли и времени сессии."""
    def __init__(self, master, db, user_info):
        super().__init__(master)
        self.db = db
        self.user = user_info
        self.start_time = datetime.datetime.now()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Внешняя рамка с отступами и светлой тенью
        self.outer_frame = ctk.CTkFrame(self, fg_color="#2a2d2e", corner_radius=10)
        self.outer_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.outer_frame.grid_columnconfigure(0, weight=1)

        # Заголовок окна
        self.title_label = ctk.CTkLabel(
            self.outer_frame,
            text="Профиль пользователя",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.grid(row=0, column=0, pady=(10, 20))

        # Аватар (emoji)
        self.avatar_label = ctk.CTkLabel(
            self.outer_frame,
            text="🧑‍💻",
            font=ctk.CTkFont(size=48)
        )
        self.avatar_label.grid(row=1, column=0, pady=10)

        # Фрейм с иконками и текстом в две колонки
        info_frame = ctk.CTkFrame(self.outer_frame, fg_color="transparent")
        info_frame.grid(row=2, column=0, pady=10, sticky="ew")
        info_frame.grid_columnconfigure(1, weight=1)  # текст растягивается

        # Переменные для текста
        self.username_var = ctk.StringVar(value=f"Пользователь: {self.user['username']}")
        self.role_var = ctk.StringVar(value=f"Права: {self.user['role']}")
        self.session_time_var = ctk.StringVar(value="Время сессии: 00:00")
        self.date_var = ctk.StringVar(value=f"Сегодня: {datetime.datetime.now().strftime('%d.%m.%Y')}")

        def make_row(row, icon, text_var, font_size=14, text_color=None):
            icon_label = ctk.CTkLabel(info_frame, text=icon, font=ctk.CTkFont(size=16))
            icon_label.grid(row=row, column=0, padx=(0, 10), sticky="w")
            text_label = ctk.CTkLabel(info_frame, textvariable=text_var, font=ctk.CTkFont(size=font_size), anchor="w")
            if text_color:
                text_label.configure(text_color=text_color)
            text_label.grid(row=row, column=1, sticky="w")

        make_row(0, "       👤", self.username_var, font_size=16, text_color="#f1c40f")
        make_row(1, "       🔑", self.role_var, font_size=14, text_color="#3498db")
        make_row(2, "       ⏱", self.session_time_var, font_size=14)
        make_row(3, "       📅", self.date_var, font_size=12)

        # Тултип для времени сессии
        def show_tooltip(event):
            if hasattr(self, 'tooltip') and self.tooltip:
                return
            x = event.widget.winfo_rootx() + 20
            y = event.widget.winfo_rooty() + 20
            self.tooltip = ctk.CTkLabel(
                self,
                text="Время сессии показывает, сколько вы уже в профиле.",
                font=ctk.CTkFont(size=10),
                fg_color="#333333",
                text_color="white",
                corner_radius=5,
                padx=5,
                pady=3
            )
            self.tooltip.place(x=x, y=y)

        def hide_tooltip(event):
            if hasattr(self, 'tooltip') and self.tooltip:
                self.tooltip.destroy()
                self.tooltip = None

        # Найдём label времени и привяжем тултип
        for child in info_frame.winfo_children():
            if isinstance(child, ctk.CTkLabel) and child.cget("textvariable") == str(self.session_time_var):
                child.bind("<Enter>", show_tooltip)
                child.bind("<Leave>", hide_tooltip)
                break

        self.tooltip = None
        self.update_timer()

    def update_timer(self):
        elapsed = datetime.datetime.now() - self.start_time
        minutes, seconds = divmod(elapsed.seconds, 60)
        self.session_time_var.set(f"Время сессии: {minutes:02d}:{seconds:02d}")
        # Обновляем дату каждые 10 минут
        if datetime.datetime.now().minute % 10 == 0:
            self.date_var.set(f"Сегодня: {datetime.datetime.now().strftime('%d.%m.%Y')}")
        self.after(1000, self.update_timer)
