import hikari
import crescent
import asyncio
from kanade import db
import aiohttp
import kanade
from kanade.plugins.main.debug import debug
from random import choice
from glob import glob


plugin = crescent.Plugin()


async def construct_embed(member: hikari.Member, guild: hikari.Guild) -> hikari.Embed:
    data = db.find_document(plugin.model.db_guilds, {'_id': guild.id})

    if not data['farewell']['enabled']:
        return
    
    try:
        embed_color = hikari.Color.from_hex_code(data['farewell']['color'])
    except ValueError:
        return hikari.Embed(title='НЕВЕРНЫЙ HEX', color=kanade.Colors.ERROR), None

    # pick random gif
    gif = choice(glob('./assets/backgrounds/*.gif'))
    card_file = hikari.File(gif)

    return hikari.Embed(
        title=data['farewell']['title'],
        description=data['farewell']['description'].format(
            guild_name=guild.name,
            user_mention=member.mention,
            username=str(member),
            member_count=guild.member_count
        ),
        color=embed_color
    ).set_image(card_file), card_file


@plugin.include
@crescent.event
async def farewell(event: hikari.MemberDeleteEvent) -> None:
    guild = await plugin.client.app.rest.fetch_guild(event.guild_id)
    r = await construct_embed(event.member, guild)
    if r is None:
        return
    embed, card_file = r

    data = db.find_document(plugin.model.db_guilds, {'_id': event.guild_id})
    try:
        await plugin.client.app.rest.create_message(
            data['farewell']['channel'],
            embed=embed,
            attachment=card_file
        )
    except hikari.NotFoundError:
        pass