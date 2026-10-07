"""Render actual execution transcripts as PNG; these are not desktop screenshots."""
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def save_case(lab, name, title, text):
    path = Path(lab) / 'images'
    path.mkdir(parents=True, exist_ok=True)
    (path / f'{name}.txt').write_text(text + '\n', encoding='utf-8')
    font_path = Path('C:/Windows/Fonts/consola.ttf')
    font = ImageFont.truetype(str(font_path), 19) if font_path.exists() else ImageFont.load_default()
    heading_path = Path('C:/Windows/Fonts/arial.ttf')
    heading = ImageFont.truetype(str(heading_path), 25) if heading_path.exists() else font
    lines = []
    for line in text.splitlines():
        lines.extend(textwrap.wrap(line, 100, replace_whitespace=False, drop_whitespace=False) or [''])
    canvas = Image.new('RGB', (1240, 130 + 28 * len(lines)), '#101a2b')
    draw = ImageDraw.Draw(canvas)
    draw.text((30, 22), title, font=heading, fill='#73e2cf')
    draw.text((30, 65), 'ACTUAL RUN OUTPUT · locally executed lab cases', font=font, fill='#9cafca')
    for i, line in enumerate(lines):
        draw.text((30, 110 + 28 * i), line, font=font, fill='#e9f2ff')
    canvas.save(path / f'{name}.png')
    print(f'PASS {name}: {title}')
