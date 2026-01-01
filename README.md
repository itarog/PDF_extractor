# ChemSIE — PDF text & molecule-image extractor

![ChemSIE overview](build/Chemsie_fig1.png)

ChemSIE extracts **chemical analysis text** (e.g., NMR / IR / MS / TLC/Rf) and **molecule figures** from PDF documents, and helps you validate/correct results via a **friendly GUI (Streamlit)** or **Label Studio**.

This repository contains the code and data accompanying the publication:

> **I. Wallwater, Y. Harnik et al.** “PDF text and image extractor”  
> DOI: https://doi.org/XXXX

---

## Highlights

- **One command / one click**: process a single PDF or a whole folder.
- **Text + figures**: parse analytical text and detect molecule segments in the same run.
- **Two image backends**:
  - `yode` (recommended): fast YOLOv5-based detection
  - `decimer`: image-to-structure (slower)
- **Human-in-the-loop**: review results in Streamlit or annotate in Label Studio.
- **Export-ready**: CSV output + rendered molecule images.

---

## Table of contents

- [Quick start (non‑coders)](#quick-start-noncoders)
- [Installation](#installation)
- [Run ChemSIE](#run-chemsie)
  - [Option A: GUI (Streamlit)](#option-a-gui-streamlit)
  - [Option B: Command line (CLI)](#option-b-command-line-cli)
  - [Option C: Python API](#option-c-python-api)
- [Human validation](#human-validation)
  - [Label Studio setup](#label-studio-setup)
- [Benchmark data](#benchmark-data)
- [Outputs](#outputs)
- [Troubleshooting](#troubleshooting)
- [Citation](#citation)
- [Support](#support)

---

## Quick start (non‑coders)

If you don’t code, you can still use ChemSIE end‑to‑end via the graphical interface.

1. **Install once** (see [Installation](#installation)).
2. **Start the GUI**:
   ```bash
   conda activate pdf_extractor
   streamlit run build/Streamlit_apps/streamlit_extraction_GUI.py
   ```
3. In the app:
   - Choose a **single PDF** or a **folder of PDFs**
   - Pick an image backend (`yode` is the default recommendation)
   - Click **Run**
   - Review results and export

> Tip: On Windows, you may need to use backslashes in paths (e.g., `build\Streamlit_apps\...`). The forward‑slash version above usually works in PowerShell and Git Bash.

---

## Installation

### 1) Clone the repository
```bash
git clone https://github.com/itarog/PDF_extractor.git
cd PDF_extractor
```

### 2) Create a Conda environment (recommended)
```bash
conda create -n pdf_extractor python=3.10
conda activate pdf_extractor
```

### 3) Install the package
```bash
python -m pip install .
```

### Model / binary downloads (first run)
On first installation or first use, the project may download required assets such as:
- YOLOv5 model files
- Poppler binaries (for PDF processing on Windows, if needed)
- Python dependencies specified by the package

If the YOLOv5 weights file `best.pt` is missing, you can download it from:
- https://drive.google.com/file/d/1tXX_-RE2sL2U7lRvFfOBUBTIIIN_MhnN/view?usp=sharing

Place `best.pt` inside the YOLOv5 model files directory used by the project.

---

## Run ChemSIE

ChemSIE supports three ways to run: **GUI**, **CLI**, and **Python API**.

### Option A: GUI (Streamlit)

```bash
conda activate pdf_extractor
streamlit run build/Streamlit_apps/streamlit_extraction_GUI.py
```

### Option B: Command line (CLI)

Process **text + molecule images**, then open the visualizer:
```bash
python main.py --input demo_data --output results --pics --backend yode --visualize
```

Process **text + molecule images** (no visualizer):
```bash
python main.py --input demo_data --output results --pics --backend yode
```

Process **text + molecule images** with DECIMER (slower):
```bash
python main.py --input demo_data --output results --pics --backend decimer
```

Process **text only**:
```bash
python main.py --input demo_data --output results
```

Open the visualizer for an **already extracted** database:
```bash
python main.py --output results --visualize-only
```

### Option C: Python API

```python
from build.streamlit_wrappers import process_pdf_dir_end_to_end

pdf_dir = "./demo_data"
database_name = "my_database"

cmd_process = process_pdf_dir_end_to_end(
    pdf_dir,
    verbose=True,
    backend="yode",  # or "decimer"
    database_name=database_name,
    graph_sketch=False,
)
```

---

## Human validation

ChemSIE is designed for practical workflows: you can **run automatic extraction**, then **quickly review and fix**.

### Streamlit review
The Streamlit GUI supports reviewing extracted text and detected images and exporting results.

### Label Studio (annotation workflow)

Fix annotations and image bounding boxes using Label Studio:

1. Start a Label Studio server
2. Send `.pkl` outputs to Label Studio
3. Annotate in the web interface
4. Pull annotations back into the local `.pkl` files

Send PKLs to Label Studio:
```bash
python send_to_label_studio.py --pkl-folder results --pdf-dir demo_data/Exdata_1 --api-key <api_key>
```

Update PKLs from Label Studio annotations:
```bash
python update_from_label_studio.py --pkl-folder results --pdf-dir demo_data/Exdata_1 --api-key <api_key>
```

---

## Benchmark data

Benchmark details live here: **build/demo_data/README.md**  
(See that file for dataset structure, expected outputs, and evaluation notes.)

---

## Outputs

ChemSIE produces outputs intended to be easy to inspect and easy to reuse.

- **One `.pkl` per PDF** containing:
  - molecule segments
  - bounding boxes
  - optional extracted molecule images
  - extracted analytical text snippets
- **Stage 3 export** (`--visualize` / `--visualize-only`) writes:
  - a **CSV** with extracted records
  - **rendered molecule images**
  - all inside your `--output` directory

Example access:
```python
from build.storeage_obj import load_pickle_by_filename

result = load_pickle_by_filename("results/example.pkl")
for segment in result.molecule_segments:
    print(segment.molecule_name)
```

---

## Troubleshooting

### “No PDF files found”
- Ensure the input folder contains `.pdf` files
- Double-check the path passed to `--input`

### `ModuleNotFoundError`
- Confirm you installed the package:
  ```bash
  python -m pip install .
  ```
- Make sure your environment is activated:
  ```bash
  conda activate pdf_extractor
  ```

### Image extraction fails
- Image extraction is optional and requires either `yode` or `decimer`
- If image extraction fails, try running **text-only** mode first:
  ```bash
  python main.py --input <pdf_dir> --output results
  ```

### Label Studio cannot open local PDFs/images
See the [Label Studio setup](#label-studio-setup) section below and ensure the relevant environment variables are set.

---

## Label Studio setup

Label Studio must be allowed to serve your **local PDFs** and **extracted images**.

Choose a root folder that contains your PDFs (examples: `Z:\` on Windows, `/home/<you>` on Linux, `/Users/<you>` on macOS).

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

Or use the helper script (sets env vars and starts Label Studio):
```bash
python start_label_studio.py
```

After starting Label Studio:
1. Open http://localhost:8080 and annotate  
2. Run `update_from_label_studio.py` to pull changes back into the PKLs

---

## Workflow at a glance

- Extract PDFs → PKLs  
  ```bash
  python main.py --input demo_data/Exdata_1 --output results --pics --backend yode
  ```
- (Optional) Send to Label Studio → annotate → update PKLs  
- Visualize or export  
  ```bash
  python main.py --output results --visualize-only
  ```

---

## Citation

If you use ChemSIE in academic work, please cite the associated paper:

```bibtex
@article{wallwater_chemsie_XXXX,
  title   = {PDF text and image extractor},
  author  = {Wallwater, I. and Harnik, Y. and others},
  journal = {XXXX},
  year    = {XXXX},
  doi     = {XXXX},
}
```

---

## Support

- Please open a **GitHub Issue** for bugs, questions, or feature requests.
- For reproducibility questions, include:
  - your OS (Windows/macOS/Linux)
  - Python version (`python --version`)
  - the exact command you ran
  - a minimal PDF example if possible

