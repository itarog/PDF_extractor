import fitz
import re
import textwrap

def clean_text(text):
    edited_text = text.replace('\n', ' ').replace('', ' ').replace(';', ' ').rstrip()
    pattern = r'(\b\d+[A-Z])\s*\(([^)]*MHz[^)]*)\)'
    edited_text = re.sub(pattern, r'\1 NMR (\2)', edited_text)
    return edited_text

def get_multi_idx(page_num, line_idx):
    return f'{page_num}_{line_idx}'

def get_norm_bbox(bbox, max_height, max_width): # adjust to (x, y, width, height)?
    norm_bbox = (round(100*bbox[0]/max_height, 2),
                 round(100*bbox[1]/max_width, 2),
                 round(100*bbox[2]/max_height, 2),
                 round(100*bbox[3]/max_width, 2)
                     )
    return norm_bbox


def get_page_text(pdf_page, page_num, max_width=250, dpi=200):
    output_list = []
    text_page = pdf_page.get_textpage()
    page_blocks = text_page.extractBLOCKS()

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    pix = pdf_page.get_pixmap(matrix=mat)
    page_w, page_h = pix.width, pix.height

    for x0, y0, x1, y1, line_text, line_num, _ in page_blocks:
        x0 *= zoom
        y0 *= zoom
        x1 *= zoom
        y1 *= zoom
        edited_text = clean_text(line_text)
        norm_bbox = get_norm_bbox((y0, x0, y1, x1), page_h, page_w) # 792, 612

        if len(edited_text) > max_width:
            wrapped_lines = textwrap.wrap(edited_text, width=max_width)
            for i, wrapped in enumerate(wrapped_lines):
                output_list.append((
                    get_multi_idx(page_num, line_num + i),
                    wrapped,
                    norm_bbox
                ))
        else:
            output_list.append((
                get_multi_idx(page_num, line_num),
                edited_text,
                norm_bbox
            ))

    temp_output_list = sorted(output_list, key=lambda x: x[2][0])

    final_output_list = [
        (get_multi_idx(page_num, new_line_num), text, bbox)
        for new_line_num, (multi_idx, text, bbox) in enumerate(temp_output_list)
    ]
    
    return final_output_list

# def get_page_text(pdf_page, page_num, max_width=250):
#     output_list = []
#     text_page = pdf_page.get_textpage()
#     page_blocks = text_page.extractBLOCKS()
    
#     for x0, y0, x1, y1, line_text, line_num, _ in page_blocks:
#         edited_text = clean_text(line_text)
#         norm_bbox = get_norm_bbox((y0, x0, y1, x1), 792, 612)

#         if len(edited_text) > max_width:
#             wrapped_lines = textwrap.wrap(edited_text, width=max_width)
#             for i, wrapped in enumerate(wrapped_lines):
#                 output_list.append((
#                     get_multi_idx(page_num, line_num + i),
#                     wrapped,
#                     norm_bbox
#                 ))
#         else:
#             output_list.append((
#                 get_multi_idx(page_num, line_num),
#                 edited_text,
#                 norm_bbox
#             ))

#     temp_output_list = sorted(output_list, key=lambda x: x[2][0])

#     final_output_list = [
#         (get_multi_idx(page_num, new_line_num), text, bbox)
#         for new_line_num, (multi_idx, text, bbox) in enumerate(temp_output_list)
#     ]
    
#     return final_output_list


# def get_page_text(pdf_page, page_num):
#     output_list = []
#     text_page = pdf_page.get_textpage()
#     page_blocks = text_page.extractBLOCKS()
#     for x_0, y_0, x_1, y_1, line_text, line_num, _ in page_blocks:
#         edited_text = clean_text(line_text) #
#         norm_bbox = get_norm_bbox((y_0, x_0, y_1, x_1), 792, 612)
#         output_list.append((get_multi_idx(page_num, line_num), edited_text, norm_bbox))
#     temp_output_list = sorted(output_list, key=lambda x: x[2][0])
#     final_output_list = [(get_multi_idx(page_num, new_line_num), text, bbox) for new_line_num, (multi_idx, text, bbox) in enumerate(temp_output_list)]
#     return final_output_list

def extract_text_with_multi_idx(pdf_path):
    document = fitz.open(pdf_path)
    text_page_num = []
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        page_lines_with_multi_idx = get_page_text(page, page_num)
        text_page_num.extend(page_lines_with_multi_idx)
    return text_page_num