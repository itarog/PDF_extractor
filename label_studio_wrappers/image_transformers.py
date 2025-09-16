import numpy as np
import os
import textwrap
from PIL import Image, ImageFont, ImageDraw
from pdf2image import convert_from_path

def np_image_to_image(array, output_filename, verbose=True):
    array = (array - np.min(array)) / (np.max(array) - np.min(array)) * 255
    array = array.astype(np.uint8)
    img = Image.fromarray(array).resize((700,1000), resample=0) 
    img.save(output_filename)
    if verbose:
        print(f"Saved: {output_filename}")

def pdf_to_np_images(pdf_path, o_pages, output_dir, dpi=300, poppler_path=None, verbose=True):
    if poppler_path:
        images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
    else:
        images = convert_from_path(pdf_path, dpi=dpi)
    np_images = [np.array(img) for img in images]
    created_files = []
    for np_img, o_page in zip(np_images, o_pages):
        output_filename = f'page_{o_page}.png'
        created_files.append(output_filename)
        output_path = os.path.join(output_dir, output_filename)
        np_image_to_image(np_img, output_path, verbose)
    return created_files

def save_text_to_image(text, export_name, image_width=500, font_size=16, line_spacing=10):
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    max_chars_per_line = 80
    lines = text.split("\n")
    new_lines = []
    for line in lines:
        if len(line)<=max_chars_per_line:
            new_lines.append(line)
        else:
            wrapped_text = textwrap.fill(line, width=max_chars_per_line)
            new_lines.extend(wrapped_text.split("\n"))
    lines = new_lines    
    text_height = 500
    img = Image.new("L", (image_width, text_height), 255)
    draw = ImageDraw.Draw(img)
    y = 20
    for line in lines:
        text_height = font_size*2.5
        draw.text((20, y), line.replace('\u03b4', ''), font=font, fill=0)
        y += text_height + line_spacing
    img.save(export_name)