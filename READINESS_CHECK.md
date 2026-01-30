# Scientific Readiness Check

## 1. Goal
To evaluate if ChemSIE v0.1 supports the scientific claims intended for its release/publication.

## 2. Claim Assessment

| Claim | Current Status | Evidence / Gap | Severity |
| :--- | :--- | :--- | :--- |
| **"Traceable Extraction"** | 🟡 Partial | **Evidence:** We have page/bbox for most entities.<br>**Gap:** We lack *method* metadata (OCR vs. Model) and text spans. | Medium |
| **"Context-Preserving"** | 🟢 Good | **Evidence:** Schema supports `Reaction` objects linking reactants/products.<br>**Gap:** Pipeline logic for reliable reaction parsing is still experimental. | Low (Architecture supports it) |
| **"Machine-Actionable"** | 🔴 Weak | **Evidence:** We extract quantities.<br>**Gap:** Units are not normalized (mg vs g). Reagent purity/grade is missing. A robot would crash. | High (Limit claims to "Discovery" not "Automation") |
| **"Verifiable Accuracy"** | 🟡 Partial | **Evidence:** `confidence` scores exist.<br>**Gap:** They are not calibrated. A 0.9 confidence might still be wrong. | Medium |

## 3. Critical Blockers for Release

1.  **Calibration:** We need to know if `confidence=0.9` implies 90% accuracy.
2.  **Normalization:** extracted values ("2.5 g") must be normalized to standard units for searchability.
3.  **Error Handling:** The system must degrade gracefully (report "Partial Extraction" rather than crashing or guessing).

## 4. Conclusion

ChemSIE is ready for **"Assisted Curation"** (Human-in-the-loop).
It is **NOT** ready for **"Fully Autonomous Database Population"**.

The paper/release should frame it as a *productivity tool for chemists*, not a replacement for them.
