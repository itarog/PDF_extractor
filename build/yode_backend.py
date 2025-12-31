# --- Add near the top, with your other imports ---
import numpy as np
import torch
from yolov5.utils.augmentations import letterbox
from yolov5.utils.general import non_max_suppression, scale_coords
from yolov5.utils.torch_utils import select_device
from yolov5.models.common import DetectMultiBackend
from yolov5.models.yolo import Model
# Singletons to avoid reloading the model on every call
_YODE_MODEL = None
_YODE_DEVICE = None
_YODE_STRIDE = 32  # will be overwritten after model load

torch.serialization.add_safe_globals([Model])

def _get_yolo_model(weights, device_str="", dnn=False, half=False, data=None):
    """
    Load (or return cached) YOLOv5 model for inference.
    """
    global _YODE_MODEL, _YODE_DEVICE, _YODE_STRIDE
    if _YODE_MODEL is not None:
        return _YODE_MODEL, _YODE_DEVICE, _YODE_STRIDE

    device = select_device(device_str)  # '' -> auto CUDA/CPU
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)

    _YODE_STRIDE = int(model.stride)
    _YODE_MODEL = model
    _YODE_DEVICE = device

    # Warmup once for the common (1,3,640,640) input
    model.warmup(imgsz=(1, 3, 640, 640))
    return _YODE_MODEL, _YODE_DEVICE, _YODE_STRIDE


@torch.no_grad()
def segment_chemical_structures_yode(
    image_np: np.ndarray,
    *,
    weights: str = "yolov5/best.pt",
    data: str = None,
    imgsz: int = 640,
    conf_thres: float = 0.25,
    iou_thres: float = 0.45,
    max_det: int = 1000,
    agnostic_nms: bool = False,
    classes=None,            # e.g., [0] if you want only class 0
    device: str = "",        # e.g., "0" for CUDA:0, "" for auto
    use_half: bool = False,  # fp16 on supported GPUs
) -> tuple[list[np.ndarray], list[tuple[int, int, int, int]]]:
    """
    Run YOLOv5 on a single numpy image and return (segments, bboxes).
    - image_np: BGR np.ndarray (H, W, 3). Accepts any resolution.
    - Returns:
        segments: list of cropped np.ndarray images (from original)
        bboxes:   list of (x1, y1, x2, y2) in original image coordinates
    """
    assert isinstance(image_np, np.ndarray) and image_np.ndim == 3 and image_np.shape[2] == 3, \
        "image_np must be a HxWx3 BGR uint8 NumPy array"

    model, device_obj, stride = _get_yolo_model(weights=weights, device_str=device, dnn=False, half=use_half, data=data)
    # Keep a copy of the original for cropping/coordinate space
    im0 = np.ascontiguousarray(image_np)
    h0, w0 = im0.shape[:2]

    # Letterbox resize to imgsz with stride alignment (like detect.py)
    # Returns: resized_img, (ratio_w, ratio_h), (pad_w, pad_h)
    lb_img, _, _ = letterbox(im0, new_shape=imgsz, stride=stride, auto=True)

    # Convert to model input: HWC BGR -> CHW RGB, float32/16, [0,1]
    img = lb_img.transpose((2, 0, 1))[::-1]  # BGR -> RGB, to CHW
    img = np.ascontiguousarray(img)
    img_t = torch.from_numpy(img).to(device_obj)
    img_t = img_t.half() if (use_half and model.fp16) else img_t.float()
    img_t /= 255.0
    if img_t.ndim == 3:
        img_t = img_t.unsqueeze(0)  # (1,3,H,W)

    # Inference
    pred = model(img_t, augment=False, visualize=False)

    # NMS
    det_list = non_max_suppression(
        pred,
        conf_thres=conf_thres,
        iou_thres=iou_thres,
        classes=classes,
        agnostic=agnostic_nms,
        max_det=max_det,
    )

    segments: list[np.ndarray] = []
    bboxes: list[tuple[int, int, int, int]] = []

    # Process single image predictions
    det = det_list[0]
    if det is not None and len(det):
        # Scale boxes from letterboxed image shape back to the original image shape
        det[:, :4] = scale_coords(img_t.shape[2:], det[:, :4], im0.shape).round()

        # Extract crops and boxes
        for *xyxy, conf, cls in det.tolist():
            x1, y1, x2, y2 = map(int, xyxy)
            # Clip just in case
            x1 = max(0, min(x1, w0 - 1))
            y1 = max(0, min(y1, h0 - 1))
            x2 = max(0, min(x2, w0 - 1))
            y2 = max(0, min(y2, h0 - 1))
            if x2 <= x1 or y2 <= y1:
                continue  # skip degenerate/empty boxes

            crop = im0[y1:y2, x1:x2].copy()
            segments.append(crop)
            bboxes.append((x1, y1, x2, y2))

    return [segments, bboxes]

