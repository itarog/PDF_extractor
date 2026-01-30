# Classification of Remaining build/ Contents

| Path | Category | Action | New Location |
| :--- | :--- | :--- | :--- |
| `build/Streamlit_apps/` | Application | Delete (Already moved to `apps/streamlit`) | N/A |
| `build/streamlit_wrappers.py` | Application | Migrate | `apps/streamlit/utils/wrappers.py` |
| `build/start_label_studio.py` | Integration | Migrate | `scripts/label_studio/start_server.py` |
| `build/send_to_label_studio.py` | Integration | Migrate | `scripts/label_studio/send_data.py` |
| `build/update_from_label_studio.py` | Integration | Migrate | `scripts/label_studio/update_data.py` |
| `build/export_images.py` | Utility | Migrate | `scripts/utils/export_images.py` |
| `build/download_decimer_weights.py` | Utility | Migrate | `scripts/utils/download_decimer.py` |
| `build/main.py` | Script | Archive | `archive/legacy_build/main.py` |
| `build/Manager/main.py` | Script | Archive | `archive/legacy_build/Manager/main.py` |
| `build/demo_data/` | Data | Archive | `archive/legacy_build/demo_data/` |
| `build/nmr_parser/` | Logic | Archive (Should be in `src/parsing` eventually) | `archive/legacy_build/nmr_parser/` |
| `build/best.pt` | Model | Delete (Use `yolov5/best.pt` or `src/models`) | N/A |
| `build/*.py` (Core Logic) | Core | Delete (Already migrated to `src/chemsie`) | N/A |
| `build/text_cleaning/` | Core | Delete (Already migrated) | N/A |
| `build/tokenizer/` | Core | Delete (Already migrated) | N/A |
| `build/text_processing/` | Core | Delete (Already migrated) | N/A |
| `build/Manager/molecules_tests.py` | Core | Delete (Already migrated) | N/A |
| `build/Chemsie_fig1.png` | Asset | Archive | `archive/legacy_build/Chemsie_fig1.png` |
| `build/Text_and_image_grab_2603.ipynb` | Notebook | Archive | `archive/legacy_build/notebooks/` |

**Strategy:**
1.  Create `scripts/` and `archive/` directories.
2.  Move useful scripts to `scripts/` and update imports to use `src/chemsie`.
3.  Move Streamlit wrappers to `apps/streamlit`.
4.  Move everything else in `build/` to `archive/legacy_build/`.
5.  Delete redundant migrated code from `archive/legacy_build/` to save space/confusion (optional, but cleaner to just archive what's left). *Correction: I will move the remaining un-migrated items to archive, and delete the ones that are confirmed duplicates in src.*
