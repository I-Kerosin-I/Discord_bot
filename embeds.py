import discord as ds
from discord import ui
from discord.commands.context import ApplicationContext


class InfoEmbed(ds.Embed):
    def __init__(self, maxwarns='—'):
        super().__init__(
            title=f'<:i_:1076535274277961748> Инфо',
            description='Привет! Я фильтратор 3000, моя задача - следить за '
                        'порядком в чате. Ниже представлены все доступные '
                        'команды. К некоторым функциям можно получить доступ, '
                        'нажав ПКМ по участнику и выбрав действие в списке '
                        'приложений.',
            colour=ds.Colour.blue())
        self.add_field(
            name='Команды для участников',
            value='</statistic:1074337419572301869> — статистика предупреждений'
                  '\n</status:1075421502326972466> — кол-во предупреждений '
                  'участника\n'
                  '</info:1074337419572301867> — это меню\n'
                  '</aki:1078347283428548658> — начать игру с акинатором')
        self.add_field(
            name='Команды для администраторов',
            value='</maxwarns:1077982791721046066> — максимальное кол-во '
                  f'предупреждений (текущ. `{maxwarns}`)\n'
                  '</remwarns:1077978599694553202> — снять предупреждения с '
                  'участника\n'
                  '</addword:1077978599694553200> — запретить слово\n'
                  '</delword:1077978599694553201> — разрешить слово\n'
                  '</clearall:1074702696457703545> — очистить статистику\n'
                  '</warn:1074762459153432687> — выдать предупреждение '
                  'участнику',
            inline=False)


class WarningEmbed(ds.Embed):
    def __init__(self, description, yes_callback, no_callback):
        super().__init__(
            title=':warning: Внимание!', description=description,
            colour=ds.Colour.yellow())

        btn_yes = ui.Button(emoji='✔️', style=ds.ButtonStyle.green)
        btn_no = ui.Button(emoji='✖️', style=ds.ButtonStyle.red)

        btn_yes.callback = yes_callback
        btn_no.callback = no_callback

        self.view = ui.View()
        self.view.add_item(btn_yes)
        self.view.add_item(btn_no)


class BanEmbed(ds.Embed):
    def __init__(self, user):
        super().__init__(
            title='БАН!',
            description=f'Участник {user.mention} был забанен за '
                        f'нецензурную лексику',
            colour=ds.Colour.from_rgb(255, 0, 0))


class WarnEmbed(ds.Embed):
    def __init__(self, user, warns, maxwarns, admin=None):
        super().__init__(
            title=':exclamation: Предупреждение', colour=ds.Colour.red(),
            description=f'%s \n'
                        f'Количество предупреждений {user.mention}:  `'
                        f'{warns}`\n'
                        f'Ещё `{maxwarns - warns}` предупреждений и '
                        f'участник будет забанен!' % (
                            f'Участник {user.mention} получил '
                            f'предупреждение за нецензурную лексику.'
                            if admin is None else

                            f'Участнику {user.mention} было выдано '
                            f'предупреждение '
                            f'администратором {admin.mention} за '
                            f'нецензурную '
                            f'лексику.'))


class StatisticEmbed(ds.Embed):
    def __init__(self, ctx: ApplicationContext, db):
        stats = db.cur.execute(
            f'SELECT * FROM id_{ctx.guild.id}').fetchall()
        super().__init__(
            title=':chart_with_upwards_trend: Статистика',
            color=ds.Color.red(),
            description='Здесь показано количество предупреждений, полученных '
                        'участниками за нецензурную лексику')
        if stats:
            self.add_field(
                name='Участники',
                value='\n'.join(
                    [ctx.guild.get_member(i[0]).mention for i in stats]),
                inline=True)
            self.add_field(
                name='предупреждения',
                value='\n'.join([f'`{i[1]}`' for i in stats]),
                inline=True)
        else:
            self.add_field(name='Пусто!', value='Здесь пока никого нет...')


class StatisticClearEmbed(ds.Embed):
    def __init__(self, ctx):
        super().__init__(
            title=':chart_with_upwards_trend: Статистика',
            description=f'Вся статистика сервера очищена '
                        f'администратором {ctx.author.mention}',
            colour=ds.Colour.green())


class StatusEmbed(ds.Embed):
    def __init__(self, ctx, db):
        super().__init__(
            title=f'<:i_:1076535274277961748> Статус', colour=ds.Colour.blue(),
            description=f'Количество предупреждений у {ctx.user.mention}:  '
                        f'`{db.get_warns(ctx.guild.id, ctx.user.id)}`')


class AddWordEmbed(ds.Embed):
    def __init__(self, ctx, word):
        super().__init__(
            title=':face_with_symbols_over_mouth: Запрещённое слово',
            description=f'Слово `{word}` было добавлено в список запрещённых '
                        f'администратором {ctx.author.mention}',
            colour=ds.Colour.red())


class DelWordEmbed(ds.Embed):
    def __init__(self, ctx, word):
        super().__init__(
            title=':partying_face: Разрешённое слово',
            description=f'Слово `{word}` было удалено из списка запрещённых '
                        f'администратором {ctx.author.mention}',
            colour=ds.Colour.green())


class ErrorEmbed(ds.Embed):
    def __init__(self, description):
        super().__init__(title=':x: Ошибка',
                         description=description,
                         colour=ds.Colour.from_rgb(255, 0, 0))
