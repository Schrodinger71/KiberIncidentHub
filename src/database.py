import sqlite3
from pathlib import Path
from src.crypto import CryptoManager
import logging

class SecureDB:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.crypto = CryptoManager()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._init_db()

    def _init_db(self):
        """Создает БД и таблицы если они не существуют"""
        if not self.db_path.exists():
            logging.info(f"Создаем новую БД: {self.db_path}")

        # Создание таблицы пользователей
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
                    история_изменения_id INTEGER PRIMARY KEY, 
                    инцидент_id INTEGER, 
                    дата_изменения DATE, 
                    описание TEXT, 
                    FOREIGN KEY (инцидент_id) REFERENCES Инциденты(инцидент_id) 
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
                (1, 'ГосСОПКА', 'Москва', '+79990001122')
            )

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

    # --- Методы для Организаций ---
    def add_organization(self, название, адрес=None, телефон=None):
        with self.conn:
            self.conn.execute(
                "INSERT INTO Организации (название, адрес, контактный_телефон) VALUES (?, ?, ?)",
                (название, адрес, телефон)
            )

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

    def close(self):
        self.conn.close()
