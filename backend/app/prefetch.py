"""Downloads and loads the OCR models once: `python -m app.prefetch`.

The container image runs this at build time, so the weights are baked in and the app starts
without network. Loading (not just downloading) also proves the models work on this machine.
"""

from app.services.ocr.mokuro_engine import get_engine
from app.services.regions.doclayout_detector import get_detector

if __name__ == "__main__":
    get_engine()
    get_detector()
    print("OCR models ready")
