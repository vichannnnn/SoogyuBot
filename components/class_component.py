from dataclasses import dataclass, field
from Database import Database
from typing import List
import datetime
import random
import lightbulb
import hikari
import sqlite3

plugin = lightbulb.Plugin("Class Component")


class __Member:
    def __init__(self, list: List[int]):
        self.list = list


class __Inventory:
    def __init__(self, list: List[str]):
        self.list = list


lst = [i[0] for i in Database.get('SELECT user_id FROM user_profile ')]
member_list = __Member(lst).list
inv_list = [i[0] for i in Database.get('SELECT card_id FROM cards ')]
inventory_list = __Inventory(inv_list).list


def profile_create(user: hikari.Member):
    try:
        Database.execute('INSERT INTO user_profile (user_id) VALUES (?) ', user.id)
        print(f"Created profile for User {user} ({user.id})")
        for card_id in inv_list:
            Database.execute('INSERT INTO inventory (user_id, card_id) VALUES (?, ?) ', user.id, card_id)
            print(f"Created Card #{card_id} for User {user} ({user.id})")

    except sqlite3.IntegrityError:
        print(f"User {user} ({user.id}) already has a user profile created.")


@plugin.listener(hikari.StartedEvent)
async def on_ready(event: hikari.StartedEvent) -> None:
    guilds = event.app.rest.fetch_my_guilds()

    async for guild in guilds:
        members = await event.app.rest.fetch_members(guild)
        for member in members:
            if not member.is_bot:
                if member.id not in member_list:
                    profile_create(member)
                    member_list.append(member.id)


@plugin.listener(hikari.GuildJoinEvent)
async def on_guild_join(event: hikari.GuildJoinEvent) -> None:
    for member in event.guild.get_members():
        if not member.is_bot:
            if member.id not in member_list:
                profile_create(member)
                member_list.append(member.id)


@plugin.listener(hikari.MemberCreateEvent)
async def on_member_join(event: hikari.MemberCreateEvent) -> None:
    if event.member.id not in member_list:
        if not event.member.is_bot:
            profile_create(event.member)
            member_list.append(event.member.id)


def card_generator():
    rarity = {
        1: 0.4,
        2: 0.25,
        3: 0.2,
        4: 0.1,
        5: 0.05
    }

    chosen_rarity = random.choices([i for i in rarity.keys()], weights=[i for i in rarity.values()], k=1)
    all_card_data = [i[0] for i in
                     Database.get(' SELECT card_id FROM cards WHERE card_rarity = ? AND card_retired = ? ',
                                  chosen_rarity[0], 0)]
    chosen_card = random.choice(all_card_data)
    return chosen_card


@dataclass
class Currency:
    guild_id: int
    symbol: str = None

    def determine_symbol(self):
        guild_currency = [i[0] for i in
                          Database.get('SELECT currency_symbol FROM guild_currency_symbol WHERE guild_id = ? ',
                                       self.guild_id)]

        if guild_currency:
            self.symbol = guild_currency[0]
            return self.symbol

        Database.execute('INSERT INTO guild_currency_symbol (guild_id) VALUES (?) ', self.guild_id)
        self.symbol = [i[0] for i in Database.get('SELECT currency_symbol FROM guild_currency_symbol WHERE guild_id = ? ', self.guild_id)][0]
        return self.symbol

    def change_symbol(self, new_symbol: str):
        Database.execute(' REPLACE INTO guild_currency_symbol VALUES (?, ?) ', self.guild_id, new_symbol)
        self.symbol = new_symbol


@dataclass
class Role:
    guild_id: int
    role_list: List = field(default_factory=list)

    def get_role_list(self):
        self.role_list = [i[0] for i in
                          Database.get('SELECT role_id FROM enabled_roles WHERE guild_id = ? ', self.guild_id)]
        return self.role_list

    def add_role(self, role: hikari.Role):
        self.get_role_list()
        if role.id in self.role_list:
            return False
        Database.execute('INSERT INTO enabled_roles VALUES (?, ?) ', self.guild_id, role.id)
        return True

    def delete_role(self, role: hikari.Role):
        self.get_role_list()
        if role.id not in self.role_list:
            return False
        Database.execute('DELETE FROM enabled_roles WHERE role_id = ? ', role.id)
        return True


@dataclass
class CooldownManager:
    user_id: int
    cooldown_type: str = None
    cooldown_timestamp: int = None
    cooldown_state = None
    cooldown_duration = None

    def get_cooldown_state(self, type: str):
        now = datetime.datetime.now().timestamp()
        user_object = User(self.user_id)
        user_object.get_user_data()
        accepted_input = ['DROP', 'DAILY', 'WORK', 'BOOST']
        if type not in accepted_input:
            raise TypeError("Cooldown type has to be either DROP, DAILY, BOOST or WORK.")
        if type == "DROP":
            self.cooldown_timestamp = user_object.drop_cooldown
            self.cooldown_duration = 300
        elif type == "DAILY":
            self.cooldown_timestamp = user_object.daily_cooldown
            self.cooldown_duration = 86400
        elif type == "WORK":
            self.cooldown_timestamp = user_object.work_cooldown
            self.cooldown_duration = 1800
        else:
            self.cooldown_timestamp = user_object.booster_drop_cooldown
            self.cooldown_duration = 300

        self.cooldown_type = type
        if now > self.cooldown_timestamp:
            self.cooldown_state = True
        else:
            self.cooldown_state = False

    def update_cooldown(self):
        if not self.cooldown_type:
            raise TypeError(
                "Cooldown type is not defined yet. Please call the get_cooldown function before call this function.")

        now = datetime.datetime.now().timestamp()
        if self.cooldown_state:
            new_cooldown = now + self.cooldown_duration
            Database.execute(f'UPDATE user_profile SET {self.cooldown_type.lower()}_cooldown = ? WHERE user_id = ? ',
                             new_cooldown, self.user_id)
            return True
        return False

    def get_cooldown(self):
        now = datetime.datetime.now().timestamp()
        remaining_cooldown = self.cooldown_timestamp - now
        return remaining_cooldown


@dataclass
class User:
    user_id: int
    bio: str = None
    fav: int = None
    balance: int = None
    drop_cooldown: int = None
    daily_cooldown: int = None
    work_cooldown: int = None
    booster_drop_cooldown: int = None

    def set_favorite_card(self, card_id: str):
        user_inventory = Inventory(self.user_id)
        user_inventory.get_card_quantity(card_id)

        if not user_inventory.quantity:
            return False

        Database.execute(' UPDATE user_profile SET fav = ? WHERE user_id = ? ', card_id, self.user_id)
        return True

    def set_biography(self, biography: str):
        Database.execute(' UPDATE user_profile SET bio = ? WHERE user_id = ? ', biography, self.user_id)

    def get_user_data(self):
        data = [i for i in Database.get('SELECT * FROM user_profile WHERE user_id = ? ', self.user_id)]

        if data:
            self.user_id, self.balance, self.bio, self.fav, self.daily_cooldown, self.work_cooldown, self.drop_cooldown, self.booster_drop_cooldown = \
                data[0]

    def balance_transaction(self, amount: int):
        if self.balance is None:
            self.get_user_data()
        self.balance += amount
        Database.execute(' UPDATE user_profile SET balance = ? WHERE user_id = ? ', self.balance, self.user_id)


@dataclass
class Card:
    card_id: str
    name: str = None
    group: str = None
    rarity: int = None
    theme: str = None
    path: str = None
    retired: int = None

    def unretire_card(self):
        Database.execute('UPDATE cards SET card_retired = ? WHERE card_id = ? ', 0, self.card_id)

    def retire_card(self):
        Database.execute('UPDATE cards SET card_retired = ? WHERE card_id = ? ', 1, self.card_id)

    def get_card_data(self):
        data = [i for i in Database.get('SELECT * FROM cards WHERE card_id = ? ', self.card_id)]

        if data:
            self.card_id, self.name, self.group, self.rarity, self.theme, self.path, self.retired = data[0]
            return True
        return False


@dataclass
class Inventory:
    user_id: int
    card_id: str = None
    quantity: int = None
    full_inventory: List = field(default_factory=list)
    cards_owned: int = None

    def get_cards_owned(self):
        data = [i[0] for i in
                Database.get('SELECT COUNT(*) FROM inventory WHERE user_id = ? AND quantity > 0', self.user_id)]

        if data:
            self.cards_owned = data[0]
        else:
            self.cards_owned = 0

    def get_group_owned(self, group: str):
        data = [i for i in
                Database.get(
                    'SELECT inventory.card_id, inventory.quantity FROM inventory INNER JOIN cards ON cards.card_id = inventory.card_id '
                    'WHERE cards.card_group = ? AND inventory.user_id = ? AND inventory.quantity > 0', group,
                    self.user_id)]
        if data:
            cards_data = []
            for id, quantity in data:
                card_object = Card(id)
                card_object.get_card_data()
                cards_data.append([card_object.card_id, card_object.name,
                                   card_object.group, card_object.rarity,
                                   card_object.theme, quantity])
            return cards_data
        else:
            return None

    def get_entire_inventory(self):
        data = [i for i in Database.get('SELECT card_id, quantity FROM inventory WHERE user_id = ? ', self.user_id)]

        if data:
            self.full_inventory = data

    def get_card_quantity(self, card_id: int):
        data = [i[0] for i in
                Database.get('SELECT quantity FROM inventory WHERE user_id = ? AND card_id = ? ', self.user_id,
                             card_id)]

        if data:
            self.quantity = data[0]
            self.card_id = card_id

    def card_transaction(self, card_id: str, quantity: int):
        self.get_card_quantity(card_id)
        try:
            self.quantity += quantity

        except TypeError:
            return None

        Database.execute('UPDATE inventory SET quantity = ? WHERE card_id = ? AND user_id = ? ', self.quantity,
                         self.card_id, self.user_id)
        return self.quantity


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
