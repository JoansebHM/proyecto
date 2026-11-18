import uuid

from playwright.sync_api import Page, expect


def _agregar(page: Page, nombre: str, cantidad: str = "2", precio: str = "1500"):
    page.get_by_placeholder("Producto").fill(nombre)
    page.get_by_placeholder("Cant.").fill(cantidad)
    page.get_by_placeholder("Precio unidad").fill(precio)
    page.get_by_role("button", name="Agregar").click()
    return page.get_by_role("listitem").filter(has_text=nombre)


def _nombre(base: str) -> str:
    # Nombre único: en Pre-Prod la lista es compartida y puede tener otros productos.
    return f"{base}-{uuid.uuid4().hex[:6]}"


def test_usuario_agrega_producto_a_la_lista(page: Page, app_url: str):
    page.goto(app_url)
    nombre = _nombre("Pan")

    fila = _agregar(page, nombre)

    expect(fila).to_be_visible()
    expect(fila).to_contain_text("2 ×")
    # Subtotal de la fila: 2 × 1500 = 3000
    expect(fila.locator("strong")).to_contain_text("3.000")
    expect(page.get_by_text("Tu lista está vacía")).to_have_count(0)

    fila.get_by_title("Eliminar").click()  # deja la lista como estaba
    expect(fila).to_have_count(0)


def test_usuario_marca_producto_como_comprado(page: Page, app_url: str):
    page.goto(app_url)
    nombre = _nombre("Leche")

    fila = _agregar(page, nombre, cantidad="1", precio="4000")
    expect(fila).to_be_visible()
    expect(fila).not_to_have_class("done")

    fila.get_by_title("Marcar como comprado").click()

    expect(fila).to_have_class("done")
    expect(fila.get_by_title("Marcar como comprado")).to_be_checked()

    fila.get_by_title("Eliminar").click()
    expect(fila).to_have_count(0)


def test_usuario_elimina_producto(page: Page, app_url: str):
    page.goto(app_url)
    nombre = _nombre("Huevos")

    fila = _agregar(page, nombre, cantidad="12", precio="500")
    expect(fila).to_be_visible()

    fila.get_by_title("Eliminar").click()

    expect(page.get_by_text(nombre)).to_have_count(0)
