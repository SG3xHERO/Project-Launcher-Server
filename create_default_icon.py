#!/usr/bin/env python3
"""
This script creates a simple default icon for modpacks.
It generates a colored square with the letter 'M' in the center.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create directory for static files
os.makedirs('static', exist_ok=True)

# Create a new image with a purple background
img = Image.new('RGB', (128, 128), (46, 49, 66))  # Dark blue background
draw = ImageDraw.Draw(img)

# Draw a slightly lighter center area
draw.rectangle([(10, 10), (118, 118)], fill=(43, 49, 78))

# Try to use a system font, or use the default
try:
    # Try a few different fonts that might be available on different systems
    font_options = ['Arial.ttf', 'DejaVuSans.ttf', 'FreeSans.ttf', 'Verdana.ttf']
    font = None
    
    for font_name in font_options:
        try:
            font = ImageFont.truetype(font_name, 80)
            break
        except IOError:
            continue
            
    if font is None:
        # Use default font if none of the above are available
        font = ImageFont.load_default()
        
except Exception:
    # Fallback to default font if there's any error
    font = ImageFont.load_default()

# Draw the letter 'M' in the center with a pink color
text_width, text_height = draw.textsize('M', font=font) if hasattr(draw, 'textsize') else (50, 60)
position = ((128 - text_width) // 2, (128 - text_height) // 2 - 10)
draw.text(position, 'M', fill=(230, 27, 114), font=font)  # Pink text

# Save the image
img.save('static/default-icon.png')

print("Default icon created at static/default-icon.png")