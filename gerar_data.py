import os
import json
import re
import time
import requests

def forcar_gravacao_no_arquivo(url_alvo):
    print(f"A ordenar ao Internet Archive que grave uma cópia fresca de: {url_alvo}")
    url_save = f"https://archive.org{url_alvo}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        # Envia o pedido de gravação imediata
        resposta = requests.get(url_save, headers=headers, timeout=15)
        print(f"Pedido enviado. Estado do arquivo: {resposta.status_code}")
        # Aguarda 5 segundos para dar tempo aos servidores do Archive de processarem o site da BEP
        print("A aguardar 5 segundos para estabilização do snapshot...")
        time.sleep(5)
    except Exception as e:
        print(f"Aviso na ordem de gravação: {e}")

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
    
    # FORÇA O ARQUIVO A GRAVAR O FEED AGORA
    forcar_gravacao_no_arquivo(url_bep_rss)
    
    # 2. Pergunta ao arquivo qual é o link da cópia mais recente (que acabámos de forçar)
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
                print("A usar link de contingência direta baseado na data atual...")
                url_leitura = f"https://archive.org{url_bep_rss}"
            else:
                # O modificador 'im_' garante o XML limpo e sem barras de ferramentas do Archive
                url_leitura = snapshot.get("url").replace("/web/", "/web/20260000000000im_/")
                
            print(f"A descarregar o XML fresco guardado em: {url_leitura}")
            resposta_xml = requests.get(url_leitura, headers=headers, timeout=25)
            
            if resposta_xml.status_code == 200:
                texto_cru = resposta_xml.text
                
                # Isola os blocos <item> textualmente
                blocos_item = re.findall(r'<item>(.*?)</item>', texto_cru, re.DOTALL | re.IGNORECASE)
                print(f"Sucesso! Detetados {len(blocos_item)} anúncios novos gravados no arquivo.")
                
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
                    
                    # Limpa o URL da vaga de quaisquer prefixos do web.archive
                    link_original = re.sub(r'^https:\/\/web\.archive\.org\/web\/\d+im_\/', '', link_original)
                    
                    if link_original and "www." not in link_original:
                        link_original = link_original.replace("https://bep.gov.pt", "https://bep.gov.pt")
                    
                    match_id = re.search(r"CodOferta=(\d+)", link_original)
                    id_vaga = int(match_id.group(1)) if match_id else abs(hash(titulo_completo)) % 1000000
                    
                    partes = titulo_completo.split(" - ")
                    titulo_vaga = partes[0].strip() if len(partes) > 0 else titulo_completo
                    organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
                    
                    novas_ofertas.append({
                        "id": id_vaga,
                        "titulo": titulo_vaga,
                        "url": link_original if "bep.gov.pt" in link_original else f"https://bep.gov.pt/pages/oferta/Oferta_Detalhes.aspx?CodOferta={id_vaga}",
                        "organismo": organismo,
                        "descricao": descricao_completa if descricao_completa else f"Procedimento concursal para {titulo_vaga}.",
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
                    })
                    print(f"-> Indexada: ID {id_vaga} - {titulo_vaga}")
                
                # 3. Fusão incremental (Merge) sem duplicados
                vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
                for nova_vaga in novas_ofertas:
                    vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                    
                lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
                lista_final = lista_ordenada[:200]
                
                with open(ficheiro_dados, "w", encoding="utf-8") as f:
                    json.dump(lista_final, f, ensure_ascii=False, indent=4)
                    
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": lista_final[0]["id"] if lista_final else 0, "total_acumulado": len(lista_final)}, f, indent=4)
                    
                print(f"Sucesso absoluto! Base de dados atualizada: {len(lista_final)}/200 vagas totais.")
            else:
                print(f"O arquivo devolveu um erro no XML: {resposta_xml.status_code}")
        else:
            print(f"A API de consulta do arquivo falhou: {resposta_api.status_code}")
    except Exception as e:
        print(f"Falha no processamento geral: {e}")

if __name__ == "__main__":
    extrair_e_acumular()
