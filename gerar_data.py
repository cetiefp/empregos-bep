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

    # 2. API pública do Diário da República que lista anúncios de Emprego Público em tempo real
    url_dre = "https://diariodarepublica.pt"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("A descarregar as publicações de emprego público em direto do DRE...")
    try:
        resposta = requests.get(url_dre, headers=headers, timeout=25)
        if resposta.status_code == 200:
            dados = resposta.json()
            itens = dados.get("results", [])
            
            print(f"Ligação bem-sucedida! Detetadas {len(itens)} publicações no DRE.")
            
            novas_ofertas = []
            for item in itens:
                titulo_cru = item.get("title", "Procedimento Concursal")
                sumario = item.get("summary", "")
                link_dre = item.get("url", "https://diariodarepublica.pt")
                id_dre = item.get("id", 0)
                
                # Extrai o nome da entidade pública do campo de emissor
                organismo = item.get("issuer", {}).get("name", "Administração Pública Portuguesa")
                
                # Tentamos pescar o CodOferta ou número do aviso para usar como âncora
                match_aviso = re.search(r"Aviso\s+n\.\º\s+(\d+/\d+)", sumario, re.IGNORECASE)
                codigo_aviso = match_aviso.group(1) if match_aviso else f"DRE-{id_dre}"
                
                # Monta a rota final de redirecionamento estável
                titulo_vaga = f"Aviso {codigo_aviso} - {titulo_cru[:60]}..."
                
                # Se não houver ID numérico nativo, geramos um ID estável a partir do identificador do DRE
                id_vaga = int(id_dre) if str(id_dre).isdigit() else abs(hash(codigo_aviso)) % 1000000
                
                # URL oficial do DRE que contém o despacho e o anexo para candidatura
                url_vaga = link_dre

                novas_ofertas.append({
                    "id": id_vaga,
                    "titulo": titulo_vaga,
                    "url": url_vaga,
                    "organismo": organismo,
                    "descricao": sumario if sumario else "Consulte os termos de abertura e prazos no despacho publicado no DRE.",
                    "dados_estruturados": {
                        "@context": "https://schema.org",
                        "@type": "JobPosting",
                        "title": titulo_vaga,
                        "description": sumario if sumario else "Detalhes de recrutamento no Diário da República.",
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
            
            # 3. Fusão incremental (Merge) sem duplicados baseada no ID único
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                if nova_vaga["id"] > 0:
                    vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            # Ordena do mais recente para o mais antigo
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            # Grava no data.json
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            with open("estado.json", "w", encoding="utf-8") as f:
                json.dump({"ultimo_id": lista_final["id"] if lista_final else 0, "total_acumulado": len(lista_final)}, f, indent=4)
                
            print(f"Sucesso! Ficheiro data.json atualizado com {len(lista_final)}/200 vagas totais.")
        else:
            print(f"O servidor do DRE respondeu com erro. Código: {resposta.status_code}")
    except Exception as e:
        print(f"Falha técnica na extração da API: {e}")

if __name__ == "__main__":
    extrair_e_acumular()
