"""Pruebas de POST /api/articles. Cada prueba cita la regla (BR) o decisión (D) de docs/ESPECIFICACION.md."""
import re

import pytest

ART = {"title": "Cómo entrenar", "description": "resumen", "body": "cuerpo", "tagList": ["a", "b"]}
ISO = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")


def create(client, headers, article=None, **override):
    data = {**(ART if article is None else article), **override}
    return client.post("/api/articles", json={"article": data}, headers=headers)


# BR-01 -----------------------------------------------------------------
def test_br01_requiere_autenticacion(client):
    r = client.post("/api/articles", json={"article": ART})
    assert r.status_code == 401 and "authorization" in r.json()["errors"]


def test_br01_401_tiene_prioridad_sobre_validacion(client):
    assert client.post("/api/articles", json={"article": {}}).status_code == 401


def test_br01_token_invalido(client):
    assert create(client, {"Authorization": "Token basura"}).status_code == 401


def test_br01_esquema_token_y_bearer(client, auth):
    jwt = auth["Authorization"].split(" ")[1]
    assert create(client, {"Authorization": f"Token {jwt}"}).status_code == 201
    assert create(client, {"Authorization": f"Bearer {jwt}"}, title="Otro").status_code == 201  # D-06


# BR-02 -----------------------------------------------------------------
def test_br02_autor_es_el_usuario_autenticado(client, auth):
    assert create(client, auth).json()["article"]["author"]["username"] == "omar"


# BR-03 / BR-04 ---------------------------------------------------------
def test_br04_slug_derivado_del_titulo(client, auth):
    assert create(client, auth).json()["article"]["slug"] == "como-entrenar"


def test_br04_el_cliente_no_controla_el_slug(client, auth):
    r = create(client, auth, slug="otro-slug")
    assert r.json()["article"]["slug"] == "como-entrenar"


def test_br04_acentos_y_enie(client, auth):
    r = create(client, auth, title="Programación ÁÉ ñandú")
    assert r.json()["article"]["slug"] == "programacion-ae-nandu"


# BR-05 -----------------------------------------------------------------
def test_br05_taglist_es_opcional(client, auth):  # corrige H-06 (original: 404)
    art = {"title": "Sin etiquetas", "description": "d", "body": "b"}
    r = create(client, auth, article=art)
    assert r.status_code == 201 and r.json()["article"]["tagList"] == []


def test_br05_etiquetas_limpias_sin_duplicados_y_ordenadas(client, auth):
    r = create(client, auth, tagList=["b", " a ", "a", ""])
    assert r.json()["article"]["tagList"] == ["a", "b"]


def test_br05_etiqueta_demasiado_larga(client, auth):
    assert create(client, auth, tagList=["x" * 51]).status_code == 422


# BR-06 / BR-07 ---------------------------------------------------------
def test_br06_titulo_duplicado_es_409(client, auth):  # corrige H-04 (original: 404)
    create(client, auth)
    r = create(client, auth)
    assert r.status_code == 409 and "title" in r.json()["errors"]


def test_br07_colision_de_slug_es_409(client, auth):  # corrige H-05 (original: 404)
    create(client, auth)
    r = create(client, auth, title="Como entrenar!")
    assert r.status_code == 409


def test_br07_titulo_sin_letras_ni_numeros_es_422(client, auth):  # corrige H-05 (original: 201 con slug vacío)
    r = create(client, auth, title="!!!")
    assert r.status_code == 422 and "title" in r.json()["errors"]


# Validación por campo (corrige H-07) ------------------------------------
@pytest.mark.parametrize(
    "payload,campo",
    [
        ({"description": "d", "body": "b"}, "title"),
        ({"title": "T", "body": "b"}, "description"),
        ({"title": "T", "description": "d", "body": "   "}, "body"),
        ({"title": "x" * 151, "description": "d", "body": "b"}, "title"),
    ],
)
def test_validacion_devuelve_422_con_campo(client, auth, payload, campo):
    r = client.post("/api/articles", json={"article": payload}, headers=auth)
    assert r.status_code == 422 and campo in r.json()["errors"]


def test_validacion_sin_wrapper_article(client, auth):
    r = client.post("/api/articles", json=ART, headers=auth)
    assert r.status_code == 422 and "article" in r.json()["errors"]


# Contrato de respuesta (H-09, H-10, H-11) --------------------------------
def test_contrato_de_respuesta(client, auth):
    r = create(client, auth)
    assert r.status_code == 201
    art = r.json()["article"]
    assert set(art) == {
        "slug", "title", "description", "body", "tagList",
        "createdAt", "updatedAt", "favorited", "favoritesCount", "author",
    }
    assert set(art["author"]) == {"username", "bio", "image", "following"}
    assert ISO.match(art["createdAt"]) and art["createdAt"] == art["updatedAt"]
    assert art["favorited"] is False and art["favoritesCount"] == 0


# Lectura por slug (apoyo para verificar) ---------------------------------
def test_get_por_slug_es_publico_y_coincide(client, auth):
    created = create(client, auth).json()
    r = client.get("/api/articles/como-entrenar")
    assert r.status_code == 200 and r.json() == created


def test_get_inexistente_es_404(client):
    assert client.get("/api/articles/no-existe").status_code == 404


# Autenticación (apoyo) -----------------------------------------------------
def test_login_y_token_utilizable(client, auth):
    r = client.post("/api/users/login", json={"user": {"email": "omar@example.com", "password": "clave-segura-1"}})
    assert r.status_code == 200
    assert create(client, {"Authorization": f"Token {r.json()['user']['token']}"}).status_code == 201


def test_login_con_clave_incorrecta_es_401(client, auth):
    r = client.post("/api/users/login", json={"user": {"email": "omar@example.com", "password": "mala"}})
    assert r.status_code == 401


def test_registro_duplicado_es_409(client, auth):
    r = client.post("/api/users", json={"user": {"username": "omar", "email": "omar@example.com", "password": "clave-segura-1"}})
    assert r.status_code == 409 and set(r.json()["errors"]) == {"email", "username"}
