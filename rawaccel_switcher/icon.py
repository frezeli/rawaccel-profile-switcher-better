"""Tray / window icon generation.

The icon is drawn at runtime with Pillow so the project needs no binary
image assets. A simple blue rounded square with a white "R" is used.
"""

from __future__ import annotations


def make_icon(size: int = 64):
    """Return a Pillow ``Image`` for use as the tray icon."""
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    pad = max(2, size // 16)
    radius = size // 5
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        fill=(38, 120, 222, 255),
    )

    try:
        font = ImageFont.truetype("arialbd.ttf", int(size * 0.6))
    except OSError:
        font = ImageFont.load_default()

    text = "R"
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.text(
        ((size - tw) / 2 - box[0], (size - th) / 2 - box[1]),
        text,
        font=font,
        fill=(255, 255, 255, 255),
    )
    return image
