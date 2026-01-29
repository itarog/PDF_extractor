import os
import numpy as np
# import gzip
from PIL import Image

# from decimer_segmentation import segment_chemical_structures
from src.models.yode_backend import segment_chemical_structures_yode
from src.models.decimer_functions import get_square_image

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
            # print ('yode')
            segs = segment_chemical_structures_yode (im)

        else:
            segs = segment_chemical_structures(im, expand = False, return_bboxes=True)

        page_segments = [entry for entry in segs]

        overall_segments.append((idx, page_segments))

    return page_images, overall_segments

class MolPic:
    def __init__(self, page_num, bbox, pic, pdf_path = None):
        self.page_num = page_num
        self.bbox = bbox # bbox is stored as (x_percent, y_percent, width_percent, height_percent)
        self.pic = pic
        self.y0 = bbox[1]

        if pdf_path != None:
            self.pdf_path = pdf_path

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

def bbox_xyxy_to_xywh(bbox, page_w, page_h):
    x0, y0, x1, y1 = bbox
    new_bbox = (round(100*x0/page_w, 2),
                round(100*y0/page_h, 2), 
                round(100*(x1-x0)/page_w, 2), 
                round(100*(y1-y0)/page_h, 2), )
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
                xywh_bbox = bbox_xyxy_to_xywh(bboxes[idx], page_w, page_h)
                molecule_pic = MolPic(page_num, xywh_bbox, image, pdf_file)
                mol_pics.append(molecule_pic)

    return mol_pics