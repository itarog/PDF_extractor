# PDF text extractor

This repository contains the code and data accompanying the upcoming publication:

> **Itamar Wallwater et al., "PDF text extractor"**  
> https://doi.org/XXXX

The scripts provided here demonstrate possible usage in the pdf data extractor.

---

## 📄 Overview

TBD

The core functionalities demonstrated in this repository includes:

- PDF image extraction - how to extract molecule images from a PDF document
- PDF text extraction - how to extract text from a PDF document
- PDF full extraction - how to extract both image and text in a paired manned from a PDF document
- PDF extraction visuallization - how to view extracted results using labal studio
- label studio data retrival - how to update extracted data from label studio changes
---

## 📂 Installing

TBD

```
git clone 
```

---

## Playground Data
While the reader can use any aproriate pdf document, some example data can be found at:

### Example data 1

10 total files., thesis work from Columbia. <br>
File path: main/database_files/features_1_df.ftr

### Example data 2

10 total files, SI from chemical science. <br>
File path: main/database_files/features_2_df.ftr

### Example data 3

10 total files, SI from ... <br>
File path: main/database_files/features_3_df.ftr

---

# PDF image extractor
Image extraction is excuted using the python package DECIMER-Segmentation (https://github.com/Kohulan/DECIMER-Image-Segmentation). <br>
Code is duplicated from their repository to ensure robust and independent work. The code duplicated can be found at main\decimer_functions.py

## Code

```
pdf_path = 'path_to_your_pdf.pdf'
mol_pics = extract_pics_from_pdf(pdf_path)
```
The output is a list where every items is a MolPic object.

## MolPic (back-end)
MolPic is a container for an image, and is initialized using three parameters:
- page_num - int, the page where the image located (used for later matching)
- image - numpy array of the image
- bbox - bbox of the location of the extracted image in the format of (x, y, width, height) where (x,y) is the upper left corner.

```
page_num = 3
image = ... # Numpy array of the image
bbox = (x, y, width, height)
mol_pic = MolPic(page_num, image, bbox)
```
## MolPicCluster (back-end)
MolPicCluster is container for multiple MolPic, where every MolPicCluster is assigned to a molecule segment, and one MolPic from the cluster is selected as the representative. \\
MolPicCluster is initialized using onr parameter:
- mol_pics - list where each item is MolPic

```
list_of_mol_pic = [mol_pic_1, mol_pic_2, ...]
mol_pic_cluster = TestTextSequence(list_of_mol_pic)
```

---

# PDF text extractor
Text extraction is excuted using the python package PyMuPDF (https://pymupdf.readthedocs.io/en/latest/index.html). <br>

```
pip install pymupdf
```

## Basic text grab (PyMuPDF wrapper)

The function '' takes the path to pdf file and return list containing all of the text lines in the pdf.
The output is a list where every item is of the form: (multi_idx, text, bbox)
- multi_idx - contains the page and line number of the extracted text, i.e 3_12 will be page 3 line 12. 
- text - the extracted text
- bbox - the location in the page where the text was located in the form of (y_0, x_0, y_1, x_1), where (y_0, x_0) is the upper left corner and (y_1, x_1) is the bottom right corner. All values are normallized by the max width and height. 

```
pdf_path = 'path_to_your_pdf.pdf'
pdf_text_with_idx = extract_text_with_multi_idx(pdf_path)
for multi_idx, line, bbox in pdf_text_with_idx:
    print(multi_idx, line, bbox)
```

## Locating molecule segments
The extracted text is divided into *MoleculeSegement* objects, where the each segment is aimed at describing one molecule. <br>
Molecule segments can initiallized manually but for text extraction, molecule segments will be created automatically. <br>
The decision of on whice text line each molecule segment begins and ends depends on locating molecule names that serve as a title. <br>
To that end, there are two free parameter that needs to be determined:
- tokens_mark - The mininum percentile of molecule-name-tokens that the text line has compared to all other text lines in the document. In order for a line to be considered the beginning of a molecule segment, the line needs to have tokens percentile above this number. (default: 40)
- spaces_mark - The maximum percentile of spaces that the text line has compared to all other text lines in the document. In order for a line to be considered the beginning of a molecule segment, the line needs to have spaces percentile below this number. (default: 20)

```
tokens_mark = 40
spaces_mark = 20
molecule_segments = locate_molecule_segments(page_lines_with_multi_idx, tokens_mark=tokens_mark, spaces_mark=spaces_mark)
```

## Processing molecule segments
After the inital molecule segments are created, each molecule segement is searched for *TestTextLine* and *TestTextSequence*

### TestTextLine (back-end)
TestTextLine is a container for text lines pertaining to targeted data, and is initialized using three parameters:
- start_multi_idx - string, the multi_idx of the start page and line where the text located
- end_multi_idx - string, the multi_idx of the end page and line where the text located
- bbox_list - a list where every item is a bbox of the location of the extracted text in the format of (y_0, x_0, y_1, x_1), where (y_0, x_0) is the upper left corner and (y_1, x_1) is the bottom right corner. All values are normallized by the max width and height.
- test_type - string of the extracted test type, i.e '1H NMR', 'Rf', ...
- test_text - string of the concatenated text pertaining to targeted data

```
start_multi_idx = '3_12'
end_multi_idx = '3_14'
bbox_list = [(0.24, 0.05, 0.31, 0.85)]
test_type = '1H NMR'
test_text = '1H NMR (600 MHz, DMSO-d6) δ/ppm = 9.04 (s, 1H, H-3), 8.69 (d, J = 4.8 Hz, 1H, H-4), 8.21 (d, J = 7.9 Hz, 1H, H-6), 8.18 (bs, 1H, NH2), 7.62 (bs, 1H, NH2), 7.48 (dd, J = 7.9, 4.8 Hz, 1H, H-5)'
test_text_line = TestTextLine(start_multi_idx, end_multi_idx, bbox_list, test_type, test_text)
```

### TestTextSequence (back-end)
TestTextSequence is a container for adjacent TestTextLines, according to their start/end multi_idx. This later helps determine if a molecule segement contains more than one molecule and divide into smaller molecule segments accordingly. TestTextSequence is initalized using one parameter:

- list_of_test_text_line - a list where every item is a TestTextLine

```
list_of_test_text_line = [test_text_line_1, test_text_line_2, ...]
test_text_sequence = TestTextSequence(list_of_test_text_line)
```

### code (front-end)

```
processed_molecule_segments = process_molecule_segment_text(molecule_segments)
```

## Molecule segments final adjustment
After all molecule segments have been processed, the molecule segments will be adjusted according to the most common test sequence. <br>
The main target of this part is to combine molecule segments that have been wrongly seperated, deduced by the most common test sequence. <br>
i.e, if the most common test sequence is ['Rf, 'IR', '1H NMR', '13C NMR'], and there are two adjacent molecule segments (and in physical proximity) that togather complete to the most common test sequence (like ['Rf'] and ['IR', '1H NMR', '13C NMR']), those segments will be united to one.

```
final_molecule_segments = adjust_molecule_segments_by_common_sequence(processed_molecule_segments)
```

### MoleculeSegment (back-end)
The main attributes of MoleculeSegment object in it's post-extraction state are:
- segment_lines - a list describing the text line in the molecule segment, where every item is of the form (multi_idx, text, bbox)
- begin_multi_idx - string, the multi_idx of the start page and line where the molecule segment is located
- end_multi_idx - string, the multi_idx of the end page and line where the molecule segment is located
- nmr_text_line_list - a list of TestTextLine of all relevant NMR tests
- ir_text_line_list - a list of TestTextLine of all relevant IR tests
- rf_text_line_list - a list of TestTextLine of all relevant Rf tests
- ms_text_line_list - a list of TestTextLine of all relevant MS tests
- mol_pics - a list of all relevant MolPicCluster
- molecule_name - the persumed name of the molecule
- has_test_text_sequence - bool, True if the molecule segment has test_text
- test_text_sequence - TestTextSequence of the relevant test text lines

# PDF full extractor

TBD

# PDF extraction visuallization

TBD

# label studio data retrival

TBD