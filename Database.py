import sqlite3

conn = sqlite3.connect('bot.db', timeout=5.0)
c = conn.cursor()

c.execute(
    ''' CREATE TABLE IF NOT EXISTS guild_currency_symbol (
    guild_id INT PRIMARY KEY,
    currency_symbol TEXT DEFAULT '🍇'
    )''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS inventory (
    user_id INT,
    card_id TEXT,
    quantity INT DEFAULT 0,
    UNIQUE(user_id, card_id)
    )''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS user_profile (
    user_id INT PRIMARY KEY,
    balance INT DEFAULT 0,
    bio TEXT DEFAULT '',
    fav TEXT DEFAULT '',
    daily_cooldown INT DEFAULT 0,
    work_cooldown INT DEFAULT 0,
    drop_cooldown INT DEFAULT 0,
    boost_cooldown INT DEFAULT 0
    )''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY,
    card_name TEXT,
    card_group TEXT,
    card_rarity TEXT,
    card_theme TEXT,
    card_path TEXT,
    card_retired INT DEFAULT 0
    )''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS enabled_roles (
    guild_id INT,
    role_id INT,
    UNIQUE(guild_id, role_id)
    )''')

class Database:
    @staticmethod
    def connect():
        conn = sqlite3.connect('bot.db', timeout=5.0)
        c = conn.cursor()
        return c

    @staticmethod
    def execute(statement, *args):
        c = Database.connect()
        c.execute(statement, args)
        c.connection.commit()
        c.connection.close()

    @staticmethod
    def get(statement, *args):
        c = Database.connect()
        c.execute(statement, args)
        res = c.fetchall()
        c.connection.close()
        return res
