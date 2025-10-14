import sqlite3, os, time
class Memory:
    def __init__(self, db_path='./data/memory.db'):
        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, user_id TEXT, role TEXT, text TEXT, ts INTEGER)""")
        self.conn.commit()
    def append_message(self, user_id, role, text):
        ts = int(time.time())
        self.conn.execute("INSERT INTO messages (user_id, role, text, ts) VALUES (?, ?, ?, ?)", (user_id, role, text, ts))
        self.conn.commit()
    def get_recent(self, user_id, limit=10):
        cur = self.conn.cursor()
        rows = cur.execute("SELECT role, text, ts FROM messages WHERE user_id=? ORDER BY ts DESC LIMIT ?", (user_id, limit)).fetchall()
        return [{'role': r[0], 'text': r[1], 'ts': r[2]} for r in rows[::-1]]
    def ping(self):
        try:
            self.conn.execute('SELECT 1').fetchone()
            return True
        except:
            return False
