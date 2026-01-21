import logging
from tkinter import ttk

import customtkinter as ctk
import tkinter.messagebox as mb


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
        
        self._start_auto_refresh()
        
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

    def _clean_value(self, value):
        """Очистка значения от проблемных символов для Treeview"""
        if value is None:
            return ""
        
        # Конвертируем в строку
        text = str(value)
        
        # Удаляем все непечатаемые символы, кроме пробелов
        import string
        # Разрешенные символы: печатаемые + кириллица + спецсимволы
        allowed_chars = set(string.printable + 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        text = ''.join(c for c in text if c in allowed_chars)
        
        # Убираем лишние пробелы
        text = ' '.join(text.split())
        
        # Если строка обрамлена кавычками и содержит запятые - убираем кавычки
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            # Проверяем, есть ли внутри запятые
            inner_text = text[1:-1]
            if ',' in inner_text:
                text = inner_text
        
        # Экранируем кавычки внутри строки
        text = text.replace('"', "'")
        
        # Обрезаем слишком длинные строки
        if len(text) > 100:
            text = text[:97] + "..."
        
        return text

    def _safe_insert_log(self, log):
        """Безопасная вставка записи лога в Treeview"""
        try:
            # Проверяем, что log имеет правильное количество элементов
            if len(log) != 8:
                # Если элементов меньше, дополняем пустыми значениями
                log_list = list(log)
                while len(log_list) < 8:
                    log_list.append("")
                log = tuple(log_list)
            
            # Очищаем каждое значение
            cleaned_log = []
            for i, value in enumerate(log):
                cleaned_value = self._clean_value(value)
                cleaned_log.append(cleaned_value)
            
            # Вставляем в таблицу
            row_id = self.tree.insert("", "end", values=tuple(cleaned_log))
            
            # Чередуем цвета строк
            row_count = len(self.tree.get_children())
            tag = "evenrow" if row_count % 2 == 0 else "oddrow"
            self.tree.item(row_id, tags=(tag,))
            
            return True
            
        except Exception as e:
            logging.warning(f"Ошибка вставки записи: {e}, данные: {log}")
            return False

    def _load_data(self):
        """Загрузка данных с учетом фильтров"""
        try:
            # Получаем параметры фильтров
            table = self.table_filter.get() if self.table_filter.get() != "Все" else None
            user = self.user_filter.get() if self.user_filter.get() != "Все" else None
            
            # Получаем логи
            logs = self.db.get_audit_logs(
                table_filter=table,
                user_filter=user,
                date_from=self.date_from.get() or None,
                date_to=self.date_to.get() or None
            )
            
            # Очищаем таблицу
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Счетчики
            success_count = 0
            error_count = 0
            
            # Загружаем данные
            if logs:
                for log in logs:
                    if self._safe_insert_log(log):
                        success_count += 1
                    else:
                        error_count += 1
                
                # Показываем статистику
                if error_count > 0:
                    self.tree.insert("", "end", values=(
                        "", "", "", 
                        f"Загружено: {success_count} записей", 
                        f"Пропущено: {error_count} записей", 
                        "", "", ""
                    ))
            else:
                # Если нет данных
                mb.showinfo("Информация", "Нет данных для отображения")
                
        except Exception as e:
            logging.error(f"Ошибка загрузки журнала: {e}", exc_info=True)
            mb.showerror("Ошибка", f"Не удалось загрузить данные журнала:\n{str(e)}")

    def _start_auto_refresh(self):
        """Автоматическое обновление данных"""
        try:
            self._load_data()
        except Exception as e:
            logging.error(f"Ошибка автообновления: {e}")
        
        # Обновляем каждые 30 секунд
        self.after(30000, self._start_auto_refresh)
