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
            return json.load(f)["ultimo_cod"]
    return 147980


def guardar_estado(cod):
    with open(ESTADO_FILE, "w") as f:
        json.dump({"ultimo_cod": cod}, f)


def get_oferta(cod):
    url = BASE_URL + str(cod)

    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        titulo = soup.find("span", {"id": "ctl00_ContentPlaceHolder1_lblDesignacao"})
        entidade = soup.find("span", {"id": "ctl00_ContentPlaceHolder1_lblOrganismo"})
        data = soup.find("span", {"id": "ctl00_ContentPlaceHolder1_lblDataPublicacao"})

        if not titulo:
            return None

        return {
            "cod": cod,
            "titulo": titulo.text.strip(),
            "entidade": entidade.text.strip() if entidade else "",
            "data": data.text.strip() if data else "",
            "link": url
        }

    except:
        return None


def main():
    ultimo_cod = carregar_estado()

    ofertas = []
    cod = ultimo_cod

    print(f"Início em {cod}")

    tentativas = 0

    # sobe até encontrar 20 novas ou parar
    while len(ofertas) < TOTAL and tentativas < 100:
        oferta = get_oferta(cod)

        if oferta:
            ofertas.append(oferta)
            print(f"✔ encontrada {cod}")
        else:
            print(f"✖ sem oferta {cod}")

        cod -= 1
        tentativas += 1
        time.sleep(1)

    if ofertas:
        novo_max = max(o["cod"] for o in ofertas)
        guardar_estado(novo_max)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(ofertas, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
