import tkinter as tk
import threading
import time
import pandas as pd # Importante ter instalado: pip install pandas
from view import ScraperView
from model import PetronectScraper

class PetronectController:
    def __init__(self):
        self.root = tk.Tk()
        self.view = ScraperView(self.root)
        
        # Conecta os DOIS botões da View aos métodos do Controller
        self.view.set_commands(
            start_cmd=self.iniciar_processo,
            import_cmd=self.importar_csv
        )
        
        self.root.mainloop()

    def importar_csv(self):
        """Lógica para ler o CSV e preencher a tela"""
        file_path = self.view.ask_csv_path()
        
        if not file_path:
            return # Usuário cancelou

        try:
            # Lê o CSV (tenta separar por vírgula ou ponto e vírgula)
            try:
                df = pd.read_csv(file_path)
            except:
                # Fallback para ponto e vírgula (comum no Brasil)
                df = pd.read_csv(file_path, sep=';')

            # Normaliza os nomes das colunas para minúsculo para facilitar a busca
            df.columns = [col.strip().lower() for col in df.columns]

            if 'oportunidade' in df.columns:
                # Pega os dados, converte para string e remove vazios (NaN)
                codigos = df['oportunidade'].dropna().astype(str).tolist()
                
                # Envia para a View preencher a tela
                self.view.set_input_codes(codigos)
                self.view.update_log(f"📂 CSV carregado! {len(codigos)} códigos importados.")
            else:
                self.view.show_error("Erro no CSV", "A coluna 'oportunidade' não foi encontrada no arquivo.")

        except Exception as e:
            self.view.show_error("Erro ao ler arquivo", f"Detalhes: {e}")

    def iniciar_processo(self):
        codigos = self.view.get_input_codes()

        if not codigos:
            self.view.show_error("Atenção", "A lista de códigos está vazia!")
            return

        thread = threading.Thread(target=self.worker_thread, args=(codigos,))
        thread.start()

    def worker_thread(self, codigos):
        self.view.toggle_buttons('disabled') # Bloqueia todos os botões
        self.view.update_log("-" * 30)
        self.view.update_log(f"Iniciando processamento de {len(codigos)} códigos...")

        scraper = None
        try:
            scraper = PetronectScraper(log_callback=self.view.update_log)
            scraper.configure_driver()

            for codigo in codigos:
                scraper.search_code(codigo)
                time.sleep(1)

            self.view.update_log("✅ Processo finalizado!")
            self.view.show_success("Sucesso", "Todos os downloads concluídos.")

        except Exception as e:
            self.view.update_log(f"❌ Erro fatal: {e}")
            self.view.show_error("Erro", f"Falha na execução: {e}")

        finally:
            self.root.after(0, lambda: self.view.toggle_buttons('normal'))