import requests
from bs4 import BeautifulSoup
import json

url = "https://www.bep.gov.pt/pages/oferta/Oferta_Listar.aspx"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html",
    "Accept-Language": "pt-PT,pt;q=0.9"
}

response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.text, "html.parser")

empregos = []

# 🔍 procurar links das ofertas
links = soup.select("a")

for link in links:
    href = link.get("href")
    texto = link.get_text(strip=True)

    if href and "Oferta" in href and texto:

        empregos.append({
            "titulo": texto,
            "entidade": "",
            "local": "",
            "data": "",
            "link": "https://www.bep.gov.pt" + href
        })

# limpar duplicados
vistos = set()
resultado = []

for e in empregos:
    if e["link"] not in vistos:
        vistos.add(e["link"])
        resultado.append(e)

# limitar a 200
resultado = resultado[:200]

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

print("OK:", len(resultado), "empregos encontrados")
