"""Smoke tests Post-Prod: validaciones rápidas, de solo lectura, contra la app en producción.

Variables de entorno: APP_BASE_URL (URL del ALB) y EXPECTED_VERSION (SHA desplegado).
"""
import json
import os
import urllib.request

BASE_URL = os.environ["APP_BASE_URL"].rstrip("/")
EXPECTED_VERSION = os.environ["EXPECTED_VERSION"]


def _get(path: str):
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as respuesta:  # nosec B310
        return respuesta.status, respuesta.read().decode("utf-8")


def test_frontend_responde_con_el_html_de_la_app():
    estado, cuerpo = _get("/")
    assert estado == 200
    assert "Lista de mercado" in cuerpo


def test_backend_saludable_con_la_version_esperada():
    estado, cuerpo = _get("/api/health")
    datos = json.loads(cuerpo)
    assert estado == 200
    assert datos["status"] == "ok"
    assert datos["version"] == EXPECTED_VERSION


def test_backend_accesible_a_traves_del_alb():
    estado, cuerpo = _get("/api/items")
    assert estado == 200
    assert isinstance(json.loads(cuerpo), list)
