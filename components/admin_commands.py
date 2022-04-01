import sqlite3
import datetime
import hikari
import lightbulb
import random
from PrefixDatabase import PrefixDatabase, prefix_dictionary
from components.class_component import Card, User, Inventory, Currency, Role
from Database import Database

plugin = lightbulb.Plugin("Admin Commands")
plugin.add_checks(lightbulb.checks.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))


def dmyConverter(seconds):
    """ Function to convert seconds directly into a statement with time left in days, hours, minutes and seconds. """

    seconds_in_days = 60 * 60 * 24
    seconds_in_hours = 60 * 60
    seconds_in_minutes = 60

    days = seconds // seconds_in_days
    hours = (seconds - (days * seconds_in_days)) // seconds_in_hours
    minutes = ((seconds - (days * seconds_in_days)) - (hours * seconds_in_hours)) // seconds_in_minutes
    seconds_left = seconds - (days * seconds_in_days) - (hours * seconds_in_hours) - (minutes * seconds_in_minutes)

    time_statement = ""

    if days != 0:
        time_statement += f"{round(days)} days, "
    if hours != 0:
        time_statement += f"{round(hours)} hours, "
    if minutes != 0:
        time_statement += f"{round(minutes)} minutes, "
    if seconds_left != 0:
        time_statement += f"{round(seconds_left)} seconds"
    if time_statement[-2:] == ", ":
        time_statement = time_statement[:-1]
    return time_statement


async def embed_creator(ctx: lightbulb.Context, title: str, description: str):
    colour = random.randint(0x0, 0xFFFFFF)
    embed = hikari.Embed(title=title, description=description, colour=hikari.Colour(colour))
    embed.set_footer(text=f"Command used by {ctx.author}", icon=ctx.author.display_avatar_url)
    return await ctx.respond(embed=embed)


@plugin.listener(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        await event.context.respond(
            f"Oh no! Something went wrong during invocation of command `{event.context.command.name}`.",
            delete_after=10)
        raise event.exception

    # Unwrap the exception to get the original cause
    exception = event.exception.__cause__ or event.exception

    if isinstance(exception, lightbulb.NotOwner):
        await event.context.respond(f"{event.context.author.mention}, You are not the owner of this bot.",
                                    delete_after=10, user_mentions=True)
    elif isinstance(exception, lightbulb.CommandIsOnCooldown):
        await event.context.respond(f"{event.context.author.mention}, "
                                    f"This command is on cooldown. Retry in {dmyConverter(exception.retry_after)}.",
                                    delete_after=10, user_mentions=True)
    elif isinstance(exception, lightbulb.MissingRequiredPermission):
        await event.context.respond(
            f"{event.context.author.mention}, You do not have the permission to run this command!", delete_after=10,
            user_mentions=True)
    else:
        raise exception


@plugin.command()
@lightbulb.option("symbol", "The new currency symbol or emote that you want to change to.", str)
@lightbulb.command("setcurrency", "Sets the currency symbol or emoji for your server. Administrator Only.",
                   auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def set_currency_command(ctx: lightbulb.Context) -> None:
    Currency(ctx.guild_id).change_symbol(ctx.options.symbol)
    await ctx.respond(
        f"{ctx.author.mention}, you've changed the currency emote to {ctx.options.symbol} for this server.")


@plugin.command()
@lightbulb.option("role", "The role that is able to use the privileged commands.", hikari.Role)
@lightbulb.command("addrole", "Adds a role into the privileged role list. Administrator Only.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def add_booster_role_command(ctx: lightbulb.Context) -> None:
    guild_booster_roles = Role(ctx.guild_id)
    try_add_role = guild_booster_roles.add_role(ctx.options.role)

    if not try_add_role:
        return await ctx.respond(f"{ctx.author.mention}, the role has already been added as a privileged role.")
    await ctx.respond(f"{ctx.author.mention}, the role has been successfully added as a privileged role.")


@plugin.command()
@lightbulb.option("role", "The role that is able to use the privileged commands.", hikari.Role)
@lightbulb.command("removerole", "Removes a role from the privileged role list. Administrator Only.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def remove_booster_role_command(ctx: lightbulb.Context) -> None:
    guild_booster_roles = Role(ctx.guild_id)
    try_remove_role = guild_booster_roles.delete_role(ctx.options.role)

    if not try_remove_role:
        return await ctx.respond(f"{ctx.author.mention}, the role is not part of the privileged role.")
    await ctx.respond(f"{ctx.author.mention}, the role has been successfully removed from a privileged role.")


@plugin.command()
@lightbulb.option("card_code", "The card ID that you're spawning.", str)
@lightbulb.command("spawn", "Spawns a card in your inventory. Administrator Only.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def spawn_command(ctx: lightbulb.Context) -> None:
    inventory_object = Inventory(ctx.author.id)
    card_object = Card(ctx.options.card_code)
    card_object.get_card_data()
    inventory_object.card_transaction(ctx.options.card_code, 1)
    inventory_object.get_card_quantity(ctx.options.card_code)
    embed = hikari.Embed(description=f"{ctx.author.mention} has spawned \n ```\n{ctx.options.card_code}\n```\n\n"
                                     f"Group:**{card_object.group}**\n"
                                     f"Name:**{int(card_object.rarity) * '⭐'} {card_object.name}**\n",
                         timestamp=datetime.datetime.now(tz=datetime.timezone.utc))
    embed.set_author(name=f"Spawn - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_footer(
        text=f"You have {inventory_object.quantity} cop{'ies' if inventory_object.quantity > 1 else 'y'} of this card.")
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.option("card_id", "The original unique ID of the card.", str)
@lightbulb.command("retire",
                   "Retires a card so that it can no longer be gotten from drops or dailies. Administrator Only.",
                   auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def retire_card_command(ctx: lightbulb.Context) -> None:
    card_object = Card(ctx.options.card_id)
    card_check = card_object.get_card_data()

    if not card_check:
        return await ctx.respond("Card unique ID does not exist. Please check if you're entered the correct ID.",
                                 flags=hikari.MessageFlag.EPHEMERAL)

    card_object.retire_card()
    embed = hikari.Embed(
        description=f"{ctx.author.mention} has retired \n ```\n{ctx.options.card_id}\n```\n\n"
                    f"Group: **{card_object.group}**\n"
                    f"Name: **{card_object.rarity}* {card_object.name}**\n")
    embed.set_author(name=f"Card Retired - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.option("card_id", "The original unique ID of the card.", str)
@lightbulb.command("resume", "Retires a card so that it can be gotten from drops again. Administrator Only.",
                   auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def resume_card_command(ctx: lightbulb.Context) -> None:
    card_object = Card(ctx.options.card_id)
    card_check = card_object.get_card_data()

    if not card_check:
        return await ctx.respond("Card unique ID does not exist. Please check if you're entered the correct ID.",
                                 flags=hikari.MessageFlag.EPHEMERAL)

    card_object.unretire_card()
    embed = hikari.Embed(
        description=f"{ctx.author.mention} has resumed \n ```\n{ctx.options.card_id}\n```\n\n"
                    f"Group: **{card_object.group}**\n"
                    f"Name: **{card_object.rarity}* {card_object.name}**\n")
    embed.set_author(name=f"Card Resumed - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.option("card_id", "The unique ID of the card.", str)
@lightbulb.option("card_name", "The new name of your card.", str)
@lightbulb.option("card_group", "The new group of your card.", str)
@lightbulb.option("card_rarity", "The new rarity of your card. (1-5)", int)
@lightbulb.option("card_theme", "The new theme of your card.", str)
@lightbulb.option("card_file_name", "The new file name of your card.", str)
@lightbulb.command("editcardproperty", "Edits a card's property from their ID. Administrator Only.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def edit_card_property_command(ctx: lightbulb.Context) -> None:
    card_object = Card(ctx.options.card_id)
    card_check = card_object.get_card_data()

    if not card_check:
        return await ctx.respond(
            "Card unique ID that you've entered does not exist. Please check if you're entered the correct ID.",
            flags=hikari.MessageFlag.EPHEMERAL)

    Database.execute(
        'REPLACE INTO cards (card_id, card_name, card_group, card_rarity, card_theme, card_path) VALUES (?, ?, ?, ?, ?, ?) ',
        ctx.options.card_id,
        ctx.options.card_name,
        ctx.options.card_group,
        ctx.options.card_rarity,
        ctx.options.card_theme,
        f'./data/{ctx.options.card_file_name}.png')

    card_object = Card(ctx.options.new_card_id)
    card_object.get_card_data()
    embed = hikari.Embed(
        description=f"{ctx.author.mention} has edited \n ```\n{ctx.options.card_id}\n```\n\n"
                    f"Group: **{card_object.group}**\n"
                    f"Name: **{card_object.rarity}* {card_object.name}**\n")
    embed.set_author(name=f"Card Edited - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.option("card_id", "The original unique ID of the card.", str)
@lightbulb.option("new_card_id", "The new unique ID of the card.", str)
@lightbulb.command("editcardid", "Edits a card's unique ID. Administrator Only.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def edit_card_id_command(ctx: lightbulb.Context) -> None:
    card_object = Card(ctx.options.new_card_id)
    card_check = card_object.get_card_data()

    if card_check:
        return await ctx.respond(
            "Card unique ID already exists. Please use a different ID to change to.",
            flags=hikari.MessageFlag.EPHEMERAL)

    card_object = Card(ctx.options.card_id)
    card_check = card_object.get_card_data()

    if not card_check:
        return await ctx.respond(
            "Card unique ID that you're changing from does not exist. Please check if you're entered the correct ID.",
            flags=hikari.MessageFlag.EPHEMERAL)

    Database.execute(' UPDATE inventory SET card_id = ? WHERE card_id = ? ', ctx.options.new_card_id,
                     ctx.options.card_id)
    Database.execute(' UPDATE cards SET card_id = ? WHERE card_id = ? ', ctx.options.new_card_id, ctx.options.card_id)
    Database.execute(' UPDATE user_profile SET fav = ? WHERE fav = ? ', ctx.options.new_card_id, ctx.options.card_id)
    card_object = Card(ctx.options.new_card_id)
    card_object.get_card_data()
    embed = hikari.Embed(
        description=f"{ctx.author.mention} has edited \n ```\n{ctx.options.card_id}\n```\n\n"
                    f"Group: **{card_object.group}**\n"
                    f"Name: **{card_object.rarity}* {card_object.name}**\n")
    embed.set_author(name=f"Card Edited - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.option("card_id", "The unique ID of your card.", str)
@lightbulb.option("card_name", "The name of your card.", str)
@lightbulb.option("card_group", "The group of your card.", str)
@lightbulb.option("card_rarity", "The rarity of your card. (1-5)", int)
@lightbulb.option("card_theme", "The theme of your card.", str)
@lightbulb.option("card_file_name", "The file name of your card.", str)
@lightbulb.command("addcard", "Adds a new card. Administrator Only.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def add_card_command(ctx: lightbulb.Context) -> None:
    if not 1 <= ctx.options.card_rarity <= 5:
        return await ctx.respond("Rarity has to be between 1 to 5.", flags=hikari.MessageFlag.EPHEMERAL)

    card_object = Card(ctx.options.card_id)
    card_check = card_object.get_card_data()

    if card_check:
        return await ctx.respond(
            "Card unique ID already exists. Please use a different ID or change the existing ID to another ID.",
            flags=hikari.MessageFlag.EPHEMERAL)

    try:
        Database.execute(
            'INSERT INTO cards (card_id, card_name, card_group, card_rarity, card_theme, card_path) VALUES (?, ?, ?, ?, ?, ?) ',
            ctx.options.card_id,
            ctx.options.card_name,
            ctx.options.card_group,
            ctx.options.card_rarity,
            ctx.options.card_theme,
            f'./data/{ctx.options.card_file_name}.png')

        user_list = [i[0] for i in Database.get(' SELECT user_id FROM user_profile ')]
        for user in user_list:
            Database.execute('INSERT INTO inventory (user_id, card_id) VALUES (?, ?) ', user, ctx.options.card_id)
    except sqlite3.IntegrityError:
        return await ctx.respond(
            "Card unique ID already exists. Please use a different ID or change the existing ID to another ID.",
            flags=hikari.MessageFlag.EPHEMERAL)

    card_object = Card(ctx.options.card_id)
    card_object.get_card_data()
    embed = hikari.Embed(
        description=f"{ctx.author.mention} has successfully created \n ```\n{ctx.options.card_id}\n```\n\n"
                    f"Group: **{card_object.group}**\n"
                    f"Name: **{card_object.rarity}* {card_object.name}**\n")
    embed.set_author(name=f"Card Created - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.option("prefix", "The new prefix of your server.", str)
@lightbulb.command("setprefix", "Updates the server's prefix. Administrator Only.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def setprefix(ctx: lightbulb.Context) -> None:
    PrefixDatabase.execute('UPDATE prefix SET prefix = ? WHERE guild_id = ? ', ctx.options.prefix, ctx.guild_id)
    embed = hikari.Embed(title="Prefix Successfully Updated",
                         description=f"Prefix for **{ctx.get_guild()}** is now set to `{ctx.options.prefix}`")
    prefix_dictionary.update({ctx.guild_id: ctx.options.prefix})
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.command("myprefix", "Checks for the server's prefix. Administrator Only.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def myprefix(ctx: lightbulb.Context) -> None:
    prefix = [i[0] for i in PrefixDatabase.get('SELECT prefix FROM prefix WHERE guild_id = ? ', ctx.guild_id)][0]
    embed = hikari.Embed(description=f"Prefix for **{ctx.get_guild()}** is `{prefix}`")
    await ctx.respond(embed=embed)


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
