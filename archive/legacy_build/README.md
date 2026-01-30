# Legacy Build Archive

This directory contains the original codebase structure of ChemSIE prior to the 2026 refactoring.

**⚠️ WARNING: DO NOT USE CODE FROM THIS DIRECTORY IN PRODUCTION.**

The contents of this directory are preserved for historical reference and to support legacy scripts that have not yet been fully migrated. The active, maintained codebase is located in `src/chemsie`.

## Migration Status

Most core logic has been migrated to `src/chemsie`.
Applications have been moved to `apps/`.
Scripts have been moved to `scripts/`.

If you find yourself importing from here, please refactor your code to use the new package structure.
