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
OUTPUT = "assets/profile-halftone.png"


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
# 1. LOAD IMAGE
# ============================================================

print("Loading image...")

image = Image.open(INPUT).convert("RGBA")

image.thumbnail(
    (MAX_INPUT_SIZE, MAX_INPUT_SIZE),
    Image.Resampling.LANCZOS
)

print("Input size:", image.size)


# ============================================================
# 2. REMOVE BACKGROUND
# ============================================================

print("Removing background...")

session = new_session("u2net")

subject = remove(
    image,
    session=session
).convert("RGBA")

print("Background removed.")


# ============================================================
# 3. CLEAN ALPHA MASK
# ============================================================

alpha = subject.getchannel("A")

# Remove faint background remnants
alpha = alpha.point(
    lambda p: 255 if p > 90 else 0
)

# Remove isolated noise
alpha = alpha.filter(
    ImageFilter.MedianFilter(3)
)

# Slightly smooth the edge
alpha = alpha.filter(
    ImageFilter.GaussianBlur(0.4)
)


# ============================================================
# 4. CROP TO SUBJECT
# ============================================================

bbox = alpha.getbbox()

if bbox:
    subject = subject.crop(bbox)
    alpha = alpha.crop(bbox)

print("Subject cropped:", subject.size)


# ============================================================
# 5. RESIZE
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
# 6. CREATE GRAYSCALE
# ============================================================

rgb = subject.convert("RGB")

gray = rgb.convert("L")

# Improve tonal range
gray = ImageOps.autocontrast(
    gray,
    cutoff=1
)

# Strong facial contrast
gray = ImageEnhance.Contrast(
    gray
).enhance(1.45)

# Remove tiny JPEG noise
gray = gray.filter(
    ImageFilter.GaussianBlur(0.35)
)


# ============================================================
# 7. OUTPUT CANVAS
# ============================================================

output = Image.new(
    "RGB",
    (OUTPUT_WIDTH, height),
    BACKGROUND
)

dots = Image.new(
    "RGBA",
    (OUTPUT_WIDTH, height),
    (0, 0, 0, 0)
)

draw = ImageDraw.Draw(dots)


# ============================================================
# 8. VARIABLE-DOT HALFTONE
# ============================================================

print("Creating halftone...")


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

        # ----------------------------------------------------
        # Subject mask
        # ----------------------------------------------------

        a = alpha.getpixel((x, y))

        if a < 100:
            continue


        # ----------------------------------------------------
        # Brightness
        # ----------------------------------------------------

        brightness = gray.getpixel(
            (x, y)
        )

        lightness = brightness / 255.0


        # ----------------------------------------------------
        # Contrast
        # ----------------------------------------------------

        lightness = lightness ** 1.30


        # ----------------------------------------------------
        # BODY / SHIRT CONTROL
        # ----------------------------------------------------

        normalized_y = y / height

        if normalized_y > 0.62:

            reduction = (
                normalized_y - 0.62
            ) / 0.38

            reduction = min(
                reduction,
                1.0
            )

            lightness *= (
                1.0 - 0.30 * reduction
            )


        # ----------------------------------------------------
        # Dark areas remain empty
        # ----------------------------------------------------

        if lightness < 0.13:
            continue


        # ----------------------------------------------------
        # Calculate dot size
        # ----------------------------------------------------

        radius = (
            MIN_RADIUS +
            lightness * MAX_RADIUS
        )


        # Keep dots separated
        radius = min(
            radius,
            DOT_SPACING * 0.40
        )


        if radius < MIN_RADIUS:
            continue


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
                245
            )
        )


# ============================================================
# 9. SUBTLE GREEN GLOW
# ============================================================

print("Adding subtle glow...")

glow = dots.filter(
    ImageFilter.GaussianBlur(5)
)

glow_alpha = glow.getchannel(
    "A"
)

glow_alpha = glow_alpha.point(
    lambda p: int(p * 0.16)
)

glow.putalpha(
    glow_alpha
)


# ============================================================
# 10. COMPOSITE
# ============================================================

output = Image.alpha_composite(
    output.convert("RGBA"),
    glow
)

output = Image.alpha_composite(
    output,
    dots
)


# ============================================================
# 11. SAVE
# ============================================================

output = output.convert("RGB")

output.save(
    OUTPUT,
    "PNG",
    optimize=True
)


# ============================================================
# DONE
# ============================================================

print()
print("========================================")
print(" GitHub Halftone Portrait Generated")
print("========================================")
print()
print("Output:", OUTPUT)
print("Color: #39D353")
print("Background: #0D1117")
print("Size:", output.size)
print()