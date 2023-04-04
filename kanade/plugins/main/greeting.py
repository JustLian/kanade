import hikari
import crescent
import asyncio
from kanade import db
import aiohttp
from io import BytesIO
from PIL import Image
from kanade.images import welcome_card
import kanade


plugin = crescent.Plugin()


@plugin.include
@crescent.event
async def greeting(event: hikari.MemberCreateEvent):
    data = db.find_document(plugin.model.db_guilds, {'_id': event.guild_id})

    if not data['greetings']['enabled']:
        return
    
    # downloading user's pfp
    io_data = None
    async with aiohttp.ClientSession() as session:
        url = event.member.avatar_url.url
        async with session.get(url) as resp:
            if resp.status == 200:
                io_data = BytesIO()
                io_data.write(await resp.read())
    
    if io_data is None:
        return
    
    # generate card
    guild = event.get_guild()
    card = await asyncio.get_event_loop().run_in_executor(
        None, welcome_card.generate, Image.open(io_data).convert('RGBA'), guild.name, str(event.member)
    )
    card_file = hikari.Bytes(card, "card.gif")

    # create embed
    embed = hikari.Embed(
        title=data['greetings']['title'],
        description=data['greetings']['description'].format(
            guild_name=guild.name,
            user_mention=event.member.mention,
            username=str(event.user),
            member_count=guild.member_count
        ),
        color=kanade.Colors.ERROR
    ).set_image(card_file)

    try:
        await plugin.client.app.rest.create_message(
            data['greetings']['channel'],
            embed=embed,
            attachment=card_file
        )
    except hikari.NotFoundError:
        pass