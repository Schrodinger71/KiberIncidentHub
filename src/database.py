# Copyright 2025 Schrodinger71
# Licensed under the Apache License, Version 2.0 (see LICENSE file)

import logging
import os
import pyodbc
import datetime
from pathlib import Path
import shutil
import hashlib
import base64

from src.crypto import CryptoManager


class SecureDB:
    backups_dir = Path("backups")

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.crypto = CryptoManager()
        self.conn = None
        self._connect()

        if not self._check_if_database_exists():
            logging.warning("База данных SQL Server не найдена или пуста. Будет инициализирована новая.")
            self._init_schema()
            self._init_db()
        else:
            logging.info("Подключение к существующей базе данных SQL Server")

    def _connect(self):
        """Устанавливает соединение с SQL Server"""
        try:
            self.conn = pyodbc.connect(self.connection_string)
            self.conn.autocommit = False  # Для транзакций
        except Exception as e:
            logging.error(f"Ошибка подключения к SQL Server: {e}")
            raise

    def _check_if_database_exists(self):
        """Проверяет, существуют ли таблицы в базе данных"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            return table_count > 0
        except Exception:
            return False

    def _start_auto_backup(self, root):
        self._create_backup("auto")
        root.after(300000, lambda: self._start_auto_backup(root))

    def _create_backup(self, prefix: str):
        """Создаёт бэкап с датой в папку backups"""
        if not self.backups_dir.exists():
            self.backups_dir.mkdir(parents=True)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"{prefix}_backup_{timestamp}.sql"
        backup_path = self.backups_dir / backup_filename

        # Для SQL Server нужно использовать другие методы бэкапа
        # Это упрощённый вариант - сохраняем SQL-скрипт структуры и данных
        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                # Здесь можно добавить экспорт структуры и данных
                f.write("-- SQL Server Backup\n")
                f.write("-- Создано: " + datetime.datetime.now().isoformat() + "\n")
            logging.info(f"Создан бэкап БД: {backup_path}")
        except Exception as e:
            logging.error(f"Ошибка при создании бэкапа: {e}")

    def close(self):
        if self.conn:
            try:
                self.conn.commit()
            except Exception as e:
                logging.error(f"Ошибка при коммите БД: {e}")
            
            # Создаём бэкап при закрытии
            self._create_backup("shutdown")
            
            self.conn.close()
            logging.info("Соединение с БД закрыто")
        else:
            logging.warning("Соединение с БД уже было закрыто или не создано")

    def _init_schema(self):
        """Создаёт таблицу пользователей"""
        cursor = self.conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
            CREATE TABLE users (
                username NVARCHAR(255) PRIMARY KEY,
                password_hash NVARCHAR(255) NOT NULL,
                role NVARCHAR(50) NOT NULL CHECK (role IN ('admin', 'user'))
            );
        """)
        self.conn.commit()

    def _seed_initial_data(self):
        """Заполняет начальные справочники"""
        cursor = self.conn.cursor()
        
        # Вставляем статусы инцидентов
        cursor.execute("""
            INSERT INTO СтатусыИнцидентов (статус) 
            SELECT N'Открыт' WHERE NOT EXISTS (SELECT 1 FROM СтатусыИнцидентов WHERE статус_инцидента_id = 1);
            INSERT INTO СтатусыИнцидентов (статус) 
            SELECT N'В работе' WHERE NOT EXISTS (SELECT 1 FROM СтатусыИнцидентов WHERE статус_инцидента_id = 2);
            INSERT INTO СтатусыИнцидентов (статус) 
            SELECT N'Закрыт' WHERE NOT EXISTS (SELECT 1 FROM СтатусыИнцидентов WHERE статус_инцидента_id = 3);
        """)

        # Вставляем организацию
        cursor.execute("""
            INSERT INTO Организации (название, адрес, контактный_телефон) 
            SELECT N'ГосСОПКА', N'Москва, ул. Кибербезопасности, 1', N'+79990001122' 
            WHERE NOT EXISTS (SELECT 1 FROM Организации WHERE организация_id = 1);
        """)
        
        # Проверяем, есть ли пользователи
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]

        if count == 0:
            # Если нет ни одного пользователя — создаём админа
            admin_pass = self.crypto.hash_password("adminpass")
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", admin_pass, "admin")
            )
            logging.info("Таблица пользователей полностью пуста. Создан новый пользователь имя:пароль -> admin:adminpass")
        
        self.conn.commit()

    def _init_db(self):
        cursor = self.conn.cursor()
        
        # Создание таблиц SQL Server
        tables_script = """
            -- Таблица статусов инцидентов
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'СтатусыИнцидентов')
            CREATE TABLE СтатусыИнцидентов (
                статус_инцидента_id INT IDENTITY(1,1) PRIMARY KEY,
                статус NVARCHAR(100) NOT NULL
            );

            -- Таблица организаций
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Организации')
            CREATE TABLE Организации (
                организация_id INT IDENTITY(1,1) PRIMARY KEY,
                название NVARCHAR(255) NOT NULL,
                адрес NVARCHAR(500),
                контактный_телефон NVARCHAR(50)
            );

            -- Таблица ответственных
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Ответственные')
            CREATE TABLE Ответственные (
                ответственный_id INT IDENTITY(1,1) PRIMARY KEY,
                имя NVARCHAR(255) NOT NULL,
                должность NVARCHAR(255),
                электронная_почта NVARCHAR(255),
                организация_id INT NULL,
                FOREIGN KEY (организация_id) REFERENCES Организации(организация_id)
            );

            -- Таблица мер реагирования
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'МерыРеагирования')
            CREATE TABLE МерыРеагирования (
                мера_реагирования_id INT IDENTITY(1,1) PRIMARY KEY,
                описание NVARCHAR(MAX) NOT NULL
            );

            -- Таблица инцидентов
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Инциденты')
            CREATE TABLE Инциденты (
                инцидент_id INT IDENTITY(1,1) PRIMARY KEY,
                название NVARCHAR(500) NOT NULL,
                дата_обнаружения DATETIME2,
                статус_инцидента_id INT,
                организация_id INT,
                ответственный_id INT,
                FOREIGN KEY (статус_инцидента_id) REFERENCES СтатусыИнцидентов(статус_инцидента_id),
                FOREIGN KEY (организация_id) REFERENCES Организации(организация_id),
                FOREIGN KEY (ответственный_id) REFERENCES Ответственные(ответственный_id)
            );

            -- Таблица паспортов инцидентов
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ПаспортаИнцидентов')
            CREATE TABLE ПаспортаИнцидентов (
                инцидент_id INT PRIMARY KEY, 
                уровень_критичности NVARCHAR(100), 
                источник_угрозы NVARCHAR(255), 
                последствия NVARCHAR(MAX), 
                тип_инцидента NVARCHAR(255), 
                категория_инцидента NVARCHAR(255), 
                FOREIGN KEY (инцидент_id) REFERENCES Инциденты(инцидент_id) 
            );

            -- Таблица истории изменений
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ИсторияИзменений')
            CREATE TABLE ИсторияИзменений (
                история_изменения_id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(255) NOT NULL,
                таблица NVARCHAR(255) NOT NULL,
                действие NVARCHAR(100) NOT NULL,
                поле NVARCHAR(255),
                старое_значение NVARCHAR(MAX),
                новое_значение NVARCHAR(MAX),
                дата_изменения DATETIME2 DEFAULT GETDATE()
            );

            -- Таблица связи инцидентов и мер
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Инцидент_Меры')
            CREATE TABLE Инцидент_Меры (
                инцидент_id INT, 
                мера_реагирования_id INT, 
                PRIMARY KEY (инцидент_id, мера_реагирования_id), 
                FOREIGN KEY (инцидент_id) REFERENCES Инциденты(инцидент_id), 
                FOREIGN KEY (мера_реагирования_id) REFERENCES МерыРеагирования(мера_реагирования_id) 
            );
        """
        
        cursor.execute(tables_script)
        self.conn.commit()

        # Заполняем справочники начальными данными
        self._seed_initial_data()

    def add_user(self, username: str, password: str, role: str = 'user'):
        """Добавляет пользователя с хэшированным паролем"""
        password_hash = self.crypto.hash_password(password)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        self.conn.commit()
            
    def get_user(self, username: str, password: str):
        """
        Ищет пользователя по username, проверяет пароль.
        Возвращает словарь с данными пользователя (username, role) или None, если нет совпадения.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT username, password_hash, role FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row is None:
            return None

        username_db, password_hash_db, role = row
        if self.crypto.verify_password(password, password_hash_db):
            return {"username": username_db, "role": role}
        else:
            return None

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username, role FROM users")
        return [{"username": row[0], "role": row[1]} for row in cursor.fetchall()]

    def delete_user(self, username: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.conn.commit()

    def change_user_role(self, username: str, new_role: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
        self.conn.commit()

    def change_user_password(self, username: str, new_password: str):
        new_hash = self.crypto.hash_password(new_password)
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
        self.conn.commit()

    # Методы для управления организациями
    def add_organization(self, название, адрес, контактный_телефон):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Организации (название, адрес, контактный_телефон) VALUES (?, ?, ?)",
            (название, адрес, контактный_телефон)
        )
        self.conn.commit()

    def update_organization(self, организация_id, название, адрес, контактный_телефон):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE Организации SET название = ?, адрес = ?, контактный_телефон = ? WHERE организация_id = ?",
            (название, адрес, контактный_телефон, организация_id)
        )
        self.conn.commit()

    def delete_organization(self, организация_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM Организации WHERE организация_id = ?",
            (организация_id,)
        )
        self.conn.commit()

    def get_organization_by_id(self, организация_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT организация_id, название, адрес, контактный_телефон FROM Организации WHERE организация_id = ?",
            (организация_id,)
        )
        return cursor.fetchone()

    def add_incident(self, название, дата_обнаружения=None, статус_id=None, организация_id=None, ответственный_id=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Инциденты (название, дата_обнаружения, статус_инцидента_id, организация_id, ответственный_id) VALUES (?, ?, ?, ?, ?)",
            (название, дата_обнаружения, статус_id, организация_id, ответственный_id)
        )
        self.conn.commit()

    def get_incidents(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT инцидент_id, название, дата_обнаружения, статус_инцидента_id, организация_id, ответственный_id FROM Инциденты"
        )
        return cursor.fetchall()

    def update_incident_status(self, инцидент_id, новый_статус_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE Инциденты SET статус_инцидента_id = ? WHERE инцидент_id = ?",
            (новый_статус_id, инцидент_id)
        )
        self.conn.commit()

    def delete_incident(self, инцидент_id):
        cursor = self.conn.cursor()
        # Сначала удалить связанные записи из ПаспортаИнцидентов
        cursor.execute(
            "DELETE FROM ПаспортаИнцидентов WHERE инцидент_id = ?",
            (инцидент_id,)
        )
        # Потом удалить сам инцидент
        cursor.execute(
            "DELETE FROM Инциденты WHERE инцидент_id = ?",
            (инцидент_id,)
        )
        self.conn.commit()
            
    def get_incident_details(self, incident_id):
        """Возвращает полные данные об инциденте в виде словаря"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM Инциденты WHERE инцидент_id = ?", 
            (incident_id,)
        )
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None

    def update_incident(self, id, **fields):
        """Обновляет указанные поля инцидента с правильными именами столбцов"""
        # Соответствие между именами параметров и столбцами БД
        column_mapping = {
            'статус_id': 'статус_инцидента_id',
            'название': 'название',
            'организация_id': 'организация_id',
            'ответственный_id': 'ответственный_id'
        }
        
        # Преобразуем имена полей к реальным именам столбцов
        db_fields = {}
        for key, value in fields.items():
            db_key = column_mapping.get(key, key)
            db_fields[db_key] = value
        
        cursor = self.conn.cursor()
        set_clause = ", ".join(f"{k} = ?" for k in db_fields)
        values = list(db_fields.values())
        values.append(id)
        
        cursor.execute(
            f"UPDATE Инциденты SET {set_clause} WHERE инцидент_id = ?",
            values
        )
        self.conn.commit()

    # --- Методы для Организаций ---
    def get_organizations(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT организация_id, название, адрес, контактный_телефон FROM Организации"
        )
        return cursor.fetchall()

    # --- Методы для Ответственных ---
    def add_responsible(self, имя, должность=None, email=None, организация_id=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Ответственные (имя, должность, электронная_почта, организация_id) VALUES (?, ?, ?, ?)",
            (имя, должность, email, организация_id)
        )
        self.conn.commit()

    def get_responsibles(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT ответственный_id, имя, должность, электронная_почта, организация_id FROM Ответственные"
        )
        return cursor.fetchall()
    
    def get_responsible_by_id(self, ответственный_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT ответственный_id, имя, должность, электронная_почта, организация_id FROM Ответственные WHERE ответственный_id = ?",
            (ответственный_id,)
        )
        return cursor.fetchone()

    def update_responsible(self, ответственный_id, имя, должность=None, email=None, организация_id=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE Ответственные SET имя = ?, должность = ?, электронная_почта = ?, организация_id = ? WHERE ответственный_id = ?",
            (имя, должность, email, организация_id, ответственный_id)
        )
        self.conn.commit()

    # --- Методы для Статусов Инцидентов ---
    def get_statuses(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT статус_инцидента_id, статус FROM СтатусыИнцидентов"
        )
        return cursor.fetchall()

    # Добавление статуса
    def add_status(self, status: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO СтатусыИнцидентов (статус) VALUES (?)",
            (status,)
        )
        self.conn.commit()

    # Удаление статуса
    def delete_status(self, status_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM СтатусыИнцидентов WHERE статус_инцидента_id = ?",
            (status_id,)
        )
        self.conn.commit()

    # --- Методы для Мер Реагирования ---
    def add_response_measure(self, описание):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO МерыРеагирования (описание) VALUES (?)",
            (описание,)
        )
        self.conn.commit()

    def get_response_measures(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT мера_реагирования_id, описание FROM МерыРеагирования"
        )
        return cursor.fetchall()

    def delete_response_measure(self, measure_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM МерыРеагирования WHERE мера_реагирования_id = ?",
            (measure_id,)
        )
        self.conn.commit()

    # --- Методы для Инцидент_Меры ---
    def add_incident_measure(self, инцидент_id, мера_реагирования_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Инцидент_Меры (инцидент_id, мера_реагирования_id) VALUES (?, ?)",
            (инцидент_id, мера_реагирования_id)
        )
        self.conn.commit()

    def get_measures_for_incident(self, инцидент_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT МерыРеагирования.мера_реагирования_id, МерыРеагирования.описание
            FROM Инцидент_Меры
            JOIN МерыРеагирования ON Инцидент_Меры.мера_реагирования_id = МерыРеагирования.мера_реагирования_id
            WHERE Инцидент_Меры.инцидент_id = ?
        """, (инцидент_id,))
        return cursor.fetchall()

    # --- Методы для ПаспортаИнцидентов ---
    def add_passport(self, инцидент_id, уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ПаспортаИнцидентов (инцидент_id, уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (инцидент_id, уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента))
        self.conn.commit()

    def get_passport(self, инцидент_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента
            FROM ПаспортаИнцидентов WHERE инцидент_id = ?
        """, (инцидент_id,))
        return cursor.fetchone()

    def update_passport(self, инцидент_id, уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE ПаспортаИнцидентов
            SET уровень_критичности = ?, источник_угрозы = ?, последствия = ?, тип_инцидента = ?, категория_инцидента = ?
            WHERE инцидент_id = ?
        """, (уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента, инцидент_id))
        self.conn.commit()

    # --- Методы для связей между инцидентами и мерами реагирования ---
    def link_incident_measure(self, инцидент_id, мера_реагирования_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Инцидент_Меры (инцидент_id, мера_реагирования_id) VALUES (?, ?)",
            (инцидент_id, мера_реагирования_id)
        )
        self.conn.commit()

    def get_measures_for_incident(self, инцидент_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT м.мера_реагирования_id, м.описание
            FROM МерыРеагирования м
            JOIN Инцидент_Меры им ON м.мера_реагирования_id = им.мера_реагирования_id
            WHERE им.инцидент_id = ?
            """,
            (инцидент_id,)
        )
        return cursor.fetchall()

    # --- Методы для журнала изменений ---
    def log_change(self, username, таблица, действие, поле=None, старое_значение=None, новое_значение=None):
        """Логирует изменения в системе"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO ИсторияИзменений (
                    username, таблица, действие, поле, 
                    старое_значение, новое_значение
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, таблица, действие, поле, старое_значение, новое_значение)
            )
            self.conn.commit()
            logging.info(f"Запись в журнал изменений {действие}")
        except Exception as e:
            logging.error(f"Ошибка при логировании: {e}")
            raise

    def get_audit_logs(self, table_filter=None, user_filter=None, date_from=None, date_to=None):
        """
        Получает записи журнала изменений с возможностью фильтрации
        
        Args:
            table_filter: Фильтр по таблице (None - все таблицы)
            user_filter: Фильтр по пользователю (None - все пользователи)
            date_from: Начальная дата (включительно)
            date_to: Конечная дата (включительно)
            
        Returns:
            Список кортежей с записями журнала
        """
        try:
            conditions = []
            params = []
            
            if table_filter:
                conditions.append("таблица = ?")
                params.append(table_filter)
                
            if user_filter:
                conditions.append("username = ?")
                params.append(user_filter)
                
            if date_from:
                conditions.append("дата_изменения >= ?")
                params.append(date_from)
                
            if date_to:
                conditions.append("дата_изменения <= ?")
                params.append(date_to + " 23:59:59")
            
            query = "SELECT * FROM ИсторияИзменений"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY дата_изменения DESC"
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
            
        except Exception as e:
            logging.error(f"Ошибка получения журнала: {e}")
            raise

    def get_all_tables(self):
        """Возвращает все таблицы в базе данных"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        )
        return [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']

    def get_audit_tables(self):
        """Возвращает список таблиц, встречающихся в журнале"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT DISTINCT таблица FROM ИсторияИзменений ORDER BY таблица"
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Ошибка получения таблиц журнала: {e}")
            return []
    
    def get_audit_users(self):
        """Возвращает список пользователей из журнала"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT DISTINCT username FROM ИсторияИзменений ORDER BY username"
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Ошибка получения пользователей журнала: {e}")
            return []
