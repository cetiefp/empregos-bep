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

    # 2. Conecta ao Feed RSS público e aberto da DGAEP (Não exige início de sessão)
    url_rss_dgaep = "https://dgaep.gov.pt"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("A descarregar o fluxo de anúncios públicos da DGAEP...")
    try:
        resposta = requests.get(url_rss_dgaep, headers=headers, timeout=25)
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            texto_cru = resposta.text
            
            # Isola os blocos <item> do feed por texto bruto
            blocos_item = re.findall(r'<item>(.*?)</item>', texto_cru, re.DOTALL | re.IGNORECASE)
            print(f"Ligação bem-sucedida! Detetados {len(blocos_item)} anúncios no feed aberto.")
            
            novas_ofertas = []
            for bloco in blocos_item:
                match_title = re.search(r'<title>(.*?)</title>', bloco, re.DOTALL | re.IGNORECASE)
                match_link = re.search(r'<link>(.*?)</link>', bloco, re.DOTALL | re.IGNORECASE)
                match_desc = re.search(r'<description>(.*?)</description>', bloco, re.DOTALL | re.IGNORECASE)
                
                titulo_completo = match_title.group(1).strip() if match_title else "Oferta de Emprego Público"
                link_original = match_link.group(1).strip() if match_link else ""
                descricao_completa = match_desc.group(1).strip() if match_desc else ""
                
                # Remove CDATA se presente
                titulo_completo = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', titulo_completo, flags=re.DOTALL)
                link_original = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', link_original, flags=re.DOTALL)
                descricao_completa = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', descricao_completa, flags=re.DOTALL)
                
                # Se o anúncio contiver ou apontar para a BEP, extraímos o ID
                id_vaga = 0
                match_id = re.search(r"CodOferta=(\d+)", link_original)
                if match_id:
                    id_vaga = int(match_id.group(1))
                else:
                    # Se o link for da DGAEP, extraímos o ID interno do artigo para servir de âncora única
                    match_id_alt = re.search(r"CE=(\d+)", link_original) or re.search(r"id=(\d+)", link_original)
                    if match_id_alt:
                        id_vaga = int(match_id_alt.group(1))
                    else:
                        # Fallback seguro baseado na assinatura do título para não perder a vaga
                        id_vaga = abs(hash(titulo_completo)) % 1000000
                
                # Reconstrói o URL canónico da BEP para garantir que o utilizador vai para o sítio certo
                url_bep_final = f"https://bep.gov.pt{id_vaga}" if match_id else link_original
                
                partes = titulo_completo.split(" - ")
                titulo_vaga = partes[0].strip() if len(partes) > 0 else titulo_completo
                organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
                
                if id_vaga > 0:
                    novas_ofertas.append({
                        "id": id_vaga,
                        "titulo": titulo_vaga,
                        "url": url_bep_final,
                        "organismo": organismo,
                        "descricao": descricao_completa if descricao_completa else f"Procedimento concursal publicado para {titulo_vaga}.",
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
            
            # 3. Fusão incremental (Merge) sem duplicados
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            # Grava os resultados finais
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            with open("estado.json", "w", encoding="utf-8") as f:
                json.dump({"ultimo_id": lista_final[0]["id"] if lista_final else 0, "total_acumulado": len(lista_final)}, f, indent=4)
                
            print(f"Sucesso! Ficheiro data.json atualizado com {len(lista_final)}/200 vagas totais.")
        else:
            print(f"O servidor da DGAEP respondeu com erro. Código: {resposta.status_code}")
    except Exception as e:
        print(f"Falha na extração de dados do feed: {e}")

if __name__ == "__main__":
    extrair_e_acumular()
