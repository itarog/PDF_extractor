import os
import numpy as np
# import gzip
from PIL import Image
from text_processing.init_processing import get_norm_bbox
from decimer_functions import get_square_image

from decimer_segmentation import segment_chemical_structures
from yode_backend import segment_chemical_structures_yode

import pymupdf  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
import cv2
from tqdm import tqdm


def segment_chemical_structures_from_file(file_path: str, expand: bool = True, pages=None, backend='decimer'):

    if file_path[-3:].lower() == "pdf":
        # Convert PDF to images using PyMuPDF with optimized settings
        pdf_document = pymupdf.open(file_path)
        images = [None] * pdf_document.page_count

        def render_page(page_num):
            page = pdf_document[page_num]
            matrix = pymupdf.Matrix(300 / 72, 300 / 72)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            return page_num, img_array

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(render_page, i) for i in range(pdf_document.page_count)]
            for future in futures:
                page_num, img_array = future.result()
                images[page_num] = img_array
        pdf_document.close()
        page_images = [img for img in images if img is not None]
    else:
        page_images = [cv2.imread(file_path, cv2.IMREAD_COLOR)]

    overall_segments = []

    iterator = tqdm(range(len(page_images)), desc='Segmenting pages', unit='page')

    for idx in iterator:
        im = page_images[idx]
        
        if im is None:
            overall_segments.append((idx, []))
            continue

        if backend == 'yode':
            segs = segment_chemical_structures_yode (im)

        else:
            segs = segment_chemical_structures(im, expand = False, return_bboxes=True)

        page_segments = [entry for entry in segs]

        overall_segments.append((idx, page_segments))

    return page_images, overall_segments

class MolPic:
    def __init__(self, page_num, pic, bbox):
        self.page_num = page_num
        self.pic = pic
        self.bbox = bbox # (y0, x0, y1, x1)
        self.y0 = bbox[0]

    def __repr__(self):
        return f'Page: {self.page_num, self.bbox}'

    def __str__(self):
        return f'Page: {self.page_num, self.bbox}'

def export_mol_pic(mol_pic, export_dir, molecule_name=None):
    pic_array = mol_pic.pic
    image_pil = Image.fromarray(pic_array)
    if molecule_name:
        export_path = os.path.join(export_dir, f'{molecule_name}.png')
    else:
        export_path = os.path.join(export_dir, 'my_molecule.png')
    image_pil.save(export_path)
    return export_path

def bbox_xyxy_to_xywh(bbox):
    x0, y0, x1, y1 = bbox
    new_bbox = (x0, y0, x1-x0, y1-y0)
    return new_bbox

def extract_pics_from_pdf(pdf_file, save_pics=False, save_dir='', pages=None, backend='decimer'):

    page_images, overalll_segments = segment_chemical_structures_from_file(
        pdf_file, expand=True, pages=pages, backend = backend
    )

    if not page_images:
        return []

    mol_pics = []


    for segment in overalll_segments:

        if len(segment) == 0:
            continue
        page_num, page_segments = segment
        # Expect (segment_images, bboxes)
        if not page_segments or not isinstance(page_segments, (tuple, list)) or len(page_segments) != 2:
            continue
        segment_images, bboxes = page_segments

        page_h = page_images[page_num].shape[0]
        page_w = page_images[page_num].shape[1]

        if len(segment_images) > 0:
            for idx, im in enumerate(segment_images):
                image = get_square_image(im, 224)
                norm_bbox = get_norm_bbox(bboxes[idx], page_h, page_w)
                xywh_bbox = bbox_xyxy_to_xywh(norm_bbox)
                molecule_pic = MolPic(page_num, image, xywh_bbox)
                mol_pics.append(molecule_pic)

    return mol_pics