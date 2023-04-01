import string
import database
from embeds import *

import discord as ds
from discord import Option
from discord.ext import commands
from discord import slash_command, user_command
from discord.interactions import Interaction
from discord.commands.context import ApplicationContext


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Db('bot.db')
        self.cur = self.db.cur
        self.conn = self.db.conn

    # Max warns
    @slash_command(name='maxwarns',
                   description='Устанавливает количество предупреждений, '
                               'необходимое для бана')
    @ds.guild_only()
    @ds.default_permissions(administrator=True)
    async def maxwarns(self, ctx: ApplicationContext, warns_amount: Option(
        int, name='количество',
        description='кол-во предупреждений')):

        cfg = self.db.get_cfg(ctx.guild.id)

        if warns_amount >= cfg['warns_to_ban']:
            cfg['warns_to_ban'] = warns_amount
            self.db.set_cfg(ctx.guild.id, cfg)
            await ctx.respond(embed=ds.Embed(
                title=f'Количество предупреждений увеличено до  '
                      f'`{warns_amount}`'))

        elif users := self.cur.execute(
                f'SELECT * FROM id_{ctx.guild.id} WHERE count >= ?',
                (int(warns_amount),)).fetchall():

            async def yes_callback(inter: Interaction):
                await ctx.delete()
                await ctx.channel.send(embed=ds.Embed(
                    title=f'Количество предупреждений снижено до  `'
                          f'{warns_amount}`'))

                cfg['warns_to_ban'] = warns_amount
                self.db.set_cfg(ctx.guild.id, cfg)

                for i in users:
                    await ctx.guild.get_member(i[0]).ban(
                        reason='Нецензурная лексика')
                    self.db.del_user(ctx.guild.id, i[0])

            async def no_callback(inter):
                await ctx.delete()

            embed = WarningEmbed(
                description=f'При выполнении этого действия будут забанены'
                            f' {len(users)} участников, имеющих {warns_amount} '
                            f'и более предупреждений',
                yes_callback=yes_callback,
                no_callback=no_callback)

            await ctx.respond(embed=embed, view=embed.view, ephemeral=True)

        else:
            cfg['warns_to_ban'] = warns_amount
            self.db.set_cfg(ctx.guild.id, cfg)
            await ctx.respond(embed=ds.Embed(
                title=f'Количество предупреждений снижено до `{warns_amount}`'))

    # Add word
    @slash_command(name='addword',
                   description='Добавляет слово в список запрещённых. '
                               'Все спецсимволы удаляются автоматически')
    @ds.guild_only()
    @ds.default_permissions(administrator=True)
    async def addword(self, ctx: ApplicationContext, word: Option(
         str,
         name='слово',
         description='Новое запрещённое слово '
                    '(без пробелов и спецсимволов)')):

        words = self.db.get_words(ctx.guild.id)
        word = word.lower().translate(
            str.maketrans('', '', string.punctuation + ' '))

        if set(words).intersection({word}):
            await ctx.respond(embed=ErrorEmbed(
                description='Это слово уже есть в списке запрещённых!'),
                ephemeral=True)
        else:
            await ctx.respond(embed=AddWordEmbed(ctx, word))
            words.append(word)
            self.db.set_words(ctx.guild.id, words)

    # Delete word
    @slash_command(name='delword',
                   description='Удаляет слово из списка запрещённых. '
                               'Все спецсимволы удаляются автоматически')
    @ds.guild_only()
    @ds.default_permissions(administrator=True)
    async def delword(self, ctx: ApplicationContext, word: Option(
        str, name='слово',
        description='Разрешённое слово '
                    '(без пробелов и спецсимволов)')):

        words = self.db.get_words(ctx.guild.id)
        word = word.lower().translate(
            str.maketrans('', '', string.punctuation + ' '))

        if set(words).intersection({word}):
            words = list(set(words) - {word})
            self.db.set_words(ctx.guild.id, words)
            await ctx.respond(embed=DelWordEmbed(ctx, word))
        else:
            await ctx.respond(embed=ErrorEmbed(
                description=f'Слова `{word}` нет в списке запрещённых!'),
                ephemeral=True)

    # Remove warns
    @slash_command(name='remwarns',
                   description='Снимает все предупреждения с участника')
    @ds.guild_only()
    @ds.default_permissions(administrator=True)
    async def remwarns(self, ctx: ApplicationContext, user: Option(
        ds.User, name='участник',
        description='Участник, с которого нужно '
                    'снять предупреждения')):
        await ctx.respond(embed=ds.Embed(
            title='Предупреждения сняты!',
            description=f'С участника {user.mention} сняты все предупреждения '
                        f'администратором {ctx.author.mention}',
            colour=ds.Colour.blue()))
        self.db.del_user(ctx.guild.id, user.id)

    @user_command(name='Снять пред-ния')
    @ds.guild_only()
    @ds.default_permissions(administrator=True)
    async def user_remwarns(self, ctx: ApplicationContext, user: ds.member):
        await ctx.invoke(self.remwarns, user)

    # Warn
    @slash_command(name='warn',
                   description='Выдаёт предупреждение за нецензурную лексику '
                               'указанному участнику')
    @ds.guild_only()
    @ds.default_permissions(administrator=True)
    async def warn(self, ctx: ApplicationContext, user: Option(
        ds.User, name='участник',
        description='участник, которому нужно выдать предупреждение')):

        cfg = self.db.get_cfg(ctx.guild.id)
        warns = self.db.get_warns(ctx.guild.id, user.id, autoregister=True)

        if warns + 1 == cfg['warns_to_ban']:
            async def yes_callback(inter: Interaction):
                await user.ban(reason='Нецензурная лексика')
                self.db.del_user(ctx.guild.id, user.id)
                await ctx.response.edit_message(embed=BanEmbed(user))

            async def no_callback(inter):
                await ctx.delete()

            embed = WarningEmbed(
                description=f'При выполнении этого действия участник '
                            f'{user.mention} будет забанен',
                yes_callback=yes_callback,
                no_callback=no_callback)

            await ctx.respond(embed=embed, view=embed.view)
            return

        self.db.inc_warns(ctx.guild.id, user.id)
        warns += 1
        await ctx.respond(
            embed=WarnEmbed(user=user, admin=ctx.author,
                            warns=warns, maxwarns=cfg['warns_to_ban']))

    @user_command(name='Предупреждение')
    @ds.guild_only()
    @ds.default_permissions(administrator=True)
    async def user_warn(self, ctx: ApplicationContext, user: ds.member):
        await ctx.invoke(self.warn, user)

    # Clear all
    @slash_command(name='clearall',
                   description='Снимает все предупреждения со '
                               'всех участников на сервере')
    @ds.guild_only()
    @ds.default_permissions(administrator=True)
    async def clearall(self, ctx: ApplicationContext):

        async def yes_callback(inter: Interaction):
            self.cur.execute(f'DELETE FROM id_{inter.guild.id}')
            await ctx.delete()
            await ctx.channel.send(
                view=ui.View(),
                embed=StatisticClearEmbed(ctx))
            self.conn.commit()

        async def no_callback(inter: Interaction):
            await ctx.delete()

        embed = WarningEmbed(
            description='Вы уверены, что хотите снять все предупреждения со '
                        'всех участников на сервере?\n **Это действие нельзя '
                        'отменить!**',
            yes_callback=yes_callback,
            no_callback=no_callback)

        await ctx.respond(embed=embed, view=embed.view, ephemeral=True)


def setup(bot):
    bot.add_cog(Admin(bot))
    print('Admin cog loaded')
