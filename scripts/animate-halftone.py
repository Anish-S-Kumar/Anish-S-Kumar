from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageOps
)

from rembg import remove, new_session


# ============================================================
# FILES
# ============================================================

INPUT = "assets/Anish.jpeg"
OUTPUT = "assets/profile-halftone.gif"


# ============================================================
# SETTINGS
# ============================================================

MAX_INPUT_SIZE = 1200
OUTPUT_WIDTH = 900

DOT_SPACING = 5

MIN_RADIUS = 0.25
MAX_RADIUS = 1.65

# GitHub green
GREEN = (57, 211, 83)

# GitHub dark background
BACKGROUND = (13, 17, 23)


# ============================================================
# ANIMATION
# ============================================================

REVEAL_FRAMES = 45

# Keep the final portrait visible
HOLD_FRAMES = 70

# Animation speed
FRAME_DURATION = 60


# ============================================================
# LOAD IMAGE
# ============================================================

print("Loading image...")

original = Image.open(
    INPUT
).convert("RGBA")

original.thumbnail(
    (MAX_INPUT_SIZE, MAX_INPUT_SIZE),
    Image.Resampling.LANCZOS
)


# ============================================================
# REMOVE BACKGROUND
# ============================================================

print("Removing background...")

session = new_session("u2net")

subject = remove(
    original,
    session=session
).convert("RGBA")

print("Background removed.")


# ============================================================
# CLEAN MASK
# ============================================================

alpha = subject.getchannel("A")

alpha = alpha.point(
    lambda p: 255 if p > 90 else 0
)

alpha = alpha.filter(
    ImageFilter.MedianFilter(3)
)

alpha = alpha.filter(
    ImageFilter.GaussianBlur(0.4)
)


# ============================================================
# CROP TO PERSON
# ============================================================

bbox = alpha.getbbox()

if bbox is None:
    raise RuntimeError(
        "Could not detect the person."
    )

subject = subject.crop(bbox)
alpha = alpha.crop(bbox)


# ============================================================
# RESIZE
# ============================================================

ratio = OUTPUT_WIDTH / subject.width

height = int(
    subject.height * ratio
)

subject = subject.resize(
    (OUTPUT_WIDTH, height),
    Image.Resampling.LANCZOS
)

alpha = alpha.resize(
    (OUTPUT_WIDTH, height),
    Image.Resampling.LANCZOS
)


# ============================================================
# GRAYSCALE
# ============================================================

gray = subject.convert("RGB").convert("L")

gray = ImageOps.autocontrast(
    gray,
    cutoff=1
)

gray = ImageEnhance.Contrast(
    gray
).enhance(1.45)

gray = gray.filter(
    ImageFilter.GaussianBlur(0.35)
)


# ============================================================
# CREATE HALFTONE DOT DATA
# ============================================================

print("Preparing halftone...")

dot_data = []


for y in range(
    DOT_SPACING // 2,
    height,
    DOT_SPACING
):

    for x in range(
        DOT_SPACING // 2,
        OUTPUT_WIDTH,
        DOT_SPACING
    ):

        # Check person mask
        a = alpha.getpixel((x, y))

        if a < 100:
            continue

        # Pixel brightness
        brightness = gray.getpixel((x, y))

        lightness = brightness / 255.0

        lightness = lightness ** 1.30

        # Dark areas remain mostly empty
        if lightness < 0.13:
            continue

        # Dot size
        radius = (
            MIN_RADIUS +
            lightness * MAX_RADIUS
        )

        radius = min(
            radius,
            DOT_SPACING * 0.40
        )

        dot_data.append(
            (
                x,
                y,
                radius
            )
        )


print(
    "Prepared",
    len(dot_data),
    "dots"
)


# ============================================================
# CREATE FRAMES
# ============================================================

frames = []

print("Creating top-to-bottom animation...")


for frame_number in range(
    REVEAL_FRAMES
):

    print(
        f"Frame {frame_number + 1}/"
        f"{REVEAL_FRAMES}"
    )

    # --------------------------------------------------------
    # Progress from top to bottom
    # --------------------------------------------------------

    progress = (
        frame_number /
        (REVEAL_FRAMES - 1)
    )

    # Smooth movement
    progress = (
        progress *
        progress *
        (3 - 2 * progress)
    )

    # Current Y position of reveal
    reveal_y = (
        height * progress
    )


    # --------------------------------------------------------
    # Canvas
    # --------------------------------------------------------

    frame = Image.new(
        "RGBA",
        (
            OUTPUT_WIDTH,
            height
        ),
        (
            BACKGROUND[0],
            BACKGROUND[1],
            BACKGROUND[2],
            255
        )
    )


    dots = Image.new(
        "RGBA",
        (
            OUTPUT_WIDTH,
            height
        ),
        (
            0,
            0,
            0,
            0
        )
    )

    draw = ImageDraw.Draw(dots)


    # ========================================================
    # DRAW REVEALED DOTS
    # ========================================================

    for x, y, radius in dot_data:

        # ----------------------------------------------------
        # Above reveal line
        # ----------------------------------------------------

        if y <= reveal_y:

            # Everything above the line is visible
            visibility = 1.0

        # ----------------------------------------------------
        # Slightly below reveal line
        # ----------------------------------------------------

        elif y <= reveal_y + 18:

            # Soft edge
            visibility = (
                1 -
                (
                    (y - reveal_y)
                    / 18
                )
            )

        else:

            visibility = 0


        if visibility <= 0:
            continue


        # Smooth edge
        visibility = (
            visibility *
            visibility *
            (3 - 2 * visibility)
        )


        alpha_value = int(
            245 * visibility
        )


        # ----------------------------------------------------
        # Draw green dot
        # ----------------------------------------------------

        draw.ellipse(
            (
                x - radius,
                y - radius,
                x + radius,
                y + radius
            ),
            fill=(
                GREEN[0],
                GREEN[1],
                GREEN[2],
                alpha_value
            )
        )


    # ========================================================
    # SUBTLE GLOW
    # ========================================================

    glow = dots.filter(
        ImageFilter.GaussianBlur(5)
    )

    glow_alpha = (
        glow.getchannel("A")
    )

    glow_alpha = glow_alpha.point(
        lambda p: int(p * 0.12)
    )

    glow.putalpha(
        glow_alpha
    )


    # ========================================================
    # COMPOSITE
    # ========================================================

    frame = Image.alpha_composite(
        frame,
        glow
    )

    frame = Image.alpha_composite(
        frame,
        dots
    )


    frames.append(
        frame.convert(
            "P",
            palette=Image.Palette.ADAPTIVE
        )
    )


# ============================================================
# HOLD FINAL FRAME
# ============================================================

print("Holding final image...")

final_frame = frames[-1]

for _ in range(HOLD_FRAMES):

    frames.append(
        final_frame.copy()
    )


# ============================================================
# SAVE GIF
# ============================================================

print("Saving GIF...")

frames[0].save(
    OUTPUT,
    save_all=True,
    append_images=frames[1:],
    duration=FRAME_DURATION,
    optimize=True
)


# ============================================================
# DONE
# ============================================================

print()
print("========================================")
print(" TOP-TO-BOTTOM HALFTONE GIF CREATED")
print("========================================")
print()
print("Output:")
print(OUTPUT)
print()
print("Animation:")
print("TOP → BOTTOM → STAYS")
print()