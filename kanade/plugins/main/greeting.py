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


plugin = crescent.Plugin[hikari.GatewayBot, Model]()


async def construct_embed(member: hikari.Member, guild: hikari.GatewayGuild) -> hikari.Embed:
    data = await plugin.model.db_guilds.find_one({'_id': guild.id})

    if not data['greetings']['enabled']:
        return
    
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
        None, welcome_card.generate, Image.open(io_data).convert('RGBA'), guild.name, str(member), "./assets/font.ttf", glow_colors, border_colors
    )
    card_file = hikari.Bytes(card, "card.gif")

    # create embed
    return hikari.Embed(
        title=data['greetings']['title'],
        description=data['greetings']['description'].format(
            guild_name=guild.name,
            user_mention=member.mention,
            username=str(member),
            member_count=(
                (await guild.app.rest.fetch_guild(guild)).approximate_member_count
                if '{member_count}' in data['greetings']['description'] else None
            )
        ),
        color=embed_color
    ).set_image(card_file), card_file


@plugin.include
@crescent.event
async def greeting(event: hikari.MemberCreateEvent):
    r = await construct_embed(event.member, event.get_guild())
    if r is None:
        return
    embed, card_file = r

    data = await plugin.model.db_guilds({'_id': event.guild_id})
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