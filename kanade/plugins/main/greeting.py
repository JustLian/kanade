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
from kanade.utils import to_rgb
from kanade.core.bot import Model
import kanade.plugins.main.embed_errors as emors
from kanade.utils import text_format


plugin = crescent.Plugin[hikari.GatewayBot, Model]()


async def construct_embed(member: hikari.Member, guild: hikari.GatewayGuild) -> hikari.Embed:
    data = await plugin.model.db_guilds.find_one({'_id': guild.id})

    if not data['greetings']['enabled']:
        return
    
    title = data['greetings']['title']
    if len(title) > 256:
        title = emors.title_exceeded + db.defaults("guilds")['greetings']['title']
    
    try:
        embed_color = hikari.Color.from_hex_code(data['greetings']['color'])
    except ValueError:
        return hikari.Embed(title='Неверный HEX в embed_color', color=kanade.Colors.ERROR), None

    try:
        glow_colors = (to_rgb(data['greetings']['glow_color1']), to_rgb(data['greetings']['glow_color2']))
    except ValueError:
        return hikari.Embed(title='Неверный HEX в glow_colors', color=kanade.Colors.ERROR), None

    try:
        border_colors = (to_rgb(data['greetings']['border_color1']), to_rgb(data['greetings']['border_color2']))
    except ValueError:
        return hikari.Embed(title='Неверный HEX в border_colors', color=kanade.Colors.ERROR), None
    
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
        None, welcome_card.generate, Image.open(io_data).convert('RGBA'), guild.name, member.username, "./assets/font.ttf", glow_colors, border_colors
    )
    card_file = hikari.Bytes(card, "card.gif")

    guild = await guild.app.rest.fetch_guild(guild)
    formatted_description = text_format(data['greetings']['description'], member, guild)

    if len(formatted_description) > 4096:
        text_data = emors.description_exceeded + db.defaults("guilds")['greetings']['description']
        formatted_description = text_format(text_data, member, guild)

    # create embed
    return hikari.Embed(
        title=title,
        description=formatted_description,
        color=embed_color
    ).set_image(card_file), card_file


@plugin.include
@crescent.event
async def greeting(event: hikari.MemberCreateEvent):
    r = await construct_embed(event.member, event.get_guild())
    if r is None:
        return
    embed, _card_file = r

    data = await plugin.model.db_guilds.find_one({'_id': event.guild_id})
    try:
        await plugin.client.app.rest.create_message(
            data['greetings']['channel'],
            embed=embed
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
