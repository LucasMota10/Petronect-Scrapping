# arquivo: model.py
import os
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class PetronectScraper:
    def __init__(self, download_folder="downloads", log_callback=None):
        self.url = "https://www.petronect.com.br/irj/go/km/docs/pccshrcontent/Site%20Content%20(Legacy)/Portal2018/pt/lista_licitacoes_publicadas_ft.html"
        # Caminho base (raiz dos downloads)
        self.base_download_dir = os.path.join(os.getcwd(), download_folder)
        self.log = log_callback if log_callback else print
        
        # Cria a pasta raiz se não existir
        if not os.path.exists(self.base_download_dir):
            os.makedirs(self.base_download_dir)

    def configure_driver(self):
        self.log("🔧 Configurando driver...")
        opcoes = Options()
        opcoes.add_experimental_option("detach", True)
        opcoes.add_argument("--start-maximized")
        
        # Configurações iniciais de download (serão sobrescritas por código, mas bom ter padrão)
        prefs = {
            "download.default_directory": self.base_download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 1 # Permite múltiplos downloads
        }
        opcoes.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opcoes)
        self.driver.get(self.url)
        self.log("🌍 Site acessado.")

    def set_download_folder(self, codigo):
        """
        Cria uma pasta específica para o código e instrui o Chrome a salvar lá.
        """
        # Cria o caminho: C:/.../downloads/7004461520
        folder_path = os.path.join(self.base_download_dir, str(codigo))
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            self.log(f"📁 Pasta criada: {folder_path}")
        
        # Mágica do Chrome: Muda a pasta de download dinamicamente sem fechar o navegador
        params = {
            "behavior": "allow",
            "downloadPath": folder_path
        }
        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
        return folder_path

    def search_code(self, codigo):
        self.log(f"🔎 Buscando: {codigo}...")
        
        # 1. Prepara a pasta para ESTE código
        current_folder = self.set_download_folder(codigo)

        try:
            search_field = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "filterNewLayoutKeyWord"))
            )
            search_field.clear()
            search_field.send_keys(str(codigo))
            
            search_button = self.driver.find_element(By.ID, "resultTableHeaderKeySubmitBtn")
            self.driver.execute_script("arguments[0].click();", search_button)

            time.sleep(2) 

            modal_id = self.open_modal(codigo)
            
            if modal_id:
                # Passamos a pasta atual para ele monitorar
                self.download_files_from_modal(modal_id, current_folder)
                self.close_modal()
            else:
                self.log(f"❌ Código {codigo} encontrado, mas falha ao abrir modal.")
                
        except Exception as e:
            self.log(f"❌ Erro crítico no código {codigo}: {e}")

    def open_modal(self, codigo):
        # Seletor específico do clipe
        seletor = f"a[data-opport-num='{codigo}'].modal-anexo"
        
        try:
            botao_anexo = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, seletor))
            )
            
            target_id = botao_anexo.get_attribute("data-target")
            
            # Lógica de fallback de ID (igual ao anterior que funcionou)
            if not target_id:
                href = botao_anexo.get_attribute("href")
                if href and "#" in href and len(href) > 1:
                    target_id = "#" + href.split("#")[1]
            
            if not target_id or target_id == "#":
                target_id = "#modal-anexo-0"

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_anexo)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", botao_anexo)

            # Espera modal abrir
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, f"{target_id} .modal-content"))
            )
            self.log(f"✅ Modal aberto ({target_id}).")
            return target_id
            
        except Exception as e:
            self.log(f"⚠️ Erro ao abrir modal: {e}")
            # Tenta modal genérico se falhar
            try:
                modais = self.driver.find_elements(By.CSS_SELECTOR, ".modal")
                for m in modais:
                    if m.is_displayed():
                        return "#" + m.get_attribute("id")
            except:
                pass
            return None

    def download_files_from_modal(self, modal_id, save_folder):
        try:
            seletor_botoes = f"{modal_id} .btn-down"
            
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, seletor_botoes))
            )
            
            botoes_download = self.driver.find_elements(By.CSS_SELECTOR, seletor_botoes)
            
            if not botoes_download:
                self.log("⚠️ Sem anexos para baixar.")
                return

            self.log(f"⬇️ Baixando {len(botoes_download)} anexos em: {os.path.basename(save_folder)}...")

            for i, btn in enumerate(botoes_download):
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.log(f"   - Clique no arquivo {i+1}")
                    # Pausa importante para o navegador registrar o clique
                    time.sleep(2) 
                except Exception as e:
                    self.log(f"   - Erro clique arquivo {i+1}: {e}")
            
            # --- MONITOR DE DOWNLOADS ---
            self.wait_for_downloads_to_finish(save_folder)

        except Exception as e:
            self.log(f"⚠️ Erro processo download: {e}")

    def wait_for_downloads_to_finish(self, folder, timeout=60):
        """
        Espera até que não existam mais arquivos .crdownload na pasta.
        """
        self.log("⏳ Aguardando término dos downloads...")
        start_time = time.time()
        
        while True:
            # Lista arquivos na pasta
            try:
                files = os.listdir(folder)
            except:
                files = []

            # Verifica se tem algum .crdownload (arquivo temporário do Chrome)
            downloads_em_andamento = [f for f in files if f.endswith('.crdownload')]
            
            if not downloads_em_andamento:
                # Verifica se pelo menos algum arquivo foi baixado (opcional)
                if len(files) > 0:
                    self.log("✅ Downloads concluídos!")
                    break
                else:
                    # Se a pasta estiver vazia, talvez o download nem começou. Espera um pouco.
                    if time.time() - start_time > 5: # Se passou 5s e nada, desiste
                        self.log("⚠️ Nenhum arquivo apareceu na pasta.")
                        break
            
            if time.time() - start_time > timeout:
                self.log("⚠️ Tempo limite de download excedido.")
                break
            
            time.sleep(1)

    def close_modal(self):
        try:
            self.driver.refresh()
            time.sleep(2)
        except:
            pass