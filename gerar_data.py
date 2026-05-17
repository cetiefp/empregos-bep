import os
import json
import re
import requests
import xml.etree.ElementTree as ET

def extrair_vagas_rss():
    # URL oficial do Feed de Ofertas da Bolsa de Emprego Público (BEP)
    url_rss = "https://bep.gov.pt"
    ofertas_estruturadas = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("A estabelecer ligação com o Feed oficial da BEP...")
    try:
        resposta = requests.get(url_rss, headers=headers, timeout=20)
        if resposta.status_code == 200:
            # Força a leitura correta dos caracteres e acentos em português
            resposta.encoding = 'utf-8'
            
            # Processa a árvore de elementos XML do feed
            root = ET.fromstring(resposta.text)
            items = root.findall(".//item")
            
            print(f"Sucesso. Encontradas {len(items)} ofertas de emprego no feed.")
            
            # Seleciona as últimas 20 ofertas do topo do feed
            for item in items[:20]:
                titulo_completo = item.find("title").text.strip() if item.find("title") is not None else "Oferta de Emprego"
                link_original = item.find("link").text.strip() if item.find("link") is not None else ""
                descricao_completa = item.find("description").text.strip() if item.find("description") is not None else ""
                
                # Extrai o número do CodOferta contido no link (ex: CodOferta=148573)
                match_id = re.search(r"CodOferta=(\d+)", link_original)
                id_vaga = int(match_id.group(1)) if match_id else 0
                
                # O feed da BEP costuma trazer "Código da Oferta - Organismo". Vamos separar:
                partes = titulo_completo.split(" - ")
                titulo_vaga = partes[0].strip()
                organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
                
                # Monta os Dados Estruturados (Schema.org / JobPosting) validados pelo Google
                dados_vaga = {
                    "id": id_vaga,
                    "titulo": titulo_vaga,
                    "url": link_original,
                    "organismo": organismo,
                    "descricao": descricao_completa if descricao_completa else "Consulte os termos e requisitos no portal oficial da BEP.",
                    "dados_estruturados": {
                        "@context": "https://schema.org",
                        "@type": "JobPosting",
                        "title": titulo_vaga,
                        "description": descricao_completa if descricao_completa else "Detalhes e candidaturas no portal oficial.",
                        "hiringOrganization": {
                            "@type": "Organization",
                            "name": organismo,
                            "sameAs": "https://bep.gov.pt"
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
                ofertas_estruturadas.append(dados_vaga)
                
            # Mantém o histórico atualizado no estado.json guardando o ID mais recente
            if ofertas_estruturadas:
                id_topo = ofertas_estruturadas[0]["id"]
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": id_topo}, f, indent=4)
                    
    except Exception as e:
        print(f"Erro ao processar o feed XML: {e}")
        
    return ofertas_estruturadas

if __name__ == "__main__":
    lista_final = extrair_vagas_rss()
    
    # Substitui os parênteses vazios pelos dados prontos
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
        
    print(f"Ficheiro data.json guardado com {len(lista_final)} registos.")
