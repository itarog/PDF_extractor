# **ChemSIE - PDF text and image extractor**

This repository contains the code and data accompanying the upcoming publication:

> **Itamar Wallwater et al., "PDF text and image extractor"**  
> https://doi.org/XXXX

The package extracts chemical analysis text and molecule images from PDF files, with support for Label Studio annotation and Streamlit visualization.

# **Navigation menu**

[Installation](#installation)
[Setting up your database](#installationsetting-up-your-database)
[Evaluate on benchmark](#benchmark-data)
---

# Installation

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
- If 'best.pt' is not downloaded - you can download it directly from: YONATAN ADD ME

# Setting your database in three steps
This will:
- Extract chemical analysis text (NMR, IR, MS, Rf)
- Detect molecule segments

## Step 1: Set your desired PDF (single or batch)
For this step, the user has three options to initiate the process:
### Option 1: Using the graphical interface 

### Option 2: Using the command line
Process images and text, then visualize:
```bash
python main.py --input demo_data --output results --pics --backend yode --visualize
```
Process images and text:
```bash
python main.py --input demo_data --output results --pics --backend yode

# With image extraction using decimer backend (much slower)
python main.py --input demo_data --output results --pics --backend decimer
```
Process text:
```bash
python main.py --input demo_data --output results
```
### Option 3: Using the python API
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
## Step 2: User validation 
For this step, the user has two options to initiate the process:

### Option 1: Using the graphical interface

### Option 2: Using Label Studio Annotation
Fix annotations and image bounding boxes using Label Studio:

1. Start Label Studio server
2. Send pkl data to Label Studio
3. Annotate in the web interface
4. Update pkl files from annotations

See [Label Studio Setup](#label-studio-setup) section below.

1. **Start Label Studio:**
Send PKLs to Label Studio:
```bash
python send_to_label_studio.py --pkl-folder results --pdf-dir demo_data/Exdata_1 --api-key <api_key>
```

Update PKLs from Label Studio annotations:
```bash
python update_from_label_studio.py --pkl-folder results --pdf-dir demo_data/Exdata_1 --api-key <api_key>
```

### Step 3: Export and Visualize
Export CSV and images, then visualize with our graohical interface:


To View already extracted databases:

```bash
python main.py --output results --visualize-only
```

---


## Benchmark Data
See `demo_data/README.md`.

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
- See [Label Studio Setup](#label-studio-setup) section below
- Ensure environment variables are set correctly

---

## Support
Open an issue on GitHub for questions or problems.



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

