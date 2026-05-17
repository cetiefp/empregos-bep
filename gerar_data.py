import os
import json
import requests
from bs4 import BeautifulSoup

def obter_id_partida():
    id_base_estimado = 148573 # O ID real que forneceu como âncora histórica
    
    # 1. Tenta ler o ficheiro estado.json para encontrar o último ponto de salvamento
    if os.path.exists("estado.json"):
        try:
            with open("estado.json", "r", encoding="utf-8") as f:
                dados_estado = json.load(f)
                if isinstance(dados_estado, dict) and "ultimo_id" in dados_estado:
                    id_guardado = int(dados_estado["ultimo_id"])
                    # Somamos uma margem de 30 IDs para o caso de terem saído novas ofertas desde a última corrida
                    print(f"Ponto de partida recuperado do estado.json: {id_guardado}. A testar novos IDs até: {id_guardado + 30}")
                    return id_guardado + 30
        except Exception as e:
            print(f"Erro ao ler estado.json, a usar ID base padrão. Erro: {e}")
            
    print(f"Ficheiro estado.json não encontrado ou vazio. A iniciar do ID padrão: {id_base_estimado}")
    return id_base_estimado

def extrair_ultimas_ofertas(quantidade=20):
    id_atual = obter_id_partida()
    ofertas_encontradas = []
    
    # Vamos recuar até 200 IDs para garantir que preenchemos as 20 vagas mesmo com falhas sequenciais
    max_tentativas = 200
    tentativas = 0
    ultimo_id_sucesso = None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9"
    }
    
    while len(ofertas_encontradas) < quantidade and tentativas < max_tentativas:
        url = f"https://bep.gov.pt{id_atual}"
        try:
            resposta = requests.get(url, headers=headers, timeout=12)
            
            if resposta.status_code == 200 and "ctl00_FormId_lblCodigo" in resposta.text:
                soup = BeautifulSoup(resposta.text, 'html.parser')
                
                elem_codigo = soup.find(id="ctl00_FormId_lblCodigo")
                titulo = elem_codigo.text.strip() if elem_codigo else None
                
                if titulo:
                    # O primeiro ID válido que o script encontrar nesta corrida será o mais alto (mais recente)
                    if ultimo_id_sucesso is None:
                        ultimo_id_sucesso = id_atual
                        
                    elem_org = soup.find(id="ctl00_FormId_lblOrganismo")
                    organismo = elem_org.text.strip() if elem_org else "Administração Pública"
                    
                    elem_desc = soup.find(id="ctl00_FormId_lblCaracterizacao")
                    descricao = elem_desc.text.strip() if elem_desc else "Consulte os detalhes no portal oficial da BEP."

                    dados_vaga = {
                        "id": id_atual,
                        "titulo": titulo,
                        "url": url,
                        "organismo": organismo,
                        "descricao": descricao,
                        "dados_estruturados": {
                            "@context": "https://schema.org",
                            "@type": "JobPosting",
                            "title": titulo,
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
                    }
                    ofertas_encontradas.append(dados_vaga)
                    print(f"-> Sucesso: Encontrado ID {id_atual} ({titulo})")
            else:
                # Silencioso para IDs inexistentes
                pass
                
        except Exception as e:
            print(f"Erro ao ligar ao ID {id_atual}: {e}")
            
        id_atual -= 1
        tentativas += 1

    # 2. SE encontrámos alguma oferta válida, gravamos o ID mais alto detetado de volta no estado.json
    if ultimo_id_sucesso:
        try:
            with open("estado.json", "w", encoding="utf-8") as f:
                json.dump({"ultimo_id": ultimo_id_sucesso}, f, indent=4)
            print(f"Novo ponto de partida guardado no estado.json: {ultimo_id_sucesso}")
        except Exception as e:
            print(f"Erro ao gravar ficheiro estado.json: {e}")

    return ofertas_encontradas

if __name__ == "__main__":
    lista_final = extrair_ultimas_ofertas(20)
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
        
    print(f"Processo concluído. Gravações efetuadas com sucesso.")
