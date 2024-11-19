import os
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import numpy as np


def load_colors():
    """
    Load colors from the JSON file in the assets directory.
    Returns:
        dict: A dictionary containing color lists for dark and light modes.
    """
    assets_dir = "assets"
    colors_file = os.path.join(assets_dir, "colors.json")

    if not os.path.exists(colors_file):
        raise FileNotFoundError(f"Colors file not found at: {colors_file}")

    with open(colors_file, "r") as file:
        colors = json.load(file)

    if "dark_mode_colors" not in colors or "light_mode_colors" not in colors:
        raise ValueError("Colors JSON must include 'dark_mode_colors' and 'light_mode_colors'.")
    
    return colors


def generate_gradient(text, dark_mode, output_file):
    """Generates a mesh-like gradient image with text in the middle of the gradient."""
    # Image size
    width, height = 1500, 600

    # Load colors from JSON
    colors = load_colors()
    color_list = colors["dark_mode_colors"] if dark_mode else colors["light_mode_colors"]

    # 1. Create a solid background
    background_color = (0, 0, 0) if dark_mode else (255, 255, 255)
    base_image = Image.new("RGB", (width, height), color=background_color)

    # 2. Create a transparent overlay for the gradient (without blur yet)
    gradient_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Add multiple overlapping radial gradients (circles)
    for _ in range(10):  # Adjust for more/less circles
        # Random position
        center_x = random.randint(0, width)
        center_y = random.randint(0, height)

        # Random radius and color
        max_radius = random.randint(300, 600)
        color = random.choice(color_list)
        color_rgba = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (255,)

        # Draw radial gradient
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for r in range(max_radius, 0, -10):  # Gradual fade
            alpha = int((r / max_radius) * 255)
            overlay_draw.ellipse(
                (center_x - r, center_y - r, center_x + r, center_y + r),
                fill=(*color_rgba[:3], alpha),
            )
        gradient_layer = Image.alpha_composite(gradient_layer, overlay)

    # 3. Add an ellipse mask to the gradient
    mask = Image.new("L", (width, height), 0)  # Black background
    mask_draw = ImageDraw.Draw(mask)
    ellipse_width = width * 1.5
    ellipse_height = height * 1.2
    ellipse_x1 = -ellipse_width // 4
    ellipse_y1 = height - (ellipse_height // 2)
    ellipse_x2 = width + (ellipse_width // 4)
    ellipse_y2 = height + (ellipse_height // 2)
    mask_draw.ellipse((ellipse_x1, ellipse_y1, ellipse_x2, ellipse_y2), fill=255)

    # Apply the mask to the gradient
    masked_gradient_color = (0, 0, 0, 0) if dark_mode else (255, 255, 255, 0)
    masked_gradient = Image.composite(gradient_layer, Image.new("RGBA", (width, height), masked_gradient_color), mask)

    # 4. Blur the masked gradient for a glow effect
    blurred_gradient = masked_gradient.filter(ImageFilter.GaussianBlur(100))

    # 5. Composite the blurred gradient onto the solid background
    final_layer = Image.alpha_composite(base_image.convert("RGBA"), blurred_gradient)

    # 6. Add text on top
    try:
        font = ImageFont.truetype("Inter-Bold.ttf", 72)
    except IOError:
        print("Font not found. Ensure 'Inter-Bold.ttf' is in the project directory.")
        return

    draw = ImageDraw.Draw(final_layer)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    text_color = "white" if dark_mode else "black"
    draw.text((text_x, text_y), text, font=font, fill=text_color)

     # 7. Add grain effect
    noise = np.random.normal(0, 25, (height, width, 3)).astype(np.uint8)
    noise_image = Image.fromarray(noise, 'RGB')
    final_image = Image.blend(final_layer.convert("RGB"), noise_image, 0.05)


    # Save the final image
    final_layer.convert("RGB").save(output_file)
    print(f"Gradient saved as {output_file}")
