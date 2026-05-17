def obter_oferta(cod):
    url = f"{BASE_URL}{cod}"
    try:
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        titulo = soup.find("span", id="ctl00_ContentPlaceHolder1_lblTitulo")
        entidade = soup.find("span", id="ctl00_ContentPlaceHolder1_lblEntidade")
        data = soup.find("span", id="ctl00_ContentPlaceHolder1_lblDataPublicacao")

        if not titulo:
            return None

        return {
            "cod": cod,
            "titulo": titulo.text.strip() if titulo else "",
            "entidade": entidade.text.strip() if entidade else "",
            "data": data.text.strip() if data else "",
            "url": url
        }

    except:
        return None
