import os
import json
import re
import requests
import xml.etree.ElementTree as ET

def extrair_vagas_rss():
    # URL corrigida com o 'www.' obrigatório exigido pelo DNS da BEP
    url_rss = "https://bep.gov.pt"
    ofertas_estruturadas = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("A estabelecer ligação segura com o DNS oficial (www.bep.gov.pt)...")
    try:
        # Efetuamos o pedido garantindo que não deixamos o requests redirecionar para domínios sem www
        resposta = requests.get(url_rss, headers=headers, timeout=20)
        
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            
            # Processa o XML do feed de dados
            root = ET.fromstring(resposta.text)
            items = root.findall(".//item")
            
            print(f"Sucesso! Encontradas {len(items)} ofertas de emprego públicas disponíveis.")
            
            # Limita às últimas 20 ofertas para a página ficar leve
            for item in items[:20]:
                titulo_completo = item.find("title").text.strip() if item.find("title") is not None else "Oferta de Emprego"
                link_original = item.find("link").text.strip() if item.find("link") is not None else ""
                descricao_completa = item.find("description").text.strip() if item.find("description") is not None else ""
                
                # Garante que os links gerados para os utilizadores e para o Google também contêm o www.
                if link_original and "www." not in link_original:
                    link_original = link_original.replace("https://bep.gov.pt", "https://www.bep.gov.pt")
                
                # Extrai o ID da vaga (ex: CodOferta=148573)
                match_id = re.search(r"CodOferta=(\d+)", link_original)
                id_vaga = int(match_id.group(1)) if match_id else 0
                
                # Separa o código do concurso do nome do ministério/organismo
                partes = titulo_completo.split(" - ")
                titulo_vaga = partes[0].strip()
                organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
                
                # MONTAGEM DOS DADOS ESTRUTURADOS (MANTEMOS O GOOGLE JOB-POSTING ATIVO!)
                dados_vaga = {
                    "id": id_vaga,
                    "titulo": titulo_vaga,
                    "url": link_original,
                    "organismo": organismo,
                    "descricao": descricao_completa if descricao_completa else "Consulte os detalhes de contratação na BEP.",
                    "dados_estruturados": {
                        "@context": "https://schema.org",
                        "@type": "JobPosting",
                        "title": titulo_vaga,
                        "description": descricao_completa if descricao_completa else "Consulte os detalhes na BEP.",
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
                ofertas_estruturadas.append(dados_vaga)
                
            # Guarda o último ID lido no estado.json para manter o histórico estável
            if ofertas_estruturadas:
                id_mais_recente = ofertas_estruturadas[0]["id"]
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": id_mais_recente}, f, indent=4)
                    
    except Exception as e:
        print(f"Erro ao processar os dados estruturados do XML: {e}")
        
    return ofertas_estruturadas

if __name__ == "__main__":
    lista_final = extrair_vagas_rss()
    
    # Grava a coleção final no ficheiro de dados do site
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
        
    print(f"Concluído. O ficheiro data.json foi atualizado com {len(lista_final)} registos válidos.")
