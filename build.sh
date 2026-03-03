#!/bin/bash
# Cria e ativa um ambiente virtual no servidor do Vercel
python3 -m venv venv
source venv/bin/activate

# Instala as dependências dentro do ambiente isolado e executa o script
pip install -r requirements.txt
python3 scraper.py
