import os
import json
import re
import requests

def extrair_e_acumular():
    ficheiro_dados = "data.json"
    ofertas_antigas = []
    
    # 1. Carrega o histórico existente do repositório GitHub
    if os.path.exists(ficheiro_dados):
        try:
            with open(ficheiro_dados, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, list):
                    ofertas_antigas = conteudo
                    print(f"Histórico carregado: {len(ofertas_antigas)} vagas.")
        except:
            pass

    url_bep_rss = "https://bep.gov.pt"
    
    # 2. Força o Internet Archive a registar uma cópia em tempo real (Sem erros de concatenação)
    url_gravar = f"https://archive.org{url_bep_rss}"
    print(f"A ordenar ao Internet Archive que grave uma cópia fresca da BEP...")
    try:
        requests.get(url_gravar, timeout=15)
    except Exception as e:
        print(f"Aviso na ordem de gravação (ignorado): {e}")

    # 3. Consulta a API para obter a última captura guardada
    url_api_archive = f"https://archive.org{url_bep_rss}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resposta_api = requests.get(url_api_archive, headers=headers, timeout=15)
        if resposta_api.status_code == 200:
            dados_api = resposta_api.json()
            snapshot = dados_api.get("archived_snapshots", {}).get("closest", {})
            
            if not snapshot or not snapshot.get("url"):
                # URL de contingência direta se a API falhar
                url_alvo = f"https://archive.org{url_bep_rss}"
            else:
                # O modificador 'im_' garante que o Archive envia o XML cru sem HTML decorativo
                url_alvo = snapshot.get("url").replace("/web/", "/web/20260000000000im_/")
                
            print(f"A descarregar o Feed RSS imune a bloqueios a partir de: {url_alvo}")
            resposta_xml = requests.get(url_alvo, headers=headers, timeout=25)
            
            if resposta_xml.status_code == 200:
                texto_cru = resposta_xml.text
                
                # Isola os blocos <item> textualmente para contornar falhas de sintaxe da BEP
                blocos_item = re.findall(r'<item>(.*?)</item>', texto_cru, re.DOTALL | re.IGNORECASE)
                print(f"Sucesso! Foram detetados {len(blocos_item)} anúncios de emprego no arquivo histórico.")
                
                novas_ofertas = []
                for bloco in blocos_item:
                    match_title = re.search(r'<title>(.*?)</title>', bloco, re.DOTALL | re.IGNORECASE)
                    match_link = re.search(r'<link>(.*?)</link>', bloco, re.DOTALL | re.IGNORECASE)
                    match_desc = re.search(r'<description>(.*?)</description>', bloco, re.DOTALL | re.IGNORECASE)
                    
                    titulo_completo = match_title.group(1).strip() if match_title else "Oferta de Emprego Público"
                    link_original = match_link.group(1).strip() if match_link else ""
                    descricao_completa = match_desc.group(1).strip() if match_desc else ""
                    
                    titulo_completo = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', titulo_completo, flags=re.DOTALL)
                    link_original = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', link_original, flags=re.DOTALL)
                    descricao_completa = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', descricao_completa, flags=re.DOTALL)
                    
                    # Limpa prefixos do Wayback se ficarem colados ao link original
                    link_original = re.sub(r'^https:\/\/web\.archive\.org\/web\/\d+im_\/', '', link_original)
                    
                    if link_original and "www." not in link_original:
                        link_original = link_original.replace("https://bep.gov.pt", "https://www.bep.gov.pt")
                    
                    match_id = re.search(r"CodOferta=(\d+)", link_original)
                    id_vaga = int(match_id.group(1)) if match_id else abs(hash(titulo_completo)) % 1000000
                    
                    partes = titulo_completo.split(" - ")
                    titulo_vaga = partes[0].strip() if len(partes) > 0 else titulo_completo
                    organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
                    
                    novas_ofertas.append({
                        "id": id_vaga,
                        "titulo": titulo_vaga,
                        "url": link_original if "bep.gov.pt" in link_original else f"https://bep.gov.pt{id_vaga}",
                        "organismo": organismo,
                        "descricao": descricao_completa if descricao_completa else f"Procedimento concursal para {titulo_vaga}.",
                        "dados_estruturados": {
                            "@context": "https://schema.org",
                            "@type": "JobPosting",
                            "title": titulo_vaga,
                            "description": descricao_completa if descricao_completa else "Consulte os termos no portal oficial.",
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
                    })
                    print(f"-> Vaga extraída: ID {id_vaga} - {titulo_vaga}")
                
                # Fusão incremental sem duplicar chaves
                vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
                for nova_vaga in novas_ofertas:
                    vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                    
                lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
                lista_final = lista_ordenada[:200]
                
                with open(ficheiro_dados, "w", encoding="utf-8") as f:
                    json.dump(lista_final, f, ensure_ascii=False, indent=4)
                    
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": lista_final[0]["id"] if lista_final else 0, "total_acumulado": len(lista_final)}, f, indent=4)
                    
                print(f"Sucesso! Ficheiro data.json sincronizado com {len(lista_final)}/200 vagas totais.")
            else:
                print(f"Erro ao descarregar do arquivo. Estado: {resposta_xml.status_code}")
        else:
            print(f"A API do Wayback Machine falhou. Estado: {resposta_api.status_code}")
    except Exception as e:
        print(f"Falha no processamento geral: {e}")

if __name__ == "__main__":
    extrair_e_acumular()
