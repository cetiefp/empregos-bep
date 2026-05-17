import json
import re
import xml.etree.ElementTree as ET

def processar_feed_local():
    ofertas_estruturadas = []
    print("A processar o ficheiro feed.xml descarregado pelo GitHub...")
    
    try:
        # Lê o ficheiro XML guardado localmente na máquina do GitHub
        tree = ET.parse("feed.xml")
        root = tree.getroot()
        items = root.findall(".//item")
        
        print(f"Sucesso! Detetadas {len(items)} ofertas de emprego no XML.")
        
        for item in items[:20]:
            titulo_completo = item.find("title").text.strip() if item.find("title") is not None else "Oferta de Emprego"
            link_original = item.find("link").text.strip() if item.find("link") is not None else ""
            descricao_completa = item.find("description").text.strip() if item.find("description") is not None else ""
            
            if link_original and "www." not in link_original:
                link_original = link_original.replace("https://bep.gov.pt", "https://bep.gov.pt")
            
            match_id = re.search(r"CodOferta=(\d+)", link_original)
            id_vaga = int(match_id.group(1)) if match_id else 0
            
            partes = titulo_completo.split(" - ")
            titulo_vaga = partes[0].strip() if len(partes) > 0 else titulo_completo
            organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
            
            # MANTÉM OS DADOS ESTRUTURADOS ATIVOS PARA O GOOGLE
            dados_vaga = {
                "id": id_vaga,
                "titulo": titulo_vaga,
                "url": link_original,
                "organismo": organismo,
                "descricao": descricao_completa,
                "dados_estruturados": {
                    "@context": "https://schema.org",
                    "@type": "JobPosting",
                    "title": titulo_vaga,
                    "description": descricao_completa,
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
            
        if ofertas_estruturadas:
            id_topo = ofertas_estruturadas[0]["id"]
            with open("estado.json", "w", encoding="utf-8") as f:
                json.dump({"ultimo_id": id_topo}, f, indent=4)
                
    except Exception as e:
        print(f"Erro ao processar o XML: {e}")
        
    return ofertas_estruturadas

if __name__ == "__main__":
    lista_final = processar_feed_local()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
    print(f"Ficheiro data.json guardado com {len(lista_final)} vagas.")
