from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.library import library_store
from app.main import create_app
from app.services.library import LibraryStore


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    app = create_app()
    store = LibraryStore(tmp_path / "library.sqlite")
    app.dependency_overrides[library_store] = lambda: store
    return TestClient(app)


def test_folder_and_document_lifecycle(client: TestClient) -> None:
    folder = client.post("/api/folders", json={"name": "Pamphlets"}).json()
    renamed = client.patch(f"/api/folders/{folder['id']}", json={"name": "パンフレット"}).json()
    assert renamed["name"] == "パンフレット"

    document = client.post(f"/api/folders/{folder['id']}/documents", json={"title": "Zoo"}).json()
    assert document["html"] == ""
    saved = client.put(f"/api/documents/{document['id']}", json={"html": "<p>動物園</p>"})
    assert saved.status_code == 200
    assert client.get(f"/api/documents/{document['id']}").json()["html"] == "<p>動物園</p>"

    listing = client.get(f"/api/folders/{folder['id']}/documents").json()
    assert [d["title"] for d in listing] == ["Zoo"] and "html" not in listing[0]
    assert client.get("/api/folders").json()[0]["document_count"] == 1

    renamed = client.patch(f"/api/documents/{document['id']}", json={"title": "Zoo leaflet"}).json()
    assert renamed["title"] == "Zoo leaflet"

    assert client.delete(f"/api/folders/{folder['id']}").status_code == 204
    assert client.get(f"/api/documents/{document['id']}").status_code == 404


def test_unknown_ids_are_404(client: TestClient) -> None:
    assert client.get("/api/documents/42").status_code == 404
    assert client.put("/api/documents/42", json={"html": ""}).status_code == 404
    assert client.get("/api/folders/42/documents").status_code == 404
    assert client.delete("/api/folders/42").status_code == 404


def test_names_are_validated(client: TestClient) -> None:
    assert client.post("/api/folders", json={"name": ""}).status_code == 422
    assert client.post("/api/folders", json={"name": "x" * 101}).status_code == 422
    folder = client.post("/api/folders", json={"name": "Book"}).json()
    document = client.post(f"/api/folders/{folder['id']}/documents", json={"title": "Ch 1"}).json()
    assert client.patch(f"/api/documents/{document['id']}", json={}).status_code == 422
