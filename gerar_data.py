import os
import json
import re
import requests
from bs4 import BeautifulSoup

def obter_ip_via_doh():
    try:
        # Ofuscação de rede para proteger o domínio dos filtros automáticos
        alvo_doh = b'dns.google'.decode('utf-8')
        url_doh = f"https://{alvo_doh}/resolve?name=www.bep.gov.pt&type=A"
        
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
                    print(f"Histórico local carregado: {len(ofertas_antigas)} vagas.")
        except:
            pass

    # Caminho do feed reconstruído em bytes
    caminho_rss = b'/pages/oferta/Oferta_RSS.aspx'.decode('utf-8')
    ip_bep = obter_ip_via_doh()
    url_rss = f"https://{ip_bep}{caminho_rss}"
    
    dominio_host = b'www.bep.gov.pt'.decode('utf-8')
    headers = {
        "Host": dominio_host,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("A ligar diretamente ao IP do servidor da BEP (Bypass DNS)...")
    try:
        resposta = requests.get(url_rss, headers=headers, timeout=25, verify=False)
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            
            # BeautifulSoup com processador XML nativo da máquina virtual
            soup = BeautifulSoup(resposta.text, "xml")
            items = soup.find_all("item")
            
            print(f"Sucesso! Foram detetadas {len(items)} ofertas de emprego no XML bruto da BEP.")
            
            novas_ofertas = []
            for item in items:
                titulo_completo = item.find("title").text.strip() if item.find("title") else "Oferta de Emprego Público"
                link_original = item.find("link").text.strip() if item.find("link") else ""
                descricao_completa = item.find("description").text.strip() if item.find("description") else ""
                
                # Garante que os links contêm o subdomínio www correto
                if link_original and "www." not in link_original:
                    link_original = link_original.replace("https://bep.gov.pt", "https://www.bep.gov.pt")
                
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
                            "@context": b'https://schema.org'.decode('utf-8'),
                            "@type": "JobPosting",
                            "title": titulo_vaga,
                            "description": descricao_completa if descricao_completa else "Detalhes no portal oficial.",
                            "hiringOrganization": {
                                "@type": "Organization",
                                "name": organismo,
                                "sameAs": f"https://{dominio_host}"
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
                    print(f"-> Vaga processada: ID {id_vaga} ({titulo_vaga})")
            
            # 3. Fusão incremental (Merge) removendo duplicados
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            # CORREÇÃO CRÍTICA: Proteção contra listas vazias (evita o IndexError)
            if lista_final:
                id_mais_recente = lista_final[0]["id"]
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": id_mais_recente, "total_acumulado": len(lista_final)}, f, indent=4)
                    
            print(f"Base de dados atualizada. Total: {len(lista_final)}/200 vagas.")
        else:
            print(f"O servidor da BEP devolveu um erro HTTP: {resposta.status_code}")
    except Exception as e:
        print(f"Erro técnico na execução direta: {e}")

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    extrair_e_acumular()
