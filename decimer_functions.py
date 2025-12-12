import numpy as np
import cv2
from PIL import Image
import os

###############################################################
##################### DECIMER FUNCTIONS #######################
###############################################################

def get_square_image(image: np.array, desired_size: int) -> np.array:
    """
    This function takes an image and resizes it without distortion
    with the result of a square image with an edge length of
    desired_size.

    Args:
        image (np.array): input image
        desired_size (int): desired output image length/height

    Returns:
        np.array: resized output image
    """
    image = Image.fromarray(image)
    old_size = image.size
    grayscale_image = image.convert("L")
    if old_size[0] or old_size[1] != desired_size:
        ratio = float(desired_size) / max(old_size)
        new_size = tuple([int(x * ratio) for x in old_size])
        grayscale_image = grayscale_image.resize(new_size, Image.LANCZOS)
    else:
        new_size = old_size
    resized_image = Image.new("L", (desired_size, desired_size), "white")

    resized_image.paste(
        grayscale_image,
        ((desired_size - new_size[0]) // 2, (desired_size - new_size[1]) // 2),
    )
    return np.array(resized_image)

def apply_mask(image, mask, color, alpha=0.5):
    """Apply the given mask to the image."""
    for c in range(3):
        image[:, :, c] = np.where(
            mask == 1,
            image[:, :, c] * (1 - alpha) + alpha * color[c] * 255,
            image[:, :, c],
        )
    return image

def get_masked_image(image: np.array, mask: np.array) -> np.array:
    """
    This function takes an image and a masks for this image
    (shape: (h, w)) and returns the masked image where only the
    masked area is not completely white and a bounding box of the
    segmented object

    Args:
        image (np.array): image of a page from a scientific publication
        mask (np.array): masks (shape: (h, w, num_masks))

    Returns:
        List[np.array]: segmented chemical structure depictions
        List[int]: bounding box of segmented object
    """
    for channel in range(image.shape[2]):
        image[:, :, channel] = image[:, :, channel] * mask[:, :]
    # Remove unwanted background
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(grayscale, 0, 255, cv2.THRESH_OTSU)
    bbox = cv2.boundingRect(thresholded)

    masked_image = np.zeros(image.shape).astype(np.uint8)
    masked_image = apply_mask(masked_image, mask, [1, 1, 1])
    masked_image = Image.fromarray(masked_image)
    masked_image = np.array(masked_image.convert("RGB"))
    x, y, w, h = bbox
    im_gray = cv2.cvtColor(masked_image, cv2.COLOR_RGB2GRAY)
    _, im_bw = cv2.threshold(im_gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Removal of transparent layer and generation of segment
    _, alpha = cv2.threshold(im_bw, 0, 255, cv2.THRESH_BINARY)
    b, g, r = cv2.split(image)
    rgba = [b, g, r, alpha]
    dst = cv2.merge(rgba, 4)
    background = dst[y : y + h, x : x + w]
    trans_mask = background[:, :, 3] == 0
    background[trans_mask] = [255, 255, 255, 255]
    return background, bbox

from general import minimize_pdf_to_relavent_pages
from pdf2image import convert_from_path
import copy

def get_page_image(pdf_path, page_num, dpi=300, poppler_path=None):

    temp_dir = os.path.dirname(os.path.abspath(pdf_path))
    temp_pdf_path = os.path.join(temp_dir, f'temp_page_{page_num}.pdf')
    minimize_pdf_to_relavent_pages(pdf_path, temp_pdf_path, [page_num])
    try:
        if poppler_path:
            images = convert_from_path(temp_pdf_path, dpi=dpi, poppler_path=poppler_path)
        else:
            images = convert_from_path(temp_pdf_path, dpi=dpi)
        page_image = np.array(images[0])
    finally:
        # Clean up temporary PDF file
        try:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
        except Exception:
            pass
    return page_image

def bbox_to_ranges(bbox, full_h, full_w):
    x, y, w, h = bbox
    x_range = (int(full_w*x/100), int(full_w*(x+w)/100))
    y_range = (int(full_h*y/100), int(full_h*(y+h)/100))
    return x_range, y_range

def get_mask_from_bbox(image, bbox):
    full_h, full_w, _ = image.shape
    mask = np.zeros((full_h, full_w))
    x_range, y_range = bbox_to_ranges(bbox, full_h, full_w)
    mask [y_range[0]:y_range[1], x_range[0]:x_range[1]] = 1
    # mask[h//3:2*h//3,w//3:2*w//3] = 1
    return mask

def get_page_image_from_file(image_dir, page_num):
    """Load page image from existing file if available"""
    page_image_path = os.path.join(image_dir, f'page_{page_num}.png')
    if os.path.exists(page_image_path):
        img = Image.open(page_image_path)
        return np.array(img)
    return None

def get_new_mol_pic(pdf_path, page_num, bbox, poppler_path=None, image_dir=None):
    # Try to load from existing image file first
    if image_dir:
        page_image = get_page_image_from_file(image_dir, page_num)
        if page_image is not None:
            mask = get_mask_from_bbox(page_image, bbox)
            new_mol_pic, _ = get_masked_image(page_image, mask)
            new_mol_pic = get_square_image(new_mol_pic, 224)
            return new_mol_pic
    
    # Fall back to PDF conversion if image not found
    page_image = get_page_image(pdf_path, page_num, poppler_path=poppler_path)
    mask = get_mask_from_bbox(page_image, bbox)
    new_mol_pic, _ = get_masked_image(page_image, mask)
    new_mol_pic = get_square_image(new_mol_pic, 224)
    # final_pic_obj = Image.fromarray(adj_pic)
    return new_mol_pic