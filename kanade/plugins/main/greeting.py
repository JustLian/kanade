import hikari
import crescent
import asyncio
from kanade import db
import aiohttp
from io import BytesIO
from PIL import Image
from kanade.images import welcome_card
import kanade
from kanade.plugins.main.debug import debug


plugin = crescent.Plugin()


async def construct_embed(member: hikari.Member, guild: hikari.Guild) -> hikari.Embed:
    data = db.find_document(plugin.model.db_guilds, {'_id': guild.id})

    if not data['greetings']['enabled']:
        return
    
    try:
        embed_color = hikari.Color.from_hex_code(data['greetings']['color'])
    except ValueError:
        return hikari.Embed(title='НЕВЕРНЫЙ HEX', color=kanade.Colors.ERROR), None
    
    # downloading user's pfp
    io_data = None
    async with aiohttp.ClientSession() as session:
        url = member.avatar_url.url
        async with session.get(url) as resp:
            if resp.status == 200:
                io_data = BytesIO()
                io_data.write(await resp.read())
    
    if io_data is None:
        return
    
    # generate card
    card = await asyncio.get_event_loop().run_in_executor(
        None, welcome_card.generate, Image.open(io_data).convert('RGBA'), guild.name, str(member)
    )
    card_file = hikari.Bytes(card, "card.gif")

    # create embed
    return hikari.Embed(
        title=data['greetings']['title'],
        description=data['greetings']['description'].format(
            guild_name=guild.name,
            user_mention=member.mention,
            username=str(member),
            member_count=guild.member_count
        ),
        color=embed_color
    ).set_image(card_file), card_file


@plugin.include
@crescent.event
async def greeting(event: hikari.MemberCreateEvent):
    guild = await plugin.client.app.rest.fetch_guild(event.guild_id)
    r = await construct_embed(event.member, guild)
    if r is None:
        return
    embed, card_file = r

    data = db.find_document(plugin.model.db_guilds, {'_id': event.guild_id})
    try:
        await plugin.client.app.rest.create_message(
            data['greetings']['channel'],
            embed=embed,
            attachment=card_file
        )
    except hikari.NotFoundError:
        pass


@plugin.include
@debug.child
@crescent.hook(kanade.hooks.is_bot_admin)
@crescent.command(
    name='greeting_preview',
    description='Предпросмотр карточки'
)
async def preview(ctx: crescent.Context) -> None:
    await ctx.defer()
    
    embed, card_file = await construct_embed(
        ctx.member, ctx.guild
    )
    await ctx.respond(
        embed=embed,
        attachment=card_file
    )