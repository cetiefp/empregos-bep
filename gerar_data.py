import os
import json
import re
import requests
from bs4 import BeautifulSoup

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
    
    if os.path.exists(ficheiro_dados):
        try:
            with open(ficheiro_dados, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, list):
                    ofertas_antigas = conteudo
        except:
            pass

    ip_bep = obter_ip_via_doh()
    url_rss = f"https://{ip_bep}/pages/oferta/Oferta_RSS.aspx"
    
    headers = {
        "Host": "www.bep.gov.pt",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("A descarregar feed da BEP...")
    try:
        resposta = requests.get(url_rss, headers=headers, timeout=25, verify=False)
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            
            # --- COMO VER O XML ORIGINAL ---
            # Imprime os primeiros 1000 caracteres no log do GitHub Actions para auditoria visual
            print("\n=== CONTEÚDO DO XML ORIGINAL DESCARREGADO (PREVIEW) ===")
            print(resposta.text[:1000])
            print("========================================================\n")
            
            # Usamos o leitor "xml" (em vez de html.parser) para capturar as tags nativas corretamente
            soup = BeautifulSoup(resposta.text, "xml")
            items = soup.find_all("item")
            
            print(f"Sucesso! Encontradas {len(items)} ofertas no XML original da BEP.")
            
            novas_ofertas = []
            for item in items:
                titulo_completo = item.find("title").text.strip() if item.find("title") else "Oferta de Emprego"
                link_original = item.find("link").text.strip() if item.find("link") else ""
                descricao_completa = item.find("description").text.strip() if item.find("description") else ""
                
                if link_original and "www." not in link_original:
                    link_original = link_original.replace("https://bep.gov.pt", "https://bep.gov.pt")
                
                match_id = re.search(r"CodOferta=(\d+)", link_original)
                id_vaga = int(match_id.group(1)) if match_id else 0
                
                partes = titulo_completo.split(" - ")
                titulo_vaga = partes[0].strip() if len(partes) > 0 else titulo_completo
                organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
                
                novas_ofertas.append({
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
                })
            
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                if nova_vaga["id"] > 0:
                    vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            if lista_final:
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": lista_final[0]["id"], "total_acumulado": len(lista_final)}, f, indent=4)
                    
            print(f"Base de dados atualizada: {len(lista_final)}/200 vagas totais.")
    except Exception as e:
        print(f"Erro na execução: {e}")

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    extrair_e_acumular()
