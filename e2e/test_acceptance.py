from playwright.sync_api import Page, expect


def test_usuario_agrega_producto_a_la_lista(page: Page, app_url: str):
    # 1-2. App en ejecución: abrir la página principal
    page.goto(app_url)
    expect(page.get_by_text("Tu lista está vacía")).to_be_visible()

    # 3-4. Llenar el formulario y pulsar "Agregar"
    page.get_by_placeholder("Producto").fill("Pan")
    page.get_by_placeholder("Cant.").fill("2")
    page.get_by_placeholder("Precio unidad").fill("1500")
    page.get_by_role("button", name="Agregar").click()

    # 5. Verificar que el producto aparece en la página
    fila = page.get_by_role("listitem").filter(has_text="Pan")
    expect(fila).to_be_visible()
    expect(fila).to_contain_text("2 ×")
    expect(page.get_by_text("Tu lista está vacía")).to_have_count(0)

    # El total estimado refleja 2 × 1500 = 3000
    total = page.get_by_text("Total estimado").locator("xpath=..").locator("strong")
    expect(total).to_contain_text("3.000")
