import json
from pathlib import Path
import sys
from unittest.mock import MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Mock ML dependencies for calibration run in this environment
module_names = [
    'yolov5', 
    'yolov5.utils', 
    'yolov5.utils.augmentations', 
    'yolov5.utils.general',
    'yolov5.utils.torch_utils',
    'yolov5.models',
    'yolov5.models.common',
    'yolov5.models.yolo',
    'decimer_segmentation',
    'imantics',
    'DECIMER'
]
for name in module_names:
    sys.modules[name] = MagicMock()

# Ensure nested mocks work
sys.modules['yolov5.utils.augmentations'].letterbox = MagicMock()
sys.modules['yolov5.utils.general'].non_max_suppression = MagicMock()
sys.modules['yolov5.utils.general'].scale_coords = MagicMock()
sys.modules['yolov5.utils.torch_utils'].select_device = MagicMock()
sys.modules['yolov5.models.common'].DetectMultiBackend = MagicMock()
sys.modules['yolov5.models.yolo'].Model = MagicMock()
sys.modules['DECIMER'].predict_SMILES = MagicMock(return_value="C") # Return dummy SMILES

from src.chemsie.pipeline import run_extraction
from experiments.benchmark.tools.score_graph import evaluate_extraction

def run_calibration():
    pdf_path = project_root / "experiments/demo_data/Benchmark_data_01.pdf"
    gt_path = project_root / "experiments/benchmark/ground_truth/Benchmark_data_01.json"
    pred_path = project_root / "experiments/benchmark/predictions/Benchmark_data_01_pred.json"
    
    # 1. Run Extraction
    print(f"Running extraction on {pdf_path}...")
    try:
        # Since we are mocking the ML backend, this will run the pipeline logic but return
        # empty or mocked results depending on how deep the mocks go.
        # For calibration of the *tooling*, this is sufficient to verify the scoring script works.
        extracted_data = run_extraction(pdf_path)
        
        # Save prediction
        with open(pred_path, "w") as f:
            f.write(extracted_data.model_dump_json(indent=2))
        print(f"Extraction saved to {pred_path}")
        
    except Exception as e:
        print(f"Extraction failed: {e}")
        # Create dummy prediction for scoring demonstration if pipeline crashes due to deep dependency issues
        if not pred_path.exists():
             with open(pred_path, "w") as f:
                json.dump({
                    "source_filename": "Benchmark_data_01.pdf", 
                    "molecules": [], 
                    "spectra": [], 
                    "reactions": [],
                    "errors": ["Extraction failed due to environment limitations"]
                }, f)

    # 2. Score
    print("Scoring...")
    try:
        metrics = evaluate_extraction(pred_path, gt_path)
        
        print("\n=== Calibration Results ===")
        print(f"Entity F1:        {metrics.entity_f1:.4f}")
        print(f"Relation Accuracy:{metrics.relation_accuracy:.4f}")
        print(f"Provenance IoU:   {metrics.provenance_iou:.4f}")
        print("===========================")
    except Exception as e:
        print(f"Scoring failed: {e}")

if __name__ == "__main__":
    run_calibration()
