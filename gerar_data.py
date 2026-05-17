import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.bep.gov.pt/pages/oferta/Oferta_Detalhes.aspx?CodOferta={}"

# começa neste código (ajusta se quiseres)
START_ID = 147969
TOTAL = 200

def extrair_dados(html):
    soup = BeautifulSoup(html, "html.parser")

    def get_text(label):
        el = soup.find("span", string=label)
        if el:
            val = el.find_next("span")
            if val:
                return val.text.strip()
        return None

    titulo = soup.find("span", id="ctl00_ContentPlaceHolder1_lblTitulo")
    entidade = soup.find("span", id="ctl00_ContentPlaceHolder1_lblEntidade")

    return {
        "titulo": titulo.text.strip() if titulo else None,
        "entidade": entidade.text.strip() if entidade else None,
    }

def main():
    resultados = []

    for cod in range(START_ID, START_ID - TOTAL, -1):
        url = BASE_URL.format(cod)

        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                dados = extrair_dados(r.text)
                dados["cod"] = cod
                dados["url"] = url

                # evitar páginas vazias
                if dados["titulo"]:
                    resultados.append(dados)

            time.sleep(1)  # evitar bloqueio
        except Exception as e:
            print(f"Erro no {cod}: {e}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"Guardado com {len(resultados)} entradas.")

if __name__ == "__main__":
    main()
