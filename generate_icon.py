"""
generate_icon.py - SRK Boost Icon Generator
Creates a purple lightning bolt icon and saves as assets/icon.ico
Requires: pip install Pillow
"""
from PIL import Image, ImageDraw
import os


def create_icon():
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Purple background circle
        draw.ellipse([0, 0, size - 1, size - 1], fill=(108, 99, 255, 255))

        # White lightning bolt (scaled to icon size)
        scale = size / 64
        points = [
            (int(38 * scale), int(4 * scale)),
            (int(24 * scale), int(30 * scale)),
            (int(36 * scale), int(30 * scale)),
            (int(26 * scale), int(60 * scale)),
            (int(44 * scale), int(28 * scale)),
            (int(32 * scale), int(28 * scale)),
        ]
        draw.polygon(points, fill=(255, 255, 255, 255))

        images.append(img)

    os.makedirs('assets', exist_ok=True)
    images[0].save(
        'assets/icon.ico',
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"✓ Icon created: assets/icon.ico ({len(sizes)} sizes: {sizes})")


if __name__ == "__main__":
    create_icon()
