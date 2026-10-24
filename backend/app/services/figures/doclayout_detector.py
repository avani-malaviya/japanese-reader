"""Picture detection with DocLayout-YOLO. See docs/decisions/0004."""

import threading

from PIL import Image

from app.services.ocr.base import Box

MODEL_REPO = "juliozhao/DocLayout-YOLO-DocStructBench"
MODEL_FILE = "doclayout_yolo_docstructbench_imgsz1024.pt"
INPUT_SIZE = 1024
MIN_SCORE = 0.4
# Ignore specks: anything smaller than this share of the page is not worth placing.
MIN_AREA_RATIO = 0.005


class DocLayoutDetector:
    def __init__(self) -> None:
        # Imported here so the app (and tests) start without loading torch.
        import torch
        from doclayout_yolo import YOLOv10
        from huggingface_hub import hf_hub_download

        self._model = YOLOv10(hf_hub_download(MODEL_REPO, MODEL_FILE))
        self._figure_class = next(i for i, name in self._model.names.items() if name == "figure")
        self._device = "mps" if torch.backends.mps.is_available() else "cpu"

    def detect(self, image: Image.Image) -> list[Box]:
        result = self._model.predict(
            image, imgsz=INPUT_SIZE, conf=MIN_SCORE, device=self._device, verbose=False
        )[0]
        min_area = image.width * image.height * MIN_AREA_RATIO
        boxes = [
            Box(*coords)
            for coords, cls in zip(result.boxes.xyxy.tolist(), result.boxes.cls.tolist())
            if int(cls) == self._figure_class
        ]
        return [box for box in boxes if box.area >= min_area]


_detector: DocLayoutDetector | None = None
_lock = threading.Lock()


def get_detector() -> DocLayoutDetector:
    global _detector
    with _lock:
        if _detector is None:
            _detector = DocLayoutDetector()
        return _detector
