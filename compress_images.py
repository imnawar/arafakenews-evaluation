"""
One-time script: resize and compress all images in the evaluation folder
so they load fast on mobile connections. Run this once, before pushing
to GitHub, then commit the smaller images instead of the originals.

Usage:
    pip install pillow
    python compress_images.py
"""

import os
from PIL import Image

# ==========================================
# 🔹 CONFIG
# ==========================================
IMAGES_FOLDER = "data/GeneratedImagesToEvaluate"   # adjust if needed
MAX_WIDTH = 900          # pixels — plenty for on-screen evaluation
JPEG_QUALITY = 80        # 70-85 is a good balance of size vs quality

image_extensions = (".png", ".jpg", ".jpeg", ".webp")

total_before = 0
total_after = 0
count = 0

for filename in os.listdir(IMAGES_FOLDER):

    if not filename.lower().endswith(image_extensions):
        continue

    path = os.path.join(IMAGES_FOLDER, filename)
    size_before = os.path.getsize(path)
    total_before += size_before

    ext = filename.lower().rsplit(".", 1)[-1]

    with Image.open(path) as img:

        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_size = (MAX_WIDTH, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        if ext in ("jpg", "jpeg"):
            img = img.convert("RGB")
            img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        else:
            # Keep PNG/webp as-is (lossless), just resized — still shrinks
            # file size a lot since dimensions are the main driver.
            img.save(path, optimize=True)

    size_after = os.path.getsize(path)
    total_after += size_after
    count += 1

print(f"✅ Compressed {count} images")
print(f"   Before: {total_before / 1024 / 1024:.1f} MB")
print(f"   After:  {total_after / 1024 / 1024:.1f} MB")
print(f"   Saved:  {(1 - total_after / total_before) * 100:.0f}%")
