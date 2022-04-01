import lightbulb
import miru
import hikari
from PrefixDatabase import prefix_dictionary

plugin = lightbulb.Plugin("Help Commands")


class HelpDropdown(miru.Select):
    def __init__(self, bot, header, selections, icon_url):
        self.bot = bot
        self.icon_url = icon_url
        options = []
        for row in selections:
            options.append(miru.SelectOption(label=row))
        super().__init__(placeholder=header, min_values=1, max_values=1, options=options)

    async def callback(self, ctx: lightbulb.Context) -> None:
        current_prefix = prefix_dictionary[ctx.guild_id]
        labels = [i.label for i in self.options]
        idx = labels.index(self.values[0])
        name = str(self.options[idx].label)
        self.view.value = name

        embed = hikari.Embed(title=f"{name} Help")
        embed.set_thumbnail(self.icon_url)
        embed.set_footer(
            text=f"React for more category help! :: {ctx.get_guild()}'s prefix currently is {current_prefix}",
            icon=self.bot.application.icon_url)

        commands = list(set([commands.name for commands in self.bot.get_plugin(name).all_commands]))

        for comm in commands:
            comm_object = self.bot.get_slash_command(comm)
            embed.add_field(name=f"{current_prefix}{comm_object.name}",
                            value=comm_object.description, inline=True)

        await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)


class View(miru.View):
    def __init__(self, item, bot):
        self.item = item
        self.bot = bot
        super().__init__(timeout=300)
        self.add_item(self.item)

    async def on_timeout(self) -> None:
        self.clear_items()
        self.add_item(miru.Select(placeholder="Command Timed-out", disabled=True, options=[miru.SelectOption(label='Placeholder')]))
        embed = hikari.Embed(description="Help command has timed out. Please restart the command.")
        await self.message.edit(embed=embed, components=self.build())

    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.interaction.user == ctx.user


@plugin.command
@lightbulb.command("help", "Help command to navigate the bot.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def help(ctx: lightbulb.Context):
    cogs = [ctx.bot.get_plugin(cog) for cog in ctx.bot.plugins if ctx.bot.get_plugin(cog).name != "Help Commands" and ctx.bot.get_plugin(cog).all_commands]
    current_prefix = prefix_dictionary[ctx.guild_id]

    embed = hikari.Embed(description=f"Type `{current_prefix}myprefix` for this server's prefix.\n"
                                     f"Type `{current_prefix}setprefix` to change the prefix for this server.")
    embed.set_author(name=f"{str(ctx.bot.get_me().username).partition('#')[0]}'s Commands and Help",
                     icon=ctx.bot.application.icon_url)
    embed.set_thumbnail(ctx.bot.application.icon_url)
    embed.set_footer(
        text=f"Select for more category help! :: The {ctx.get_guild()}'s prefix is currently {current_prefix}",
        icon=ctx.bot.application.icon_url)

    for cog in cogs:
        commands_list = ''
        lst = list(set([commands.name for commands in cog.all_commands]))
        for command in lst:
            commands = ctx.bot.get_slash_command(command)
            commands_list += f'`{commands.name}` '
        embed.add_field(name=cog.name, value=commands_list, inline=False)

    lst = [cog.name for cog in cogs]
    view = View(HelpDropdown(ctx.bot, "Choose a category", lst, ctx.bot.application.icon_url), ctx.bot)
    proxy = await ctx.respond(embed=embed, components=view.build())
    message = await proxy.message()
    view.start(message)
    await view.wait()


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
