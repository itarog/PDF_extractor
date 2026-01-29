# Strategic Plan for ChemSIE Refactoring

## 1. Assessment of Current State

### Main Branch (`main`)
- **Structure:** Flat, legacy structure with most code in `build/` and root. Mixed source, scripts, and data.
- **Issues:** Hard to maintain, poor separation of concerns, mixing of model weights/data with code.
- **Status:** Functional but technically indebted.

### Updates Branch (`origin/Updates-II`)
- **Structure:** Transitioning to `src` layout.
  - `src/chemsie`: Core package.
  - `src/models`: ML model wrappers.
  - `src/parsing`: Parsing logic.
  - `apps/streamlit`: UI logic.
  - `experiments`: Benchmarks and demo data.
- **Status:** Work-in-Progress.
  - **Schema Mismatch:** `src/chemsie/pipeline.py` references a `Spectrum` class that does not exist in `src/chemsie/schemas.py`.
  - **Bridge Code:** `pipeline.py` relies on a "Temporary Bridge" to legacy code in `build/` (or copied to `src/chemsie/internal`).
  - **Legacy Artifacts:** `build/` still exists and contains code that duplicates or overlaps with `src/`.

## 2. Strategic Roadmap

The goal is to complete the migration started in `Updates-II`, fix the broken implementations, and finalize the `src/chemsie` package.

### Phase 1: Stabilization & Schema Fixes (Immediate)
- **Objective:** Make `src/chemsie` functional and consistent.
- **Actions:**
  1.  **Fix Schemas:** Resolve the discrepancy between `pipeline.py` and `schemas.py`. Define a generic `Spectrum` model or properly utilize `NMRData`. Ensure `Molecule` and `Spectrum` are correctly linked (likely via `ExtractedData`).
  2.  **Refine Pipeline:** Update `pipeline.py` to return the comprehensive `ExtractedData` object (or a list of molecules if that's the intended unit, but `ExtractedData` is better for document-level extraction).
  3.  **Tests:** Add a basic test to verify `run_extraction` can run (even if mocking the deep logic) and produce valid Pydantic models.

### Phase 2: Core Logic Migration (Short Term)
- **Objective:** Remove dependency on `build/` and `src/chemsie/internal` "wrappers".
- **Actions:**
  1.  **Move Parsing:** Complete the relocation of parsing logic (from `nmr_parser` etc.) to `src/parsing`.
  2.  **Move Models:** Ensure `src/models` contains all necessary model code (YOLO, Decimer, etc.) and is decoupled from the main pipeline logic.
  3.  **Eliminate "Internal":** Refactor `src/chemsie/internal/wrappers.py` into proper modules within `chemsie` or `parsing`, removing the "temporary bridge".

### Phase 3: Application & Clean Up (Medium Term)
- **Objective:** Finalize the repo structure.
- **Actions:**
  1.  **Streamlit:** Ensure the refactored app in `apps/streamlit` works with the new `src/chemsie` package.
  2.  **Clean Root:** Remove `build/` directory entirely. Remove top-level scripts that have been moved.
  3.  **Packaging:** Ensure `setup.py` or `pyproject.toml` correctly installs `chemsie` as a library.

## 3. Immediate Action Items (Next Steps for Cloud Agent)

1.  **Checkout `Updates-II`**: This branch contains the critical work-in-progress. I will merge it into the current feature branch `cursor/repository-strategic-plan-8a61` to continue the work.
2.  **Fix `schemas.py`**: Add the missing `Spectrum` class or adjust `pipeline.py`.
3.  **Fix `pipeline.py`**: Ensure it constructs valid objects matching `schemas.py`.
4.  **Verify Setup**: Ensure the package is installable.

## 4. Addressing Open Issues

- **#4 Define Pydantic Data Models**: Will be addressed by fixing `schemas.py`.
- **#5 Establish Canonical Execution Spine**: Will be addressed by refining `pipeline.py`.
- **#3 Create src/chemsie Package Skeleton**: Mostly done, needs cleanup.
- **#7 Isolate ML Model Wrappers**: Verify `src/models`.
- **#6 Relocate Parsing Logic**: Verify `src/parsing`.
- **#8 Refactor Streamlit App**: Check `apps/streamlit`.
- **#9 Quarantine Experimental Code**: Check `experiments`.

---
*Created by Cloud Agent on 2026-01-29*
