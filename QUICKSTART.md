# Quick Start Guide

Get started with the PDF Chemical Analysis Extractor in 5 minutes!

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/PDF_extractor.git
cd PDF_extractor

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### 1. Process Demo Data

The package includes demo data in the `demo_data` folder. Let's process it:

```bash
python main.py --input demo_data/Exdata_1 --output results
```

This will:
- Process all PDF files in `demo_data/Exdata_1`
- Extract chemical analysis text (NMR, IR, MS, Rf)
- Detect molecule segments
- Save results to `results/` folder as pickle files

### 2. View Results

Run the example script to see what was extracted:

```bash
python example_usage.py
```

This demonstrates:
- Processing a single PDF
- Batch processing multiple PDFs
- Loading and analyzing saved results

### 3. Process Your Own PDFs

```bash
python main.py --input /path/to/your/pdfs --output my_results
```

## What Gets Extracted?

For each PDF, the extractor identifies:

1. **Molecule Segments** - Sections describing individual molecules
2. **Molecule Names** - Detected from text patterns
3. **Chemical Tests**:
   - NMR spectra (1H, 13C, etc.)
   - IR spectroscopy data
   - Mass spectrometry (MS, HRMS)
   - Retention factors (Rf)
4. **Bounding Boxes** - Location of each text element on the page

## Output Format

Results are saved as `.pkl` files containing:

```python
ProccessedPdf:
  ├── file_name: "example.pdf"
  ├── metadata: {...}
  ├── molecule_segments: [
  │     MoleculeSegment:
  │       ├── molecule_name: "Compound 1"
  │       ├── start_page: 3
  │       ├── end_page: 3
  │       ├── test_text_sequence:
  │       │     ├── test_type_list: ["1H NMR", "13C NMR", "HRMS"]
  │       │     └── test_text_lines: [...]
  │       └── ...
  │   ]
  └── mol_pic_clusters: [...]  # If --pics flag used
```

## Loading Results

```python
from storeage_obj import load_pickle_by_filename

# Load results
result = load_pickle_by_filename('results/example.pkl')

# Access data
for segment in result.molecule_segments:
    print(f"Molecule: {segment.molecule_name}")
    if segment.has_test_text_sequence:
        for test in segment.test_text_sequence.test_text_lines:
            print(f"  {test.test_type}: {test.text}")
```

## Advanced: Image Extraction

To also extract molecule images (requires DECIMER):

```bash
# Install DECIMER
pip install decimer-segmentation

# Process with image extraction
python main.py --input demo_data/Exdata_1 --output results --pics
```

## Command Reference

```bash
# Basic text extraction
python main.py --input INPUT_FOLDER --output OUTPUT_FOLDER

# With image extraction
python main.py --input INPUT_FOLDER --output OUTPUT_FOLDER --pics

# Quiet mode (less output)
python main.py --input INPUT_FOLDER --output OUTPUT_FOLDER --quiet

# Help
python main.py --help
```

## Troubleshooting

### "No PDF files found"
- Check that your input folder contains `.pdf` files
- Verify the path is correct

### "ModuleNotFoundError"
- Make sure you installed requirements: `pip install -r requirements.txt`

### Image extraction fails
- Image extraction is optional and requires DECIMER
- The tool will automatically fall back to text-only mode

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [example_usage.py](example_usage.py) for programmatic usage
- Explore Label Studio integration for data annotation

## Support

For issues or questions, please open an issue on GitHub.



