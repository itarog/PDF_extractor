# ChemSIE Repository Structure

## Directory Layout

*   **`src/chemsie/`**: The core, self-contained Python package for chemical extraction.
    *   `pipeline.py`: Main entry point (`run_extraction`).
    *   `schemas.py`: Pydantic data models.
    *   `internal/`: Internal logic migrated from the old `build/`.
    *   `utils/`: Shared utilities.
    *   `models/`: ML model wrappers.
*   **`apps/`**: Application-level code.
    *   `streamlit/`: The refactored Streamlit GUI.
*   **`scripts/`**: Standalone utility scripts.
    *   `label_studio/`: Scripts for Label Studio integration.
    *   `utils/`: General utilities (e.g., model downloading, image export).
*   **`archive/legacy_build/`**: The frozen, read-only archive of the original codebase.
    *   Contains the original `build/` contents for reference.
*   **`tests/`**: Test suite.
    *   `test_pipeline.py`: Verifies the core pipeline logic using mocks.

## Validation Status

*   ✅ **Pipeline Verification**: `tests/test_pipeline.py` passes, confirming that `run_extraction()` works correctly using the new `src/chemsie` structure.
*   ✅ **Clean Architecture**: No production code in `src/chemsie/` imports from `archive/` or the now-deleted `build/`.
*   ✅ **Self-Contained**: The core library is isolated from application code and scripts.

## Go/No-Go Decision

**GO.** The repository has been successfully refactored. `src/chemsie` is a clean, installable library, and the legacy code is safely archived.
