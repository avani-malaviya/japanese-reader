import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.ocr import ocr_engine
from app.main import create_app
from app.services.ocr.base import Box, TextBlock


class FakeOcrEngine:
    def read_blocks(self, image: Image.Image) -> list[TextBlock]:
        return [
            TextBlock(box=Box(0, 0, 10, 100), vertical=True, lines=["二番目"]),
            TextBlock(box=Box(50, 0, 60, 100), vertical=True, lines=["一番", "目"]),
        ]


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    app.dependency_overrides[ocr_engine] = FakeOcrEngine
    return TestClient(app)


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_serves_frontend(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_ocr_returns_paragraphs_in_reading_order(client: TestClient) -> None:
    response = client.post("/api/ocr", files={"image": ("page.png", png_bytes(), "image/png")})
    assert response.status_code == 200
    assert response.json() == {"paragraphs": ["一番目", "二番目"], "text": "一番目\n\n二番目"}


def test_ocr_rejects_non_image(client: TestClient) -> None:
    response = client.post("/api/ocr", files={"image": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 400
