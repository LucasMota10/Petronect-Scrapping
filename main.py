import requests
from bs4 import BeautifulSoup

url = "https://brasil.googleblog.com/"

try:
    response = requests.get(url)
    # Verifique se a requisição foi bem-sucedida (código 200)
    response.raise_for_status() 
except requests.exceptions.RequestException as e:
    print(f"Erro ao acessar a página: {e}")
    exit()

# 3. Use o Beautiful Soup para analisar o HTML da página
soup = BeautifulSoup(response.text, 'html.parser')


print(soup)