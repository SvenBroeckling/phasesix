import os

from PIL import Image
from django.conf import settings
from django.contrib.staticfiles import finders


def render_string(string, context):
    from django.template import Template, Context

    t = Template(string)
    c = Context(context)
    return t.render(c)


def crit_successes(value, crit_threshold=11):
    """Returns the number of additional successes caused by crits"""
    ca = 0
    while value > crit_threshold - 1:
        value -= 6
        ca += 1
    return ca


def static_thumbnail(image_file, geometry_string, crop="center", quality=99):
    """
    Create a thumbnail of an image using Pillow library.

    Parameters:
    - image_file (str): Path to the input image file.
    - geometry_string (str): Desired size and geometry for the thumbnail (e.g., '300x200').
    - crop (str): Crop method, default is 'center'.
    - quality (int): JPEG quality, default is 99.

    Returns:
    - Image object: The created thumbnail image.
    """

    if "x" not in geometry_string:
        geometry_string = f"{geometry_string}x{geometry_string}"

    path = os.path.join(settings.MEDIA_ROOT, "static_thumbnails")
    os.makedirs(path, exist_ok=True)
    target_file_parts = os.path.basename(image_file).split(".")
    target_file_parts.insert(-1, geometry_string)
    target_file_name = ".".join(target_file_parts)
    target_path = os.path.join(path, target_file_name)
    target_url = f"{settings.MEDIA_URL}/static_thumbnails/{target_file_name}"

    if os.path.exists(target_path):
        return target_url

    with Image.open(finders.find(image_file)) as img:
        width, height = map(int, geometry_string.split("x"))
        aspect_ratio = img.width / img.height

        if aspect_ratio > width / height:
            new_width = width
            new_height = int(width / aspect_ratio)
        else:
            new_height = height
            new_width = int(height * aspect_ratio)

        img = img.resize((new_width, new_height), Image.BICUBIC)

        if crop == "center":
            left = (new_width - width) // 2
            top = (new_height - height) // 2
            right = (new_width + width) // 2
            bottom = (new_height + height) // 2
            img = img.crop((left, top, right, bottom))
        elif crop == "top-left":
            img = img.crop((0, 0, width, height))

        img = img.convert("RGB")
        img.save(target_path, format="JPEG", quality=quality)
        return target_url
