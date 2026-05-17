import os
import json
import re
import requests
import xml.etree.ElementTree as ET

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

    # 2. Rota imune: Feed RSS do Google News filtrado por concursos públicos do DRE
    # A Google tem acesso total e o GitHub tem acesso total à Google. Bloqueio zero.
    url_proxy_google = "https://google.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("A descarregar os registos oficiais indexados via infraestrutura da Google...")
    try:
        resposta = requests.get(url_proxy_google, headers=headers, timeout=25)
        
        if resposta.status_code == 200:
            resposta.encoding = 'utf-8'
            
            # Processamos o XML estável da Google
            root = ET.fromstring(resposta.text)
            items = root.findall(".//item")
            
            print(f"Ligação bem-sucedida! Detetados {len(items)} novos anúncios arquivados.")
            
            novas_ofertas = []
            for item in items:
                titulo_completo = item.find("title").text.strip() if item.find("title") is not None else "Procedimento Concursal"
                link_google = item.find("link").text.strip() if item.find("link") is not None else "https://diariodarepublica.pt"
                
                # Limpa o sufixo do Google News se presente no título
                titulo_completo = re.sub(r'\s+-\s+diáriodarepublica\.pt.*$', '', titulo_completo, flags=re.IGNORECASE)
                titulo_completo = re.sub(r'\s+-\s+Google\s+News.*$', '', titulo_completo, flags=re.IGNORECASE)
                
                # Extrai uma referência numérica estável do URL para servir de ID único
                match_id = re.search(r'/(\d+)/', link_google) or re.search(r'id=(\d+)', link_google)
                id_vaga = int(match_id.group(1)) if match_id else abs(hash(titulo_completo)) % 1000000
                
                # Isola termos do organismo se o título seguir o padrão comum
                partes = titulo_completo.split(" - ")
                titulo_vaga = partes[0].strip()
                organismo = partes[1].strip() if len(partes) > 1 else "Administração Pública Portuguesa"
                
                desc_vaga = f"Publicação oficial de procedimento concursal comum associado ao organismo: {organismo}. Consulte o articulado completo e anexos de candidatura no Diário da República."

                novas_ofertas.append({
                    "id": id_vaga,
                    "titulo": titulo_completo,
                    "url": link_google,
                    "organismo": organismo,
                    "descricao": desc_vaga,
                    "dados_estruturados": {
                        "@context": "https://schema.org",
                        "@type": "JobPosting",
                        "title": titulo_completo,
                        "description": desc_vaga,
                        "hiringOrganization": {
                            "@type": "Organization",
                            "name": organismo,
                            "sameAs": "https://diariodarepublica.pt"
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
                print(f"-> Vaga indexada com sucesso: {id_vaga}")
            
            # 3. Fusão incremental (Merge) sem duplicados
            vagas_mapeadas = {vaga["id"]: vaga for vaga in ofertas_antigas}
            for nova_vaga in novas_ofertas:
                vagas_mapeadas[nova_vaga["id"]] = nova_vaga
                
            # Ordena e limita a 200 itens
            lista_ordenada = sorted(vagas_mapeadas.values(), key=lambda x: x["id"], reverse=True)
            lista_final = lista_ordenada[:200]
            
            # Grava no data.json
            with open(ficheiro_dados, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=4)
                
            with open("estado.json", "w", encoding="utf-8") as f:
                json.dump({"ultimo_id": lista_final[0]["id"] if lista_final else 0, "total_acumulado": len(lista_final)}, f, indent=4)
                
            print(f"Sucesso absoluto! O data.json tem agora {len(lista_final)}/200 vagas estáveis acumuladas.")
        else:
            print(f"A infraestrutura intermédia devolveu um código de aviso: {resposta.status_code}")
            
    except Exception as e:
        print(f"Erro no processamento da rota imune: {e}")

if __name__ == "__main__":
    extrair_e_acumular()
