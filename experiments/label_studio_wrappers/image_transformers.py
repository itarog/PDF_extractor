import numpy as np
import os
import textwrap
from PIL import Image, ImageFont, ImageDraw
from pdf2image import convert_from_path
from tqdm import tqdm

def np_image_to_image(array, output_filename, verbose=True):
    array = (array - np.min(array)) / (np.max(array) - np.min(array)) * 255
    array = array.astype(np.uint8)
    img = Image.fromarray(array).resize((700,1000), resample=0) 
    img.save(output_filename)
    if verbose:
        print(f"Saved: {output_filename}")

def pdf_to_np_images(pdf_path, o_pages, output_dir, dpi=300, poppler_path=None, verbose=True, overwrite=False, use_tqdm=False):
    """
    Convert selected pages of a PDF to PNGs. If overwrite=False, existing images
    are reused and not regenerated.
    """
    # If all target images already exist and we are not overwriting, skip conversion
    if not overwrite:
        all_exist = all(os.path.exists(os.path.join(output_dir, f'page_{p}.png')) for p in o_pages)
        if all_exist:
            return [f'page_{p}.png' for p in o_pages]

    if poppler_path:
        images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
    else:
        images = convert_from_path(pdf_path, dpi=dpi)
    np_images = [np.array(img) for img in images]
    created_files = []
    iterator = zip(np_images, o_pages)
    if verbose and use_tqdm:
        iterator = tqdm(list(iterator), desc="Pages", unit="page")
    # Suppress individual "Saved" messages when using progress bar
    save_verbose = verbose and not use_tqdm
    for np_img, o_page in iterator:
        output_filename = f'page_{o_page}.png'
        created_files.append(output_filename)
        output_path = os.path.join(output_dir, output_filename)
        if overwrite or not os.path.exists(output_path):
            np_image_to_image(np_img, output_path, save_verbose)
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