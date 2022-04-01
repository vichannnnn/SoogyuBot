import sqlite3
from abc import ABC
import lightbulb
import yaml
import hikari
from os import listdir
from os.path import abspath
import miru
from PrefixDatabase import PrefixDatabase, prefix_dictionary

[prefix_dictionary.update({i[0]: i[1]}) for i in PrefixDatabase.get(f'SELECT guild_id, prefix FROM prefix')]

with open("authentication.yaml", "r", encoding="utf8") as stream:
    yaml_data = yaml.safe_load(stream)

intents = hikari.Intents.ALL
test_guilds = (660135595250810881, 948311226159624254, 958754866153537586)

async def determine_prefix(bot, message):
    try:
        current_prefix = prefix_dictionary[message.guild_id]
        return current_prefix
    except KeyError:
        PrefixDatabase.execute(''' REPLACE INTO prefix VALUES (?, ?) ''', message.guild_id, default_prefix)
        prefix_dictionary.update({message.guild_id: default_prefix})
        print(f"Error Detected: Created a prefix database for {message.guild_id}")

        return default_prefix


default_prefix = ';'


class Yuna(lightbulb.BotApp, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load_configuration(self):
        self.load_all_extensions()

    def load_all_extensions(self):
        for file in listdir(abspath("components/")):
            if file.endswith(".py"):
                f = file
                file = "components." + file[:-3]
                self.load_extensions(file)
                print(f"Successfully loaded {f[:-3]}")


def main():
    instance = Yuna(token=yaml_data['Token'], prefix=lightbulb.when_mentioned_or(determine_prefix),
                    default_enabled_guilds=test_guilds, intents=intents, help_class=None)
    miru.load(instance)

    @instance.listen()
    async def on_ready(event: hikari.StartedEvent) -> None:
        guilds = instance.rest.fetch_my_guilds()

        async for guild in guilds:
            try:
                PrefixDatabase.execute('INSERT INTO prefix VALUES (?, ?) ', guild.id, default_prefix)
            except sqlite3.IntegrityError:
                print(f"Prefix database already created for {guild} ({guild.id})")
        print(f"{instance.get_me().username} ({instance.get_me().id}) successfully started.")
        print(f"Currently in {await guilds.count()} guilds.")

    instance.load_configuration()
    instance.run()


main()
