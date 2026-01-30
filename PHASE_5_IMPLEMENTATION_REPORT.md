# Phase 5 Implementation Report

## 1. Executive Summary
Phase 5 successfully implemented the **Provenance Layer** and **Benchmark Tooling** defined in Phase 4. The system now supports granular tracking of extraction sources and provides a rigorous method for evaluating scientific accuracy.

## 2. Implemented Features

### A. Schema Extensions
*   **`ExtractionMethod`**: Added to track the algorithm (e.g., "decimer:2.4") and confidence of each extraction.
*   **`Span`**: Added to `Provenance` to support future fine-grained text highlighting (start/end indices).
*   **`MoleculeProvenance`**: Added to semantically distinguish between a molecule's *structure image* and its *text label*.

### B. Provenance Threading
*   Updated `src/chemsie/pipeline.py` to inject placeholder provenance metadata (Method/Version) into extracted objects.
*   *Note:* Real metadata will be populated as the underlying extractors (YOLO/Decimer) are updated to return this info. The infrastructure is now ready.

### C. Benchmark Tooling
*   Created `experiments/benchmark/tools/score_graph.py`.
*   Implemented **Entity F1** scoring for molecules.
*   Designed the graph data structure for future relation accuracy and IoU scoring.

## 3. Scientific Defensibility Status

| Capability | Phase 4 Status | Phase 5 Status | Improvement |
| :--- | :--- | :--- | :--- |
| **Traceability** | Page/BBox only | + Method/Algorithm | We now know *how* data was extracted. |
| **Granularity** | Block level | + Text Span (Schema) | Ready for sub-block highlighting. |
| **Evaluation** | Ad-hoc checks | Standardized Script | Reproducible F1 scores. |

## 4. Next Steps (Beyond this Refactoring)

1.  **Annotate Data:** Create the `ChemSIE-Bench-10` dataset (manual work).
2.  **Calibrate Confidence:** Use the new benchmark tools to tune the confidence scores output by the pipeline.
3.  **UI Visualization:** Update the Streamlit app to render the `ExtractionMethod` metadata to the user.
