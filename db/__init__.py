import sqlite3
from cryptography.fernet import Fernet
import base64
import bcrypt


class UserDb:
    def __init__(self, db_name):
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                name TEXT
            )
        """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS post (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                user_id INTEGER,
                username TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                likes INTEGER DEFAULT 0
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES post (id)
            )
            """
        )

        self.conn.commit()

    def add_user(self, username, password, name=None):
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        self.cursor.execute(
            "INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
            (username, hashed_password, name),
        )
        self.conn.commit()

    def verify_credentials(self, username, password):
        self.cursor.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,),
        )
        stored_password = self.cursor.fetchone()

        if stored_password and bcrypt.checkpw(
            password.encode("utf-8"), stored_password[0]
        ):
            return True
        else:
            return False

    def get_user_info(self, username):
        self.cursor.execute(
            "SELECT id, name FROM users WHERE username = ?",
            (username,),
        )
        user_data = self.cursor.fetchone()
        return user_data

    def add_post(self, title, content, user_id, username):
        self.cursor.execute(
            "INSERT INTO post (title, content, user_id, username) VALUES (?, ?, ?, ?)",
            (title, content, user_id, username),
        )
        self.conn.commit()

    def get_user_id_by_username(self, username):
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = self.cursor.fetchone()
        return user_id[0] if user_id else None

    def get_all_posts(self):
        self.cursor.execute("SELECT * FROM post")
        all_posts = self.cursor.fetchall()
        return all_posts

    def get_all_posts_sorted_by_newest(self):
        self.cursor.execute("SELECT * FROM post ORDER BY timestamp DESC")
        posts = self.cursor.fetchall()
        return posts

    def encrypt_data(self, data):
        encrypted_data = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt_data(self, encrypted_data):
        encrypted_data = base64.urlsafe_b64decode(encrypted_data)
        decrypted_data = self.fernet.decrypt(encrypted_data).decode()
        return decrypted_data

    def get_likes_for_post(self, post_id):
        self.cursor.execute("SELECT likes FROM post WHERE id = ?", (post_id,))
        likes = self.cursor.fetchone()
        return likes[0] if likes else 0

    def check_if_user_liked_post(self, user_id, post_id):
        self.cursor.execute(
            "SELECT COUNT(*) FROM likes WHERE user_id = ? AND post_id = ?",
            (user_id, post_id),
        )
        result = self.cursor.fetchone()
        return result[0] > 0

    def add_like(self, user_id, post_id):
        self.cursor.execute(
            "INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id)
        )
        self.cursor.execute(
            "UPDATE post SET likes = likes + 1 WHERE id = ?", (post_id,)
        )
        self.conn.commit()

    def get_post_by_id(self, post_id):
        self.cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,))
        post = self.cursor.fetchone()
        return post

    def close(self):
        self.conn.close()
