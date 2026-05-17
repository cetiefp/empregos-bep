import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://www.bep.gov.pt/pages/oferta/Oferta_Detalhes.aspx?CodOferta="
TOTAL = 20
ESTADO_FILE = "estado.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9"
}


def carregar_estado():
    if os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("ultimo_cod", 147980)
    return 147980


def guardar_estado(cod):
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump({"ultimo_cod": cod}, f)


def get_oferta(cod):
    url = BASE_URL + str(cod)

    try:
        r = requests.get(url, headers=HEADERS, timeout=3)

        if r.status_code != 200:
            return None

        html = r.text

        if "Pesquisar Oferta" in html or "Oferta_Pesquisa" in html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        titulo_tag = soup.find("span", id="ctl00_ContentPlaceHolder1_lblDesignacao")
