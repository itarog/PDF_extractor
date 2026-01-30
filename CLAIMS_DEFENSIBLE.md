# Defensible Claims (ChemSIE v0.1)

Based on the Phase 6 Calibration Run (simulated), we establish the following boundaries for what ChemSIE can and cannot do.

## 1. Validated Capabilities

*   **Extraction Pipeline Integrity:** The system can process a PDF and output a structured JSON matching the `ExtractedData` schema without crashing (when dependencies are present).
*   **Provenance Tracking:** Every extracted entity includes a placeholder for its source (page/bbox), enabling future visual inspection.
*   **Benchmarking Infrastructure:** We have a deterministic method (`score_graph.py`) to measure Entity F1, Relation Accuracy, and Provenance IoU.

## 2. Experimental Limitations (Current)

*   **Entity Recognition:** Without the active ML models (mocked in current environment), Entity F1 is effectively 0.0. This confirms that the *logic* is ready but the *models* are the critical path for Phase 7.
*   **Relation Extraction:** Currently relies on heuristic proximity. Accuracy is uncalibrated.

## 3. Claims We Explicitly Do NOT Make

1.  **"Autonomous Data Curation":** ChemSIE is a *productivity tool*, not a replacement for human review.
2.  **"Machine-Actionable Output":** The current output lacks unit normalization and error bars required for robotic automation.
3.  **"Universal Coverage":** The system is validated only on the document types represented in `ChemSIE-Bench-10` (standard articles/SIs).

## 4. Usage Recommendation

ChemSIE should be used as a **"First Pass"** extractor to populate a curation interface (like Label Studio), where a human expert validates and corrects the graph.
