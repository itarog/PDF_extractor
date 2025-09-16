import os
import numpy as np
# import gzip
from PIL import Image
from .text_processing.init_processing import get_norm_bbox
# from decimer_segmentation import segment_chemical_structures_from_file_modified, get_square_image

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
    
# def get_save_name(page_idx):
#     return f'page_{page_idx}.npy.gz'

# def save_page_pics(page_pics, dir_location):
#     current_dir = os.getcwd()
#     os.chdir(dir_location)
#     for page_idx, page_array in enumerate(page_pics):
#         file_name = get_save_name(page_idx)
#         with gzip.GzipFile(file_name, 'w') as f:
#             np.save(file=f, arr=page_array)
#     os.chdir(current_dir)

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

def extract_pics_from_pdf(pdf_file, save_pics=False, save_dir='', pages=None):
    page_images, overalll_segments = segment_chemical_structures_from_file_modified(pdf_file, expand=True, pages=pages)
    # if save_pics:
    #     save_page_pics(page_images, dir_location=save_dir)
    page_height = page_images[0].shape[0]
    page_width = page_images[0].shape[1]
    mol_pics = []
    for page_num, page_segments in overalll_segments:
        if len(page_segments)>0:
            for segment, bbox in page_segments:
                image = get_square_image(segment, 224)
                norm_bbox = get_norm_bbox(bbox, page_height, page_width)
                xywh_bbox = bbox_xyxy_to_xywh(norm_bbox)
                molecule_pic = MolPic(page_num, image, xywh_bbox)
                mol_pics.append(molecule_pic)
    return mol_pics