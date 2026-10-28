import pytest

from app.services.residuos import decidir, formatear_item


@pytest.mark.parametrize("material,estado,esperado", [
    ("metal", "limpio", "blanco"),
    ("metal", "con_liquido", "blanco"),
    ("plastico", "sucio", "blanco"),
    ("vidrio", "limpio", "blanco"),
    ("tetrapak", "limpio", "blanco"),
    ("papel", "limpio", "blanco"),
    ("carton", "sucio", "negro"),       # caja de pizza grasosa
    ("papel", "con_liquido", "negro"),
    ("organico", "sucio", "verde"),
    ("ordinario", "limpio", "negro"),
    ("peligroso", "limpio", "especial"),
])
def test_contenedor(material, estado, esperado):
    assert decidir(material, estado)["contenedor"] == esperado


def test_lata_con_liquido_pide_vaciar():
    pasos = decidir("metal", "con_liquido")["pasos"]
    assert any("Vací" in p for p in pasos)


def test_desconocido_no_inventa_contenedor():
    assert decidir("desconocido")["contenedor"] is None
    assert decidir("algo_raro")["contenedor"] is None
    assert decidir(None)["contenedor"] is None


def test_estado_nulo_se_trata_como_limpio():
    assert decidir("metal", None)["contenedor"] == "blanco"


def test_formato_incluye_nombre_y_contenedor():
    txt = formatear_item("lata de gaseosa", "metal", "con_liquido", 2)
    assert "lata de gaseosa" in txt and "Blanco" in txt and "2×" in txt
