import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://www.bep.gov.pt/pages/oferta/Oferta_Detalhes.aspx?CodOferta="
TOTAL = 20
ESTADO_FILE = "estado.json"


def carregar_estado():
    if os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE, "r") as f:
            return json.load(f).get("ultimo_cod", 147980)
    return 147980


def guardar_estado(cod):
    with open(ESTADO_FILE, "w") as f:
        json.dump({"ultimo_cod": cod}, f)


def get_oferta(cod):
    url = BASE_URL + str(cod)

    try:
        r = requests.get(url, timeout=10)

        # 🔴 Proteção: páginas inválidas
        if "Pesquisar Oferta" in r.text:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        spans = soup.find_all("span")

        if len(spans) < 10:
            return None

        titulo = None
        entidade = None
        data = None

        for s in spans:
            texto = s.text.strip()

            if not titulo and len(texto) > 10:
                titulo = texto

            if "Município" in texto or "Instituto" in texto or "Serviço" in texto:
                entidade = texto

            if "/" in texto and len(texto) <= 10:
                data = texto

        # 🔴 validação forte
        if not titulo or "Pesquisar" in titulo:
            return None

        return {
            "cod": cod,
            "titulo": titulo,
            "entidade": entidade or "",
            "data": data or "",
            "link": url
        }

    except Exception:
        return None


def main():
    ultimo_cod = carregar_estado()

    ofertas = []
    cod = ultimo_cod + 50
    tentativas = 0

    while len(ofertas) < TOTAL and tentativas < 300:
        print(f"A testar {cod}")

