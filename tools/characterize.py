"""Ejecuta los mismos casos contra una o varias APIs y imprime una tabla Markdown comparativa.

Uso:  python tools/characterize.py --base original=http://localhost:8080 --base nuevo=http://localhost:8000
Requiere: pip install httpx
"""
import argparse
import random
import string

import httpx


def summary(r: httpx.Response) -> str:
    try:
        d = r.json()
    except ValueError:
        return "sin JSON"
    if isinstance(d, dict) and "article" in d:
        a = d["article"]
        return f"slug='{a.get('slug')}' tagList={a.get('tagList')}"
    if isinstance(d, dict) and "errors" in d:
        return "errors: " + ", ".join(d["errors"])
    if isinstance(d, dict) and "detail" in d:
        return "detail"
    return "-"


def run(base: str) -> list[tuple[str, int, str]]:
    c = httpx.Client(base_url=base, timeout=15)
    s = "".join(random.choices(string.ascii_lowercase, k=6))
    email, pw = f"u{s}@example.com", "clave-segura-1"
    c.post("/api/users", json={"user": {"username": f"u{s}", "email": email, "password": pw}})
    tok = c.post("/api/users/login", json={"user": {"email": email, "password": pw}}).json()["user"]["token"]
    tok_h, bearer_h = {"Authorization": f"Token {tok}"}, {"Authorization": f"Bearer {tok}"}
    t = f"Caso {s}"
    ok = {"title": t, "description": "d", "body": "b", "tagList": ["a", "b"]}
    cases = [
        ("Sin autenticación", {}, {"article": ok}),
        ("Esquema Bearer", bearer_h, {"article": {**ok, "title": t + " bearer"}}),
        ("Caso feliz con tagList", tok_h, {"article": ok}),
        ("Título duplicado", tok_h, {"article": ok}),
        ("Colisión de slug (título distinto)", tok_h, {"article": {**ok, "title": t + "!"}}),
        ("Sin tagList", tok_h, {"article": {"title": t + " sin tags", "description": "d", "body": "b"}}),
        ("tagList vacío", tok_h, {"article": {**ok, "title": t + " vacio", "tagList": []}}),
        ("Etiquetas repetidas y con espacios", tok_h, {"article": {**ok, "title": t + " tags", "tagList": ["a", "a", " b "]}}),
        ("Slug enviado por el cliente", tok_h, {"article": {**ok, "title": t + " cliente", "slug": "otro"}}),
        ("Título con acentos", tok_h, {"article": {**ok, "title": f"Programación ÁÉ ñandú {s}"}}),
        ("Título solo símbolos", tok_h, {"article": {**ok, "title": "!!!"}}),
        ("Sin title", tok_h, {"article": {"description": "d", "body": "b"}}),
        ("Sin description", tok_h, {"article": {"title": t + " x", "body": "b"}}),
        ("Título de 151 caracteres", tok_h, {"article": {**ok, "title": "x" * 151}}),
        ("Sin wrapper 'article'", tok_h, ok),
    ]
    out = []
    for label, headers, payload in cases:
        r = c.post("/api/articles", json=payload, headers=headers)
        out.append((label, r.status_code, summary(r)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", action="append", required=True, metavar="NOMBRE=URL")
    targets = [b.split("=", 1) for b in ap.parse_args().base]
    results = {name: run(url) for name, url in targets}
    names = [n for n, _ in targets]
    print("| Caso | " + " | ".join(names) + " |")
    print("|---|" + "---|" * len(names))
    for i, (label, *_ ) in enumerate(results[names[0]]):
        cells = [f"{results[n][i][1]} · {results[n][i][2]}" for n in names]
        print(f"| {label} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
