from PIL import Image, ImageDraw, ImageFont
import math
import random
from pathlib import Path

# Generates a decorative, animated GitHub-style contribution skyline GIF.
# This uses illustrative sample data, not your private or live GitHub history.

OUT = Path(__file__).resolve().parent.parent / "assets" / "contribution-skyline.gif"
WIDTH, HEIGHT = 1100, 460
BG = (13, 17, 23)          # GitHub dark background
TEXT = (230, 237, 243)
MUTED = (139, 148, 158)
GREEN = (57, 211, 83)      # GitHub green
EMPTY = (22, 27, 34)
GRID = (48, 54, 61)

WEEKS, DAYS = 52, 7
CELL, GAP = 12, 4
FRAMES = 54
FRAME_MS = 70

def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()

FONT_TITLE = font(27, True)
FONT_SUB = font(14)
FONT_LABEL = font(12)
FONT_SMALL = font(11)

# Deterministic illustrative pattern: consistent every time the script runs.
rng = random.Random(2026)
counts = []
for week in range(WEEKS):
    column = []
    for day in range(DAYS):
        # A varied pattern with some quiet days and occasional busy streaks.
        wave = (math.sin(week * 0.48 + day * 0.85) + 1) / 2
        chance = 0.23 + 0.52 * wave
        if rng.random() < chance:
            column.append(rng.choices([1, 2, 3, 4], weights=[42, 30, 20, 8])[0])
        else:
            column.append(0)
    counts.append(column)

def level_color(level):
    palette = [EMPTY, (14, 68, 35), (0, 109, 50), (38, 166, 65), GREEN]
    return palette[level]

def mix(a, b, t):
    return tuple(int(a[i] * (1-t) + b[i] * t) for i in range(3))

def ease(t):
    return t * t * (3 - 2*t)

def draw_frame(progress):
    # progress 0 = flat heatmap, progress 1 = isometric skyline
    e = ease(progress)
    im = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(im)

    d.text((48, 28), "CONTRIBUTION SKYLINE", font=FONT_TITLE, fill=TEXT)
    d.text((50, 64), "A year of coding activity · illustrative preview", font=FONT_SUB, fill=MUTED)

    # Draw a subtly framed panel.
    panel = (38, 98, WIDTH - 38, HEIGHT - 42)
    d.rounded_rectangle(panel, radius=15, outline=GRID, width=1)

    # 2D placement (52 columns x 7 rows).
    flat_cell = 13
    flat_gap = 4
    flat_w = WEEKS * (flat_cell + flat_gap) - flat_gap
    flat_h = DAYS * (flat_cell + flat_gap) - flat_gap
    flat_x = (WIDTH - flat_w) // 2
    flat_y = 210

    # 3D isometric placement.
    iso_x_step = 13.0
    iso_y_step = 4.2
    bar_w = 8.2
    base_x = WIDTH / 2 - (WEEKS * iso_x_step) / 2 + 14
    base_y = 260

    # Draw each contribution cell as it morphs from square to isometric bar.
    for w in range(WEEKS):
        for day in range(DAYS):
            val = counts[w][day]
            color = level_color(val)

            fx = flat_x + w * (flat_cell + flat_gap)
            fy = flat_y + day * (flat_cell + flat_gap)

            # Isometric projection: week advances right/down; day advances left/down.
            ix = base_x + w * iso_x_step - day * iso_y_step * 0.78
            iy = base_y + w * iso_y_step * 0.42 + day * iso_y_step * 0.72
            height = 4 + val * 8.5

            # Blend the cell centre from the flat grid to the isometric base.
            cx0, cy0 = fx + flat_cell / 2, fy + flat_cell / 2
            cx1, cy1 = ix, iy
            cx = cx0 * (1-e) + cx1 * e
            cy = cy0 * (1-e) + cy1 * e

            if e < 0.02:
                x0, y0 = cx - flat_cell/2, cy - flat_cell/2
                d.rounded_rectangle((x0, y0, x0 + flat_cell, y0 + flat_cell), radius=2, fill=color)
            else:
                # A simple isometric cuboid, growing out of the projected base.
                bw = bar_w
                depth = 4.5
                top_y = cy - height * e
                left = (cx - bw/2, top_y)
                right = (cx + bw/2, top_y - depth/2)
                back = (cx + bw/2 + depth, top_y + depth/2)
                front = (cx - bw/2 + depth, top_y + depth)
                # Side faces and top; darker sides add depth.
                d.polygon([left, (left[0], cy), (left[0] + depth, cy + depth), front], fill=mix(color, (0,0,0), 0.30))
                d.polygon([left, right, back, front], fill=mix(color, (255,255,255), 0.13))
                d.polygon([right, (right[0], cy), (back[0], cy + depth), back], fill=mix(color, (0,0,0), 0.18))
                d.polygon([left, right, back, front], fill=color)

    # Labels, intentionally minimal to keep the chart readable.
    if progress < 0.45:
        labels_y = flat_y - 22
        for i, month in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
            x = flat_x + int(i * (WEEKS / 12)) * (flat_cell + flat_gap)
            d.text((x, labels_y), month, font=FONT_SMALL, fill=MUTED)
        for i, label in enumerate(["Mon", "Wed", "Fri"]):
            row = [0, 2, 4][i]
            d.text((flat_x - 37, flat_y + row * (flat_cell + flat_gap)), label, font=FONT_SMALL, fill=MUTED)

    # Legend.
    legend_y = HEIGHT - 70
    d.text((WIDTH - 270, legend_y), "Less", font=FONT_SMALL, fill=MUTED)
    for i in range(5):
        x = WIDTH - 230 + i * 17
        d.rounded_rectangle((x, legend_y + 1, x + 12, legend_y + 13), radius=2, fill=level_color(i))
    d.text((WIDTH - 135, legend_y), "More", font=FONT_SMALL, fill=MUTED)
    d.text((50, HEIGHT - 70), "2D  ↔  3D", font=FONT_LABEL, fill=GREEN)
    return im

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Animate flat -> skyline, hold, then skyline -> flat for a seamless loop.
    frames = []
    path = [ease(i / 23) for i in range(24)]
    path += [1.0] * 7
    path += [1.0 - ease(i / 23) for i in range(24)]
    for p in path:
        frames.append(draw_frame(p))
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Created: {OUT}")
    print(f"Frames: {len(frames)}")
    print("Note: this version uses illustrative sample contributions, not live GitHub data.")

if __name__ == "__main__":
    main()
