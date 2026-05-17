import os
import json
import re
import requests
from bs4 import BeautifulSoup

def extrair_ultimas_ofertas(quantidade=20):
    # Definimos um ID alto de partida para fazer a contagem decrescente
    id_atual = 148000 
    ofertas_encontradas = []
    tentativas = 0
    
    print("A iniciar a recolha de ofertas na BEP...")
    
    # Executa até encontrar 20 ofertas válidas ou atingir o limite de segurança
    while len(ofertas_encontradas) < quantidade and tentativas < 150:
        url = f"https://bep.gov.pt{id_atual}"
        try:
            resposta = requests.get(url, timeout=10)
            if resposta.status_code == 200 and "Código da Oferta" in resposta.text:
                soup = BeautifulSoup(resposta.text, 'html.parser')
                
                # Extração do Código/Título da Oferta (Ex: OE2026...)
                elem_codigo = soup.find(id="ctl00_FormId_lblCodigo")
                titulo = elem_codigo.text.strip() if elem_codigo else f"Oferta BEP Código {id_atual}"
                
                # Extração do Organismo Emissor
                elem_org = soup.find(id="ctl00_FormId_lblOrganismo")
                organismo = elem_org.text.strip() if elem_org else "Administração Pública Portuguesa"
                
                # Extração da Caracterização/Descrição do Posto de Trabalho
                elem_desc = soup.find(id="ctl00_FormId_lblCaracterizacao")
                descricao = elem_desc.text.strip() if elem_desc else "Consulte os detalhes e requisitos completos no portal oficial da BEP."

                # Construção do bloco de dados estruturados (Schema.org / JobPosting) para a Google
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
                        "datePosted": "2026-05-17",
                        "validThrough": "2026-06-17",
                        "employmentType": "FULL_TIME",
                        "hiringOrganization": {
                            "@type": "Organization",
                            "name": organismo,
                            "sameAs": "https://bep.gov.pt"
                        },
                        "jobLocation": {
                            "@type": "Place",
                            "address": {
                                "@type": "PostalAddress",
                                "addressCountry": "PT",
                                "addressRegion": "Portugal"
                            }
                        }
                    }
                }
                ofertas_encontradas.append(dados_vaga)
                print(f"Sucesso: Oferta {id_atual} adicionada.")
        except Exception as erro:
            print(f"Erro ao processar o ID {id_atual}: {erro}")
        
        id_atual -= 1
        tentativas += 1
        
    return ofertas_encontradas

if __name__ == "__main__":
    lista_final = extrair_ultimas_ofertas(20)
    
    # Grava os resultados exatamente no ficheiro data.json esperado
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
        
    print(f"Ficheiro data.json atualizado com {len(lista_final)} ofertas.")
