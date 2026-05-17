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
    
    # 1. Carrega o histórico de ofertas que já temos no repositório
    if os.path.exists(ficheiro_dados):
        try:
            with open(ficheiro_dados, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, list):
                    ofertas_antigas = conteudo
        except:
            pass

    # 2. Liga-se diretamente à página inicial (default.aspx) da BEP usando o IP resolvido
    ip_bep = obter_ip_via_doh()
    url_inicial = f"https://{ip_bep}/default.aspx"
    
    headers = {
        "Host": "www.bep.gov.pt",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("A aceder à página inicial da BEP...")
    try:
        resposta = requests.get(url_inicial, headers=headers, timeout=25, verify=False)
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            
            # Analisa o HTML da página inicial do portal
            soup = BeautifulSoup(resposta.text, "lxml")
            
            # Localiza a tabela ou grelha de dados das últimas ofertas
            linhas_tabela = soup.find_all("tr")
            novas_ofertas = []
            
            print(f"A escanear elementos estruturais da página... Encontradas {len(linhas_tabela)} linhas.")
            
            for linha in linhas_tabela:
                texto_linha = linha.text
                # Procura linhas que contenham o padrão de Código da BEP (ex: OE2026...)
                if "OE20" in texto_linha and "Procedimento" in texto_linha or "Contrato" in texto_linha:
                    celulas = linha.find_all("td")
                    if len(celulas) >= 5:
                        codigo = celulas[0].text.strip()
                        carreira = celulas[2].text.strip()
                        organismo = celulas[3].text.strip()
                        data_limite = celulas[4].text.strip()
                        
                        # Tenta extrair o link oculto no elemento de clique da linha
                        link_elemento = linha.find("a") or celulas[0].find("a")
                        url_vaga = "https://bep.gov.pt"
                        id_vaga = 0
                        
                        if link_element and link_elemento.get("href"):
                            href = link_elemento.get("href")
                            match_id = re.search(r"CodOferta=(\d+)", href)
                            if match_id:
                                id_vaga = int(match_id.group(1))
                                url_vaga = f"https://bep.gov.pt?CodOferta={id_vaga}"
                        
                        # Se não encontrar ID no link, gera um hash numérico único baseado no código OE
                        if id_vaga == 0:
                            match_num = re.search(r"OE\d+/(\d+)", codigo)
                            id_vaga = int(match_num.group(1)) if match_num else hash(codigo) & 0xfffffff
                            url_vaga = f"https://bep.gov.pt?CodOferta={id_vaga}"

                        titulo_vaga = f"{codigo} - {carreira}"
                        descricao = f"Procedimento concursal para a carreira de {carreira} no organismo {organismo}. Data limite de candidatura: {data_limite}."
                        
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
                                "validThrough": data_limite if "-" in data_limite else "2026-12-31",
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
                        print(f"Detetada no HTML: {codigo} - {organismo}")
            
            # 3. Fusão incremental (Merge) sem duplicados
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            # Ordena a lista
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            # Grava no data.json
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            if lista_final:
                with open("estado.json", "w", encoding="utf-8") as f:
                    json.dump({"ultimo_id": lista_final[0]["id"] if lista_final else 0, "total_acumulado": len(lista_final)}, f, indent=4)
                    
            print(f"Sucesso. Base de dados atualizada no HTML: {len(lista_final)}/200 vagas totais.")
        else:
            print(f"A página inicial da BEP devolveu o erro de estado: {resposta.status_code}")
    except Exception as e:
        print(f"Erro crítico no processamento HTML: {e}")

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    extrair_e_acumular()
