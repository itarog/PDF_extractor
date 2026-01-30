# Scientific Readiness Check

## 1. Goal
To evaluate if ChemSIE v0.1 supports the scientific claims intended for its release/publication.

## 2. Claim Assessment

| Claim | Current Status | Evidence / Gap | Severity |
| :--- | :--- | :--- | :--- |
| **"Traceable Extraction"** | 🟢 Good | **Evidence:** Schema now supports `Span` and `ExtractionMethod`. Pipeline injects provenance placeholders. | Low |
| **"Context-Preserving"** | 🟢 Good | **Evidence:** Experimental Graph Benchmark (`score_graph.py`) explicitly measures relations. | Low |
| **"Machine-Actionable"** | 🔴 Weak | **Evidence:** We extract quantities.<br>**Gap:** Units are not normalized. See `CLAIMS_DEFENSIBLE.md`. | High (Limit claims to "Discovery") |
| **"Verifiable Accuracy"** | 🟡 Partial | **Evidence:** Benchmarking tooling exists.<br>**Gap:** Actual F1 scores are pending model integration. | Medium |

## 3. Critical Blockers for Release

1.  **Model Integration:** The ML models (YOLO, DECIMER) must be active and calibrated to produce non-zero F1 scores.
2.  **Normalization:** extracted values ("2.5 g") must be normalized to standard units.

## 4. Conclusion

ChemSIE has graduated from "Prototype" to **"Instrumented System"**.
It is now ready for **Model Training & tuning** (Phase 7), as the measurement apparatus (Benchmark) is in place.
