import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.api.ocr import layout_detector, ocr_engine
from app.main import create_app
from app.services.ocr.base import Box, TextBlock
from app.services.regions.base import Region
from tests.factories import block, block_of, line


class FakeOcrEngine:
    def read_blocks(self, image: Image.Image) -> list[TextBlock]:
        return [
            block("二番目", 5, 0, 10, 100, vertical=True),
            block_of([line("一番", 55, 0, 60, 100, True), line("目", 50, 0, 55, 100, True)], True),
        ]


class NoRegions:
    def detect(self, image: Image.Image) -> list[Region]:
        return []


class OneFigure:
    def detect(self, image: Image.Image) -> list[Region]:
        return [Region(Box(0, 0, 20, 20), "figure", 0.9)]


@pytest.fixture
def app() -> FastAPI:
    app = create_app()
    app.dependency_overrides[ocr_engine] = FakeOcrEngine
    app.dependency_overrides[layout_detector] = NoRegions
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def image_bytes(format: str = "PNG") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buffer, format=format)
    return buffer.getvalue()


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_serves_frontend(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert client.get("/js/main.js").headers["cache-control"] == "no-cache"


def test_ocr_returns_paragraphs_in_reading_order(client: TestClient) -> None:
    response = client.post("/api/ocr", files={"image": ("page.png", image_bytes(), "image/png")})
    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"type": "paragraph", "text": "一番目", "ruby": [], "role": "body", "level": 0},
            {"type": "paragraph", "text": "二番目", "ruby": [], "role": "body", "level": 0},
        ],
        "text": "一番目\n\n二番目",
    }


def test_ocr_returns_figures_as_dithered_png(app: FastAPI) -> None:
    app.dependency_overrides[layout_detector] = OneFigure
    response = TestClient(app).post(
        "/api/ocr", files={"image": ("page.png", image_bytes(), "image/png")}
    )
    items = response.json()["items"]
    # Vertical page, read right to left: 一番目 (x≈55), picture (x≈10), 二番目 (x≈5).
    assert [item["type"] for item in items] == ["paragraph", "figure", "paragraph"]
    assert items[1]["src"].startswith("data:image/png;base64,")


def test_ocr_accepts_heic(client: TestClient) -> None:
    files = {"image": ("photo.heic", image_bytes("HEIF"), "image/heic")}
    assert client.post("/api/ocr", files=files).status_code == 200


def test_reading_marks_contextual_reading(client: TestClient) -> None:
    response = client.post("/api/reading", json={"text": "今日", "context": "今日は", "offset": 0})
    assert response.status_code == 200
    readings = response.json()["readings"]
    assert {"kana": "きょう", "label": "きょう", "kind": "word", "contextual": True} in readings


def test_meaning(client: TestClient) -> None:
    response = client.post("/api/meaning", json={"text": "食べました"})
    assert response.status_code == 200
    body = response.json()
    assert body["looked_up"] == "食べる"
    assert body["entries"][0]["senses"][0]["glosses"] == ["to eat"]


def test_reading_rejects_empty_text(client: TestClient) -> None:
    assert client.post("/api/reading", json={"text": ""}).status_code == 422


def test_ocr_rejects_non_image(client: TestClient) -> None:
    response = client.post("/api/ocr", files={"image": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 400
