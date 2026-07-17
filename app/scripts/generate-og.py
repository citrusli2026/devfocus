#!/usr/bin/env python3
"""Generate Open Graph image (1200x630) using Pillow."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "public" / "og.png"
W, H = 1200, 630

# Palette
BG = "#f5f3fa"
CARD_BG = "#ffffff"
CARD_BORDER = "#d4cde0"
TEXT_PRIMARY = "#1a1530"
TEXT_SECONDARY = "#4a4560"
VIOLET = "#6a5fc1"
CORAL = "#d97040"
TAG_BG = "#ede9f5"

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# Background glow
glow_center = (W // 2, -80)
for r in range(400, 0, -10):
    alpha = int(30 * (r / 400) ** 0.5)
    color = (106, 95, 193)
    draw.ellipse(
        [glow_center[0] - r, glow_center[1] - r, glow_center[0] + r, glow_center[1] + r],
        fill=(*color,),
    )

# Card
card_margin = 60
card_box = [card_margin, card_margin, W - card_margin, H - card_margin]
draw.rounded_rectangle(card_box, radius=32, fill=CARD_BG, outline=CARD_BORDER, width=1)

# Try to load fonts, fall back to default
font_paths = [
    "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]

def load_font(size, bold=False):
    for path in font_paths:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            continue
    return ImageFont.load_default()

font_title = load_font(72, bold=True)
font_title_cn = load_font(64, bold=True)
font_subtitle = load_font(30)
font_tag = load_font(22)

# Logo-ish circle with gradient approximation
cx, cy = W // 2, 145
for r in range(45, 0, -1):
    ratio = r / 45
    # Interpolate violet -> coral
    rr = int(106 + (217 - 106) * (1 - ratio))
    gg = int(95 + (112 - 95) * (1 - ratio))
    bb = int(193 + (64 - 193) * (1 - ratio))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(rr, gg, bb))
# Lightning bolt (simple polygon)
bolt = [(cx - 8, cy - 20), (cx + 12, cy - 2), (cx - 2, cy - 2), (cx + 8, cy + 20), (cx - 12, cy + 2), (cx + 2, cy + 2)]
draw.polygon(bolt, fill="white")

# Title
title_text = "DevFocus"
draw.text((W // 2, 230), title_text, font=font_title, fill=TEXT_PRIMARY, anchor="mm")
# Chinese subtitle next to it? Let's do two lines for clarity
# Title line: DevFocus 开发者聚焦
# Use smaller CN font placed beside
cn_text = "开发者聚焦"
bbox = draw.textbbox((0, 0), title_text, font=font_title)
title_w = bbox[2] - bbox[0]
cn_x = W // 2 + title_w // 2 + 16
draw.text((cn_x, 230), cn_text, font=font_title_cn, fill=VIOLET, anchor="lm")

# Subtitle
subtitle = "每日自动整理的开发者资讯 · AI / GitHub / 产品"
draw.text((W // 2, 315), subtitle, font=font_subtitle, fill=TEXT_SECONDARY, anchor="mm")

# Tags
tags = ["Hacker News", "GitHub Trending", "Product Hunt"]
tag_h = 52
tag_padding = 24
tag_spacing = 18
# Compute total width
total_w = 0
tag_dims = []
for tag in tags:
    bbox = draw.textbbox((0, 0), tag, font=font_tag)
    tw = bbox[2] - bbox[0] + tag_padding * 2
    tag_dims.append(tw)
    total_w += tw
total_w += tag_spacing * (len(tags) - 1)
start_x = (W - total_w) // 2
y = 390
for tag, tw in zip(tags, tag_dims):
    draw.rounded_rectangle([start_x, y, start_x + tw, y + tag_h], radius=tag_h // 2, fill=TAG_BG)
    draw.text((start_x + tw // 2, y + tag_h // 2), tag, font=font_tag, fill=VIOLET, anchor="mm")
    start_x += tw + tag_spacing

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, "PNG")
print(f"[OG] generated {OUT}")
