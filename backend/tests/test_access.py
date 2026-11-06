import base64

from fastapi.testclient import TestClient

from app.main import create_app


def basic(password: str) -> dict[str, str]:
    token = base64.b64encode(f"anyone:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_no_password_leaves_the_app_open():
    client = TestClient(create_app())
    assert client.get("/api/health").status_code == 200


def test_password_is_required_for_pages_and_api():
    client = TestClient(create_app(password="sesame"))
    for path in ("/", "/api/health"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"].startswith("Basic")


def test_wrong_password_is_refused_and_right_one_lets_in():
    client = TestClient(create_app(password="sesame"))
    assert client.get("/api/health", headers=basic("nope")).status_code == 401
    assert client.get("/api/health", headers=basic("sesame")).status_code == 200
    assert client.get("/", headers=basic("sesame")).status_code == 200
