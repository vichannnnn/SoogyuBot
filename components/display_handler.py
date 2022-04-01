import lightbulb
import miru
import hikari
import math
import asyncio

plugin = lightbulb.Plugin("Display Handler")

class Pages(miru.View):
    def __init__(self, n, data):
        super().__init__(timeout=60)
        self.value = 1
        self.data = data
        self.current_page = None
        self.n = n
        self.pages = math.ceil(len(self.data) / n)

    async def view_check(self, ctx: miru.Context) -> bool:
        # user who interacted with button == user who invoked command
        return ctx.interaction.user.id == ctx.user.id

    @miru.button(label="Previous", style=hikari.ButtonStyle.PRIMARY, emoji="◀", disabled=True)
    async def previous_button(self, button: miru.Button, ctx: miru.Context) -> None:

        self.value -= 1
        self.current_page = [item for item in self.data[self.n * (self.value - 1):self.value * self.n]]

        description = ""
        for id, name, group, rarity, theme, quantity in self.current_page:
            description += f'`{id}`|**{int(rarity) * "⭐"} {name}** ({theme}) - {quantity:,}\n'

        embed = hikari.Embed(description=description)
        embed.set_author(name=f"Inventory - {ctx.user}", url=str(ctx.user.display_avatar_url))
        embed.set_thumbnail(str(ctx.user.display_avatar_url))
        embed.set_footer(text=f"Page {self.value} of {self.pages}")

        if self.value <= 1:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False
        if self.value >= self.pages:
            self.children[1].disabled = True
        else:
            self.children[1].disabled = False
        await self.message.edit(embed=embed, components=self.build())

    @miru.button(label="Next", style=hikari.ButtonStyle.PRIMARY, emoji="▶")
    async def next_button(self, button: miru.Button, ctx: miru.Context) -> None:
        self.value += 1

        if self.value > self.pages:
            self.children[1].disabled = True
            return await self.message.edit(components=self.build())

        self.current_page = [item for item in self.data[self.n * (self.value - 1):self.value * self.n]]

        description = ""
        for id, name, group, rarity, theme, quantity in self.current_page:
            description += f'`{id}`|**{int(rarity) * "⭐"} {name}** ({theme}) - {quantity:,}\n'

        embed = hikari.Embed(description=description)
        embed.set_author(name=f"Inventory - {ctx.user}", url=str(ctx.user.display_avatar_url))
        embed.set_thumbnail(str(ctx.user.display_avatar_url))
        embed.set_footer(text=f"Page {self.value} of {self.pages}")

        if self.value <= 1:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False
        if self.value >= self.pages:
            self.children[1].disabled = True
        else:
            self.children[1].disabled = False
        await self.message.edit(embed=embed, components=self.build())

    @miru.button(label="Exit", style=hikari.ButtonStyle.DANGER, emoji="❎")
    async def cancel(self, button: miru.Button, ctx: miru.Context):
        embed = hikari.Embed(description="Successfully closed the command.")
        await self.message.edit(embed=embed, components=[])
        await asyncio.sleep(5)
        await self.message.edit()

    async def on_timeout(self) -> None:
        embed = hikari.Embed(description="Command has timed out. Please restart the command.")
        await self.message.edit(embed=embed, components=[])


class Confirm(miru.View):
    def __init__(self, user):
        self.value = None
        self.user: int = user
        super().__init__(timeout=300)

    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.interaction.user.id == self.user

    async def on_timeout(self) -> None:
        i = 0
        for button in self.children:
            if not i:
                button.emoji = "❎"
                button.label = "Timed Out"
                button.style = hikari.ButtonStyle.DANGER
                button.disabled = True
                i += 1
                continue
            self.remove_item(button)
        await self.message.edit(components=self.build())

    # Define a new Button with the Style of success (Green)
    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS, emoji="☑")
    async def confirm(self, button: miru.Button, ctx: miru.Context) -> None:
        await ctx.respond("Successfully confirmed.", flags=hikari.MessageFlag.EPHEMERAL)
        button.label = "Confirmed"
        button.emoji = "☑"
        button.disabled = True

        for b in self.children:
            if b is not button:
                self.remove_item(b)

        await self.message.edit(components=self.build())
        self.value = True
        self.stop()

    # Define a new Button that when pressed will stop the view & invalidate all the buttons in this view
    @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER, emoji="❎")
    async def stop_button(self, button: miru.Button, ctx: miru.Context) -> None:
        await ctx.respond("Successfully cancelled.", flags=hikari.MessageFlag.EPHEMERAL)
        button.label = "Cancelled"
        button.emoji = "❎"
        button.disabled = True

        for b in self.children:
            if b is not button:
                self.remove_item(b)

        await self.message.edit(components=self.build())
        self.value = False
        self.stop()


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
