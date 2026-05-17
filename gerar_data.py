import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.bep.gov.pt/pages/oferta/Oferta_Detalhes.aspx?CodOferta="

# Começa num número recente (ajusta se necessário)
START_ID = 147980  

TOTAL = 20

def get_oferta(cod):
    url = BASE_URL + str(cod)

    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        titulo = soup.find("span", {"id": "ctl00_ContentPlaceHolder1_lblDesignacao"} )
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
    ofertas = []
    cod = START_ID

    while len(ofertas) < TOTAL and cod > START_ID - 200:
        print(f"A verificar {cod}")
        oferta = get_oferta(cod)

        if oferta:
            ofertas.append(oferta)

        cod -= 1
        time.sleep(1)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(ofertas, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
