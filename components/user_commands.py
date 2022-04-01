import hikari
import lightbulb
import random
from PrefixDatabase import PrefixDatabase, prefix_dictionary
from components.class_component import User, Card, Inventory, CooldownManager, Currency, Role, card_generator
from components.display_handler import Pages
import random
import datetime
import math

plugin = lightbulb.Plugin("User Commands")


def dmyConverter(seconds):
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


@plugin.command()
@lightbulb.option("biography", "The biography text that you want to set.", str)
@lightbulb.command("setbio", "You can set your biography for your user profile.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def set_biography_command(ctx: lightbulb.Context) -> None:
    user_object = User(ctx.author.id)
    user_object.set_biography(ctx.options.biography)
    await ctx.respond(f"Successfully set your biography.")


@plugin.command()
@lightbulb.option("user", "The user you're checking the inventory of. Optional.", hikari.Member, default=None)
@lightbulb.option("group", "The group you're checking.", str)
@lightbulb.command("inventory", "Checks the cards that you own of a group, you can check someone else's as well.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def inventory_command(ctx: lightbulb.Context) -> None:
    if ctx.options.user:
        target = ctx.get_guild().get_member(ctx.options.user).id
    else:
        target = ctx.author.id

    inventory_object = Inventory(target)
    group_data = inventory_object.get_group_owned(ctx.options.group)

    if not group_data:
        return await ctx.respond(
            f"{ctx.author.mention}, you do not have any cards belonging to **{ctx.options.group}**.")

    description = ''
    i = 1
    n = 15
    every_page = [item for item in group_data[n * (i - 1):i * n]]
    for id, name, group, rarity, theme, quantity in every_page:
        description += f'`{id}`|**{int(rarity) * "⭐"} {name}** ({theme}) - {quantity:,}\n'

    embed = hikari.Embed(description=description)
    embed.set_author(name=f"Inventory - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_footer(text=f"Page 1 of {math.ceil(len(group_data))}")
    embed.set_thumbnail(str(ctx.author.display_avatar_url))

    view = Pages(n, group_data)
    proxy = await ctx.respond(embed=embed, components=view.build())
    message = await proxy.message()
    view.start(message)


@plugin.command()
@lightbulb.command("cooldown", "Checks the cooldown of your commands.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def check_cooldown_command(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed()
    user_object = User(ctx.author.id)
    user_object.get_user_data()
    now = int(datetime.datetime.now().timestamp())
    drop_cd = user_object.drop_cooldown - now if (user_object.drop_cooldown - now) > 0 else "Ready"
    daily_cd = user_object.daily_cooldown - now if (user_object.daily_cooldown - now) > 0 else "Ready"
    work_cd = user_object.work_cooldown - now if (user_object.work_cooldown - now) > 0 else "Ready"
    description = f'{"✅" if drop_cd == "Ready" else "❌"} Drop: {dmyConverter(int(drop_cd)) if drop_cd != "Ready" else "Ready"}\n'
    description += f'{"✅" if daily_cd == "Ready" else "❌"} Daily: {dmyConverter(int(daily_cd)) if daily_cd != "Ready" else "Ready"}\n'
    description += f'{"✅" if work_cd == "Ready" else "❌"} Work: {dmyConverter(int(work_cd)) if work_cd != "Ready" else "Ready"}\n'
    embed.add_field(name='⏰ Cooldowns', value=description)
    embed.set_author(name=f"{ctx.author}'s Cooldown", url=str(ctx.author.display_avatar_url))
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.option("card_code", "The card ID that you're setting the favorite of.", str)
@lightbulb.command("setfav", "You can set a favorite card from your inventory to be displayed on your profile.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def set_favorite_command(ctx: lightbulb.Context) -> None:
    user_object = User(ctx.author.id)
    favorite_check = user_object.set_favorite_card(ctx.options.card_code)

    if not favorite_check:
        return await ctx.respond(
            f"You do not possess the card you're trying to favorite. Please make sure you own at least a copy of it. ",
            flags=hikari.MessageFlag.EPHEMERAL)

    await ctx.respond(f"Successfully set your favorite card to **ID {ctx.options.card_code}**.")


@plugin.command()
@lightbulb.option("card_code", "The card ID that you're viewing.", str)
@lightbulb.command("view", "Views a card that you own.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def view_card_command(ctx: lightbulb.Context) -> None:
    inventory_object = Inventory(ctx.author.id)
    inventory_object.get_card_quantity(ctx.options.card_code)

    if inventory_object.quantity <= 0:
        return await ctx.respond(f"{ctx.author.mention}, you do not own any **{ctx.options.card_code}** card.")

    card_object = Card(ctx.options.card_code)
    card_object.get_card_data()
    embed = hikari.Embed(description=f"**You're viewing:** ```\n{ctx.options.card_code}\n```\n\n"
                                     f"Group:**{card_object.group}**\n"
                                     f"Name:**{int(card_object.rarity) * '⭐'} {card_object.name}**\n",
                         timestamp=datetime.datetime.now(tz=datetime.timezone.utc))
    embed.set_author(name=f"Viewing Card - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_footer(
        text=f"You have {inventory_object.quantity} cop{'ies' if inventory_object.quantity > 1 else 'y'} of this card.")
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)

@plugin.command()
@lightbulb.option("currency", "The amount that you're sending.", int)
@lightbulb.option("user", "The user you're sending currency to.", hikari.Member)
@lightbulb.command("send", "Gifts currency that you own to someone else.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def gift_currency_command(ctx: lightbulb.Context) -> None:
    user_object = User(ctx.author.id)
    user_object.get_user_data()

    if ctx.get_guild().get_member(ctx.options.user).is_bot:
        return await ctx.respond(f"{ctx.author.mention}, you're not allowed to give currency to a bot.")

    if ctx.member.id == ctx.options.user.id:
        return await ctx.respond(f"{ctx.author.mention}, you cannot give yourself currency!")

    if user_object.balance < ctx.options.currency:
        return await ctx.respond(f"{ctx.author.mention}, you do not have enough currency to send.")

    giftee_member = ctx.get_guild().get_member(ctx.options.user)
    giftee_object = User(giftee_member.id)
    user_object.balance_transaction(-ctx.options.currency)
    giftee_object.balance_transaction(ctx.options.currency)

    await ctx.respond(f"{ctx.author.mention}, you've sent {ctx.options.currency:,} "
                      f"{Currency(ctx.guild_id).determine_symbol()} to {giftee_member.mention}.")

@plugin.command()
@lightbulb.option("card_code", "The card ID that you're gifting.", str)
@lightbulb.option("user", "The user you're gifting a card to.", hikari.Member)
@lightbulb.command("gift", "Gifts a card that you own to someone else.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def gift_card_command(ctx: lightbulb.Context) -> None:
    inventory_object = Inventory(ctx.author.id)
    inventory_object.get_card_quantity(ctx.options.card_code)

    if ctx.get_guild().get_member(ctx.options.user).is_bot:
        return await ctx.respond(f"{ctx.author.mention}, you're not allowed to give cards to a bot.")

    if ctx.member.id == ctx.options.user.id:
        return await ctx.respond(f"{ctx.author.mention}, you cannot give yourself cards!")

    if inventory_object.quantity <= 0:
        return await ctx.respond(f"{ctx.author.mention}, you do not own any **{ctx.options.card_code}** card.")

    inventory_object.card_transaction(ctx.options.card_code, -1)
    giftee_member = ctx.get_guild().get_member(ctx.options.user)
    giftee_object = Inventory(giftee_member.id)
    giftee_object.card_transaction(ctx.options.card_code, 1)

    card_object = Card(ctx.options.card_code)
    card_object.get_card_data()
    embed = hikari.Embed(description=f"**You've gifted:** ```\n{ctx.options.card_code}\n```\n\n"
                                     f"Group:**{card_object.group}**\n"
                                     f"Name:**{int(card_object.rarity) * '⭐'} {card_object.name}**\n",
                         timestamp=datetime.datetime.now(tz=datetime.timezone.utc))
    embed.set_author(name=f"Gifting Card - {ctx.author} to {giftee_member}", url=str(ctx.author.display_avatar_url))
    embed.set_footer(
        text=f"You have {inventory_object.quantity} cop{'ies' if inventory_object.quantity > 1 else 'y'} of this card.")
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.command("boosterdrop", "Get a random card from any rarity. 5 minutes cooldown. Booster Only.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def booster_drop_command(ctx: lightbulb.Context) -> None:
    required_roles = Role(ctx.guild_id).get_role_list()
    author_roles = [i.id for i in ctx.member.get_roles()]
    guild_object = ctx.get_guild()

    if not any([role in required_roles for role in author_roles]):
        return await ctx.respond(f"You do not have the required role to use this command.\n\nRequired Role: "
                                 f"{''.join([guild_object.get_role(i).mention for i in required_roles if guild_object.get_role(i)])}",
                                 flags=hikari.MessageFlag.EPHEMERAL)

    inventory_object = Inventory(ctx.author.id)
    cooldown_manager = CooldownManager(ctx.author.id)
    cooldown_manager.get_cooldown_state('BOOST')
    cooldown_check = cooldown_manager.update_cooldown()

    if not cooldown_check:
        seconds_left = cooldown_manager.get_cooldown()
        return await ctx.respond(f"Command is on cooldown. Please try again in {dmyConverter(seconds_left)}.",
                                 flags=hikari.MessageFlag.EPHEMERAL)

    generated_card_id = card_generator()
    card_object = Card(generated_card_id)
    card_object.get_card_data()
    inventory_object.card_transaction(generated_card_id, 1)
    inventory_object.get_card_quantity(generated_card_id)
    embed = hikari.Embed(description=f"{ctx.author.mention} has dropped \n ```\n{generated_card_id}\n```\n\n"
                                     f"Group:**{card_object.group}**\n"
                                     f"Name:**{int(card_object.rarity) * '⭐'} {card_object.name}**\n",
                         timestamp=datetime.datetime.now(tz=datetime.timezone.utc))
    embed.set_author(name=f"Drop - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_footer(
        text=f"You have {inventory_object.quantity} cop{'ies' if inventory_object.quantity > 1 else 'y'} of this card.")
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.command("drop", "Get a random card from any rarity. 5 minutes cooldown.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def drop_command(ctx: lightbulb.Context) -> None:
    inventory_object = Inventory(ctx.author.id)
    cooldown_manager = CooldownManager(ctx.author.id)
    cooldown_manager.get_cooldown_state('DROP')
    cooldown_check = cooldown_manager.update_cooldown()

    if not cooldown_check:
        seconds_left = cooldown_manager.get_cooldown()
        return await ctx.respond(f"Command is on cooldown. Please try again in {dmyConverter(seconds_left)}.",
                                 flags=hikari.MessageFlag.EPHEMERAL)
    generated_card_id = card_generator()
    card_object = Card(generated_card_id)
    card_object.get_card_data()
    inventory_object.card_transaction(generated_card_id, 1)
    inventory_object.get_card_quantity(generated_card_id)
    embed = hikari.Embed(description=f"{ctx.author.mention} has dropped \n ```\n{generated_card_id}\n```\n\n"
                                     f"Group:**{card_object.group}**\n"
                                     f"Name:**{int(card_object.rarity) * '⭐'} {card_object.name}**\n",
                         timestamp=datetime.datetime.now(tz=datetime.timezone.utc))
    embed.set_author(name=f"Drop - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_footer(
        text=f"You have {inventory_object.quantity} cop{'ies' if inventory_object.quantity > 1 else 'y'} of this card.")
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.command("daily", "Get a random card from any rarity and gives you 2,500 balance. 24 hours cooldown.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def daily_command(ctx: lightbulb.Context) -> None:
    user_object = User(ctx.author.id)
    inventory_object = Inventory(ctx.author.id)
    cooldown_manager = CooldownManager(ctx.author.id)
    cooldown_manager.get_cooldown_state('DAILY')
    cooldown_check = cooldown_manager.update_cooldown()

    if not cooldown_check:
        seconds_left = cooldown_manager.get_cooldown()
        return await ctx.respond(f"Command is on cooldown. Please try again in {dmyConverter(seconds_left)}.",
                                 flags=hikari.MessageFlag.EPHEMERAL)
    generated_card_id = card_generator()
    card_object = Card(generated_card_id)
    card_object.get_card_data()
    user_object.balance_transaction(2500)
    inventory_object.card_transaction(generated_card_id, 1)
    inventory_object.get_card_quantity(generated_card_id)
    embed = hikari.Embed(description=f"{ctx.author.mention} has dropped \n ```\n{generated_card_id}\n```\n\n"
                                     f"Group:**{card_object.group}**\n"
                                     f"Name:**{int(card_object.rarity) * '⭐'} {card_object.name}**\n",
                         timestamp=datetime.datetime.now(tz=datetime.timezone.utc))
    embed.set_author(name=f"Drop - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_image(card_object.path)
    await ctx.respond(embed=embed)
    embed = hikari.Embed(description=f"You've claimed your daily and gotten 2,500 "
                                     f"{Currency(ctx.guild_id).determine_symbol()}!",
                         timestamp=datetime.datetime.now(tz=datetime.timezone.utc))
    embed.set_author(name=f"Daily - {ctx.author}", url=str(ctx.author.display_avatar_url))
    embed.set_footer(
        text=f"You have {inventory_object.quantity} cop{'ies' if inventory_object.quantity > 1 else 'y'} of this card.")
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.command("work", "Allows you to get between 500 - 1,500 balance every 30 minutes.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def work_command(ctx: lightbulb.Context) -> None:
    user_object = User(ctx.author.id)
    cooldown_manager = CooldownManager(ctx.author.id)
    cooldown_manager.get_cooldown_state('WORK')
    cooldown_check = cooldown_manager.update_cooldown()

    if not cooldown_check:
        seconds_left = cooldown_manager.get_cooldown()
        return await ctx.respond(f"Command is on cooldown. Please try again in {dmyConverter(seconds_left)}.",
                                 flags=hikari.MessageFlag.EPHEMERAL)

    amount_gotten = random.choice(range(500, 1501))
    user_object.balance_transaction(amount_gotten)
    embed = hikari.Embed(description=f"You worked as an idol and got {amount_gotten:,} "
                                     f"{Currency(ctx.guild_id).determine_symbol()}!",
                         timestamp=datetime.datetime.now(tz=datetime.timezone.utc))
    embed.set_author(name=f"Work - {ctx.author}", url=str(ctx.author.display_avatar_url))
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.command("profile", "Allows you to see your own bio, favorite card and amount of total cards owned.",
                   auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def profile_command(ctx: lightbulb.Context) -> None:
    user_object = User(ctx.author.id)
    user_inventory = Inventory(ctx.author.id)
    user_inventory.get_cards_owned()
    user_object.get_user_data()
    embed = hikari.Embed()
    embed.set_thumbnail(ctx.author.display_avatar_url)
    embed.set_author(name=f"{ctx.author}'s Profile", url=str(ctx.author.display_avatar_url))
    if user_object.bio:
        embed.add_field(name=f"BIO:", value=user_object.bio)
    embed.add_field(name=f"Cards:", value=f"{user_inventory.cards_owned:,}")
    embed.add_field(name=f"Currensan:", value=f"{user_object.balance:,} {Currency(ctx.guild_id).determine_symbol()}")

    if user_object.fav:
        fav_card_object = Card(user_object.fav)
        fav_card_object.get_card_data()
        embed.add_field(name=f"Favorite Card:", value=f"{int(fav_card_object.rarity) * '⭐'} __{fav_card_object.name}__")
        embed.set_image(fav_card_object.path)

    await ctx.respond(embed=embed)


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
