import json
import os

import discord as ds
from discord.ext import commands

with open('config.json', 'r') as file:
    config = json.load(file)

bot = commands.Bot(intents=ds.Intents.all())

cog_files = [f'cogs.{filename[:-3]}' for filename in os.listdir('./cogs/') if
             filename.endswith('.py')]

bot.run(config['token'])
