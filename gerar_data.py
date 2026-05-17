import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://www.bep.gov.pt/pages/oferta/Oferta_Detalhes.aspx?CodOferta="
TOTAL = 20
ESTADO_FILE = "estado.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-PT,pt;q=0.9"
}


def carregar_estado():
    if os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("ultimo_cod", 147980)
    return 147980


def guardar_estado(cod):
