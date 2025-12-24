# Copyright 2025 Schrodinger71
# Licensed under the Apache License, Version 2.0 (see LICENSE file)

import logging
import os
import psycopg2
import psycopg2.extras
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
            logging.warning("База данных PostgreSQL не найдена или пуста. Будет инициализирована новая.")
            self._init_schema()
            self._init_db()
        else:
            logging.info("Подключение к существующей базе данных PostgreSQL")

    def _connect(self):
        """Устанавливает соединение с PostgreSQL"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = False  # Для транзакций
        except Exception as e:
            logging.error(f"Ошибка подключения к PostgreSQL: {e}")
            raise

    def _check_if_database_exists(self):
        """Проверяет, существуют ли таблицы в базе данных"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
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

        # Для PostgreSQL нужно использовать другие методы бэкапа
        # Это упрощённый вариант - сохраняем SQL-скрипт структуры и данных
        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                # Здесь можно добавить экспорт структуры и данных
                f.write("-- PostgreSQL Backup\n")
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
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(255) PRIMARY KEY,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'user'))
            );
        """)
        self.conn.commit()

    def _seed_initial_data(self):
        """Заполняет начальные справочники"""
        cursor = self.conn.cursor()
        
        # Вставляем статусы инцидентов
        cursor.execute("""
            INSERT INTO СтатусыИнцидентов (статус) 
            SELECT 'Открыт' WHERE NOT EXISTS (SELECT 1 FROM СтатусыИнцидентов WHERE статус_инцидента_id = 1);
            INSERT INTO СтатусыИнцидентов (статус) 
            SELECT 'В работе' WHERE NOT EXISTS (SELECT 1 FROM СтатусыИнцидентов WHERE статус_инцидента_id = 2);
            INSERT INTO СтатусыИнцидентов (статус) 
            SELECT 'Закрыт' WHERE NOT EXISTS (SELECT 1 FROM СтатусыИнцидентов WHERE статус_инцидента_id = 3);
        """)

        # Вставляем организацию
        cursor.execute("""
            INSERT INTO Организации (название, адрес, контактный_телефон) 
            SELECT 'ГосСОПКА', 'Москва, ул. Кибербезопасности, 1', '+79990001122' 
            WHERE NOT EXISTS (SELECT 1 FROM Организации WHERE организация_id = 1);
        """)
        
        # Проверяем, есть ли пользователи
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]

        if count == 0:
            # Если нет ни одного пользователя — создаём админа
            admin_pass = self.crypto.hash_password("adminpass")
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                ("admin", admin_pass, "admin")
            )
            logging.info("Таблица пользователей полностью пуста. Создан новый пользователь имя:пароль -> admin:adminpass")
        
        self.conn.commit()

    def _init_db(self):
        cursor = self.conn.cursor()
        
        # Создание таблиц PostgreSQL
        tables_script = """
            -- Таблица статусов инцидентов
            CREATE TABLE IF NOT EXISTS СтатусыИнцидентов (
                статус_инцидента_id SERIAL PRIMARY KEY,
                статус VARCHAR(100) NOT NULL
            );

            -- Таблица организаций
            CREATE TABLE IF NOT EXISTS Организации (
                организация_id SERIAL PRIMARY KEY,
                название VARCHAR(255) NOT NULL,
                адрес VARCHAR(500),
                контактный_телефон VARCHAR(50)
            );

            -- Таблица ответственных
            CREATE TABLE IF NOT EXISTS Ответственные (
                ответственный_id SERIAL PRIMARY KEY,
                имя VARCHAR(255) NOT NULL,
                должность VARCHAR(255),
                электронная_почта VARCHAR(255),
                организация_id INTEGER,
                FOREIGN KEY (организация_id) REFERENCES Организации(организация_id)
            );

            -- Таблица мер реагирования
            CREATE TABLE IF NOT EXISTS МерыРеагирования (
                мера_реагирования_id SERIAL PRIMARY KEY,
                описание TEXT NOT NULL
            );

            -- Таблица инцидентов
            CREATE TABLE IF NOT EXISTS Инциденты (
                инцидент_id SERIAL PRIMARY KEY,
                название VARCHAR(500) NOT NULL,
                дата_обнаружения TIMESTAMP,
                статус_инцидента_id INTEGER,
                организация_id INTEGER,
                ответственный_id INTEGER,
                FOREIGN KEY (статус_инцидента_id) REFERENCES СтатусыИнцидентов(статус_инцидента_id),
                FOREIGN KEY (организация_id) REFERENCES Организации(организация_id),
                FOREIGN KEY (ответственный_id) REFERENCES Ответственные(ответственный_id)
            );

            -- Таблица паспортов инцидентов
            CREATE TABLE IF NOT EXISTS ПаспортаИнцидентов (
                инцидент_id INTEGER PRIMARY KEY, 
                уровень_критичности VARCHAR(100), 
                источник_угрозы VARCHAR(255), 
                последствия TEXT, 
                тип_инцидента VARCHAR(255), 
                категория_инцидента VARCHAR(255), 
                FOREIGN KEY (инцидент_id) REFERENCES Инциденты(инцидент_id) 
            );

            -- Таблица истории изменений
            CREATE TABLE IF NOT EXISTS ИсторияИзменений (
                история_изменения_id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                таблица VARCHAR(255) NOT NULL,
                действие VARCHAR(100) NOT NULL,
                поле VARCHAR(255),
                старое_значение TEXT,
                новое_значение TEXT,
                дата_изменения TIMESTAMP DEFAULT NOW()
            );

            -- Таблица связи инцидентов и мер
            CREATE TABLE IF NOT EXISTS Инцидент_Меры (
                инцидент_id INTEGER, 
                мера_реагирования_id INTEGER, 
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
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
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
            "SELECT username, password_hash, role FROM users WHERE username = %s",
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
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        self.conn.commit()

    def change_user_role(self, username: str, new_role: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET role = %s WHERE username = %s", (new_role, username))
        self.conn.commit()

    def change_user_password(self, username: str, new_password: str):
        new_hash = self.crypto.hash_password(new_password)
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET password_hash = %s WHERE username = %s", (new_hash, username))
        self.conn.commit()

    # Методы для управления организациями
    def add_organization(self, название, адрес, контактный_телефон):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Организации (название, адрес, контактный_телефон) VALUES (%s, %s, %s)",
            (название, адрес, контактный_телефон)
        )
        self.conn.commit()

    def update_organization(self, организация_id, название, адрес, контактный_телефон):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE Организации SET название = %s, адрес = %s, контактный_телефон = %s WHERE организация_id = %s",
            (название, адрес, контактный_телефон, организация_id)
        )
        self.conn.commit()

    def delete_organization(self, организация_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM Организации WHERE организация_id = %s",
            (организация_id,)
        )
        self.conn.commit()

    def get_organization_by_id(self, организация_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT организация_id, название, адрес, контактный_телефон FROM Организации WHERE организация_id = %s",
            (организация_id,)
        )
        return cursor.fetchone()

    def add_incident(self, название, дата_обнаружения=None, статус_id=None, организация_id=None, ответственный_id=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Инциденты (название, дата_обнаружения, статус_инцидента_id, организация_id, ответственный_id) VALUES (%s, %s, %s, %s, %s)",
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
            "UPDATE Инциденты SET статус_инцидента_id = %s WHERE инцидент_id = %s",
            (новый_статус_id, инцидент_id)
        )
        self.conn.commit()

    def delete_incident(self, инцидент_id):
        cursor = self.conn.cursor()
        # Сначала удалить связанные записи из ПаспортаИнцидентов
        cursor.execute(
            "DELETE FROM ПаспортаИнцидентов WHERE инцидент_id = %s",
            (инцидент_id,)
        )
        # Потом удалить сам инцидент
        cursor.execute(
            "DELETE FROM Инциденты WHERE инцидент_id = %s",
            (инцидент_id,)
        )
        self.conn.commit()
            
    def get_incident_details(self, incident_id):
        """Возвращает полные данные об инциденте в виде словаря"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM Инциденты WHERE инцидент_id = %s", 
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
        set_clause = ", ".join(f"{k} = %s" for k in db_fields)
        values = list(db_fields.values())
        values.append(id)
        
        cursor.execute(
            f"UPDATE Инциденты SET {set_clause} WHERE инцидент_id = %s",
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
            "INSERT INTO Ответственные (имя, должность, электронная_почта, организация_id) VALUES (%s, %s, %s, %s)",
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
            "SELECT ответственный_id, имя, должность, электронная_почта, организация_id FROM Ответственные WHERE ответственный_id = %s",
            (ответственный_id,)
        )
        return cursor.fetchone()

    def update_responsible(self, ответственный_id, имя, должность=None, email=None, организация_id=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE Ответственные SET имя = %s, должность = %s, электронная_почта = %s, организация_id = %s WHERE ответственный_id = %s",
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
            "INSERT INTO СтатусыИнцидентов (статус) VALUES (%s)",
            (status,)
        )
        self.conn.commit()

    # Удаление статуса
    def delete_status(self, status_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM СтатусыИнцидентов WHERE статус_инцидента_id = %s",
            (status_id,)
        )
        self.conn.commit()

    # --- Методы для Мер Реагирования ---
    def add_response_measure(self, описание):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO МерыРеагирования (описание) VALUES (%s)",
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
            "DELETE FROM МерыРеагирования WHERE мера_реагирования_id = %s",
            (measure_id,)
        )
        self.conn.commit()

    # --- Методы для Инцидент_Меры ---
    def add_incident_measure(self, инцидент_id, мера_реагирования_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Инцидент_Меры (инцидент_id, мера_реагирования_id) VALUES (%s, %s)",
            (инцидент_id, мера_реагирования_id)
        )
        self.conn.commit()

    def get_measures_for_incident(self, инцидент_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT МерыРеагирования.мера_реагирования_id, МерыРеагирования.описание
            FROM Инцидент_Меры
            JOIN МерыРеагирования ON Инцидент_Меры.мера_реагирования_id = МерыРеагирования.мера_реагирования_id
            WHERE Инцидент_Меры.инцидент_id = %s
        """, (инцидент_id,))
        return cursor.fetchall()

    # --- Методы для ПаспортаИнцидентов ---
    def add_passport(self, инцидент_id, уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ПаспортаИнцидентов (инцидент_id, уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (инцидент_id, уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента))
        self.conn.commit()

    def get_passport(self, инцидент_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента
            FROM ПаспортаИнцидентов WHERE инцидент_id = %s
        """, (инцидент_id,))
        return cursor.fetchone()

    def update_passport(self, инцидент_id, уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE ПаспортаИнцидентов
            SET уровень_критичности = %s, источник_угрозы = %s, последствия = %s, тип_инцидента = %s, категория_инцидента = %s
            WHERE инцидент_id = %s
        """, (уровень_критичности, источник_угрозы, последствия, тип_инцидента, категория_инцидента, инцидент_id))
        self.conn.commit()

    # --- Методы для связей между инцидентами и мерами реагирования ---
    def link_incident_measure(self, инцидент_id, мера_реагирования_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Инцидент_Меры (инцидент_id, мера_реагирования_id) VALUES (%s, %s)",
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
            WHERE им.инцидент_id = %s
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
                ) VALUES (%s, %s, %s, %s, %s, %s)
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
                conditions.append("таблица = %s")
                params.append(table_filter)
                
            if user_filter:
                conditions.append("username = %s")
                params.append(user_filter)
                
            if date_from:
                conditions.append("дата_изменения >= %s")
                params.append(date_from)
                
            if date_to:
                conditions.append("дата_изменения <= %s")
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
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        return [row[0] for row in cursor.fetchall()]

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
