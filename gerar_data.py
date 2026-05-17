import os
import json
import re
import requests

def extrair_e_acumular():
    ficheiro_dados = "data.json"
    ofertas_antigas = []
    
    # 1. Carrega o histórico existente do repositório para fazermos a acumulação até 200
    if os.path.exists(ficheiro_dados):
        try:
            with open(ficheiro_dados, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, list):
                    ofertas_antigas = conteudo
                    print(f"Histórico carregado: {len(ofertas_antigas)} vagas.")
        except:
            pass

    # URL oficial direta. Sob a rede Windows do GitHub, o DNS e a Firewall deverão cooperar
    url_rss = "https://bep.gov.pt"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"A tentar estabelecer ligação segura com: {url_rss}")
    try:
        resposta = requests.get(url_rss, headers=headers, timeout=25)
        print(f"Resposta recebida do servidor da BEP. Código de Estado: {resposta.status_code}")
        
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            texto_cru = resposta.text
            
            # Isola cirurgicamente cada bloco <item> do XML usando Regex
            blocos_item = re.findall(r'<item>(.*?)</item>', texto_cru, re.DOTALL)
            print(f"Sucesso! Encontrados {len(blocos_item)} registos de emprego no feed da BEP.")
            
            novas_ofertas = []
            for bloco in blocos_item:
                def buscar_tag(tag, texto):
                    match = re.search(f'<{tag}>(.*?)</{tag}>', texto, re.DOTALL)
                    return match.group(1).strip() if match else ""
                
                titulo_completo = buscar_tag("title", bloco)
                link_original = buscar_tag("link", bloco)
                descricao_completa = buscar_tag("description", bloco)
                
                # Normaliza o link garantindo o subdomínio www
                if link_original and "www." not in link_original:
                    link_original = link_original.replace("https://bep.gov.pt", "https://bep.gov.pt")
                
                # Captura o ID da vaga (CodOferta=XXXXXX)
                match_id = re.search(r"CodOferta=(\d+)", link_original)
                id_vaga = int(match_id.group(1)) if match_id else 0
                
                # Separa o código do concurso do nome do ministério/organismo
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
                            "description": descricao_completa if descricao_completa else "Consulte os termos no portal oficial.",
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
                    print(f"-> Vaga processada: ID {id_vaga} ({titulo_vaga})")
            
            # 3. Fusão de listas (Merge) protegendo contra duplicados baseados no ID único
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            # Ordenação decrescente (mais recentes primeiro)
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            
            # Limita ao histórico pretendido das últimas 200 ofertas
            lista_final = lista_ordenada[:200]
            
            # Guarda a coleção finalizada
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            with open("estado.json", "w", encoding="utf-8") as f:
                json.dump({"ultimo_id": lista_final[0]["id"] if lista_final else 0, "total_acumulado": len(lista_final)}, f, indent=4)
                
            print(f"Processo concluído. Ficheiro data.json sincronizado com {len(lista_final)}/200 vagas.")
        else:
            print(f"Acesso negado ou link inválido. Estado do servidor: {resposta.status_code}")
            
    except Exception as e:
        print(f"Falha na ligação à rede da BEP: {e}")

if __name__ == "__main__":
    extrair_e_acumular()
