import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.bep.gov.pt/pages/oferta/Oferta_Detalhes.aspx?CodOferta="

def obter_oferta(cod):
    url = f"{BASE_URL}{cod}"
    try:
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        titulo = soup.find("span", id="ctl00_ContentPlaceHolder1_lblTitulo")
        entidade = soup.find("span", id="ctl00_ContentPlaceHolder1_lblEntidade")

        if not titulo:
            return None

        return {
            "cod": cod,
            "titulo": titulo.text.strip() if titulo else "",
            "entidade": entidade.text.strip() if entidade else "",
            "url": url
        }

    except:
        return None


def obter_ultimas(n=20, start=148500):
    resultados = []

    cod = start

    while len(resultados) < n and cod > 0:
        oferta = obter_oferta(cod)

        if oferta:
            print(f"✔ Encontrado {cod}")
            resultados.append(oferta)

        cod -= 1
        time.sleep(0.5)  # evitar bloqueio

    return resultados


dados = obter_ultimas()

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)
