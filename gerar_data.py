import json

def main():
    dados = [
        {
            "cod": 123,
            "titulo": "Teste",
            "entidade": "Teste Entidade",
            "data": "2026-05-17",
            "link": "https://www.bep.gov.pt"
        }
    ]

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://www.bep.gov.pt/pages/oferta/Oferta_Detalhes.aspx?CodOferta="
TOTAL = 20
ESTADO_FILE = "estado.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "pt-PT,pt;q=0.9"
}

def carregar_estado():
    if os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("ultimo_cod", 147980)
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

        if "Pesquisar Oferta" in html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        titulo_tag = soup.find("span", id="ctl00_ContentPlaceHolder1_lblDesignacao")
        entidade_tag = soup.find("span", id="ctl00_ContentPlaceHolder1_lblOrganismo")
        data_tag = soup.find("span", id="ctl00_ContentPlaceHolder1_lblDataPublicacao")

        if not titulo_tag:
            return None

        titulo = titulo_tag.text.strip()

        return {
            "cod": cod,
            "titulo": titulo,
            "entidade": entidade_tag.text.strip() if entidade_tag else "",
