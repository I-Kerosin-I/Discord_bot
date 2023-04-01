import database
from embeds import *

import discord as ds
from discord import Option
from discord.ext import commands
from discord import slash_command, user_command
from discord.commands.context import ApplicationContext


class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Db('bot.db')
        self.cur = self.db.cur
        self.conn = self.db.conn

    # Info
    @slash_command(name='info',
                   description='Информация о боте и все доступные команды')
    @ds.guild_only()
    async def info(self, ctx: ApplicationContext):
        await ctx.respond(embed=InfoEmbed(self.db.get_cfg(ctx.guild.id)
                                          ['warns_to_ban']), ephemeral=True)

    # Statistic command
    @slash_command(
        name='statistic',
        description='Показывает статистику предупреждений на сервере')
    @ds.guild_only()
    async def statistic(self, ctx: ApplicationContext):
        await ctx.response.defer(ephemeral=True)
        await ctx.followup.send(embed=StatisticEmbed(ctx, self.db))

    # Status command
    @slash_command(name='status',
                   description='Показывает количество предупреждений у вас или '
                               'у выбранного участника')
    @ds.guild_only()
    async def status(self, ctx: ApplicationContext, user: Option(
         ds.User,
         name='участник',
         description='Участник, чью статистику хотите посмотреть',
         required=False,
         default=None)):

        if user is None:
            user = ctx.user
        await ctx.respond(embed=StatusEmbed(ctx, self.db), ephemeral=True)

    @user_command(name='Статус')
    @ds.guild_only()
    async def user_status(self, ctx: ApplicationContext, user):
        await ctx.invoke(self.status, user)


def setup(bot):
    bot.add_cog(User(bot))
    print('User cog loaded')
