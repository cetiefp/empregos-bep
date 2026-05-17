import requests
from bs4 import BeautifulSoup
import json

URL = "https://www.bep.gov.pt/pages/oferta/Oferta_Listar.aspx"
headers = {"User-Agent": "Mozilla/5.0"}

session = requests.Session()
empregos = []

response = session.get(URL, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

tabela = soup.find("table")

if tabela:
    linhas = tabela.find_all("tr")[1:]

    for linha in linhas:
        colunas = linha.find_all("td")

        if len(colunas) >= 4:
            titulo = colunas[0].get_text(strip=True)
            entidade = colunas[1].get_text(strip=True)
            local = colunas[2].get_text(strip=True)
            data = colunas[3].get_text(strip=True)

            link_tag = colunas[0].find("a")
            link = "https://www.bep.gov.pt" + link_tag["href"] if link_tag else ""

            empregos.append({
                "titulo": titulo,
                "entidade": entidade,
                "local": local,
                "data": data,
                "link": link
            })

# limitar a 200
empregos = empregos[:200]

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(empregos, f, ensure_ascii=False, indent=2)

print(f"{len(empregos)} empregos guardados")
