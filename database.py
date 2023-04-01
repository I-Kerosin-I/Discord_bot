import sqlite3
import json

with open('cenz.json', 'r') as f:
    default_cenz = ''.join(f)

with open('default_cfg.json', 'r') as f:
    default_cfg = ''.join(f)


class Db:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()

    def add_guild(self, guild):
        self.cur.execute(
            f'CREATE TABLE IF NOT EXISTS id_{guild}(userid INT, count INT)')
        self.cur.execute(f'INSERT INTO configs VALUES(?, ?, ?)',
                         (guild, default_cfg, default_cenz))
        self.conn.commit()

    def del_guild(self, guild):
        self.cur.execute(f'DROP TABLE id_{guild}')
        self.cur.execute(f'DELETE FROM configs WHERE id == ?', (guild,))
        self.conn.commit()

    def sync(self, guilds):
        self.cur.execute('CREATE TABLE IF NOT EXISTS configs('
                         'id INT, config TEXT, words TEXT)')
        ids_bot = {str(i.id) for i in guilds}
        ids_db = {str(i[0]) for i in
                  self.cur.execute('SELECT * FROM configs').fetchall()}
        tables = {i[0][3:] for i in self.cur.execute(
            'SELECT name FROM sqlite_master WHERE type="table"').fetchall() if
                  i[0][:3] == 'id_'}

        print('Generating configs for\n{}'.format('\n'.join(ids_bot - ids_db)))
        for i in ids_bot - ids_db:
            self.cur.execute(f'INSERT INTO configs VALUES(?, ?, ?)',
                             (i, default_cfg, default_cenz))

        print('Deleting configs for\n{}'.format('\n'.join(ids_db - ids_bot)))
        for i in ids_db - ids_bot:
            self.cur.execute(f'DELETE FROM configs WHERE id == ?', (i,))

        print('Creating new tables for\n{}'.format('\n'.join(ids_bot - tables)))
        for i in ids_bot - tables:
            self.cur.execute(
                f'CREATE TABLE IF NOT EXISTS id_{i}(userid INT, count INT)')

        print('Deleting tables for\n{}'.format('\n'.join(tables - ids_bot)))
        for i in tables - ids_bot:
            self.cur.execute(f'DROP TABLE id_{i}')

        self.conn.commit()

    def get_warns(self, guild, user, autoregister=False) -> int:
        warns = self.cur.execute(f'SELECT count FROM id_{guild} '
                                 f'WHERE userid == ?', (user,)).fetchone()
        if warns is None and autoregister:
            self.cur.execute(f'INSERT INTO id_{guild} VALUES(?, ?)', (user, 0))
            self.conn.commit()
        return 0 if warns is None else warns[0]

    def inc_warns(self, guild, user):
        self.cur.execute(f'UPDATE id_{guild} SET count == count + 1 WHERE'
                         f' userid == ?', (user,))
        self.conn.commit()

    def get_cfg(self, guild) -> dict:
        return json.loads(self.cur.execute(f'SELECT config FROM configs WHERE'
                                           f' id == ?', (guild,)).fetchone()[0])

    def set_cfg(self, guild, cfg):
        self.cur.execute(f'UPDATE configs SET config == ? WHERE id == ?',
                         (json.dumps(cfg), guild))
        self.conn.commit()

    def get_words(self, guild) -> list:
        return json.loads(self.cur.execute(
            'SELECT words FROM configs WHERE id == ?', (guild,)).fetchone()[0])

    def set_words(self, guild, words: list):
        self.cur.execute(f'UPDATE configs SET words == ? WHERE id == ?',
                         (json.dumps(words), guild))
        self.conn.commit()

    def del_user(self, guild, user):
        self.cur.execute(f'DELETE FROM id_{guild} WHERE userid == ?',
                         (user,))
        self.conn.commit()
