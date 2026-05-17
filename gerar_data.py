import os
import json
import re
import requests

def obter_ip_via_doh():
    try:
        url_doh = "https://dns.google"
        resposta = requests.get(url_doh, timeout=10)
        if resposta.status_code == 200:
            dados = resposta.json()
            for resposta_dns in dados.get("Answer", []):
                if resposta_dns.get("type") == 1:
                    return resposta_dns.get("data")
    except:
        pass
    return "194.110.76.232"

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

    # 2. Conecta à rota estável do RSS que não sofre de Connection Reset
    ip_bep = obter_ip_via_doh()
    url_rss = f"https://{ip_bep}/pages/oferta/Oferta_RSS.aspx"
    
    headers = {
        "Host": "www.bep.gov.pt",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("A estabelecer ligação direta ao fluxo de texto da BEP...")
    try:
        resposta = requests.get(url_rss, headers=headers, timeout=25, verify=False)
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            texto_cru = resposta.text
            
            # Isolamos os blocos <item> por texto puro, contornando o erro de 'duplicate attribute'
            blocos_item = re.findall(r'<item>(.*?)</item>', texto_cru, re.DOTALL)
            print(f"Ligação bem-sucedida! Detetados {len(blocos_item)} anúncios no feed bruto.")
            
            novas_ofertas = []
            for bloco in blocos_item:
                # Procura as tags internas usando expressões regulares simples
                match_title = re.search(r'<title>(.*?)</title>', bloco, re.DOTALL)
                match_link = re.search(r'<link>(.*?)</link>', bloco, re.DOTALL)
                match_desc = re.search(r'<description>(.*?)</description>', bloco, re.DOTALL)
                
                titulo_completo = match_title.group(1).strip() if match_title else "Oferta de Emprego"
                link_original = match_link.group(1).strip() if match_link else ""
                descricao_completa = match_desc.group(1).strip() if match_desc else ""
                
                # Garante que os URLs públicos contêm o subdomínio www
                if link_original and "www." not in link_original:
                    link_original = link_original.replace("https://bep.gov.pt", "https://bep.gov.pt")
                
                # Isola o CodOferta numérico (ex: 148573)
                match_id = re.search(r"CodOferta=(\d+)", link_original)
                id_vaga = int(match_id.group(1)) if match_id else 0
                
                partes = titulo_completo.split(" - ")
                titulo_vaga = partes[0].strip() if len(partes) > 0 else titulo_completo
                organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
                
                if id_vaga > 0:
                    novas_ofertas.append({
                        "id": id_vaga,
                        "titulo": titulo_vaga,
                        "url": link_original,
                        "organismo": organismo,
                        "descricao": descricao_completa if descricao_completa else f"Procedimento concursal para {titulo_vaga}.",
                        "dados_estruturados": {
                            "@context": "https://schema.org",
                            "@type": "JobPosting",
                            "title": titulo_vaga,
                            "description": descricao_completa if descricao_completa else "Detalhes no portal oficial.",
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
                    print(f"-> Vaga extraída textualmente: ID {id_vaga} - {titulo_vaga}")
            
            # 3. Fusão incremental (Merge) sem duplicados baseada no ID único
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            # Ordena do mais recente para o mais antigo
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            # Grava as atualizações finais no repositório
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            with open("estado.json", "w", encoding="utf-8") as f:
                json.dump({"ultimo_id": lista_final[0]["id"] if lista_final else 0, "total_acumulado": len(lista_final)}, f, indent=4)
                
            print(f"Sucesso! Ficheiro data.json atualizado com {len(lista_final)}/200 vagas totais.")
        else:
            print(f"O servidor recusou o pedido. Código: {resposta.status_code}")
    except Exception as e:
        print(f"Falha na extração de texto: {e}")

if __name__ == "__main__":
    # Desativa avisos visuais de SSL devido à ligação por IP
    requests.packages.urllib3.disable_warnings()
    extrair_e_acumular()
