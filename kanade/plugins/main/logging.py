import hikari
import crescent
import kanade
from kanade import db
from datetime import datetime, timezone


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
    await send(event.guild_id, 'messages', embed=hikari.Embed(
        title='Сообщение изменено',
        color=kanade.Colors.WARNING,
        timestamp=datetime.now(tz=timezone.utc)
    ).add_field(
        'Автор сообщения', '{} ({})'.format(event.author, event.author_id)
    ).add_field(
        'Канал', '<#{}>'.format(event.channel_id)
    ).add_field(
        'До изменения', (event.old_message.content if event.old_message.content else '`пусто`') if event.old_message else '`нет информации`'
    ).add_field(
        'После изменения', event.message.content if event.message.content else '`пусто`'
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
async def role_added(event: hikari.MemberUpdateEvent):
    old, new = set(event.old_member.role_ids), set(event.member.role_ids)
    if old == new:
        return

    roles = old.difference(new)
    rr = None
    for r in roles:
        rr = r
        break

    embed = hikari.Embed(
        color=kanade.Colors.WARNING,
        timestamp=datetime.now(tz=timezone.utc)
    ).add_field(
        'Роли', ' '.join(['<@{}>'.format(r) for r in roles])
    ).set_footer(
        event.member.id
    )
    if rr in new:
        embed.title='Роли добавлены'
        embed.description='{} добавляет роли пользователю {}'.format(event.user, event.member)
    else:
        embed.title='Роли убраны'
        embed.description='{} убирает роли пользователя {}'.format(event.user, event.member)
    await send(event.guild_id, 'roles', embed=embed)