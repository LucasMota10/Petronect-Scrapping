# arquivo: model.py
import os
import time
import shutil
import re
import zipfile # <--- Importante para descompactar
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class PetronectScraper:
    def __init__(self, download_folder="downloads", log_callback=None):
        self.url = "https://www.petronect.com.br/irj/go/km/docs/pccshrcontent/Site%20Content%20(Legacy)/Portal2018/pt/lista_licitacoes_publicadas_ft.html"
        self.base_download_dir = os.path.join(os.getcwd(), download_folder)
        self.log = log_callback if log_callback else print
        
        if not os.path.exists(self.base_download_dir):
            os.makedirs(self.base_download_dir)

    def configure_driver(self):
        self.log("🔧 Configurando driver...")
        opcoes = Options()
        opcoes.add_experimental_option("detach", True)
        opcoes.add_argument("--start-maximized")
        
        prefs = {
            "download.default_directory": self.base_download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        opcoes.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opcoes)
        self.driver.get(self.url)
        self.log("🌍 Site acessado.")

    def sanitize_text(self, text):
        """Limpa texto para nome de pasta"""
        text = str(text).strip()
        text = text.replace("/", "_")
        text = re.sub(r'[^\w\s\-\_]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text[:60].strip()

    def set_download_folder(self, folder_name):
        folder_path = os.path.join(self.base_download_dir, folder_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            self.log(f"📁 Pasta criada: {folder_name}")
        
        params = {"behavior": "allow", "downloadPath": folder_path}
        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
        return folder_path

    def get_opportunity_details(self):
        try:
            linha = self.driver.find_element(By.CSS_SELECTOR, "#result tr")
            colunas = linha.find_elements(By.TAG_NAME, "td")
            
            if len(colunas) > 6:
                objeto_raw = colunas[1].text
                data_fim_raw = colunas[6].text
                
                objeto_limpo = self.sanitize_text(objeto_raw)
                data_fim_limpa = self.sanitize_text(data_fim_raw)
                
                return objeto_limpo, data_fim_limpa
            return "DETALHES_NAO_ENCONTRADOS", "DATA_ND"
        except:
            return "ERRO_LEITURA", "DATA_ND"

    def search_code(self, codigo):
        self.log(f"🔎 Buscando: {codigo}...")
        
        try:
            # 1. Busca
            search_field = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "filterNewLayoutKeyWord"))
            )
            search_field.clear()
            search_field.send_keys(str(codigo))
            
            search_button = self.driver.find_element(By.ID, "resultTableHeaderKeySubmitBtn")
            self.driver.execute_script("arguments[0].click();", search_button)

            time.sleep(3) 

            # 2. Verifica se existe
            page_source = self.driver.page_source
            if "Nenhum registro encontrado" in page_source or "No records found" in page_source:
                self.log(f"⚠️ Código {codigo} não encontrado.")
                return

            # 3. Cria pasta com nome formatado
            objeto, data_fim = self.get_opportunity_details()
            nome_pasta = f"{codigo}_{objeto}_{data_fim}"
            current_folder = self.set_download_folder(nome_pasta)

            # 4. Abre modal
            modal_id = self.open_modal(codigo)
            
            if modal_id:
                # Baixa e extrai
                self.download_files_from_modal(modal_id, current_folder)
                self.close_modal()
            else:
                self.log(f"ℹ️ Código {codigo} sem anexos públicos.")
                try:
                    os.rmdir(current_folder)
                except:
                    pass
                
        except Exception as e:
            self.log(f"❌ Erro no código {codigo}: {e}")

    def open_modal(self, codigo):
        seletor = f"a[data-opport-num='{codigo}'].modal-anexo"
        
        try:
            botao_anexo = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, seletor))
            )
            
            target_id = botao_anexo.get_attribute("data-target")
            if not target_id or target_id == "#":
                href = botao_anexo.get_attribute("href")
                if href and "#" in href and len(href) > 1:
                    target_id = "#" + href.split("#")[1]
                else:
                    target_id = "#modal-anexo-0"

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_anexo)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", botao_anexo)

            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, f"{target_id} .modal-content"))
            )
            return target_id
            
        except TimeoutException:
            return None
        except Exception as e:
            self.log(f"⚠️ Erro ao abrir modal: {e}")
            return None

    def download_files_from_modal(self, modal_id, save_folder):
        try:
            seletor_botoes = f"{modal_id} .btn-down"
            
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, seletor_botoes))
            )
            
            botoes_download = self.driver.find_elements(By.CSS_SELECTOR, seletor_botoes)
            
            if not botoes_download:
                self.log("⚠️ Sem botões de download.")
                return

            self.log(f"⬇️ Baixando {len(botoes_download)} arquivos...")

            for i, btn in enumerate(botoes_download):
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2) 
                except Exception as e:
                    pass
            
            # Aguarda downloads
            if self.wait_for_downloads_to_finish(save_folder):
                # Se terminou com sucesso, extrai os ZIPs
                self.extract_zips_in_folder(save_folder)

        except Exception as e:
            self.log(f"⚠️ Erro download: {e}")

    def wait_for_downloads_to_finish(self, folder, timeout=60):
        self.log("⏳ Finalizando downloads...")
        start_time = time.time()
        
        while True:
            try:
                files = os.listdir(folder)
            except:
                files = []

            downloads_em_andamento = [f for f in files if f.endswith('.crdownload')]
            
            if not downloads_em_andamento:
                if len(files) > 0:
                    self.log(f"✅ Download concluído na pasta: {os.path.basename(folder)}")
                    return True # Retorna True para autorizar a extração
                else:
                    if time.time() - start_time > 5:
                        self.log("⚠️ Pasta vazia.")
                        return False
            
            if time.time() - start_time > timeout:
                self.log("⚠️ Timeout de download.")
                return False
            
            time.sleep(1)

    def extract_zips_in_folder(self, folder):
        """
        Varre a pasta, extrai arquivos .zip e deleta o arquivo compactado original.
        """
        self.log("📦 Verificando arquivos ZIP...")
        try:
            files = os.listdir(folder)
            count = 0
            for file in files:
                if file.lower().endswith(".zip"):
                    file_path = os.path.join(folder, file)
                    # Cria uma pasta com o mesmo nome do arquivo zip (sem a extensão)
                    folder_name = os.path.splitext(file)[0]
                    extract_path = os.path.join(folder, folder_name)
                    
                    try:
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_path)
                        
                        self.log(f"   ✨ Extraído: {file}")
                        
                        # Remove o zip original para limpar
                        os.remove(file_path)
                        count += 1
                    except Exception as e:
                        self.log(f"   ❌ Erro ao extrair {file}: {e}")
            
            if count == 0:
                self.log("   (Nenhum arquivo zip encontrado para extrair)")
                
        except Exception as e:
            self.log(f"⚠️ Erro na rotina de extração: {e}")

    def close_modal(self):
        try:
            self.driver.refresh()
            time.sleep(2)
        except:
            pass