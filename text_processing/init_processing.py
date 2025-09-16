import fitz

def clean_text(text):
    edited_text = text.replace('\n', ' ').replace('', ' ').replace(';', ' ').rstrip()
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

def get_page_text(pdf_page, page_num):
    output_list = []
    text_page = pdf_page.get_textpage()
    page_blocks = text_page.extractBLOCKS()
    for x_0, y_0, x_1, y_1, line_text, line_num, _ in page_blocks:
        edited_text = clean_text(line_text) #
        norm_bbox = get_norm_bbox((y_0, x_0, y_1, x_1), 792, 612)
        output_list.append((get_multi_idx(page_num, line_num), edited_text, norm_bbox))
    temp_output_list = sorted(output_list, key=lambda x: x[2][0])
    final_output_list = [(get_multi_idx(page_num, new_line_num), text, bbox) for new_line_num, (multi_idx, text, bbox) in enumerate(temp_output_list)]
    return final_output_list

def extract_text_with_multi_idx(pdf_path):
    document = fitz.open(pdf_path)
    text_page_num = []
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        page_lines_with_multi_idx = get_page_text(page, page_num)
        text_page_num.extend(page_lines_with_multi_idx)
    return text_page_num