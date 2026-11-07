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


def test_get_items_vacio(client):
    r = client.get("/items")
    assert r.status_code == 200 and r.json() == []


def test_post_crea_y_get_lo_lista(client):
    r = client.post("/items", json=VALID)
    assert r.status_code == 201
    assert r.json() == {"id": 1, **VALID, "price": 4500.0, "purchased": False}
    assert client.get("/items").json() == [r.json()]


def test_post_invalido_devuelve_400_con_message(client):
    r = client.post("/items", json={**VALID, "name": ""})
    assert r.status_code == 400
    assert r.json() == {"message": "El nombre es obligatorio", "statusCode": 400}


def test_post_sin_body_devuelve_400(client):
    r = client.post("/items")
    assert r.status_code == 400
    assert "message" in r.json()


def test_patch_actualiza(client):
    client.post("/items", json=VALID)
    r = client.patch("/items/1", json={"purchased": True})
    assert r.status_code == 200 and r.json()["purchased"] is True


def test_patch_inexistente_404(client):
    r = client.patch("/items/99", json={"price": 1})
    assert r.status_code == 404
    assert r.json()["message"] == "Producto 99 no existe"


def test_patch_id_no_numerico_400(client):
    assert client.patch("/items/abc", json={}).status_code == 400


def test_delete_204_y_desaparece(client):
    client.post("/items", json=VALID)
    r = client.delete("/items/1")
    assert r.status_code == 204 and r.content == b""
    assert client.get("/items").json() == []


def test_delete_inexistente_404(client):
    assert client.delete("/items/99").status_code == 404


def test_cors_habilitado(client):
    r = client.get("/items", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "*"
