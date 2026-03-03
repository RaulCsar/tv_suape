#!/bin/bash

# Define os binários que serão usados pelo SO Debian/Amazon Linux subjacente da Vercel
# ignorando completamente os empacotadores da Vercel que estão quebrando binários do C.

# Tira de cena configs auto da Vercel
export PYTHONPATH=""

# Baixa as libs localmente em uma pasta garantidamente isolada em tempo de build usando o pip oficial do S.O
pip3 install -r requirements.txt -t packages --no-cache-dir

# Adiciona ao runtime a pasta real onde os pacotes compilados agorinha foram parar 
export PYTHONPATH=$(pwd)/packages

python3 scraper.py
