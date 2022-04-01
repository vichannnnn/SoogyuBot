import sqlite3

conn = sqlite3.connect('prefix.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row

c.execute('''CREATE TABLE IF NOT EXISTS prefix (
        `guild_id` INT PRIMARY KEY,
        `prefix` TEXT)''')

prefix_dictionary = {}


class PrefixDatabase:
    @staticmethod
    def connect():
        conn = sqlite3.connect('prefix.db', timeout=5.0)
        c = conn.cursor()
        return c

    @staticmethod
    def execute(statement, *args):
        c = PrefixDatabase.connect()
        c.execute(statement, args)
        c.connection.commit()
        c.connection.close()

    @staticmethod
    def get(statement, *args):
        c = PrefixDatabase.connect()
        c.execute(statement, args)
        res = c.fetchall()
        c.connection.close()
        return res
