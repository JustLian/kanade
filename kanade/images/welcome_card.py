from glob import glob
from io import BytesIO
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import numpy as np
import itertools


def compose_border(
        size, rotation,
        color1: tuple[int, int, int] = (255, 0, 0),
        color2: tuple[int, int, int] = (0, 0, 0)
    ) -> Image.Image:
    """Generatres animated two-color gradient border. """
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(
        ((0, 0), size), fill=None,
        outline=255, width=round(size[0] * .01)
    )

    gs = size[0] * 3
    gradient = generate_gradient((255, 0, 0), (0, 0, 0), gs, gs)
    gradient = gradient.rotate(rotation)

    res = gradient.crop(
        (
            (gs - size[0]) // 2,
            (gs - size[1]) // 2,
            (gs + size[0]) // 2,
            (gs + size[1]) // 2
        )
    )
    res.putalpha(mask)
    return res


def add_corners(im) -> Image.Image:
    """Makes image round"""
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(im.size, Image.LANCZOS)
    im.putalpha(mask)
    return im


def generate_gradient(
        colour1, colour2, width: int, height: int
    ) -> Image.Image:
    """Generate a vertical gradient."""
    base = Image.new('RGB', (width, height), colour1)
    top = Image.new('RGB', (width, height), colour2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


def generate_glow(
        size,
        color1: tuple[int, int, int] = (255, 255, 255),
        color2: tuple[int, int, int] = (225, 0, 0)
    ) -> Image.Image:
    """Generate two color gradient glow"""
    im = generate_gradient(
        color1, color2, *size
    )
    Y = np.linspace(-1, 1, size[0])[None, :] * 255
    X = np.linspace(-1, 1, size[1])[:, None] * 255
    alpha = np.sqrt(X ** 2 + Y ** 2)
    alpha = 255 - np.clip(0, 255, alpha)

    # Push that radial gradient transparency onto red image and save
    im.putalpha(Image.fromarray(alpha.astype(np.uint8)))
    return im


def get_text_size(text, width, font_path='./assets/font.ttf') -> tuple[float, int]:
    """Find font size for specific text, that would fit to passed width"""
    for size in range(1, 150):
        font = ImageFont.truetype(font_path, size=size)
        w, h = font.getsize(text)
    
        if w > width:
            break
        
    return size, w, h


def composite_frame(guild, username, img, pfp, glow, border, u_font, g_font, uw, uh, gw, gh):
    """Composite single frame of welcome card"""
    img = img.copy()

    # Creating border
    img.paste(border, (0, 0), border)

    # Drawing text
    d = ImageDraw.ImageDraw(img)
    text_spacing = img.size[1] * 0.05
    d.text(
        ((img.size[0] + uw) // 2,
        (img.size[1] - uh - gh + text_spacing) // 2),
        username, (255,) * 3, u_font,
        anchor='mm', align='center'
    )
    d.text(
        ((img.size[0]) // 2 + gw * 1.5,
        (img.size[1] + uh + gh - text_spacing) // 2),
        guild, (150,) * 3, g_font,
        anchor='mm', align='center'
    )

    # Adding image glow and pfp
    img.paste(glow, (
        (img.size[0] // 2 - glow.size[0]) // 2,
        (img.size[1] - glow.size[1]) // 2
    ), glow)
    img.paste(pfp, (
        (img.size[0] // 2 - pfp.size[0]) // 2,
        (img.size[1] - pfp.size[1]) // 2
    ), pfp)
    return img


def generate(pfp: Image.Image, guild: str, username: str, font_path="./assets/font.ttf") -> BytesIO:
    """Generate welcome card gif"""

    # Creating background generator
    bg_fp = random.choice(glob('./assets/backgrounds/*'))
    bg = Image.open(bg_fp)
    if not hasattr(bg, "is_animated"):
        def bg_sequence():
            yield bg
    else:
        def bg_sequence():
            bg.seek(1)

            try:
                while True:
                    bg.seek(bg.tell() + 1)
                    yield bg.filter(ImageFilter.GaussianBlur(4))
            except EOFError:
                pass

    # pfp stuff
    pfp = add_corners(
        pfp.resize((round(bg.size[1] * .8),) * 2)
    )

    # creating glow around the image
    glow = generate_glow((round(pfp.size[0] * 1.3),) * 2)\
        .filter(ImageFilter.GaussianBlur(4))

    # Settings up text
    username_size, uw, uh = get_text_size(username, round(bg.size[0] // 2 * .95))
    guild_size, gw, gh = get_text_size(guild, round(bg.size[0] // 2 * .3))
    u_font = ImageFont.truetype(font_path, username_size)
    g_font = ImageFont.truetype(font_path, guild_size)

    frames = []
    for bg_frame, d1, d2 in zip(
        itertools.cycle(bg_sequence()), itertools.cycle(range(0, 360, 30)), range(0, 360, 15)
    ):
        frame = composite_frame(
            guild, username, bg_frame, pfp, glow.rotate(d1), compose_border(bg.size, d2),
            u_font, g_font, uw, uh, gw, gh
        )
        fobj = BytesIO()
        frame.save(fobj, 'GIF')
        frame = Image.open(fobj)
        frames.append(frame)

    output = BytesIO()
    frames[0].save(
        output,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=120,
        loop=0)
    output.seek(0)

    return output