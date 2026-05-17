import os
import json
import re
import requests
import xml.etree.ElementTree as ET

def obter_ip_via_doh():
    print("A resolver o DNS de www.bep.gov.pt através da API segura da Google...")
    try:
        # Bypassa o DNS do GitHub fazendo uma consulta HTTPS direta à Google
        url_doh = "https://dns.google"
        resposta = requests.get(url_doh, timeout=10)
        if resposta.status_code == 200:
            dados = resposta.json()
            for resposta_dns in dados.get("Answer", []):
                if resposta_dns.get("type") == 1:  # Tipo A (IPv4)
                    ip = resposta_dns.get("data")
                    print(f"IP da BEP resolvido com sucesso: {ip}")
                    return ip
    except Exception as e:
        print(f"Falha na resolução DoH: {e}")
    # Fallback histórico caso a API falhe
    return "194.110.76.232"

def extrair_e_acumular():
    ficheiro_dados = "data.json"
    ofertas_antigas = []
    
    # 1. Carrega o histórico existente do repositório
    if os.path.exists(ficheiro_dados):
        try:
            with open(ficheiro_dados, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, list):
                    ofertas_antigas = conteudo
                    print(f"Histórico local carregado: {len(ofertas_antigas)} vagas.")
        except Exception as e:
            print(f"Erro ao ler data.json: {e}")

    # 2. Resolve o IP e descarrega o XML contornando o bloqueio de DNS
    ip_bep = obter_ip_via_doh()
    url_rss = f"https://{ip_bep}/pages/oferta/Oferta_RSS.aspx"
    
    headers = {
        "Host": "www.bep.gov.pt",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("A ligar diretamente ao IP do servidor da BEP...")
    try:
        # verify=False é necessário porque ligamos por IP e o certificado SSL espera o domínio
        resposta = requests.get(url_rss, headers=headers, timeout=25, verify=False)
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            
            root = ET.fromstring(resposta.text)
            items = root.findall(".//item")
            print(f"Feed descarregado. Detetadas {len(items)} vagas recentes.")
            
            novas_ofertas = []
            for item in items:
                titulo_completo = item.find("title").text.strip() if item.find("title") is not None else "Oferta de Emprego"
                link_original = item.find("link").text.strip() if item.find("link") is not None else ""
                descricao_completa = item.find("description").text.strip() if item.find("description") is not None else ""
                
                if link_original and "www." not in link_original:
                    link_original = link_original.replace("https://bep.gov.pt", "https://www.bep.gov.pt")
                
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
            
            # 3. Fusão incremental (Merge) removendo duplicados pelo ID único
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            # Ordena do ID mais recente para o mais antigo
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            
            # Trunca no limite histórico de 200 itens solicitado
            lista_final = lista_ordenada[:200]
            
            # Grava as alterações de volta no data.json
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            # Atualiza o estado para monitorização
            if lista_final:
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": lista_final[0]["id"], "total_acumulado": len(lista_final)}, f, indent=4)
                    
            print(f"Sucesso! Base de dados atualizada: {len(lista_final)}/200 vagas totais.")
        else:
            print(f"O servidor da BEP respondeu com erro: {resposta.status_code}")
            
    except Exception as e:
        print(f"Erro crítico durante a execução: {e}")

if __name__ == "__main__":
    # Desativa avisos visuais de SSL causados pela ligação direta por IP
    requests.packages.urllib3.disable_warnings()
    extrair_e_acumular()
