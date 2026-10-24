"""Page layout detection with DocLayout-YOLO. See docs/decisions/0004 and 0005."""

import threading

from PIL import Image

from app.services.inference import gpu_lock
from app.services.ocr.base import Box
from app.services.regions.base import Region, RegionKind

MODEL_REPO = "juliozhao/DocLayout-YOLO-DocStructBench"
MODEL_FILE = "doclayout_yolo_docstructbench_imgsz1024.pt"
INPUT_SIZE = 1024

# The model's class names, mapped onto ours.
KINDS: dict[str, RegionKind] = {
    "title": "title",
    "plain text": "text",
    "abandon": "abandon",
    "figure": "figure",
    "figure_caption": "caption",
    "table": "table",
    "table_caption": "caption",
    "table_footnote": "caption",
    "isolate_formula": "text",
    "formula_caption": "caption",
}
# Wrongly dropping text (abandon) or restyling it (title) is worse than missing one.
MIN_SCORE: dict[RegionKind, float] = {
    "title": 0.5,
    "text": 0.3,
    "caption": 0.4,
    "figure": 0.4,
    "table": 0.4,
    "abandon": 0.6,
}
# Ignore specks: pictures smaller than this share of the page are not worth placing.
MIN_PICTURE_AREA_RATIO = 0.005
# The model sometimes reports one picture as both figure and table.
DUPLICATE_IOU = 0.7


def _iou(a: Box, b: Box) -> float:
    inter = Box(max(a.x1, b.x1), max(a.y1, b.y1), min(a.x2, b.x2), min(a.y2, b.y2))
    overlap = inter.area if inter.x2 > inter.x1 and inter.y2 > inter.y1 else 0.0
    return overlap / (a.area + b.area - overlap) if overlap else 0.0


class DocLayoutDetector:
    def __init__(self) -> None:
        # Imported here so the app (and tests) start without loading torch.
        import torch
        from doclayout_yolo import YOLOv10
        from huggingface_hub import hf_hub_download

        self._model = YOLOv10(hf_hub_download(MODEL_REPO, MODEL_FILE))
        self._device = "mps" if torch.backends.mps.is_available() else "cpu"

    def detect(self, image: Image.Image) -> list[Region]:
        with gpu_lock:
            result = self._model.predict(
                image,
                imgsz=INPUT_SIZE,
                conf=min(MIN_SCORE.values()),
                device=self._device,
                verbose=False,
            )[0]
        min_picture_area = image.width * image.height * MIN_PICTURE_AREA_RATIO
        regions: list[Region] = []
        detections = zip(result.boxes.xyxy.tolist(), result.boxes.cls.tolist(), result.boxes.conf.tolist())
        for coords, cls, score in sorted(detections, key=lambda d: -d[2]):
            kind = KINDS.get(self._model.names[int(cls)])
            box = Box(*coords)
            if kind is None or score < MIN_SCORE[kind]:
                continue
            if kind in ("figure", "table"):
                if box.area < min_picture_area:
                    continue
                if any(r.kind in ("figure", "table") and _iou(r.box, box) > DUPLICATE_IOU for r in regions):
                    continue
            regions.append(Region(box=box, kind=kind, score=score))
        return regions


_detector: DocLayoutDetector | None = None
_lock = threading.Lock()


def get_detector() -> DocLayoutDetector:
    global _detector
    with _lock:
        if _detector is None:
            _detector = DocLayoutDetector()
        return _detector
