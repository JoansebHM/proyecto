import pytest

from app.service import ItemsService, NotFoundError, ValidationError

VALID = {"name": "Arroz", "quantity": 2, "price": 4500}


@pytest.fixture
def service():
    return ItemsService()


class TestFindAll:
    def test_lista_vacia_al_inicio(self, service):
        assert service.find_all() == []

    def test_devuelve_los_creados(self, service):
        service.create(VALID)
        service.create({**VALID, "name": "Leche"})
        assert [i["name"] for i in service.find_all()] == ["Arroz", "Leche"]


class TestCreate:
    def test_guarda_en_lista_interna_con_purchased_false(self, service):
        item = service.create(VALID)
        assert item == {"id": 1, **VALID, "price": 4500.0, "purchased": False}
        assert item in service.find_all()

    def test_incrementa_id(self, service):
        assert service.create(VALID)["id"] == 1
        assert service.create(VALID)["id"] == 2

    def test_recorta_nombre_y_convierte_texto_numerico(self, service):
        item = service.create({"name": "  Pan ", "quantity": "3", "price": "1200"})
        assert (item["name"], item["quantity"], item["price"]) == ("Pan", 3, 1200)

    def test_acepta_precio_cero(self, service):
        assert service.create({**VALID, "price": 0})["price"] == 0

    @pytest.mark.parametrize(
        "data,msg",
        [
            ({**VALID, "name": "   "}, "nombre"),
            ({"quantity": 1, "price": 1}, "nombre"),
            ({**VALID, "name": 5}, "nombre"),
            ({**VALID, "quantity": 0}, "cantidad"),
            ({**VALID, "quantity": 1.5}, "cantidad"),
            ({**VALID, "quantity": "x"}, "cantidad"),
            ({**VALID, "quantity": True}, "cantidad"),
            ({**VALID, "quantity": None}, "cantidad"),
            ({**VALID, "price": -1}, "precio"),
            ({**VALID, "price": "x"}, "precio"),
            ({**VALID, "price": float("inf")}, "precio"),
        ],
    )
    def test_rechaza_datos_invalidos(self, service, data, msg):
        with pytest.raises(ValidationError, match=msg):
            service.create(data)
        assert service.find_all() == []


class TestUpdate:
    def test_modifica_campo_y_conserva_el_resto(self, service):
        item = service.create(VALID)
        updated = service.update(item["id"], {"price": 5000})
        assert (updated["name"], updated["quantity"], updated["price"]) == ("Arroz", 2, 5000)
        assert service.find_all()[0]["price"] == 5000

    def test_modifica_nombre_y_cantidad(self, service):
        item = service.create(VALID)
        updated = service.update(item["id"], {"name": "Frijol", "quantity": 4})
        assert (updated["name"], updated["quantity"]) == ("Frijol", 4)

    def test_marca_y_desmarca_comprado(self, service):
        item = service.create(VALID)
        assert service.update(item["id"], {"purchased": True})["purchased"] is True
        assert service.update(item["id"], {"purchased": False})["purchased"] is False

    def test_ignora_purchased_no_booleano(self, service):
        item = service.create(VALID)
        assert service.update(item["id"], {"purchased": "si"})["purchased"] is False

    def test_dato_invalido_no_modifica(self, service):
        item = service.create(VALID)
        with pytest.raises(ValidationError):
            service.update(item["id"], {"quantity": 0})
        assert service.find_all()[0]["quantity"] == 2

    def test_id_inexistente(self, service):
        with pytest.raises(NotFoundError):
            service.update(99, {"price": 1})


class TestRemove:
    def test_elimina_de_la_lista(self, service):
        a = service.create(VALID)
        b = service.create({**VALID, "name": "Leche"})
        service.remove(a["id"])
        assert service.find_all() == [b]

    def test_id_inexistente(self, service):
        with pytest.raises(NotFoundError):
            service.remove(99)


def test_encuentra_producto_que_no_es_el_primero(service):
    service.create(VALID)
    second = service.create({**VALID, "name": "Leche"})
    assert service.update(second["id"], {"purchased": True})["name"] == "Leche"
