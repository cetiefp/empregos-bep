import os
import json
import re
import requests
import xml.etree.ElementTree as ET

def extrair_vagas_rss():
    # URL único e absoluto da API proxy, evitando qualquer erro de concatenação em Python
    url_completo_proxy = "https://allorigins.win"
    ofertas_estruturadas = []
    
    print("A descarregar o Feed através da rota corrigida da API AllOrigins...")
    try:
        resposta = requests.get(url_completo_proxy, timeout=25)
        
        if resposta.status_code == 200:
            dados_json = resposta.json()
            # A API devolve o XML original dentro da chave "contents"
            xml_texto = dados_json.get("contents", "")
            
            if not xml_texto:
                print("Erro: A API respondeu mas o conteúdo do XML está vazio.")
                return []
                
            # Processa a árvore de elementos XML
            root = ET.fromstring(xml_texto)
            items = root.findall(".//item")
            
            print(f"Sucesso total! Foram capturadas {len(items)} ofertas de emprego em tempo real.")
            
            # Seleciona as últimas 20 ofertas para otimização de SEO
            for item in items[:20]:
                titulo_completo = item.find("title").text.strip() if item.find("title") is not None else "Oferta de Emprego"
                link_original = item.find("link").text.strip() if item.find("link") is not None else ""
                descricao_completa = item.find("description").text.strip() if item.find("description") is not None else ""
                
                # Garante que os links contêm o subdomínio correto para o utilizador
                if link_original and "www." not in link_original:
                    link_original = link_original.replace("https://bep.gov.pt", "https://bep.gov.pt")
                
                # Extrai o ID numérico da oferta (ex: 148573)
                match_id = re.search(r"CodOferta=(\d+)", link_original)
                id_vaga = int(match_id.group(1)) if match_id else 0
                
                # Divide a string para separar o código do concurso do nome da entidade pública
                partes = titulo_completo.split(" - ")
                titulo_vaga = partes[0].strip() if len(partes) > 0 else titulo_completo
                organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
                
                # MONTAGEM DOS DADOS ESTRUTURADOS PARA SEO (Google JobPosting)
                dados_vaga = {
                    "id": id_vaga,
                    "titulo": titulo_vaga,
                    "url": link_original,
                    "organismo": organismo,
                    "descricao": descricao_completa if descricao_completa else "Consulte os detalhes de admissão no portal oficial da BEP.",
                    "dados_estruturados": {
                        "@context": "https://schema.org",
                        "@type": "JobPosting",
                        "title": titulo_vaga,
                        "description": descricao_completa if descricao_completa else "Consulte os requisitos na plataforma BEP.",
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
                
            # Atualiza o estado.json com o ID do topo do feed para manter o histórico estável
            if ofertas_estruturadas:
                id_topo = ofertas_estruturadas[0]["id"]
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": id_topo}, f, indent=4)
        else:
            print(f"A API do proxy devolveu o estado de erro: {resposta.status_code}")
                    
    except Exception as e:
        print(f"Erro ao converter a árvore de dados XML: {e}")
        
    return ofertas_estruturadas

if __name__ == "__main__":
    lista_final = extrair_vagas_rss()
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
        
    print(f"Concluído. Ficheiro data.json guardado com {len(lista_final)} vagas.")
