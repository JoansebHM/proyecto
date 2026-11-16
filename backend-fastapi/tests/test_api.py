import pytest
from fastapi.testclient import TestClient

from app import main
from app.service import ItemsService

VALID = {"name": "Arroz", "quantity": 2, "price": 4500}


@pytest.fixture
def client(monkeypatch):
    # Servicio nuevo en cada test para aislar el estado.
    monkeypatch.setattr(main, "service", ItemsService())
    return TestClient(main.app)


def test_health_local(client, monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": "local"}


def test_health_con_version(client, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "abc123")
    assert client.get("/api/health").json() == {"status": "ok", "version": "abc123"}


def test_rutas_sin_prefijo_api_no_existen(client):
    assert client.get("/items").status_code == 404


def test_get_items_vacio(client):
    r = client.get("/api/items")
    assert r.status_code == 200 and r.json() == []


def test_post_crea_y_get_lo_lista(client):
    r = client.post("/api/items", json=VALID)
    assert r.status_code == 201
    assert r.json() == {"id": 1, **VALID, "price": 4500.0, "purchased": False}
    assert client.get("/api/items").json() == [r.json()]


def test_post_invalido_devuelve_400_con_message(client):
    r = client.post("/api/items", json={**VALID, "name": ""})
    assert r.status_code == 400
    assert r.json() == {"message": "El nombre es obligatorio", "statusCode": 400}


def test_post_sin_body_devuelve_400(client):
    r = client.post("/api/items")
    assert r.status_code == 400
    assert "message" in r.json()


def test_patch_actualiza(client):
    client.post("/api/items", json=VALID)
    r = client.patch("/api/items/1", json={"purchased": True})
    assert r.status_code == 200 and r.json()["purchased"] is True


def test_patch_inexistente_404(client):
    r = client.patch("/api/items/99", json={"price": 1})
    assert r.status_code == 404
    assert r.json()["message"] == "Producto 99 no existe"


def test_patch_id_no_numerico_400(client):
    assert client.patch("/api/items/abc", json={}).status_code == 400


def test_delete_204_y_desaparece(client):
    client.post("/api/items", json=VALID)
    r = client.delete("/api/items/1")
    assert r.status_code == 204 and r.content == b""
    assert client.get("/api/items").json() == []


def test_delete_inexistente_404(client):
    assert client.delete("/api/items/99").status_code == 404


def test_cors_habilitado(client):
    r = client.get("/api/items", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "*"
