import hikari
import crescent
import kanade
from kanade import db
from datetime import datetime, timezone
from time import time


plugin = crescent.Plugin()


async def send(guild, event, **kwargs):
    c = db.find_document(
        plugin.model.db_guilds, {'_id': guild}
    )['logs'][event]

    if c is None:
        return
    
    await plugin.client.app.rest.create_message(
        c, **kwargs
    )


@plugin.include
@crescent.event
async def message_edit(event: hikari.GuildMessageUpdateEvent):
    if event.author.is_bot:
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
        description=str(event.member),
        timestamp=datetime.now(tz=timezone.utc),
        color=kanade.Colors.SUCCESS
    ).add_field(
        'Дата регистрации', '<t:{}:R>'.format(event.member.created_at.timestamp())
    ).add_field(
        'Количество участников', event.get_guild().member_count
    ))