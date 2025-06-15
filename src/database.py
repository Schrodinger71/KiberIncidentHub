# Copyright 2025 Schrodinger71
# Licensed under the Apache License, Version 2.0 (see LICENSE file)

import logging
import os
import sqlite3
import datetime
from pathlib import Path
import shutil

from src.crypto import CryptoManager


class SecureDB:
    backups_dir = Path("backups")

    def __init__(self, encrypted_path: str):
        self.encrypted_path = Path(encrypted_path)
        self.crypto = CryptoManager()
        self.conn = sqlite3.connect(":memory:")  # Работаем только в памяти
        self.conn.execute("PRAGMA foreign_keys = ON;")

        if self.encrypted_path.exists():
            self._load_encrypted_into_memory()
        else:
            logging.warning("Зашифрованная БД не найдена. Будет создана новая.")
            self._init_schema()
            self._init_db()

    def _start_auto_backup(self, root):
        self._create_backup("auto")
        root.after(300000, lambda: self._start_auto_backup(root))

    def _create_backup(self, prefix: str):
        """Создаёт зашифрованный бэкап с датой в папку backups"""
        if not self.backups_dir.exists():
            self.backups_dir.mkdir(parents=True)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"{prefix}_backup_{timestamp}.db.enc"
        backup_path = self.backups_dir / backup_filename

        # Просто копируем текущий зашифрованный файл в бэкап
        if self.encrypted_path.exists():
            shutil.copy2(self.encrypted_path, backup_path)
            logging.info(f"Создан бэкап БД: {backup_path}")
        else:
            logging.warning("Файл зашифрованной БД не найден для бэкапа")

    def _load_encrypted_into_memory(self):
        logging.info("Загружаю зашифрованную БД в память")

        # Перед загрузкой БД создаём бэкап
        self._create_backup("startup")

        decrypted_data = self.crypto.cipher.decrypt(self.encrypted_path.read_bytes())
        
        # Временный файл для расшифрованной БД
        temp_path = self.encrypted_path.with_suffix('.tmp.db')
        try:
            with open(temp_path, "wb") as f:
                f.write(decrypted_data)
            temp_conn = sqlite3.connect(temp_path)
            temp_conn.backup(self.conn)
            temp_conn.close()
            logging.info("БД успешно загружена в память")
        except Exception as e:
            logging.error(f"Ошибка при расшифровке и загрузке БД: {e}")
        finally:
            if temp_path.exists():
                os.remove(temp_path)


    def _encrypt_db_file(self):
        temp_path = self.encrypted_path.with_suffix('.tmp.db')
        try:
            disk_conn = sqlite3.connect(temp_path)
            self.conn.backup(disk_conn)
            disk_conn.close()

            with open(temp_path, "rb") as f:
                raw_data = f.read()
            encrypted_data = self.crypto.cipher.encrypt(raw_data)

            if encrypted_data:
                with open(self.encrypted_path, "wb") as f:
                    f.write(encrypted_data)
                logging.info(f"БД зашифрована в файл {self.encrypted_path}")
            else:
                logging.error("Ошибка: зашифрованные данные пусты!")
        except Exception as e:
            logging.error(f"Ошибка при шифровании БД: {e}")
        finally:
            if temp_path.exists():
                os.remove(temp_path)

    def close(self):
        if self.conn:
            try:
                self.conn.commit()
            except Exception as e:
                logging.error(f"Ошибка при коммите БД: {e}")
            self._encrypt_db_file()
            
            # Создаём бэкап при закрытии
            self._create_backup("shutdown")
            
            self.conn.close()
            logging.info("Соединение с БД закрыто и зашифровано")
        else:
            logging.warning("Соединение с БД уже было закрыто или не создано")

    def _init_schema(self):
        """Создаёт таблицу пользователей"""
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'user'))
                );
            ''')

    def _seed_initial_data(self):
        """Заполняет начальные справочники"""
        with self.conn:
            self.conn.executemany(
                "INSERT OR IGNORE INTO СтатусыИнцидентов VALUES (?, ?)",
                [(1, 'Открыт'), (2, 'В работе'), (3, 'Закрыт')]
            )

            self.conn.execute(
                "INSERT OR IGNORE INTO Организации VALUES (?, ?, ?, ?)",
                (1, 'ГосСОПКА', 'Москва, ул. Кибербезопасности, 1', '+79990001122')
            )
            
            # Проверка: есть ли пользователи
            cur = self.conn.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]

            if count == 0:
                # Если нет ни одного пользователя — создаём админа
                admin_pass = self.crypto.hash_password("adminpass")
                self.conn.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    ("admin", admin_pass, "admin")
                )
                logging.info("Таблица пользователей полностью пуста. Создан новый пользователь имя:пароль -> admin:adminpass")

    def _init_db(self):
        self._init_schema()
        # Создание остальных таблиц
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS СтатусыИнцидентов (
                    статус_инцидента_id INTEGER PRIMARY KEY,
                    статус TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS Организации (
                    организация_id INTEGER PRIMARY KEY,
                    название TEXT NOT NULL,
                    адрес TEXT,
                    контактный_телефон TEXT
                );
                
                CREATE TABLE IF NOT EXISTS Ответственные (
                    ответственный_id INTEGER PRIMARY KEY,
                    имя TEXT NOT NULL,
                    должность TEXT,
                    электронная_почта TEXT,
                    организация_id INTEGER NULL,
                    FOREIGN KEY (организация_id) REFERENCES Организации(организация_id)
                );

                CREATE TABLE IF NOT EXISTS МерыРеагирования (
                    мера_реагирования_id INTEGER PRIMARY KEY,
                    описание TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS Инциденты (
                    инцидент_id INTEGER PRIMARY KEY,
                    название TEXT NOT NULL,
                    дата_обнаружения DATE,
                    статус_инцидента_id INTEGER,
                    организация_id INTEGER,
                    ответственный_id INTEGER,
                    FOREIGN KEY (статус_инцидента_id) REFERENCES СтатусыИнцидентов(статус_инцидента_id),
                    FOREIGN KEY (организация_id) REFERENCES Организации(организация_id),
                    FOREIGN KEY (ответственный_id) REFERENCES Ответственные(ответственный_id)
                );
                
                CREATE TABLE IF NOT EXISTS ПаспортаИнцидентов (
                    инцидент_id INTEGER PRIMARY KEY, 
                    уровень_критичности TEXT, 
                    источник_угрозы TEXT, 
                    последствия TEXT, 
                    тип_инцидента TEXT, 
                    категория_инцидента TEXT, 
                    FOREIGN KEY (инцидент_id) REFERENCES Инциденты(инцидент_id) 
                );
                
                CREATE TABLE IF NOT EXISTS ИсторияИзменений (
                    история_изменения_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    таблица TEXT NOT NULL,
                    действие TEXT NOT NULL,
                    поле TEXT,
                    старое_значение TEXT,
                    новое_значение TEXT,
                    дата_изменения TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS Инцидент_Меры (
                    инцидент_id INTEGER, 
                    мера_реагирования_id INTEGER, 
                    PRIMARY KEY (инцидент_id, мера_реагирования_id), 
                    FOREIGN KEY (инцидент_id) REFERENCES Инциденты(инцидент_id), 
                    FOREIGN KEY (мера_реагирования_id) REFERENCES МерыРеагирования(мера_реагирования_id) 
                );
            """)

        # Заполняем справочники начальными данными
        self._seed_initial_data()

    def add_user(self, username: str, password: str, role: str = 'user'):
        """Добавляет пользователя с хэшированным паролем"""
        password_hash = self.crypto.hash_password(password)
        with self.conn:
            self.conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            
    def get_user(self, username: str, password: str):
        """
        Ищет пользователя по username, проверяет пароль.
        Возвращает словарь с данными пользователя (username, role) или None, если нет совпадения.
        """
        cursor = self.conn.execute(
            "SELECT username, password_hash, role FROM users WHERE username = ?", (username,)
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
        cursor = self.conn.execute("SELECT username, role FROM users")
        return [{"username": row[0], "role": row[1]} for row in cursor.fetchall()]

    def delete_user(self, username: str):
        with self.conn:
            self.conn.execute("DELETE FROM users WHERE username = ?", (username,))

    def change_user_role(self, username: str, new_role: str):
        with self.conn:
            self.conn.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))

    def change_user_password(self, username: str, new_password: str):
        new_hash = self.crypto.hash_password(new_password)
        with self.conn:
            self.conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))

    # Методы для управления организациями
    def add_organization(self, название, адрес, контактный_телефон):
        with self.conn:
            self.conn.execute(
                "INSERT INTO Организации (название, адрес, контактный_телефон) VALUES (?, ?, ?)",
                (название, адрес, контактный_телефон)
            )

    def update_organization(self, организация_id, название, адрес, контактный_телефон):
        with self.conn:
            self.conn.execute(
                "UPDATE Организации SET название = ?, адрес = ?, контактный_телефон = ? WHERE организация_id = ?",
                (название, адрес, контактный_телефон, организация_id)
            )

    def delete_organization(self, организация_id):
        with self.conn:
            self.conn.execute(
                "DELETE FROM Организации WHERE организация_id = ?",
                (организация_id,)
            )

    def get_organization_by_id(self, организация_id):
        cursor = self.conn.execute(
            "SELECT организация_id, название, адрес, контактный_телефон FROM Организации WHERE организация_id = ?",
            (организация_id,)
        )
        return cursor.fetchone()

    def add_incident(self, название, дата_обнаружения=None, статус_id=None, организация_id=None, ответственный_id=None):
        with self.conn:
            self.conn.execute(
                "INSERT INTO Инциденты (название, дата_обнаружения, статус_инцидента_id, организация_id, ответственный_id) VALUES (?, ?, ?, ?, ?)",
                (название, дата_обнаружения, статус_id, организация_id, ответственный_id)
            )

    def get_incidents(self):
        cursor = self.conn.execute(
            "SELECT инцидент_id, название, дата_обнаружения, статус_инцидента_id, организация_id, ответственный_id FROM Инциденты"
        )
        return cursor.fetchall()

    def update_incident_status(self, инцидент_id, новый_статус_id):
        with self.conn:
            self.conn.execute(
                "UPDATE Инциденты SET статус_инцидента_id = ? WHERE инцидент_id = ?",
                (новый_статус_id, инцидент_id)
            )

    def delete_incident(self, инцидент_id):
        with self.conn:
            self.conn.execute(
                "DELETE FROM Инциденты WHERE инцидент_id = ?",
                (инцидент_id,)
            )
            
    def get_incident_details(self, incident_id):
        """Возвращает полные данные об инциденте в виде словаря"""
        cursor = self.conn.execute(
            "SELECT * FROM Инциденты WHERE инцидент_id = ?", 
            (incident_id,)
        )
        columns = [col[0] for col in cursor.description]
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
        
        with self.conn:
            set_clause = ", ".join(f"{k} = ?" for k in db_fields)
            values = list(db_fields.values())
            values.append(id)
            
            self.conn.execute(
                f"UPDATE Инциденты SET {set_clause} WHERE инцидент_id = ?",
                values
            )

    # --- Методы для Организаций ---
    def get_organizations(self):
        cursor = self.conn.execute(
            "SELECT организация_id, название, адрес, контактный_телефон FROM Организации"
        )
        return cursor.fetchall()

    # --- Методы для Ответственных ---
    def add_responsible(self, имя, должность=None, email=None, организация_id=None):
        with self.conn:
            self.conn.execute(
                "INSERT INTO Ответственные (имя, должность, электронная_почта, организация_id) VALUES (?, ?, ?, ?)",
                (имя, должность, email, организация_id)
            )

    def get_responsibles(self):
        cursor = self.conn.execute(
            "SELECT ответственный_id, имя, должность, электронная_почта, организация_id FROM Ответственные"
        )
        return cursor.fetchall()
    
    def get_responsible_by_id(self, ответственный_id):
        cursor = self.conn.execute(
            "SELECT ответственный_id, имя, должность, электронная_почта, организация_id FROM Ответственные WHERE ответственный_id = ?",
            (ответственный_id,)
        )
        return cursor.fetchone()

    def update_responsible(self, ответственный_id, имя, должность=None, email=None, организация_id=None):
        with self.conn:
            self.conn.execute(
                "UPDATE Ответственные SET имя = ?, должность = ?, электронная_почта = ?, организация_id = ? WHERE ответственный_id = ?",
                (имя, должность, email, организация_id, ответственный_id)
            )

    # --- Методы для Статусов Инцидентов ---
    def get_statuses(self):
        cursor = self.conn.execute(
            "SELECT статус_инцидента_id, статус FROM СтатусыИнцидентов"
        )
        return cursor.fetchall()

    # --- Методы для Мер Реагирования ---
    def add_response_measure(self, описание):
        with self.conn:
            self.conn.execute(
                "INSERT INTO МерыРеагирования (описание) VALUES (?)",
                (описание,)
            )

    def get_response_measures(self):
        cursor = self.conn.execute(
            "SELECT мера_реагирования_id, описание FROM МерыРеагирования"
        )
        return cursor.fetchall()

    # --- Методы для связей между инцидентами и мерами реагирования ---
    def link_incident_measure(self, инцидент_id, мера_реагирования_id):
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO Инцидент_Меры (инцидент_id, мера_реагирования_id) VALUES (?, ?)",
                (инцидент_id, мера_реагирования_id)
            )

    def get_measures_for_incident(self, инцидент_id):
        cursor = self.conn.execute(
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
            self.conn.execute(
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
        except sqlite3.Error as e:
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
            
            cursor = self.conn.execute(query, params)
            return cursor.fetchall()
            
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения журнала: {e}")
            raise

    def get_all_tables(self):
        """Возвращает все таблицы в базе данных"""
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']

    def get_audit_tables(self):
        """Возвращает таблицы, которые встречаются в журнале изменений"""
        try:
            cursor = self.conn.execute(
                "SELECT DISTINCT таблица FROM ИсторияИзменений ORDER BY таблица"
            )
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения таблиц журнала: {e}")
            return []

    def get_audit_tables(self):
        """Возвращает список таблиц, встречающихся в журнале"""
        try:
            cursor = self.conn.execute(
                "SELECT DISTINCT таблица FROM ИсторияИзменений ORDER BY таблица"
            )
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения таблиц журнала: {e}")
            return []
    
    def get_audit_users(self):
        """Возвращает список пользователей из журнала"""
        try:
            cursor = self.conn.execute(
                "SELECT DISTINCT username FROM ИсторияИзменений ORDER BY username"
            )
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения пользователей журнала: {e}")
            return []
