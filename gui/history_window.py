import logging
from tkinter import ttk

import customtkinter as ctk


class HistoryViewer(ctk.CTkFrame):
    def __init__(self, master, db_manager, user_info):
        super().__init__(master)
        self.db = db_manager
        self.user = user_info
        
        # Конфигурация сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Для таблицы
        
        self._setup_ui()
        self._load_data()
        
        # Установка заголовка окна
        # master.title(f"Журнал изменений (пользователь: {self.user['username']} | Роль: {self.user['role']})")

    def _setup_ui(self):
        """Настройка интерфейса окна"""
        # Цвета
        BG_COLOR = "#2b2b2b"
        HEADER_COLOR = "#3b3b3b"
        SELECTION_COLOR = "#1f6aa5"
        TEXT_COLOR = "white"
        
        # Frame для фильтров
        filter_frame = ctk.CTkFrame(self)
        filter_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Заголовок фильтров
        ctk.CTkLabel(filter_frame, text="Фильтры:").grid(row=0, column=0, padx=5)
        
        # Фильтр по таблице
        all_tables = self.db.get_all_tables()
        audit_tables = self.db.get_audit_tables()
        
        # Сортируем и делаем уникальными
        tables = sorted(set(all_tables + audit_tables))
        
        self.table_filter = ctk.CTkComboBox(
            filter_frame, 
            values=["Все"] + tables,
            width=180
        )
        self.table_filter.grid(row=0, column=1, padx=5)
        self.table_filter.set("Все")
        
        # Фильтр по пользователю
        self.user_filter = ctk.CTkComboBox(
            filter_frame,
            values=["Все"] + self.db.get_audit_users(),
            width=150
        )
        self.user_filter.grid(row=0, column=2, padx=5)
        self.user_filter.set("Все")
        
        # Фильтр по дате
        self.date_from = ctk.CTkEntry(filter_frame, placeholder_text="От (ГГГГ-ММ-ДД)", width=120)
        self.date_from.grid(row=0, column=3, padx=5)
        self.date_to = ctk.CTkEntry(filter_frame, placeholder_text="До (ГГГГ-ММ-ДД)", width=120)
        self.date_to.grid(row=0, column=4, padx=5)
        
        # Кнопки
        apply_btn = ctk.CTkButton(filter_frame, text="Применить фильтры", command=self._load_data)
        apply_btn.grid(row=0, column=5, padx=5)

        # Таблица данных
        self.tree_frame = ctk.CTkFrame(
            self,
            border_width=1,
            border_color="#3b3b3b"
        )
        self.tree_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        
        # Настройка стиля Treeview
        style = ttk.Style()
        style.theme_use("default")
        
        # Основной стиль таблицы
        style.configure(
            "Treeview",
            background=BG_COLOR,
            foreground=TEXT_COLOR,
            fieldbackground=BG_COLOR,
            bordercolor=HEADER_COLOR,
            borderwidth=0
        )
        
        # Стиль заголовков
        style.configure(
            "Treeview.Heading",
            background=HEADER_COLOR,
            foreground=TEXT_COLOR,
            relief="flat",
            font=('Helvetica', 10, 'bold')
        )
        
        # Стиль выделения
        style.map(
            "Treeview",
            background=[("selected", SELECTION_COLOR)],
            foreground=[("selected", TEXT_COLOR)]
        )
        
        # Стиль скроллбара
        style.configure(
            "Vertical.TScrollbar",
            background=HEADER_COLOR,
            bordercolor=BG_COLOR,
            arrowcolor=TEXT_COLOR,
            troughcolor=BG_COLOR
        )
        
        # Создание Treeview
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("id", "user", "table", "action", "field", "old_val", "new_val", "date"),
            show="headings",
            selectmode="browse",
            style="Treeview"
        )
        
        # Настройка колонок
        columns = [
            ("id", "ID", 20),
            ("user", "Пользователь", 120),
            ("table", "Таблица", 120),
            ("action", "Действие", 160),
            ("field", "Поле", 100),
            ("old_val", "Старое значение", 200),
            ("new_val", "Новое значение", 200),
            ("date", "Дата изменения", 150)
        ]
        
        for col_id, heading, width in columns:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width, anchor="w")
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(
            self.tree_frame,
            orient="vertical",
            command=self.tree.yview,
            style="Vertical.TScrollbar"
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Теги для чередования строк
        self.tree.tag_configure("oddrow", background="#333333")
        self.tree.tag_configure("evenrow", background=BG_COLOR)
        
        # Кнопка обновления
        refresh_btn = ctk.CTkButton(self, text="Обновить данные", command=self._load_data)
        refresh_btn.grid(row=2, column=0, pady=10)

    def _load_data(self):
        """Загрузка данных с учетом фильтров"""
        try:
            table = self.table_filter.get() if self.table_filter.get() != "Все" else None
            user = self.user_filter.get() if self.user_filter.get() != "Все" else None
            
            logs = self.db.get_audit_logs(
                table_filter=table,
                user_filter=user,
                date_from=self.date_from.get() or None,
                date_to=self.date_to.get() or None
            )
            
            self.tree.delete(*self.tree.get_children())
            for log in logs:
                self.tree.insert("", "end", values=log)
                
        except Exception as e:
            logging.error(f"Ошибка загрузки журнала: {e}")
            ctk.CTkMessagebox(
                title="Ошибка",
                message=f"Не удалось загрузить данные журнала:\n{str(e)}",
                icon="cancel"
            )
