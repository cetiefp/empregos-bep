name: Executar Scraper BEP Automático

on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  recortar-e-publicar:
    runs-on: ubuntu-latest
    steps:
    - name: Descarregar Código do Repositório
      uses: actions/checkout@v4

    - name: Configurar Ambiente Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Instalar Dependências Necessárias
      # Instalamos a biblioteca bs4 para lidar com o erro de XML malformado
      run: pip install requests beautifulsoup4

    - name: Executar Atualização e Acumulação Python
      run: python gerar_data.py

    - name: Gravar Histórico Incremental no Repositório
      run: |
        git config --global user.name "github-actions[bot]"
        git config --global user.email "github-actions[bot]@://github.com"
        git add data.json estado.json
        git commit -m "Sistema: Atualização incremental automática (Máx 200)" || echo "Sem novidades"
        git push origin main
