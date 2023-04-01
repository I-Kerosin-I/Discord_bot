import string
import database
from discord.ext import commands
from embeds import *


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Db('bot.db')
        self.cur = self.db.cur
        self.conn = self.db.conn

    @commands.Cog.listener(name='on_ready')
    async def on_ready(self):
        self.db.sync(self.bot.guilds)
        if self.conn:
            print('Database synchronized')

    @commands.Cog.listener(name='on_guild_join')
    async def on_guild_join(self, guild: ds.Guild):
        self.db.add_guild(guild.id)
        await guild.system_channel.send(embed=InfoEmbed(3))

    @commands.Cog.listener(name='on_guild_remove')
    async def on_guild_remove(self, guild: ds.Guild):
        self.db.del_guild(guild.id)

    @commands.Cog.listener(name='on_member_join')
    async def on_member_join(self, member: ds.Member):
        await member.send(embed=InfoEmbed())

    @commands.Cog.listener(name='on_message')
    async def on_message(self, msg):
        if msg.guild is None or msg.author.id == self.bot.application_id:
            return None
        words = set(self.db.get_words(msg.guild.id))
        if {i.lower().translate(str.maketrans('', '', string.punctuation)) for i
            in msg.content.split(' ')}.intersection(words) != set():

            await msg.delete()

            cfg = self.db.get_cfg(msg.guild.id)
            warns = self.db.get_warns(msg.guild.id, msg.author.id,
                                      autoregister=True)

            if warns + 1 < cfg['warns_to_ban']:
                self.db.inc_warns(msg.guild.id, msg.author.id)
                await msg.channel.send(
                    embed=WarnEmbed(msg.author, warns + 1, cfg['warns_to_ban']))

            elif warns == cfg['warns_to_ban']:
                self.db.del_user(msg.guild.id, msg.author.id)
                await msg.channel.send(embed=BanEmbed(msg.author))
                await msg.author.ban(reason='Нецензурная лексика')


def setup(bot):
    bot.add_cog(Events(bot))
    print('Events cog loaded')
