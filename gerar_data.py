import os
import json
import time
import requests
from bs4 import BeautifulSoup

def obter_id_partida():
    id_base_padrao = 148573 # O ID real conhecido
    
    if os.path.exists("estado.json"):
        try:
            with open("estado.json", "r", encoding="utf-8") as f:
                dados_estado = json.load(f)
                if isinstance(dados_estado, dict) and "ultimo_id" in dados_estado:
                    id_guardado = int(dados_estado["ultimo_id"])
                    # Olha 15 IDs à frente para tentar capturar novos anúncios
                    print(f"Ponto de partida recuperado do estado.json: {id_guardado}. Margem aplicada para procurar novos IDs.")
                    return id_guardado + 15
        except Exception as e:
            print(f"Erro ao ler estado.json: {e}")
            
    print(f"A iniciar do ID padrão estável: {id_base_padrao}")
    return id_base_padrao

def extrair_ultimas_ofertas(quantidade=20):
    id_atual = obter_id_partida()
    ofertas_encontradas = []
    
    max_tentativas = 100
    tentativas = 0
    ultimo_id_sucesso = None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9"
    }
    
    print(f"A executar varredura a partir do ID {id_atual}...")
    
    while len(ofertas_encontradas) < quantidade and tentativas < max_tentativas:
        url = f"https://www.bep.gov.pt/pages/oferta/Oferta_Detalhes.aspx?CodOferta={id_atual}"
        try:
            resposta = requests.get(url, headers=headers, timeout=12)
            
            # Pequeno atraso de 2 segundos para respeitar o servidor e evitar o bloqueio (anti-scraping)
            time.sleep(2)
            
            if resposta.status_code == 200 and "ctl00_FormId_lblCodigo" in resposta.text:
                soup = BeautifulSoup(resposta.text, 'html.parser')
                elem_codigo = soup.find(id="ctl00_FormId_lblCodigo")
                
                if elem_codigo and elem_codigo.text.strip():
                    titulo = elem_codigo.text.strip()
                    
                    if ultimo_id_sucesso is None:
                        ultimo_id_sucesso = id_atual
                        
                    elem_org = soup.find(id="ctl00_FormId_lblOrganismo")
                    organismo = elem_org.text.strip() if elem_org else "Administração Pública"
                    
                    elem_desc = soup.find(id="ctl00_FormId_lblCaracterizacao")
                    descricao = elem_desc.text.strip() if elem_desc else "Consulte os detalhes na BEP."

                    dados_vaga = {
                        "id": id_atual,
                        "titulo": titulo,
                        "url": url,
                        "organismo": organismo,
                        "descricao": descricao,
                        "dados_estruturados": {
                            "@context": "https://schema.org",
                            "@type": "JobPosting",
                            "title": titulo,
                            "description": descricao,
                            "hiringOrganization": {
                                "@type": "Organization",
                                "name": organismo,
                                "sameAs": "https://www.bep.gov.pt"
                            },
                            "jobLocation": {
                                "@type": "Place",
                                "address": {
                                    "@type": "PostalAddress",
                                    "addressCountry": "PT"
                                }
                            }
                        }
                    }
                    ofertas_encontradas.append(dados_vaga)
                    print(f"Encontrado ID válido: {id_atual}")
        except Exception as e:
            print(f"Erro no ID {id_atual}: {e}")
            
        id_atual -= 1
        tentativas += 1

    # Atualiza o ponto de partida incremental no estado.json para a próxima execução
    if ultimo_id_sucesso:
        try:
            with open("estado.json", "w", encoding="utf-8") as f:
                json.dump({"ultimo_id": ultimo_id_sucesso}, f, indent=4)
            print(f"Estado sincronizado com o ID mais recente: {ultimo_id_sucesso}")
        except Exception as e:
            print(f"Falha ao gravar estado.json: {e}")

    return ofertas_encontradas

if __name__ == "__main__":
    lista_final = extrair_ultimas_ofertas(20)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
    print("Ficheiro data.json atualizado.")
