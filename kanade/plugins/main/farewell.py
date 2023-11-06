import hikari
import crescent
import kanade
from random import choice
from glob import glob
from kanade.core.bot import Model


plugin = crescent.Plugin[hikari.GatewayBot, Model]()


async def construct_embed(user: hikari.User, guild: hikari.RESTGuild) -> hikari.Embed:
    data = await plugin.model.db_guilds.find_one({'_id': guild.id})

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
            user_mention=user.mention,
            username=user.username,
            member_count=guild.approximate_member_count
        ),
        color=embed_color
    ).set_image(card_file), card_file


@plugin.include
@crescent.event
async def farewell(event: hikari.MemberDeleteEvent) -> None:
    guild = await plugin.client.app.rest.fetch_guild(event.guild_id)
    r = await construct_embed(event.user, guild)
    if r is None:
        return
    embed, _card_file = r

    data = await plugin.model.db_guilds.find_one({'_id': event.guild_id})
    try:
        await plugin.client.app.rest.create_message(
            data['farewell']['channel'],
            embed=embed
        )
    except hikari.NotFoundError and hikari.BadRequestError:
        pass
