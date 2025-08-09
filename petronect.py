import sys
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class PetronectScraper:
    def __init__(self, url: str, codigo: str):
        self.url = url
        self.codigo = codigo
        self.driver = None
        self.soup = None

    def setup_driver(self):
        """
        Configura o driver do Chrome usando o webdriver-manager.
        """
        try:
            options = webdriver.ChromeOptions()
            # Opcional: Adiciona argumentos para o navegador rodar em modo 'headless'
            # options.add_argument("--headless") 
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("Driver do Chrome configurado com sucesso.")
        except Exception as e:
            print(f"Erro ao configurar o driver do Chrome: {e}")
            sys.exit(1)

    def request(self):
        """
        Acessa a URL usando o Selenium e espera a página carregar.
        """
        if not self.driver:
            self.setup_driver()

        try:
            print(f"Acessando a URL: {self.url}")
            self.driver.get(self.url)
            
            # Espera 5 segundos para que o JavaScript carregue a tabela
            sleep(5) 
            
            # Obtém o HTML da página já renderizada
            self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            print("Conteúdo da página obtido com sucesso.")

        except Exception as e:
            print(f"Erro ao acessar a página: {e}")
            self.close_driver()
            sys.exit(1)

    def load_table(self):
        """
        Extrai os dados da tabela usando BeautifulSoup.
        """
        if not self.soup:
            print("O conteúdo da página não foi carregado. Execute o método 'request()' primeiro.")
            self.close_driver()
            sys.exit(1)

        tabela = self.soup.find('table', class_='table1')
        
        if not tabela:
            print("Erro: A tabela com a classe 'table1' não foi encontrada.")
            self.close_driver()
            return
        
        tbody = tabela.find('tbody', id="result")
        
        if not tbody:
            print("Erro: O tbody com o id 'result' não foi encontrado na tabela.")
            self.close_driver()
            return

        linhas = tbody.find_all('tr')
        dados_tabela = []
        for linha in linhas:
            celulas = linha.find_all('td')
            if celulas:
                dados_linha = [celula.get_text(strip=True) for celula in celulas]
                dados_tabela.append(dados_linha)
        
        return dados_tabela

    def close_driver(self):
        """
        Fecha o driver do navegador.
        """
        if self.driver:
            self.driver.quit()

# ---
# Exemplo de uso
# ---

if __name__ == '__main__':
    # Use a URL da página da Petronect que contém a tabela
    url_petronect = "https://www.petronect.com.br/irj/go/km/docs/pccshrcontent/Site%20Content%20(Legacy)/Portal2018/pt/lista_licitacoes_publicadas_ft.html"
    
    scraper = PetronectScraper(url_petronect, "teste")
    
    # Executa a requisição e carrega a tabela
    scraper.request()
    
    # Extrai os dados
    tabela_de_dados = scraper.load_table()

    # Imprime os dados extraídos
    if tabela_de_dados:
        print("\nDados da tabela encontrados:")
        for dado in tabela_de_dados:
            print(dado)
    else:
        print("\nNenhum dado foi encontrado na tabela.")
        
    # É essencial fechar o driver do navegador ao final
    scraper.close_driver()