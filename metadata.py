import fitz  # PyMuPDF
import re
class MetaData:
    def __init__(self, amended_metadata, raw_metadata):
        self.__dict__.update(amended_metadata)
        self.__dict__.update(raw_metadata)

    def __str__(self):
        return str(self.__dict__)
    
    def __repr__(self):
        return str(self.__dict__)

def extract_metadata_from_text(text):
    metadata = {}
    patterns = {
        'Text_title': re.compile(r'(?:Title|Thesis Title):\s*(.*)', re.IGNORECASE),
        'Text_author': re.compile(r'(?:Author|Candidate):\s*(.*)', re.IGNORECASE),
        'Text_university': re.compile(r'(?:University|Institution):\s*(.*)', re.IGNORECASE),
        'Text_year': re.compile(r'(?:Year|Date):\s*(\d{4})', re.IGNORECASE),
        'Text_subject': re.compile(r'(?:Subject|Discipline):\s*(.*)', re.IGNORECASE)
    }
    
    for key, pattern in patterns.items():
        match = pattern.search(text)
        if match:
            metadata[key] = match.group(1).strip()
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'Text_title' not in metadata and i < 5:
            metadata['Text_title'] = line.strip()
        if 'Text_author' not in metadata and 'by' in line.lower():
            metadata['Text_author'] = line.strip().split('by')[-1].strip()
        if 'Text_university' not in metadata and 'university' in line.lower():
            metadata['Text_university'] = line.strip()
        if 'Text_year' not in metadata and re.search(r'\b\d{4}\b', line):
            metadata['Text_year'] = re.search(r'\b\d{4}\b', line).group()
        if 'Text_subject' not in metadata and 'subject' in line.lower():
            metadata['Text_subject'] = line.strip()
    
    return metadata

def extract_metadata_from_amended_pdf(pdf_path):
    document = fitz.open(pdf_path)
    metadata = document.metadata
    amended_metadata = {'Author_metadata:': metadata.get('author'),
                        'Title_metadata:': metadata.get('title'),
                        'subject_metadata:': metadata.get('subject'),}
    return amended_metadata

def extract_metadata_from_raw_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_idx in range(5):
        page = document.load_page(page_idx)
        text += page.get_text()
    raw_metadata = extract_metadata_from_text(text)
    return raw_metadata