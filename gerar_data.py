import os
import json
import re
import requests

def extrair_e_acumular():
    ficheiro_dados = "data.json"
    ofertas_antigas = []
    
    # 1. Carrega o histórico existente do repositório GitHub para acumular até 200
    if os.path.exists(ficheiro_dados):
        try:
            with open(ficheiro_dados, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, list):
                    ofertas_antigas = conteudo
                    print(f"Histórico carregado: {len(ofertas_antigas)} vagas.")
        except:
            pass

    # 2. Endpoint oficial de pesquisa da API do Diário da República Eletrónico
    url_dre_api = "https://diariodarepublica.pt"
    
    # Payload estruturado para pesquisar procedimentos concursais abertos na 2.ª Série do DRE
    payload = {
        "query": "procedimento concursal comum",
        "facets": {
            "serie": ["2"]
        },
        "page": 1,
        "perPage": 20,
        "sort": "pubDate,desc"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json"
    }
    
    print("A descarregar os concursos públicos oficiais em direto da API do DRE...")
    try:
        # Fazemos um pedido POST enviando os critérios de pesquisa
        resposta = requests.post(url_dre_api, json=payload, headers=headers, timeout=25)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            # A API do DRE devolve os resultados dentro da chave 'items'
            itens = dados.get("items", [])
            
            print(f"Ligação bem-sucedida! Detetadas {len(itens)} publicações recentes no DRE.")
            
            novas_ofertas = []
            for item in itens:
                titulo_cru = item.get("title", "Procedimento Concursal")
                sumario = item.get("summary", "")
                id_dre = item.get("id", 0)
                
                # Constrói o link público para o utilizador ler o diploma completo no DRE
                url_vaga = f"https://diariodarepublica.pt{id_dre}"
                
                # Extrai a entidade pública que emitiu o concurso
                organismo = item.get("issuingBody", "Administração Pública Portuguesa")
                
                # Tenta capturar o número do Aviso impresso no sumário para servir de referência
                match_aviso = re.search(r"Aviso\s+n\.\º\s+(\d+/\d+)", sumario, re.IGNORECASE)
                codigo_aviso = match_aviso.group(1) if match_aviso else f"DRE-{id_dre}"
                
                titulo_vaga = f"Aviso {codigo_aviso} - {titulo_cru[:65]}..."
                id_vaga = int(id_dre) if str(id_dre).isdigit() else abs(hash(codigo_aviso)) % 1000000

                novas_ofertas.append({
                    "id": id_vaga,
                    "titulo": titulo_vaga,
                    "url": url_vaga,
                    "organismo": organismo,
                    "descricao": sumario if sumario else "Consulte os requisitos e termos de candidatura no Diário da República.",
                    "dados_estruturados": {
                        "@context": "https://schema.org",
                        "@type": "JobPosting",
                        "title": titulo_vaga,
                        "description": sumario if sumario else "Detalhes de recrutamento oficial no DRE.",
                        "hiringOrganization": {
                            "@type": "Organization",
                            "name": organismo,
                            "sameAs": "https://diariodarepublica.pt"
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
                print(f"-> Vaga indexada do DRE: {codigo_aviso}")
            
            # 3. Fusão incremental (Merge) sem duplicados baseada no ID único do diploma
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                if nova_vaga["id"] > 0:
                    vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            # Ordena a coleção (mais recentes primeiro)
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            # Atualiza o data.json do site estático
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            with open("estado.json", "w", encoding="utf-8") as f:
                json.dump({"ultimo_id": lista_final[0]["id"] if lista_final else 0, "total_acumulado": len(lista_final)}, f, indent=4)
                
            print(f"Sucesso! Ficheiro data.json atualizado com {len(lista_final)}/200 vagas totais do DRE.")
        else:
            print(f"A API do DRE rejeitou o pedido POST. Código HTTP: {resposta.status_code}")
            
    except Exception as e:
        print(f"Erro no processamento dos dados da API do DRE: {e}")

if __name__ == "__main__":
    extrair_e_acumular()
