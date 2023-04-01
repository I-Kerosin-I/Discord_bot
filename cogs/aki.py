import akinator.exceptions
import discord as ds
from akinator.async_aki import Akinator
from discord import ButtonStyle as Style
from discord import slash_command
from discord import ui
from discord.commands.context import ApplicationContext
from discord.ext import commands
from discord.interactions import Interaction


class Aki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        name='aki',
        description='Загадайте персонажа и ответьте на несколько '
                    'вопросов, а я попытаюсь отгадать его.')
    @ds.guild_only()
    async def aki(self, ctx: ApplicationContext):
        await ctx.response.defer()

        async def user_check(inter):
            if inter.user != ctx.author:
                await inter.response.send_message(
                    'Это не ваша игра. Используйте '
                    '</aki:1078347283428548658>, чтобы начать свою',
                    ephemeral=True)
                return True

        class LoseEmbed(ds.Embed):
            def __init__(self, inter):
                super().__init__(
                    title=f'Браво, {inter.user}!',
                    description='Ты победил меня!',
                    colour=ds.Colour.gold())

        class PlayAgainView(ui.View):
            def __init__(self):
                super().__init__()

            @ds.ui.button(label='Играть снова', style=Style.green)
            async def play_again(self, btn, inter: Interaction):
                if await user_check(inter):
                    return
                await inter.response.defer()
                aki.attempts = 0
                aki.wrong_guesses = []
                q = await aki.start_game(language='ru')
                await inter.edit_original_response(embed=ds.Embed(
                    title='Вопрос 1',
                    description=q,
                    colour=ds.Colour.gold()), view=AnswerView())

        class WinView(ui.View):
            def __init__(self, guess):
                super().__init__()
                self.guess = guess

            @ds.ui.button(label='Да', style=Style.gray)
            async def yes_callback(self, btn, inter):
                if await user_check(inter):
                    return
                await inter.response.defer()
                embed = ds.Embed(title='Отлично, я снова угадал !',
                                 colour=ds.Colour.gold())
                embed.add_field(
                    name=self.guess['name'],
                    value=f'{self.guess["description"]}\n'
                          f'Рейтинг **#{self.guess["ranking"]}**')
                embed.set_thumbnail(
                    url=self.guess['absolute_picture_path'])
                await inter.edit_original_response(embed=embed,
                                                   view=PlayAgainView())
                await aki.close()

            @ds.ui.button(label='Нет', style=Style.gray)
            async def no_callback(self, btn, inter: Interaction):
                if await user_check(inter):
                    return
                await inter.response.defer()
                if aki.attempts < 4:
                    aki.wrong_guesses.append(self.guess['id'])
                    # [aki.wrong_guesses.append(i['id']) for i in aki.guesses]
                    await inter.edit_original_response(embed=ds.Embed(
                        title=f'Вопрос {aki.step + 1}',
                        description=aki.question,
                        colour=ds.Colour.gold()), view=AnswerView())
                else:
                    await inter.edit_original_response(embed=LoseEmbed(inter),
                                                       view=PlayAgainView())
                    await aki.close()

        class AnswerView(ui.View):
            def __init__(self):
                super().__init__()

            @ds.ui.button(label='Да', style=Style.gray)
            async def y_cb(self, btn, inter):
                await self.callback(inter, 'y')

            @ds.ui.button(label='Нет', style=Style.gray)
            async def n_cb(self, btn, inter):
                await self.callback(inter, 'n')

            @ds.ui.button(label='Я не знаю', style=Style.gray)
            async def i_cb(self, btn, inter):
                await self.callback(inter, 'i')

            @ds.ui.button(label='Скорее да', style=Style.gray)
            async def p_cb(self, btn, inter):
                await self.callback(inter, 'p')

            @ds.ui.button(label='Скорее нет', style=Style.gray)
            async def pn_cb(self, btn, inter):
                await self.callback(inter, 'pn')

            @ds.ui.button(label='Назад', style=Style.red)
            async def b_cb(self, btn, inter):
                await self.callback(inter, 'b')

            @staticmethod
            async def callback(inter: Interaction, ans):
                if await user_check(inter):
                    return
                await inter.response.defer()

                if ans == 'b':
                    try:
                        q = await aki.back()
                    except akinator.exceptions.CantGoBackAnyFurther:
                        await inter.followup.send(
                            'Это первый вопрос, дальше некуда', ephemeral=True)
                        return
                else:
                    q = await aki.answer(ans)

                if aki.progression > 85:
                    await aki.win()
                    aki.attempts += 1
                    if (guess := next((i for i in aki.guesses if
                                       i['id'] not in aki.wrong_guesses),
                                      None)) is None:
                        await inter.edit_original_response(
                            embed=LoseEmbed(inter),
                            view=PlayAgainView())
                        await aki.close()
                        return

                    embed = ds.Embed(title='Я думаю это',
                                     colour=ds.Colour.gold())
                    embed.add_field(
                        name=guess['name'],
                        value=f'{guess["description"]}\n'
                              f'Рейтинг **#{guess["ranking"]}**')
                    embed.set_image(
                        url=guess['absolute_picture_path'])
                    await inter.edit_original_response(embed=embed,
                                                       view=WinView(guess))
                else:
                    await inter.edit_original_response(
                        embed=ds.Embed(
                            title=f'Вопрос {aki.step + 1}',
                            description=q,
                            colour=ds.Colour.gold()))

        aki = Akinator()
        aki.attempts = 0
        aki.wrong_guesses = []

        await ctx.followup.send(embed=ds.Embed(
            title='Вопрос 1',
            description=await aki.start_game(language='ru'),
            colour=ds.Colour.gold()), view=AnswerView())


def setup(bot):
    bot.add_cog(Aki(bot))
    print('Aki cog loaded')
