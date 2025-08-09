import sys
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import requests
import random

class PetronectScraper:
    def __init__(self, url: str, code: str):
        self.url = url
        self.code = code
        self.driver = None
        self.soup = None
        self.job_data = None
        self.page_found = None

    def setup_driver(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("Driver do Chrome configurado com sucesso.")
        except Exception as e:
            print(f"Erro ao configurar o driver do Chrome: {e}")
            sys.exit(1)

    def make_request(self):
        if not self.driver:
            self.setup_driver()
        try:
            print(f"Acessando a URL: {self.url}")
            self.driver.get(self.url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'table1'))
            )
            print("Página carregada com sucesso.")
        except Exception as e:
            print(f"Erro ao acessar a página: {e}")
            self.close_driver()
            sys.exit(1)

    def find_code_in_page(self):
        """Busca o código na página atual e retorna os dados se encontrado."""
        self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        table = self.soup.find('table', class_='table1')
        if not table:
            return None

        tbody = table.find('tbody', id="result")
        if not tbody:
            return None

        rows = tbody.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if cells:
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data and row_data[0] == self.code:
                    return row_data
        return None

    def find_code_by_paginating(self):
        page_number = 1
        while True:
            print(f"\nBuscando código '{self.code}' na página {page_number}...")
            
            job_data = self.find_code_in_page()
            if job_data:
                self.job_data = job_data
                self.page_found = page_number
                print(f"Código '{self.code}' encontrado na página {page_number}.")
                return True

            try:
                next_button = self.driver.find_element(By.ID, 'next')
                if 'disabled' in next_button.get_attribute('class'):
                    print("Código não encontrado e botão 'Próximo' está desativado. Fim da busca.")
                    break
                next_button.click()
                
                sleep(random.uniform(5, 10))
                
                page_number += 1
            except Exception:
                print("Botão 'Próximo' não foi encontrado. Fim da busca.")
                break

        print(f"Código '{self.code}' não foi encontrado em nenhuma página.")
        return False

    def create_folder(self):
        if not self.job_data:
            print("Nenhum dado encontrado para criar a pasta.")
            sys.exit(1)
        folder_path = os.path.join(os.getcwd(), self.code)
        if not os.path.isdir(folder_path):
            print(f"Criando a pasta do código '{self.code}'...")
            os.makedirs(folder_path, exist_ok=True)
            print("Pasta criada com sucesso!")
        else:
            print(f"A pasta com o código '{self.code}' já existe.")
        return folder_path

    def download_attachments(self, folder_path):
        if not self.page_found:
            print("Não é possível baixar anexos, pois o código não foi encontrado.")
            return

        print(f"Navegando para a página {self.page_found} para baixar anexos...")
        self.driver.get(self.url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'table1'))
        )

        for _ in range(self.page_found - 1):
            try:
                next_button = self.driver.find_element(By.ID, 'next')
                next_button.click()
                sleep(random.uniform(5, 10))
            except Exception:
                print("Erro ao navegar para a página correta.")
                return

        try:
            target_row_selector = f'a[data-opport-num="{self.code}"]'
            row_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, target_row_selector))
            ).find_element(By.XPATH, './ancestor::tr')

            if not row_element:
                print("Erro: A linha do código não foi encontrada novamente.")
                return

            attachment_link = row_element.find_element(By.CSS_SELECTOR, '.modal-anexo')
            attachment_link.click()
            print("Link de anexo clicado. Aguardando o modal...")

            attachments_modal_div = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, 'table_1'))
            )
            print("Conteúdo do modal carregado com sucesso. Buscando anexos...")
            
            modal_table = attachments_modal_div.find_element(By.TAG_NAME, 'table')
            attachment_rows = modal_table.find_elements(By.TAG_NAME, 'tr')
            
            if not attachment_rows:
                print("Nenhum anexo encontrado no modal.")
                return

            for attachment_row in attachment_rows:
                try:
                    file_name = attachment_row.find_element(By.CLASS_NAME, 'anexo_description').text
                    download_button = attachment_row.find_element(By.CLASS_NAME, 'btn-down')
                    download_id = download_button.get_attribute('data-id')
                    
                    if download_id:
                        print(f"Anexo encontrado: '{file_name}' com ID: '{download_id}'")
                        self.download_file_by_id(download_id, file_name, folder_path)
                    else:
                        print(f"Botão de download sem ID na linha do anexo '{file_name}'.")
                except Exception as e:
                    print(f"Erro ao processar linha do anexo: {e}")
            
            try:
                close_button = self.driver.find_element(By.CSS_SELECTOR, '.modal-header button.close')
                close_button.click()
            except:
                pass
        
        except Exception as e:
            print(f"Erro ao tentar baixar os anexos: {e}")
            
    def download_file_by_id(self, download_id, file_name, folder_path):
        download_url = f"https://www.petronect.com.br/irj/go/km/docs/download/pccshrcontent/download?id={download_id}"
        
        try:
            print(f"Tentando baixar o arquivo '{file_name}'...")
            response = requests.get(download_url, stream=True, verify=False)
            response.raise_for_status()
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Arquivo '{file_name}' baixado com sucesso!")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao baixar o arquivo '{file_name}': {e}")
        except Exception as e:
            print(f"❌ Erro inesperado ao salvar o arquivo '{file_name}': {e}")

    def close_driver(self):
        if self.driver:
            self.driver.quit()

if __name__ == '__main__':
    base_url = "https://www.petronect.com.br/irj/go/km/docs/pccshrcontent/Site%20Content%20(Legacy)/Portal2018/pt/lista_licitacoes_publicadas_ft.html"
    search_code = input("Digite o Código da Vaga que deseja Buscar: ")
    scraper = PetronectScraper(base_url, str(search_code))
    
    scraper.make_request()
    
    if scraper.find_code_by_paginating():
        print("\nDados do código encontrado:")
        print(scraper.job_data)
        folder_path = scraper.create_folder()
        scraper.download_attachments(folder_path)
    else:
        print("Finalizando o script.")
    
    scraper.close_driver()