from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random


def generate_gradient(text, dark_mode, output_file):
    """Generates a mesh-like gradient image with text in the middle of the gradient."""
    # Image size
    width, height = 1500, 600

    # 1. Create a solid background
    background_color = (0, 0, 0) if dark_mode else (255, 255, 255)
    base_image = Image.new("RGB", (width, height), color=background_color)

    # 2. Create a transparent overlay for the gradient (without blur yet)
    gradient_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Add multiple overlapping radial gradients (circles)
    for _ in range(10):  # Adjust for more/less circles
        center_x = random.randint(0, width)
        center_y = random.randint(0, height)
        max_radius = random.randint(300, 600)
        color = tuple(random.randint(50, 150) for _ in range(3)) if dark_mode else tuple(random.randint(180, 255) for _ in range(3))
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for r in range(max_radius, 0, -10):  # Gradual fade
            alpha = int((r / max_radius) * 255)
            overlay_draw.ellipse(
                (center_x - r, center_y - r, center_x + r, center_y + r),
                fill=(*color, alpha),
            )
        gradient_layer = Image.alpha_composite(gradient_layer, overlay)

    # 3. Add an ellipse mask to the gradient
    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    ellipse_width = width * 1.5
    ellipse_height = height * 1.2
    ellipse_x1 = -ellipse_width // 4
    ellipse_y1 = height - (ellipse_height // 2)
    ellipse_x2 = width + (ellipse_width // 4)
    ellipse_y2 = height + (ellipse_height // 2)
    mask_draw.ellipse((ellipse_x1, ellipse_y1, ellipse_x2, ellipse_y2), fill=255)

    masked_gradient = Image.composite(gradient_layer, Image.new("RGBA", (width, height), (0, 0, 0, 0)), mask)

    # 4. Blur the masked gradient for a glow effect
    blurred_gradient = masked_gradient.filter(ImageFilter.GaussianBlur(150))

    # 5. Composite the blurred gradient onto the solid background
    final_layer = Image.alpha_composite(base_image.convert("RGBA"), blurred_gradient)

    # 6. Add text on top with tracking-tight effect
    try:
        font = ImageFont.truetype("Inter-Bold.ttf", 72)
    except IOError:
        print("Font not found. Ensure 'Inter-Bold.ttf' is in the project directory.")
        return

    draw = ImageDraw.Draw(final_layer)
    text_color = "white" if dark_mode else "black"

    # Calculate total text width for centering
    tracking_adjustment = -3  # Negative value to reduce spacing between letters (tracking-tight)
    total_width = sum(
        [draw.textbbox((0, 0), char, font=font)[2] for char in text]
    ) + tracking_adjustment * (len(text) - 1)
    text_x = (width - total_width) // 2
    text_y = (height - draw.textbbox((0, 0), text, font=font)[3]) // 2

    # Draw each character with adjusted tracking
    x = text_x
    for char in text:
        char_bbox = draw.textbbox((0, 0), char, font=font)
        char_width = char_bbox[2] - char_bbox[0]
        draw.text((x, text_y), char, font=font, fill=text_color)
        x += char_width + tracking_adjustment  # Move x forward with tracking adjustment

    # Save the final image
    final_layer.convert("RGB").save(output_file)
