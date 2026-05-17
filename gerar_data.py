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

    # Mudamos obrigatoriamente para http:// (Porta 80) para contornar a firewall da BEP
    ip_bep = obter_ip_via_doh()
    url_inicial = f"http://{ip_bep}/default.aspx"
    
    headers = {
        "Host": "www.bep.gov.pt",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print(f"A aceder à página inicial da BEP via canal HTTP desprotegido...")
    try:
        resposta = requests.get(url_inicial, headers=headers, timeout=25, allow_redirects=False)
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            
            soup = BeautifulSoup(resposta.text, "lxml")
            linhas_tabela = soup.find_all("tr")
            novas_ofertas = []
            
            print(f"Página descarregada. A analisar {len(linhas_tabela)} linhas do HTML...")
            
            for linha in linhas_tabela:
                texto_linha = linha.text
                if "OE20" in texto_linha and ("Procedimento" in texto_linha or "Contrato" in texto_linha):
                    celulas = linha.find_all("td")
                    if len(celulas) >= 5:
                        codigo = celulas[0].text.strip()
                        carreira = celulas[2].text.strip()
                        organismo = celulas[3].text.strip()
                        data_limite = celulas[4].text.strip()
                        
                        link_elemento = linha.find("a") or celulas[0].find("a")
                        id_vaga = 0
                        
                        if link_elemento and link_elemento.get("href"):
                            href = link_elemento.get("href")
                            match_id = re.search(r"CodOferta=(\d+)", href)
                            if match_id:
                                id_vaga = int(match_id.group(1))
                        
                        if id_vaga == 0:
                            match_num = re.search(r"OE\d+/(\d+)", codigo)
                            id_vaga = int(match_num.group(1)) if match_num else abs(hash(codigo)) % 1000000
                        
                        url_vaga = f"https://bep.gov.pt{id_vaga}"
                        titulo_vaga = f"{codigo} - {carreira}"
                        descricao = f"Oferta de emprego público para {carreira} no organismo {organismo}. Prazo limite: {data_limite}."
                        
                        novas_ofertas.append({
                            "id": id_vaga,
                            "titulo": titulo_vaga,
                            "url": url_vaga,
                            "organismo": organismo,
                            "descricao": descricao,
                            "dados_estruturados": {
                                "@context": "https://schema.org",
                                "@type": "JobPosting",
                                "title": titulo_vaga,
                                "description": descricao,
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
                        print(f"-> Vaga capturada com sucesso: {codigo}")
            
            # Fusão de tabelas sem duplicar IDs
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            if lista_final:
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": lista_final[0]["id"], "total_acumulado": len(lista_final)}, f, indent=4)
                    
            print(f"Base de dados guardada. Total atual: {len(lista_final)}/200 vagas.")
        else:
            print(f"O servidor rejeitou o canal HTTP público. Estado: {resposta.status_code}")
    except Exception as e:
        print(f"Falha técnica na extração: {e}")

if __name__ == "__main__":
    extrair_e_acumular()
