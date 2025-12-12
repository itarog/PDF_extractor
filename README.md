# PDF Chemical Analysis Extractor

This repository contains the code and data accompanying the upcoming publication:

> **Itamar Wallwater et al., "PDF text extractor"**  
> https://doi.org/XXXX

The package extracts chemical analysis text and molecule images from PDF files, with support for Label Studio annotation and Streamlit visualization.

---

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/itarog/PDF_extractor.git
cd PDF_extractor
```

2. **Create a conda environment (recommended):**
```bash
conda create -n pdf_extractor python=3.10
conda activate pdf_extractor
```

3. **Install the package:**
```bash
python -m pip install .
```

**Note:** The installation process will automatically download required dependencies including:
- YOLOv5 model files
- Poppler binaries (for PDF processing on Windows)
- All Python package dependencies listed in `setup.py`


## Typical Usage (concrete paths)
### Step 2: Optional - Label Studio Annotation

Process a folder of PDF files:

```bash
# Text extraction only
python main.py --input demo_data/Exdata_1 --output results

# With image extraction 
python main.py --input demo_data/Exdata_1 --output results --pics

# With image extraction using decimer backend (much slower)
python main.py --input demo_data/Exdata_1 --output results --pics --backend decimer
```

This will:
- Process all PDF files in the input folder
- Extract chemical analysis text (NMR, IR, MS, Rf)
- Detect molecule segments
- Save results to `results/` folder as pickle files (`.pkl`)

### Step 2: Optional - Label Studio Annotation

Fix annotations and image bounding boxes using Label Studio:

1. Start Label Studio server
2. Send pkl data to Label Studio
3. Annotate in the web interface
4. Update pkl files from annotations

See [Label Studio Setup](#label-studio-setup) section below.

1. **Start Label Studio:**
```bash
python main.py --input demo_data/Exdata_1 --output results --pics --backend yode
```

Send PKLs to Label Studio:
```bash
python send_to_label_studio.py --pkl-folder results --pdf-dir demo_data/Exdata_1 --api-key <api_key>
```

Update PKLs from Label Studio annotations:
```bash
python update_from_label_studio.py --pkl-folder results --pdf-dir demo_data/Exdata_1 --api-key <api_key>
```


### Step 3: Export and Visualize

Export CSV and images, then visualize with Streamlit:

```bash
python main.py --output results --visualize-only
```

Process and visualize in one step:
```bash
python main.py --input demo_data/Exdata_1 --output results --pics --visualize
```

---

## Label Studio Setup

Label Studio must be allowed to serve your local PDFs and extracted images.

### Set environment variables
- Choose a root that contains your PDFs (e.g., `Z:\` on Windows, `/Users/<you>` or `/home/<you>` on macOS/Linux).

**Windows (cmd):**
```cmd
set LOCAL_FILES_SERVING_ENABLED=true
set LOCAL_FILES_DOCUMENT_ROOT=Z:\
label-studio
```

**macOS/Linux (bash/zsh):**
```bash
export LOCAL_FILES_SERVING_ENABLED=true
export LOCAL_FILES_DOCUMENT_ROOT=/path/to/root
label-studio
```

Or use the helper (sets env vars and starts LS):
```bash
python start_label_studio.py
```

### After starting LS
1. Open http://localhost:8080 and annotate.  
2. Run `update_from_label_studio.py` to pull changes back into the PKLs.

---

## Workflow at a Glance
- Extract PDFs → PKLs: `main.py --input demo_data/Exdata_1 --output results [--pics --backend yode]`
- (Optional) Send to Label Studio, annotate, then update PKLs.
- Visualize or export with `main.py --output results --visualize-only [--graph-sketch]`.

---

## Output Format (brief)

- `.pkl` per PDF with molecule segments, bounding boxes, and optional molecule images.
- Stage 3 export (`--visualize-only` or `--visualize`) writes a CSV of extracted data plus rendered molecule images into the `--output` folder.

Example access:
```python
from storeage_obj import load_pickle_by_filename
result = load_pickle_by_filename('results/example.pkl')
for segment in result.molecule_segments:
    print(segment.molecule_name)
```

---

## Programmatic Usage

### From Python

```python
from streamlit_wrappers import process_pdf_dir_end_to_end

pdf_dir = './demo_data'
database_name = 'my_database'
cmd_process = process_pdf_dir_end_to_end(
    pdf_dir,
    verbose=True,
    backend='yode',  # or 'decimer'
    database_name=database_name,
    graph_sketch=False
)
```

---

## Technical Details

### PDF Image Extraction

Image extraction uses DECIMER-Segmentation or YOLOv5 (YoDe). Code is duplicated from DECIMER repository for robustness and can be found at `decimer_functions.py`.

```python
from mol_pic import extract_pics_from_pdf

pdf_path = 'path_to_your_pdf.pdf'
mol_pics = extract_pics_from_pdf(pdf_path, backend='decimer')  # or 'yode'
```

**MolPic** - Container for an image:
- `page_num` - Page where image is located
- `image` - Numpy array of the image
- `bbox` - Bounding box (x, y, width, height)

**MolPicCluster** - Container for multiple MolPic objects, where one is selected as representative.

### PDF Text Extraction

Text extraction uses PyMuPDF. The function `extract_text_with_multi_idx` returns a list where each item is: `(multi_idx, text, bbox)`

- `multi_idx` - Page and line number (e.g., `3_12` = page 3, line 12)
- `text` - Extracted text
- `bbox` - Location in page (y_0, x_0, y_1, x_1), normalized

```python
from text_processing.init_processing import extract_text_with_multi_idx

pdf_path = 'path_to_your_pdf.pdf'
pdf_text_with_idx = extract_text_with_multi_idx(pdf_path)
```

### Locating Molecule Segments

Text is divided into `MoleculeSegment` objects. Parameters:
- `tokens_mark` - Minimum percentile of molecule-name-tokens (default: 40)
- `spaces_mark` - Maximum percentile of spaces (default: 20)

```python
from molecule_segment.segments_creation import locate_molecule_segments

molecule_segments = locate_molecule_segments(
    page_lines_with_multi_idx,
    tokens_mark=40,
    spaces_mark=20
)
```

### Processing Molecule Segments

Each molecule segment is searched for `TestTextLine` and `TestTextSequence`.

**TestTextLine** - Container for text lines:
- `start_multi_idx`, `end_multi_idx` - Start/end page and line
- `bbox_list` - List of bounding boxes
- `test_type` - Test type (e.g., '1H NMR', 'IR', 'MS')
- `text` - Extracted text

**TestTextSequence** - Container for adjacent TestTextLines.

```python
from full_process import process_doc_text_first, process_doc_pics_first

# Text first, then images
molecule_segments, mol_pic_clusters = process_doc_text_first(pdf_path)

# Images first, then text
molecule_segments, mol_pic_clusters = process_doc_pics_first(pdf_path)
```

### Molecule Segment Final Adjustment

Segments are adjusted according to the most common test sequence to combine wrongly separated segments.

```python
from molecule_segment.segements_merging import adjust_molecule_segments_by_common_sequence

final_molecule_segments = adjust_molecule_segments_by_common_sequence(processed_molecule_segments)
```

### MoleculeSegment Attributes

- `segment_lines` - List of (multi_idx, text, bbox)
- `begin_multi_idx`, `end_multi_idx` - Start/end locations
- `nmr_text_line_list`, `ir_text_line_list`, `rf_text_line_list`, `ms_text_line_list` - Test text lines
- `mol_pics` - List of MolPicCluster
- `molecule_name` - Presumed name
- `has_test_text_sequence` - Boolean
- `test_text_sequence` - TestTextSequence object

---

## Troubleshooting

### "No PDF files found"
- Check that your input folder contains `.pdf` files
- Verify the path is correct

### "ModuleNotFoundError"
- Make sure you installed the package: `python -m pip install .`
- Activate your conda environment if using one

### Image extraction fails
- Image extraction is optional and requires DECIMER or YOLOv5
- The tool will automatically fall back to text-only mode if images fail

### Label Studio errors
- See [Label Studio Setup](#label-studio-setup) section above
- Ensure environment variables are set correctly

---

## Benchmark Data
See `demo_data/README.md`.

## Support
Open an issue on GitHub for questions or problems.
