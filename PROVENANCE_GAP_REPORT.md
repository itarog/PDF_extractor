# Provenance Gap Report

## 1. Executive Summary

The current ChemSIE data model (`src/chemsie/schemas.py`) provides a solid foundation for provenance tracking through the `Provenance` and `BoundingBox` models. Every major entity (`Molecule`, `NMRPeak`, `Reaction`, `MeasuredValue`) requires provenance.

However, significant gaps exist in **granularity**, **decision traceability**, and **confidence scoring**. While we know *where* something came from (page/bbox), we often don't know *why* it was extracted or *how* specific values were derived (e.g., which OCR engine, which heuristic).

## 2. Current Capabilities

*   **Location Tracking:** We can track the page number and bounding box for molecules, spectra peaks, and measured values.
*   **Source Modality:** We distinguish between text, image, and table sources.
*   **Basic Confidence:** A single float `confidence` score is available but undefined in scope (is it OCR confidence? Model confidence?).

## 3. Identified Gaps

### A. Granularity of Text Provenance
*   **Issue:** `Provenance` points to a bounding box. For text, this is often a paragraph or a line.
*   **Gap:** We cannot pinpoint the exact *character span* (start/end indices) within the raw text that generated a value. This makes highlighting specific numbers in a UI imprecise.
*   **Impact:** Users cannot verify if "78%" yield came from "78%" or "7.8%".

### B. Decision Traceability (The "Why")
*   **Issue:** We have no record of *which* algorithm or model produced a result.
*   **Gap:** Was a molecule extracted by `DECIMER` or `YOLO`? Was a peak parsed by regex or an LLM?
*   **Impact:** Debugging is hard; scientific defensibility is weak because we can't cite the specific method for each datum.

### C. Compound Evidence
*   **Issue:** A `Molecule` often relies on multiple pieces of evidence: an image of the structure, a text label ("Compound 3a"), and a caption.
*   **Gap:** The current `provenance: List[Provenance]` is a flat list. It doesn't semantically distinguish between "this is the structure image" and "this is the text label".
*   **Impact:** We can't visualize the *link* between label and structure, which is the most common failure mode in OCSR.

### D. Confidence Ambiguity
*   **Issue:** `confidence` is a generic float.
*   **Gap:** We lack specific confidence metrics. For OCR, we need character probability. For structure recognition, we need validity scores.
*   **Impact:** Users cannot filter data based on specific quality criteria (e.g., "show me only molecules with >90% structure confidence").

## 4. Proposed Schema Extensions

To address these gaps without over-engineering, I propose the following minimal extensions to `src/chemsie/schemas.py`:

1.  **Add `Span` to `Provenance`:**
    ```python
    class Span(BaseModel):
        start: int
        end: int
        text: str  # The exact snippet extracted
    ```

2.  **Add `Method` metadata:**
    Add a `method` field to `Provenance` or a new `ExtractionMethod` model to track the source algorithm (e.g., "decimer:2.4", "regex:yield_pattern_a").

3.  **Semantic Roles for Provenance:**
    Instead of a generic list, `Molecule` could have specific provenance fields or tagged provenance:
    ```python
    class MoleculeProvenance(Provenance):
        role: Literal["structure_image", "label_text", "caption_text"]
    ```

## 5. Next Steps

1.  **Visual Provenance Design:** Design the data flow to support these new fields.
2.  **Benchmark Definition:** Ensure the benchmark evaluates these specific provenance links.
