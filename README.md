# PDF text extractor

This repository contains the code and data accompanying the upcoming publication:

> **Itamar Wallwater et al., "PDF text extractor"**  
> https://doi.org/XXXX

The scripts provided here demonstrate possible usage in the pdf data extractor.

---

## 📄 Overview

The core functionalities demonstrated in this repository includes:

- PDF image extraction - how to extract molecule images from a PDF document
- PDF text extraction - how to extract text from a PDF document
- PDF full extraction - how to extract both image and text in a paired manned from a PDF document
- PDF extraction visuallization - how to view extracted results using labal studio
- label studio data retrival - how to update extracted data from label studio changes
---

## 📂 Installing

```
git clone https://github.com/itarog/PDF_extractor
```

currently, dependices need to be installed seperately.

---

## Playground Data
While the reader can use any aproriate pdf document, some example data can be found at:

### Example data 1

10 total files., thesis work from Columbia University NY. <br>
File path: ../demo_data/Exdata_1/

### Example data 2

10 total files, SI from the RSC journal chemical science. <br>
File path: ../demo_data/Exdata_2/

### Example data 3

10 total files, SI from publications by the Jonathan Burton group (University of Oxford) <br>
File path: ../demo_data/Exdata_3/

---

# PDF image extractor
Image extraction is excuted using the python package DECIMER-Segmentation (https://github.com/Kohulan/DECIMER-Image-Segmentation). <br>
Code is duplicated from their repository to ensure robust and independent work. The code duplicated can be found at ../decimer_functions.py <br>
**Activation of this code requires GPU**

```
from mol_pic import extract_pics_from_pdf
pdf_path = 'path_to_your_pdf.pdf'
mol_pics = extract_pics_from_pdf(pdf_path)
```

### The output
The output is a list where every items is a MolPic object.

## back-end
### MolPic (back-end)
MolPic is a container for an image, and is initialized using three parameters:
- **page_num** - int, the page where the image located (used for later matching)
- **image** - numpy array of the image
- **bbox** - tuple of the bbox indicating location of the extracted image in the format of (x, y, width, height) where (x,y) is the upper left corner. All x/width values are normallized according to page width and all y/height values are normallized according to page height

```
from mol_pic import MolPic
page_num = 3
image = ... # Numpy array of the image
bbox = (0.24, 0.05, 0.09, 0.8)
mol_pic = MolPic(page_num, image, bbox)
```
### MolPicCluster (back-end)
MolPicCluster is container for multiple MolPic, where every MolPicCluster is assigned to a molecule segment, and one MolPic from the cluster is selected as the representative. <br>
MolPicCluster is initialized using onr parameter:
- **mol_pics** - list where each item is MolPic

```
from mol_pic_cluster import MolPicCluster
list_of_mol_pic = [mol_pic_1, mol_pic_2, ...]
mol_pic_cluster = MolPicCluster(list_of_mol_pic)
```

---

# PDF text extractor
Text extraction is excuted using the python package PyMuPDF (https://pymupdf.readthedocs.io/en/latest/index.html). <br>

```
pip install pymupdf
```

## Basic text grab (PyMuPDF wrapper)

The function **pdf_text_with_idx** takes the path to pdf file and return list containing all of the text lines in the pdf. <br>
- **multi_idx** - contains the page and line number of the extracted text, i.e 3_12 will be page 3 line 12
- **text** - the extracted text
- **bbox** - the location in the page where the text was located in the form of (y_0, x_0, y_1, x_1), where (y_0, x_0) is the upper left corner and (y_1, x_1) is the bottom right corner. All values are normallized by the max width and height. 

```
from text_processing.init_processing import extract_text_with_multi_idx
pdf_path = 'path_to_your_pdf.pdf'
pdf_text_with_idx = extract_text_with_multi_idx(pdf_path)
```

### The output
The output is a list where every item is of the form: (multi_idx, text, bbox)

## Full text grab
The full extraction process is wrapped by the function **process_text_doc** takes the path to pdf file and return the data processed as **MoleculeSegement** objects

```
from text_processing.init_processing import extract_text_with_multi_idx
pdf_path = 'path_to_your_pdf.pdf'
pdf_text_with_idx = extract_text_with_multi_idx(pdf_path)
```

The following describes the three operation stages that **process_text_doc** takes for it's analysis:

### Stage 1 - locating molecule segments
The extracted text is divided into **MoleculeSegement** objects, where the each segment is aimed at describing one molecule. <br>
Molecule segments can initiallized manually but for text extraction, molecule segments will be created automatically. <br>
The decision of on whice text line each molecule segment begins and ends depends on locating molecule names that serve as a title. <br>
To that end, there are two free parameter that needs to be determined:
- **tokens_mark** - The mininum percentile of molecule-name-tokens that the text line has compared to all other text lines in the document. In order for a line to be considered the beginning of a molecule segment, the line needs to have tokens percentile above this number. (default: 40)
- **spaces_mark** - The maximum percentile of spaces that the text line has compared to all other text lines in the document. In order for a line to be considered the beginning of a molecule segment, the line needs to have spaces percentile below this number. (default: 20)

```
from molecule_segment.segments_creation import locate_molecule_segments 
tokens_mark = 40
spaces_mark = 20
molecule_segments = locate_molecule_segments(page_lines_with_multi_idx, tokens_mark=tokens_mark, spaces_mark=spaces_mark)
```

### Stage 2 - processing molecule segments
After the inital molecule segments are created, each molecule segement is searched for **TestTextLine** and **TestTextSequence**

```
from molecule_segment.sequences2segments import process_molecule_segment_text 
processed_molecule_segments = process_molecule_segment_text(molecule_segments)
```

### Stage 3 - molecule segments final adjustment
After all molecule segments have been processed, the molecule segments will be adjusted according to the most common test sequence. <br>
The main target of this part is to combine molecule segments that have been wrongly seperated, deduced by the most common test sequence. <br>
i.e, if the most common test sequence is ['Rf, 'IR', '1H NMR', '13C NMR'], and there are two adjacent molecule segments (and in physical proximity) that togather complete to the most common test sequence (like ['Rf'] and ['IR', '1H NMR', '13C NMR']), those segments will be united to one.

```
from molecule_segment.segements_merging import adjust_molecule_segments_by_common_sequence
final_molecule_segments = adjust_molecule_segments_by_common_sequence(processed_molecule_segments)
```

### The output
The output is a list where every item is a MoleculeSegment

## back-end
### Molecule segments - initiation (back-end)
To create a **MoleculeSegement** object, you need to provide one parameter:
- **segment_lines** - a list describing the text line in the molecule segment, where every item is of the form (multi_idx, text, bbox)

```
from molecule_segment.molecule_segment_obj import MoleculeSegment 
pdf_path = 'path_to_your_pdf.pdf'
pdf_text_with_idx = extract_text_with_multi_idx(pdf_path)
molecule_segment_1 = MoleculeSegment(pdf_text_with_idx)
molecule_segment_2 = MoleculeSegment(pdf_text_with_idx[5:10])
```

### MoleculeSegment - after text extraction (back-end)
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


### TestTextLine (back-end)
TestTextLine is a container for text lines pertaining to targeted data, and is initialized using three parameters:
- **start_multi_idx** - string, the multi_idx of the start page and line where the text located
- **end_multi_idx** - string, the multi_idx of the end page and line where the text located
- **bbox_list** - a list where every item is a bbox of the location of the extracted text in the format of (y_0, x_0, y_1, x_1), where (y_0, x_0) is the upper left corner and (y_1, x_1) is the bottom right corner. All values are normallized by the max width and height.
- **test_type** - string of the extracted test type, i.e '1H NMR', 'Rf', ...
- **test_text** - string of the concatenated text pertaining to targeted data

```
from test_text_line import TestTextLine 
start_multi_idx = '3_12'
end_multi_idx = '3_14'
bbox_list = [(0.24, 0.05, 0.31, 0.85)]
test_type = '1H NMR'
test_text = '1H NMR (600 MHz, DMSO-d6) δ/ppm = 9.04 (s, 1H, H-3), 8.69 (d, J = 4.8 Hz, 1H, H-4), 8.21 (d, J = 7.9 Hz, 1H, H-6), 8.18 (bs, 1H, NH2), 7.62 (bs, 1H, NH2), 7.48 (dd, J = 7.9, 4.8 Hz, 1H, H-5)'
test_text_line_ex = TestTextLine(start_multi_idx, end_multi_idx, bbox_list, test_type, test_text)
```

### TestTextSequence (back-end)
TestTextSequence is a container for adjacent TestTextLines, according to their start/end multi_idx. This later helps determine if a molecule segement contains more than one molecule and divide into smaller molecule segments accordingly. TestTextSequence is initalized using one parameter:

- **list_of_test_text_line** - a list where every item is a TestTextLine

```
from test_text_sequence import TestTextSequence
list_of_test_text_line = [test_text_line_1, test_text_line_2, ...]
test_text_sequence_ex = TestTextSequence(list_of_test_text_line)
```

# PDF full extractor
In full extraction mode, there are two options:
- extracting molecule images first, then extract text (**recommended**)
- extracting text first, then molecule images

The reason behind the order being pivotal, is that initial extracted data can help guide further extraction. <br>
By extracting molecule images first, the process of identifying molecule segments can be improved by optimizing the two hyperparameters **tokens_mark** and **spaces_mark**. The optimization process is brute-force over the following options:

```
optimize_options = [{'tokens': 40, 'spaces': 20},
                    {'tokens': 40, 'spaces': 30},
                    {'tokens': 40, 'spaces': 40},
                    {'tokens': 60, 'spaces': 20},
                    {'tokens': 60, 'spaces': 30},
                    {'tokens': 60, 'spaces': 40},
                    {'tokens': 80, 'spaces': 20},
                    {'tokens': 80, 'spaces': 30},
                    {'tokens': 80, 'spaces': 40}]
```

## Extracting images first

```
from wrappers import process_doc_list_pics_first
final_molecule_segments = adjust_molecule_segments_by_common_sequence(processed_molecule_segments)
```

### Working with previously obtained images
Since the process of extracting images requires GPU and can be time consuming, the extraction process also allows to extract images ahead of time and possibily on a different using a stored pickle file saved at the end of the images extraction process.

### The output
The output is in the form of a dictionary, where every key is the file name, and the values in form of a tuple (molecule_segments, mol_pic_clusters) 

## Extracting text first

```
from wrappers import process_doc_list_text_first
final_molecule_segments = adjust_molecule_segments_by_common_sequence(processed_molecule_segments)
```


# PDF extraction visuallization (via label-studio)

## Configuring label-studio
TBD


# label-studio data retrival

TBD