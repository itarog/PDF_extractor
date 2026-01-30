# Phase 4 Design Report: Scientific Defensibility & Validation

## 1. Introduction
Phase 4 focused on shifting ChemSIE from a working prototype to a scientifically defensible system. We assessed the system's ability to provide traceable, verifiable, and context-aware chemical data.

## 2. Key Findings

### A. Provenance
*   **Status:** Foundational (BBox/Page exists).
*   **Gap:** Lack of fine-grained text spans and algorithm traceability.
*   **Solution:** Designed a new schema extension for `Span` and `ExtractionMethod` (see `PROVENANCE_GAP_REPORT.md`).

### B. Visual Inspection
*   **Design:** Conceptualized a "Triple-Pane Inspector" (Graph, Document, Evidence).
*   **Requirement:** The frontend must support precise SVG overlays on PDF renderings to build trust.
*   **Blueprint:** See `VISUAL_PROVENANCE_DESIGN.md`.

### C. Benchmarking
*   **Shift:** Moved away from "OCR Accuracy" to "Experimental Graph Quality".
*   **Metric:** Defined a 3-Tier metric system (Entity F1 -> Relation Accuracy -> Provenance IoU).
*   **Next Step:** Create `ChemSIE-Bench-10` gold standard dataset.
*   **Detail:** See `EXPERIMENTAL_GRAPH_BENCHMARK.md`.

### D. Readiness
*   **Verdict:** Ready for "Assisted Curation". Not ready for "Autonomous Automation".
*   **Constraint:** Claims must be carefully scoped to avoid overpromising "machine-actionability" regarding units and reaction conditions.

## 3. Implementation Roadmap (Phase 5 Candidates)

1.  **Schema Upgrade:** Implement the `Span` and `ExtractionMethod` models in `src/chemsie/schemas.py`.
2.  **Dataset Creation:** Manually annotate 10 PDFs to create the `ChemSIE-Bench-10` validation set.
3.  **Scoring Script:** Implement `scripts/benchmark/score.py` to calculate Tier 1/2/3 metrics.
4.  **UI Update:** Update the Streamlit app to render the "Visual Provenance" overlays.

## 4. Conclusion
ChemSIE has a robust architecture. The next phase should focus strictly on **validation tools** (benchmarks, scoring) and **provenance visualization** to ensure the outputs are trusted by scientists.
