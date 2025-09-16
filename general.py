from pypdf import PdfReader, PdfWriter

def get_page_num_and_line_num_from_multi_idx(multi_idx):
    return map(int, multi_idx.split('_'))

def get_actual_idx_from_multi_idx(multi_idx_list, requested_multi_idx):
    for actual_idx, multi_idx in enumerate(multi_idx_list):
        if requested_multi_idx == multi_idx:
            return actual_idx
    return False

def minimize_pdf_to_relavent_pages(input_pdf_path, output_pdf_path, page_numbers):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    for page_num in page_numbers:
        writer.add_page(reader.pages[page_num])
    with open(output_pdf_path, "wb") as output_pdf:
        writer.write(output_pdf)