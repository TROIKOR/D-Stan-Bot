import sqlite3

class DB:
    def __init__(self):
        self.db = sqlite3.connect("dstan.db")
        self.db.row_factory = sqlite3.Row
        self.cur = self.db.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            admin INTEGER DEFAULT 0
        )""")
        self.db.commit()

    def register(self, user_id, username):
        if self.user_exists(user_id):
            return False
        self.cur.execute("INSERT INTO users(id, username, balance, admin) VALUES (?, ?, 0, 0)",
                         (user_id, username))
        self.db.commit()
        return True

    def user_exists(self, user_id):
        r = self.cur.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone()
        return bool(r)

    def get_user(self, user_id):
        return self.cur.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    def get_id_by_username(self, username):
        r = self.cur.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        return r["id"] if r else None

    def get_user_by_username_raw(self, username):
        r = self.cur.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return r

    def add_balance(self, user_id, amount):
        self.cur.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
        self.db.commit()

    def get_all_users(self):
        return self.cur.execute("SELECT * FROM users ORDER BY balance DESC").fetchall()

    def get_admins(self):
        return self.cur.execute("SELECT * FROM users WHERE admin=1").fetchall()

    def get_admin_ids(self):
        r = self.cur.execute("SELECT id FROM users WHERE admin=1").fetchall()
        return [x["id"] for x in r]

    def make_admin(self, user_id):
        self.cur.execute("UPDATE users SET admin=1 WHERE id=?", (user_id,))
        self.db.commit()
