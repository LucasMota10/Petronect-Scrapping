import sys
import os
import requests
import random
import shutil
import time
import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class PetronectScraper:
    def __init__(self, url: str):
        self.url = url
        self.temp_download_dir = os.path.join(os.getcwd(), "temp_downloads")
        self.driver = None
        self.soup = None
        self.job_data = None
        self.page_found = None
        self.session = requests.Session()
        self.current_code = None
        self.current_obj = None
        self.current_end_date = None
        
    def setup_driver(self):
        try:
            if not os.path.exists(self.temp_download_dir):
                os.makedirs(self.temp_download_dir)
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # options.add_argument("--headless") # Descomente se não quiser ver o navegador
            prefs = {
                "download.default_directory": self.temp_download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safeBrowse.enabled": True,
                "profile.default_content_setting_values.automatic_downloads": 1
            }
            options.add_experimental_option("prefs", prefs)
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("Driver do Chrome configurado para downloads automáticos e múltiplos.")
        except Exception as e:
            print(f"Erro ao configurar o driver do Chrome: {e}")
            sys.exit(1)

    def go_to_first_page(self):
        if not self.driver:
            self.setup_driver()
        try:
            # Verifica se já estamos na URL correta para evitar recarregamentos desnecessários
            if self.driver.current_url != self.url:
                print(f"\nAcessando a URL inicial: {self.url}")
                self.driver.get(self.url)
            
            # Espera pela tabela de resultados e pela barra de pesquisa
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'table1')))
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, 'filterNewLayoutKeyWord')))
            
            # Garante que não há modais bloqueando (clica no corpo da página se necessário)
            try:
                self.driver.find_element(By.TAG_NAME, 'body').click()
            except:
                pass

            if not self.session.cookies:
                self.get_session_cookies()
        except Exception as e:
            print(f"Erro ao acessar a página: {e}")
            self.close_driver()
            sys.exit(1)

    def get_session_cookies(self):
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])
        # print("Cookies da sessão coletados.")

    def find_code_in_page(self):
        """
        Analisa a tabela visível para encontrar o código desejado.
        """
        self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        table = self.soup.find('table', class_='table1')
        if not table: return None
        tbody = table.find('tbody', id="result")
        if not tbody: return None
        rows = tbody.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if cells:
                row_data = [cell.get_text(strip=True) for cell in cells]
                # Verifica se a primeira coluna corresponde ao código atual
                if row_data and row_data[0] == self.current_code:
                    self.current_obj = row_data[1]
                    self.current_end_date = row_data[6].replace("/","_")
                    return row_data
        return None

    def search_code_and_verify(self, code_to_find):
        """
        Usa a barra de pesquisa do site para encontrar o código diretamente.
        Usa JS Click para evitar erros de interceptação.
        """
        self.current_code = str(code_to_find).strip()
        self.go_to_first_page() 
        
        print(f"\nBuscando código '{self.current_code}' usando a barra de pesquisa...")

        try:
            # 1. Localiza a caixa de texto
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'filterNewLayoutKeyWord'))
            )
            
            # 2. Limpa e insere o código
            search_input.clear()
            search_input.send_keys(self.current_code)
            
            # 3. Localiza o botão de busca
            search_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'resultTableHeaderKeySubmitBtn'))
            )
            
            # CORREÇÃO: Usar JavaScript para clicar, ignorando overlays/modais transparentes
            self.driver.execute_script("arguments[0].click();", search_button)
            
            # 4. Espera resultados
            # print("Aguardando resultados...")
            sleep(random.uniform(3, 5)) 

            # 5. Verifica resultados
            job_data = self.find_code_in_page()
            
            if job_data:
                self.job_data = job_data
                self.page_found = 1 
                print(f"✅ Código '{self.current_code}' encontrado e dados coletados.")
                return True
            else:
                print(f"❌ Código '{self.current_code}' não encontrado nos resultados da busca.")
                return False

        except Exception as e:
            print(f"Erro durante a busca pelo código '{self.current_code}': {e}")
            # Se der erro de clique ou timeout, damos refresh para limpar a tela para a próxima tentativa
            try:
                print("Tentando recuperar interface com Refresh...")
                self.driver.refresh()
                sleep(3)
            except:
                pass
            return False

    def create_folder(self):
        if not self.job_data:
            print("Nenhum dado encontrado para criar a pasta.")
            return None
        # Limpa caracteres inválidos para nome de pasta
        safe_obj = "".join([c for c in self.current_obj if c.isalnum() or c in (' ', '-', '_')]).strip()
        folder_name = f"{self.current_code}_{safe_obj}_{self.current_end_date}"
        folder_path = os.path.join(os.getcwd(), folder_name)
        
        os.makedirs(folder_path, exist_ok=True)
        print(f"Pasta de destino '{folder_path}' garantida.")
        return folder_path

    def download_attachments(self):
        if not self.page_found:
            return []
        print(f"\nIniciando o processo de download de anexos via Selenium...")
        modal_id = None
        try:
            target_row_selector = f'a[data-opport-num="{self.current_code}"]'
            row_element_link = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, target_row_selector)))
            row_element = row_element_link.find_element(By.XPATH, './ancestor::tr')
            attachment_link = row_element.find_element(By.CSS_SELECTOR, '.modal-anexo')
            modal_id = attachment_link.get_attribute('data-target')
            
            # Abre o modal com JS click para garantir
            self.driver.execute_script("arguments[0].click();", attachment_link)
            print(f"Link de anexo clicado. Aguardando o modal com ID: {modal_id}...")
            
            modal_table = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, f'{modal_id} table.table')))
            print("Conteúdo do modal carregado. Clicando nos botões de download...")
            sleep(2)
            
            attachment_rows = modal_table.find_elements(By.TAG_NAME, 'tr')
            downloaded_files_names = []
            for attachment_row in attachment_rows:
                if attachment_row.find_elements(By.TAG_NAME, 'th'):
                    continue
                try:
                    file_name = attachment_row.find_element(By.CLASS_NAME, 'anexo_description').text
                    download_button = attachment_row.find_element(By.CLASS_NAME, 'btn-down')
                    print(f"Clicando para baixar '{file_name}'...")
                    self.driver.execute_script("arguments[0].click();", download_button)
                    downloaded_files_names.append(file_name)
                    sleep(random.uniform(2, 4)) 
                except Exception as e:
                    print(f"Erro ao processar linha do anexo: {e}")
            
            return downloaded_files_names

        except Exception as e:
            print(f"Erro ao tentar baixar os anexos: {e}")
            return []
        
        finally:
            # CORREÇÃO: Garante que o modal será fechado e espera ele sumir
            if modal_id:
                try:
                    # Tenta encontrar o botão de fechar dentro do header do modal específico
                    close_buttons = self.driver.find_elements(By.CSS_SELECTOR, f'{modal_id} .modal-header button.close')
                    if close_buttons:
                        self.driver.execute_script("arguments[0].click();", close_buttons[0])
                        # Espera o modal ficar invisível
                        try:
                            WebDriverWait(self.driver, 5).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, modal_id)))
                        except:
                            # Se não ficar invisível, tenta clicar no body para tirar o foco
                            self.driver.find_element(By.TAG_NAME, 'body').click()
                except Exception as e:
                    print(f"Aviso: Não foi possível fechar o modal corretamente: {e}")

    def close_driver(self):
        if self.driver:
            self.driver.quit()
            print("\nDriver do Chrome fechado.")
        if os.path.exists(self.temp_download_dir):
            try:
                shutil.rmtree(self.temp_download_dir)
                print(f"Pasta temporária '{self.temp_download_dir}' removida.")
            except Exception as e:
                print(f"Erro ao remover pasta temporária: {e}")

def wait_for_downloads_and_move(temp_dir, final_dir):
    print("\nAguardando a finalização dos downloads...")
    timeout = 120
    start_time = time.time()
    while any(f.endswith('.crdownload') for f in os.listdir(temp_dir)):
        if time.time() - start_time > timeout:
            print("AVISO: Tempo de espera para downloads excedido. Alguns arquivos podem estar incompletos.")
            break
        sleep(1)
    
    sleep(2)

    files_in_temp = os.listdir(temp_dir)
    if not files_in_temp:
        print("AVISO: Nenhum arquivo foi baixado na pasta temporária.")
        return

    print("Movendo arquivos para a pasta de destino...")
    for file_name in files_in_temp:
        if file_name.endswith('.crdownload'):
            continue
        
        temp_path = os.path.join(temp_dir, file_name)
        final_path = os.path.join(final_dir, file_name)
        
        moved_successfully = False
        for attempt in range(5):
            try:
                shutil.move(temp_path, final_path)
                print(f"✅ Arquivo '{file_name}' movido com sucesso.")
                moved_successfully = True
                break
            except PermissionError:
                print(f"  - Arquivo '{file_name}' está ocupado. Tentando novamente em 1 segundo... (Tentativa {attempt + 1}/5)")
                sleep(1)
            except Exception as e:
                print(f"❌ Ocorreu um erro inesperado ao mover '{file_name}': {e}")
                break

        if not moved_successfully:
            print(f"❌ Falha ao mover o arquivo '{file_name}' após múltiplas tentativas.")

    print("Limpeza da pasta temporária para a próxima oportunidade...")
    for f in os.listdir(temp_dir):
        try:
            os.remove(os.path.join(temp_dir, f))
        except:
            pass

def extract_zip_files_in_folder(folder_path, delete_zip_after_extraction=True):
    print("\nIniciando processo de extração de arquivos .zip...")
    found_zips = False
    for item in os.listdir(folder_path):
        if item.lower().endswith('.zip'):
            found_zips = True
            zip_path = os.path.join(folder_path, item)
            extract_dir_name = os.path.splitext(item)[0]
            extract_path = os.path.join(folder_path, extract_dir_name)
            print(f"Extraindo '{item}' para a pasta '{extract_path}'...")
            try:
                os.makedirs(extract_path, exist_ok=True)
                shutil.unpack_archive(zip_path, extract_path)
                print(f"✅ Arquivo '{item}' extraído com sucesso.")
                if delete_zip_after_extraction:
                    os.remove(zip_path)
                    print(f"  - Arquivo .zip original '{item}' removido.")
            except Exception as e:
                print(f"❌ Erro ao extrair o arquivo '{item}': {e}")
    if not found_zips:
        print("Nenhum arquivo .zip encontrado para extrair.")

def get_codes_from_file(file_path):
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            print("Formato de arquivo não suportado. Use .csv ou .xlsx")
            return []
        
        df.columns = [col.lower() for col in df.columns]

        if 'oportunidade' not in df.columns:
            print("Erro: A coluna 'oportunidade' não foi encontrada no arquivo.")
            return []
            
        codes = df['oportunidade'].dropna().astype(str).tolist()
        return codes

    except FileNotFoundError:
        print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
        return []
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")
        return []

def processar_oportunidade(code, scraper_instance):
    code = str(code).strip()
    print(f"\n{'='*20} PROCESSANDO OPORTUNIDADE: {code} {'='*20}")

    ja_processado = False
    for pasta in os.listdir(os.getcwd()):
        if pasta.startswith(code + "_") and os.path.isdir(pasta):
            print(f"⏩ AVISO: Já existe uma pasta iniciando com '{code}'. Pulando para a próxima.")
            ja_processado = True
            break
    
    if ja_processado:
        return

    if scraper_instance.search_code_and_verify(code):
        print("\nDados do código encontrado:")
        print(scraper_instance.job_data)
        folder_path = scraper_instance.create_folder()
        if folder_path:
            expected_files_list = scraper_instance.download_attachments()
            if expected_files_list:
                wait_for_downloads_and_move(scraper_instance.temp_download_dir, folder_path)
                extract_zip_files_in_folder(folder_path, delete_zip_after_extraction=True)
            else:
                print("Nenhum download foi iniciado para esta oportunidade.")
    else:
        print(f"Não foi possível processar a oportunidade '{code}', pois ela não foi encontrada.")

if __name__ == '__main__':
    base_url = "https://www.petronect.com.br/irj/go/km/docs/pccshrcontent/Site%20Content%20(Legacy)/Portal2018/pt/lista_licitacoes_publicadas_ft.html"
    
    print("Selecione o modo de operação:")
    print("1: Buscar um código de oportunidade individual")
    print("2: Processar um arquivo com múltiplos códigos")
    
    choice = input("Digite sua escolha (1 ou 2): ").strip()

    scraper = PetronectScraper(base_url)
    
    if choice == '1':
        search_code = input("Digite o Código da Oportunidade que deseja Buscar: ").strip()
        if not search_code:
            print("Código inválido.")
        else:
            processar_oportunidade(search_code, scraper)

    elif choice == '2':
        file_path = input("Digite o caminho completo para o seu arquivo (.csv ou .xlsx): ").strip()
        codes_to_process = get_codes_from_file(file_path)
        
        if codes_to_process:
            print(f"\nEncontrados {len(codes_to_process)} códigos para processar.")
            for code in codes_to_process:
                processar_oportunidade(code, scraper)
        else:
            print("Nenhum código para processar. Encerrando o script.")
    
    else:
        print("Escolha inválida. Encerrando o script.")

    scraper.close_driver()
    print("\nProcesso finalizado.")