import asyncio
import hikari
import crescent
import kanade
from kanade import db
from datetime import datetime, timezone
from time import time
from kanade.core.bot import Model


plugin = crescent.Plugin[hikari.GatewayBot, Model]()
handeled = []
quited = {}


async def send(guild, event, **kwargs):
    c = await plugin.model.db_guilds.find_one({'_id': guild})['logs'][event]

    if c is None:
        return
    
    await plugin.client.app.rest.create_message(
        c, **kwargs
    )


@plugin.include
@crescent.event
async def message_edit(event: hikari.GuildMessageUpdateEvent):
    if event.author and event.author.is_bot:
        return
    before = (event.old_message.content if event.old_message.content else '`пусто`') if event.old_message else '`нет информации`'
    after = event.message.content if event.message.content else '`пусто`'
    if before == after:
        return
    await send(event.guild_id, 'messages', embed=hikari.Embed(
        title='Сообщение изменено',
        color=kanade.Colors.WARNING,
        timestamp=datetime.now(tz=timezone.utc)
    ).add_field(
        'Автор сообщения', '{} ({})'.format(event.author, event.author_id)
    ).add_field(
        'Канал', '<#{}>'.format(event.channel_id)
    ).add_field(
        'До изменения', before
    ).add_field(
        'После изменения', after
    ).set_footer(
        event.message_id
    ))


@plugin.include
@crescent.event
async def message_deletion(event: hikari.GuildMessageDeleteEvent):
    if event.old_message is None:
        await send(
            event.guild_id, 'messages', embed=hikari.Embed(
                title='Сообщение удалено',
                description='Неудалось найти автора и содержание сообщения',
                color=kanade.Colors.ERROR
            ).add_field(
                'Канал', '<#{}>'.format(event.channel_id)
            )
        )
        return

    await send(event.guild_id, 'messages', embed=hikari.Embed(
        title='Сообщение удалено',
        color=kanade.Colors.ERROR,
        timestamp=datetime.now(tz=timezone.utc)
    ).add_field(
        'Автор сообщения', '{} ({})'.format(event.old_message.author, event.old_message.author.id)
    ).add_field(
        'Канал', '<#{}>'.format(event.channel_id)
    ).add_field(
        'Содержимое сообщения', event.old_message.content if event.old_message.content else '`пусто`'
    ).set_footer(
        event.message_id
    ))


@plugin.include
@crescent.event
async def roles(event: hikari.AuditLogEntryCreateEvent):
    if event.entry.action_type == hikari.AuditLogEventType.MEMBER_ROLE_UPDATE:
        removed, added = [], []
        for change in event.entry.changes:
            if change.key == hikari.AuditLogChangeKey.REMOVE_ROLE_FROM_MEMBER:
                removed.extend(change.new_value.keys())
            elif change.key == hikari.AuditLogChangeKey.ADD_ROLE_TO_MEMBER:
                added.extend(change.new_value.keys())
        if removed != []:
            await send(
                event.guild_id, 'roles', embed=hikari.Embed(
                    title='Роли убраны',
                    description='{} убирает роли пользователя {}'.format(
                        await event.entry.fetch_user(),
                        await event.entry.app.rest.fetch_user(event.entry.target_id)
                    ), color=kanade.Colors.WARNING,
                    timestamp=datetime.now(tz=timezone.utc)
                ).set_footer(
                    event.entry.target_id
                ).add_field(
                    'Роли', ' '.join(['<@&{}>'.format(r) for r in removed])
                )
            )

        if added != []:
            await send(
                event.guild_id, 'roles', embed=hikari.Embed(
                    title='Роли добавлены',
                    description='{} добавляет роли пользователю {}'.format(
                        await event.entry.fetch_user(),
                        await event.entry.app.rest.fetch_user(event.entry.target_id)
                    ), color=kanade.Colors.SUCCESS,
                    timestamp=datetime.now(tz=timezone.utc)
                ).set_footer(
                    event.entry.target_id
                ).add_field(
                    'Роли', ' '.join(['<@&{}>'.format(r) for r in added])
                )
            )
    elif event.entry.action_type == hikari.AuditLogEventType.MEMBER_BAN_ADD:
        for _ in range(5):
            if event.entry.target_id in quited:
                break
            await asyncio.sleep(1.5)
        else:
            return

        mem = quited[event.entry.target_id]
        handeled.append(mem.id)
        await send(
            event.guild_id, 'kick', embed=hikari.Embed(
                title='Блокировка выдана',
                description='{} выдаёт блокировку пользователю {} ({})'.format(
                    await event.entry.fetch_user(), mem, mem.id
                ), color=kanade.Colors.ERROR
            ).add_field(
                'Причина', event.entry.reason if event.entry.reason else '`не указана`'
            )
        )
    
    elif event.entry.action_type == hikari.AuditLogEventType.MEMBER_KICK:
        for _ in range(5):
            if event.entry.target_id in quited:
                break
            await asyncio.sleep(1.5)
        else:
            return

        mem = quited[event.entry.target_id]
        handeled.append(mem.id)
        await send(
            event.guild_id, 'kick', embed=hikari.Embed(
                title='Пользователь выгнан',
                description='{} выгоняет {} ({})'.format(
                    await event.entry.fetch_user(), mem, mem.id
                ), color=kanade.Colors.ERROR
            ).add_field(
                'Причина', event.entry.reason if event.entry.reason else '`не указана`'
            )
        )

@plugin.include
@crescent.event
async def invite_created(event: hikari.InviteCreateEvent):
    i = event.invite
    await send(event.guild_id, 'invites', embed=hikari.Embed(
        title='Приглашение создано',
        color=kanade.Colors.SUCCESS,
        timestamp=datetime.now(tz=timezone.utc)
    ).add_field(
        'Код приглашения', '[{0}](https://discord.gg/{0})'.format(i.code)
    ).add_field(
        'Канал', '<#{}>'.format(i.channel_id)
    ).add_field(
        'Приглашающий', str(i.inviter)
    ))


@plugin.include
@crescent.event
async def member_joined(event: hikari.MemberCreateEvent):
    await send(event.guild_id, 'join', embed=hikari.Embed(
        title='Пользователь присоединился к серверу',
        description="{} ({})".format(event.member, event.member.id),
        timestamp=datetime.now(tz=timezone.utc),
        color=kanade.Colors.SUCCESS
    ).add_field(
        'Дата регистрации', '<t:{}:R>'.format(round(event.member.created_at.timestamp()))
    ).add_field(
        'Количество участников', event.get_guild().member_count
    ))


@plugin.include
@crescent.event
async def member_left(event: hikari.MemberDeleteEvent):
    global quited
    quited[event.old_member.id] = event.old_member
    await asyncio.sleep(4)
    if event.old_member.id in handeled:
        handeled.remove(event.old_member.id)
        return

    await send(event.guild_id, 'quit', embed=hikari.Embed(
        title='Пользователь покинул сервер',
        description="{} ({})".format(event.old_member, event.old_member.id),
        timestamp=datetime.now(tz=timezone.utc),
        color=kanade.Colors.SUCCESS
    ).add_field(
        'Количество участников', event.get_guild().member_count
    ))
