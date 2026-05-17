import os
import json
import re
import requests
from bs4 import BeautifulSoup

def obter_ip_via_doh():
    try:
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

    # Usamos o bypass de IP apontando para a página inicial default.aspx (onde está a tabela real)
    caminho_default = b'/default.aspx'.decode('utf-8')
    ip_bep = obter_ip_via_doh()
    url_alvo = f"https://{ip_bep}{caminho_default}"
    
    dominio_host = b'www.bep.gov.pt'.decode('utf-8')
    headers = {
        "Host": dominio_host,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9"
    }
    
    print("A ligar à tabela da página inicial da BEP via Rota de Contingência IP...")
    try:
        # verify=False contorna o alerta de certificado SSL na ligação direta por IP
        resposta = requests.get(url_alvo, headers=headers, timeout=25, verify=False)
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            
            # Processa o HTML da página inicial do portal
            soup = BeautifulSoup(resposta.text, "lxml")
            linhas = soup.find_all("tr")
            
            novas_ofertas = []
            print(f"Página descarregada. A analisar {len(linhas)} linhas estruturais do HTML...")
            
            for linha in linhas:
                texto_linha = linha.text
                # Filtra apenas as linhas da tabela que listam os concursos públicos vigentes
                if "OE20" in texto_linha and ("Procedimento" in texto_linha or "Contrato" in texto_linha):
                    celulas = linha.find_all("td")
                    if len(celulas) >= 5:
                        codigo = celulas[0].text.strip()
                        carreira = celulas[1].text.strip()
                        organismo = celulas[2].text.strip()
                        data_limite = celulas[4].text.strip()
                        
                        # Captura o link real de clique para extrair o CodOferta numérico
                        link_elemento = linha.find("a") or celulas[0].find("a")
                        id_vaga = 0
                        
                        if link_elemento and link_elemento.get("href"):
                            href = link_elemento.get("href")
                            match_id = re.search(r"CodOferta=(\d+)", href)
                            if match_id:
                                id_vaga = int(match_id.group(1))
                        
                        # Fallback se o ID estiver mascarado: gera um ID estável a partir do código OE
                        if id_vaga == 0:
                            match_num = re.search(r"OE\d+/(\d+)", codigo)
                            id_vaga = int(match_num.group(1)) if match_num else abs(hash(codigo)) % 1000000
                            
                        url_vaga = f"https://bep.gov.pt{id_vaga}"
                        titulo_vaga = f"{codigo} - {carreira}"
                        descricao = f"Procedimento concursal para a carreira de {carreira} no organismo {organismo}. Data limite de candidatura: {data_limite}."
                        
                        novas_ofertas.append({
                            "id": id_vaga,
                            "titulo": titulo_vaga,
                            "url": url_vaga,
                            "organismo": organismo,
                            "descricao": descricao,
                            "dados_estruturados": {
                                "@context": b'https://schema.org'.decode('utf-8'),
                                "@type": "JobPosting",
                                "title": titulo_vaga,
                                "description": descricao,
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
                        print(f"-> Vaga capturada com sucesso: {codigo}")
            
            # 3. Fusão incremental (Merge) sem duplicados baseada no ID único
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            # Ordena a lista pondo as mais recentes no topo
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            # Grava no data.json
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            if lista_final:
                id_mais_recente = lista_final[0]["id"]
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": id_mais_recente, "total_acumulado": len(lista_final)}, f, indent=4)
                    
            print(f"Base de dados finalizada. Total acumulado: {len(lista_final)}/200 vagas.")
        else:
            print(f"O servidor da BEP devolveu um erro de rede: {resposta.status_code}")
    except Exception as e:
        print(f"Erro técnico na extração direta do HTML: {e}")

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    extrair_e_acumular()
