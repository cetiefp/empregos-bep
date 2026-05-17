import os
import json
import requests
from bs4 import BeautifulSoup

def extrair_ultimas_ofertas(quantidade=20):
    # Usamos o ID que forneceu como ponto de partida mais alto
    id_atual = 148573 
    ofertas_encontradas = []
    
    # Tentamos inspecionar até 150 IDs anteriores para encontrar 20 válidos
    max_tentativas = 150
    tentativas = 0
    
    # Cabeçalhos para simular que o GitHub é um navegador Chrome real em Portugal
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }
    
    print(f"A iniciar a pesquisa reversa a partir do ID real: {id_atual}")
    
    while len(ofertas_encontradas) < quantidade and tentativas < max_tentativas:
        url = f"https://bep.gov.pt{id_atual}"
        try:
            # Faz o pedido simulando um navegador real
            resposta = requests.get(url, headers=headers, timeout=12)
            
            # Se a página carregar e contiver a estrutura de uma oferta válida
            if resposta.status_code == 200 and "ctl00_FormId_lblCodigo" in resposta.text:
                soup = BeautifulSoup(resposta.text, 'html.parser')
                
                elem_codigo = soup.find(id="ctl00_FormId_lblCodigo")
                titulo = elem_codigo.text.strip() if elem_codigo else None
                
                # Só guardamos se encontrarmos um código de oferta válido (ex: OE2026...)
                if titulo:
                    elem_org = soup.find(id="ctl00_FormId_lblOrganismo")
                    organismo = elem_org.text.strip() if elem_org else "Administração Pública"
                    
                    elem_desc = soup.find(id="ctl00_FormId_lblCaracterizacao")
                    descricao = elem_desc.text.strip() if elem_desc else "Consulte os detalhes completos no portal oficial da BEP."

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
                # Se o ID não existir ou estiver vazio, o script ignora e avança para o próximo sem quebrar
                print(f"ID {id_atual} indisponível ou vazio. A saltar...")
                
        except Exception as e:
            print(f"Erro ao ligar ao ID {id_atual}: {e}")
            
        # Continua a descer para os IDs anteriores
        id_atual -= 1
        tentativas += 1

    return ofertas_encontradas

if __name__ == "__main__":
    lista_final = extrair_ultimas_ofertas(20)
    
    # Atualiza o ficheiro data.json com os novos dados estruturados
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
        
    print(f"Processo terminado. Foram gravadas {len(lista_final)} ofertas válidas.")
