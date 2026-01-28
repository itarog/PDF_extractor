"""
This Streamlit application serves as a visual tool to analyze and verify the
output of the ChemSIE pipeline, focusing on visual provenance.

It allows a user to upload a PDF and its corresponding extraction data (in the
canonical JSON format) to see exactly where in the document each piece of
information was extracted from.

This app is a concrete demonstration of the "trust but verify" principle,
which is critical for the adoption of automated extraction tools in a
scientific context.
"""
import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io

# As part of the refactor, we assume a project structure where the 'src'
# directory is in the PYTHONPATH.
from chemsie.schemas import ExtractedData, Provenance, Molecule

# ==============================================================================
# Core Functions
# ==============================================================================

@st.cache_data
def load_extraction_data(json_bytes: bytes) -> ExtractedData | None:
    """Loads and validates the extraction data from the uploaded JSON file."""
    if not json_bytes:
        return None
    try:
        data = ExtractedData.parse_raw(json_bytes)
        return data
    except Exception as e:
        st.error(f"Error parsing JSON file: {e}")
        return None

@st.cache_data
def highlight_provenance_on_page(pdf_bytes: bytes, page_num: int, bboxes: list, color: tuple, width: int = 2) -> Image.Image | None:
    """
    Renders a specific PDF page and highlights the given bounding boxes.

    Args:
        pdf_bytes: The content of the PDF file.
        page_num: The 0-indexed page number to render.
        bboxes: A list of BoundingBox objects to draw.
        color: The (r, g, b) color for the stroke.
        width: The stroke width of the rectangle.

    Returns:
        A PIL Image of the rendered page with highlights, or None on error.
    """
    try:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if page_num >= len(pdf_doc):
            st.warning(f"Page number {page_num} is out of bounds for this PDF.")
            return None
        
        page = pdf_doc.load_page(page_num)
        
        # Draw all bounding boxes
        for bbox_item in bboxes:
            # PyMuPDF uses fitz.Rect for drawing
            rect = fitz.Rect(bbox_item.x0, bbox_item.y0, bbox_item.x1, bbox_item.y1)
            page.draw_rect(rect, color=color, width=width)
            
        # Render page to an image
        pix = page.get_pixmap(dpi=200)  # Higher DPI for better quality
        img_bytes = pix.tobytes("png")
        return Image.open(io.BytesIO(img_bytes))

    except Exception as e:
        st.error(f"Failed to render PDF page with highlights: {e}")
        return None
    finally:
        if 'pdf_doc' in locals() and pdf_doc:
            pdf_doc.close()


# ==============================================================================
# Page Configuration and Title
# ==============================================================================

st.set_page_config(
    page_title="ChemSIE Visual Provenance Explorer",
    layout="wide",
)

st.title("🔬 ChemSIE Visual Provenance Explorer")
st.markdown("Upload a PDF and its corresponding ChemSIE JSON output to visually verify extraction results.")

# ==============================================================================
# Sidebar for File Uploads
# ==============================================================================

st.sidebar.header("Data Input")

pdf_file = st.sidebar.file_uploader(
    "1. Upload Source PDF",
    type="pdf"
)

json_file = st.sidebar.file_uploader(
    "2. Upload ChemSIE Extraction JSON",
    type="json"
)

# --- Main app logic ---
if not pdf_file or not json_file:
    st.info("Please upload both a PDF and a JSON file to begin.")
    st.stop()

# Load data - bytes are used to leverage Streamlit's file handling
pdf_bytes = pdf_file.getvalue()
json_bytes = json_file.getvalue()
extraction_data = load_extraction_data(json_bytes)

if not extraction_data:
    st.error("Could not load or parse the JSON file. Please check the file and try again.")
    st.stop()

# ==============================================================================
# Main View - Entity Selection and Display
# ==============================================================================

st.header(f"Document: `{extraction_data.source_filename}`")

# Create a mapping from molecule ID to molecule object for easy lookup
molecule_map = {mol.id: mol for mol in extraction_data.molecules}

# Let the user select an entity to inspect
entity_options = [f"Molecule: {mol.label or mol.id}" for mol in extraction_data.molecules]
# This could be expanded to include Reactions, Spectra, etc.

if not entity_options:
    st.warning("No molecules found in the extraction data.")
    st.stop()

selected_entity_str = st.selectbox(
    "Select an extracted molecule to inspect:",
    options=entity_options
)

# Find the selected molecule object
selected_mol_id = selected_entity_str.split(": ")[1]
selected_molecule = next((mol for mol in extraction_data.molecules if (mol.label or mol.id) == selected_mol_id), None)

if not selected_molecule:
    st.error("Could not find the selected molecule. This should not happen.")
    st.stop()

st.markdown("---")

# ==============================================================================
# Provenance Visualization
# ==============================================================================

st.subheader(f"Provenance for Molecule: {selected_molecule.label or selected_molecule.id}")

# Display extracted data for the selected molecule
col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("**Extracted Data**")
    st.json({
        "label": selected_molecule.label,
        "smiles": selected_molecule.smiles,
        "inchi": selected_molecule.inchi,
        "id": selected_molecule.id
    })

# The provenance list might contain multiple entries (e.g., from image and text)
# We group them by page number to render them together.
from collections import defaultdict
provenance_by_page = defaultdict(list)
for prov in selected_molecule.provenance:
    provenance_by_page[prov.page_number].append(prov)

# Display each page with its corresponding highlights
with col2:
    if not provenance_by_page:
        st.warning("No provenance information available for this molecule.")
    else:
        for page_num, prov_items in sorted(provenance_by_page.items()):
            st.markdown(f"**Source: Page {page_num + 1}** (0-indexed: {page_num})")
            
            # Extract bounding boxes for the current page
            bboxes_on_page = [p.bbox for p in prov_items]
            
            # Render the highlighted page
            highlighted_image = highlight_provenance_on_page(
                pdf_bytes=pdf_bytes,
                page_num=page_num,
                bboxes=bboxes_on_page,
                color=(1, 0, 0)  # Red color for highlight
            )

            if highlighted_image:
                st.image(highlighted_image, use_column_width=True)
            else:
                st.error(f"Could not render page {page_num + 1}.")