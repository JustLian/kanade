import hikari
import crescent
import kanade
import asyncio
import re
from kanade import db
from kanade.core.hooks import is_server_manager
from kanade.core.bot import Model


plugin = crescent.Plugin[hikari.GatewayBot, Model]()


class Patterns:
    text_channel = re.compile(r'<#[0-9]+>')


settings = {
    'logs': {
        '_': 'логи',
        'join': ('вход', hikari.GuildTextChannel),
        'quit': ('выход', hikari.GuildTextChannel),
        'kick': ('кик/бан', hikari.GuildTextChannel),
        'invites': ('приглашения', hikari.GuildTextChannel),
        'messages': ('сообщения', hikari.GuildTextChannel),
        'roles': ('роли', hikari.GuildTextChannel)
    },
    'greetings': {
        '_': 'сообщения при входе',
        'title': ('заголовок', str),
        'description': ('описание', str),
        'channel': ('канал', hikari.GuildTextChannel),
        'enabled': ('включить?', bool),
        'color': ('цвет сообщения (HEX)', str),
        'glow_color1': ('первый цвет подсветки (HEX)', str),
        'glow_color2': ('второй цвет подсветки (HEX)', str),
        'border_color1': ('первый цвет рамки (HEX)', str),
        'border_color2': ('второй цвет рамки (HEX)', str)
    },
    'farewell': {
        '_': 'сообщения при выходе',
        'title': ('заголовок', str),
        'description': ('описание', str),
        'channel': ('канал', hikari.GuildTextChannel),
        'enabled': ('включить?', bool),
        'color': ('цвет (HEX)', str)
    }
}


async def section_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
):
    # return toolbox.as_command_choices([[settings[key]['_'], key] for key in settings.keys()])
    return [[settings[key]['_'], key] for key in settings.keys()]


async def key_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
):
    if 'section' not in ctx.options:
        return []
    if ctx.options['section'] not in settings:
        return []
    
    # return toolbox.as_command_choices([[v[0], k] for k, v in settings[
    #     ctx.options['section']
    # ].items() if k != '_'])
    return [[v[0], k] for k, v in settings[
        ctx.options['section']
    ].items() if k != '_']


async def parse_param(msg: hikari.Message, t):

    if t == hikari.GuildTextChannel:
        matches = Patterns.text_channel.findall(msg.content)
        if len(matches) == 0:
            return None
        c = await plugin.client.app.rest.fetch_channel(matches[0][2:-1])
        
        if not isinstance(c, hikari.GuildTextChannel):
            return None
        if c.guild_id != msg.guild_id:
            return None
        
        return (c.id, c.mention)

    if t == str:
        val = msg.content
        if val.startswith('```'):
            val = val[3:]
        if val.endswith('```'):
            val = val[:-3]
        
        if val.startswith('`'):
            val = val[1:]
        if val.endswith('`'):
            val = val[:-1]

        if len(val) == 0:
            return (None, '`пусто`')
        
        return (val, val)

    if t == bool:
        if '+' in msg.content:
            return (True, '+')
        
        elif '-' in msg.content:
            return (False, '-')

    return None


@plugin.include
@crescent.hook(is_server_manager)
@crescent.command(
    name='dashboard_access',
    description='Выдать/забрать права на управление ботом через веб-панель (kanade.ekr.moe/dashboard)'
)
class DashAccess:
    target_user = crescent.option(hikari.User, 'Пользователь')
    toggle = crescent.option(str, 'Выдать права?', choices=(('да', '1'), ('нет', '0')))

    async def callback(self, ctx: crescent.Context):
        if int(self.toggle):
            prev_managers = (await plugin.model.db_guilds.find_one({'_id': ctx.guild_id}))['managers']
            if self.target_user.id not in prev_managers:
                prev_managers.append(self.target_user.id)
                plugin.model.db_guilds.update_one({'_id': ctx.guild_id}, {'$set': {'managers': prev_managers}})

            await ctx.respond(embed=hikari.Embed(
                title='Права выданы',
                description='Теперь {} может управлять ботом через https://kanade.ekr.moe'.format(
                    self.target_user.mention
                ), color=kanade.Colors.SUCCESS
            ))
            return

        prev_managers = (await plugin.model.db_guilds.find_one({'_id': ctx.guild_id}))['managers']
        if self.target_user.id in prev_managers:
            prev_managers.remove(self.target_user.id)
            plugin.model.db_guilds.update_one({'_id': ctx.guild_id}, {'$set': {'managers': prev_managers}})
        
        await ctx.respond(embed=hikari.Embed(
            title='Права удалены',
            description='Теперь {} не может управлять ботом через сайт'.format(
                self.target_user.mention
            ), color=kanade.Colors.SUCCESS
        ))


@plugin.include
@crescent.hook(is_server_manager)
@crescent.command(
    name='settings',
    description='Изменить настройки этого сервера'
)
class Settings:
    section = crescent.option(str, 'Категория настроек', autocomplete=section_autocomplete)
    key = crescent.option(str, 'Параметр', autocomplete=key_autocomplete)

    async def callback(self, ctx: crescent.Context):
        if self.section not in list(settings.keys()):
            return await ctx.respond(embed=hikari.Embed(
                title='Ошибка параметров',
                description='Выбранная вами категория не существует',
                color=kanade.Colors.ERROR
            ))

        if self.key not in settings[self.section]:
            return await ctx.respond(embed=hikari.Embed(
                title='Ошибка параметров',
                description='Выбранный вами параметр не существует',
                color=kanade.Colors.ERROR
            ))

        embed = hikari.Embed(
            title='Новое значение',
            color=kanade.Colors.WAIT
        )
        t = settings[self.section][self.key][1]
        if t == hikari.GuildTextChannel:
            embed.description = 'Введите упоминание текстового канал'

        elif t == str:
            embed.description = 'Введите новое текстовое значение (можно использовать \\`\\`\\`ЗНАЧЕНИЕ\\`\\`\\`)'

        elif t == bool:
            embed.description = 'Отправьте + или -'

        else:
            return await ctx.respond(embed=hikari.Embed(title='unknown param type', color=kanade.Colors.ERROR))

        await ctx.respond(embed=embed)

        try:
            msg: hikari.GuildMessageCreateEvent = await plugin.app.wait_for(hikari.MessageCreateEvent, 15, lambda msg: msg.author_id == ctx.user.id)
        except asyncio.TimeoutError:
            return await ctx.respond(embed=hikari.Embed(
                title='Время вышло.', color=kanade.Colors.ERROR
            ))

        r = await parse_param(msg.message, t)
        
        if r is None:
            return await ctx.respond(embed=hikari.Embed(
                title='Ошибка типа',
                description='Вы ввели неверное значение',
                color=kanade.Colors.ERROR
            ))

        await plugin.model.db_guilds.update_one(
            {'_id': ctx.guild_id},
            {'$set': {self.section + '.' + self.key: r[0]}}
        )
        await ctx.respond(embed=hikari.Embed(
            title='Успешно',
            description='Новое значение параметра: {}'.format(r[1]),
            color=kanade.Colors.SUCCESS
        ).set_footer('raw: {}'.format(r[0] if len(str(r[0])) < 80 else '`too long`')))
