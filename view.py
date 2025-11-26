# arquivo: view.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter import font as tkfont

class ScraperView:
    def __init__(self, root):
        self.root = root
        self.root.title("Petronect Downloader Pro 🚀")
        self.root.geometry("600x700")
        self.root.configure(bg="#F0F2F5") # Fundo cinza moderno
        
        # Definição de Cores
        self.colors = {
            "bg": "#F0F2F5",
            "primary": "#2C3E50",    # Azul Escuro
            "accent": "#2980B9",     # Azul Claro
            "success": "#27AE60",    # Verde
            "text": "#333333",
            "white": "#FFFFFF",
            "log_bg": "#1E1E1E",     # Fundo do terminal
            "log_fg": "#00FF00"      # Texto do terminal
        }

        self._setup_styles()
        self._setup_ui()

    def _setup_styles(self):
        """Configura estilos personalizados para o ttk"""
        style = ttk.Style()
        style.theme_use('clam') # Tema base mais limpo que o padrão

        # Estilo de Frames
        style.configure("Card.TFrame", background=self.colors["white"], relief="flat")
        
        # Estilo de Labels
        style.configure("Header.TLabel", background=self.colors["primary"], foreground=self.colors["white"], font=("Segoe UI", 16, "bold"))
        style.configure("SubHeader.TLabel", background=self.colors["white"], foreground=self.colors["text"], font=("Segoe UI", 10, "bold"))
        style.configure("Body.TLabel", background=self.colors["white"], foreground=self.colors["text"], font=("Segoe UI", 10))

    def _setup_ui(self):
        # --- CABEÇALHO ---
        header_frame = tk.Frame(self.root, bg=self.colors["primary"], height=80)
        header_frame.pack(fill="x", side="top")
        
        lbl_title = tk.Label(header_frame, text="AUTOMAÇÃO PETRONECT", bg=self.colors["primary"], fg=self.colors["white"], font=("Segoe UI", 18, "bold"))
        lbl_title.pack(pady=(20, 5))
        
        lbl_subtitle = tk.Label(header_frame, text="Gerenciador de Downloads de Editais", bg=self.colors["primary"], fg="#BDC3C7", font=("Segoe UI", 10))
        lbl_subtitle.pack(pady=(0, 20))

        # --- CONTAINER PRINCIPAL ---
        main_container = tk.Frame(self.root, bg=self.colors["bg"])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- SEÇÃO DE INPUT (Card Branco) ---
        input_card = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        input_card.pack(fill="x", pady=(0, 15))

        lbl_instrucoes = ttk.Label(input_card, text="Entrada de Dados", style="SubHeader.TLabel")
        lbl_instrucoes.pack(anchor="w", marginBottom=10)

        # Botão Importar (Estilizado manualmente com tk.Button para cor exata)
        self.btn_importar = tk.Button(input_card, text="📂 Importar Planilha (.csv)", 
                                      bg=self.colors["accent"], fg="white", 
                                      font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                      activebackground="#3498DB", activeforeground="white", pady=8)
        self.btn_importar.pack(fill="x", pady=5)

        lbl_ou = ttk.Label(input_card, text="— ou digite os códigos abaixo —", style="Body.TLabel")
        lbl_ou.pack(pady=5)

        # Área de Texto
        self.txt_input = tk.Text(input_card, height=6, font=("Consolas", 11), 
                                 bd=1, relief="solid", highlightthickness=0)
        self.txt_input.pack(fill="x", pady=5)
        self.txt_input.insert("1.0", "7004461520\n")

        # --- SEÇÃO DE AÇÃO ---
        self.btn_iniciar = tk.Button(main_container, text="🚀 INICIAR DOWNLOADS", 
                                     bg=self.colors["success"], fg="white", 
                                     font=("Segoe UI", 12, "bold"), relief="flat", cursor="hand2",
                                     activebackground="#2ECC71", activeforeground="white", pady=12)
        self.btn_iniciar.pack(fill="x", pady=(0, 15))

        # --- SEÇÃO DE LOG (Terminal) ---
        log_frame = ttk.Frame(main_container, style="Card.TFrame", padding=2) # Borda fina
        log_frame.pack(fill="both", expand=True)

        lbl_log = tk.Label(log_frame, text="Terminal de Execução", bg="white", fg="#7F8C8D", font=("Segoe UI", 9, "bold"))
        lbl_log.pack(anchor="w", padx=5, pady=5)

        self.txt_log = scrolledtext.ScrolledText(log_frame, state='disabled', 
                                                 font=("Consolas", 10), 
                                                 bg=self.colors["log_bg"], 
                                                 fg=self.colors["log_fg"],
                                                 bd=0, highlightthickness=0)
        self.txt_log.pack(fill="both", expand=True)

        # Rodapé
        lbl_footer = tk.Label(self.root, text="v2.0 - Desenvolvido para Petronect Scraper", bg=self.colors["bg"], fg="#95A5A6", font=("Segoe UI", 8))
        lbl_footer.pack(side="bottom", pady=5)

    # --- MÉTODOS DE INTERFACE (Mantidos iguais para compatibilidade) ---

    def set_commands(self, start_cmd, import_cmd):
        self.btn_iniciar.config(command=start_cmd)
        self.btn_importar.config(command=import_cmd)

    def get_input_codes(self):
        raw_text = self.txt_input.get("1.0", tk.END)
        return [c.strip() for c in raw_text.split('\n') if c.strip()]

    def set_input_codes(self, codes_list):
        self.txt_input.delete("1.0", tk.END)
        for code in codes_list:
            self.txt_input.insert(tk.END, f"{code}\n")

    def ask_csv_path(self):
        return filedialog.askopenfilename(
            title="Selecione o arquivo CSV",
            filetypes=[("Arquivos de Dados", "*.csv *.xlsx *.xls"), ("CSV", "*.csv"), ("Todos", "*.*")]
        )

    def update_log(self, message):
        self.txt_log.config(state='normal')
        
        # Adiciona emojis baseados no texto para ficar bonito
        prefix = "•"
        if "Erro" in message or "❌" in message:
            self.txt_log.tag_config("error", foreground="#FF5555")
            tag = "error"
        elif "Sucesso" in message or "✅" in message:
            self.txt_log.tag_config("success", foreground="#50FA7B")
            tag = "success"
        elif "Baixando" in message or "⬇️" in message:
            self.txt_log.tag_config("info", foreground="#8BE9FD")
            tag = "info"
        else:
            tag = "normal"

        self.txt_log.insert(tk.END, f"{message}\n", tag)
        self.txt_log.see(tk.END)
        self.txt_log.config(state='disabled')

    def toggle_buttons(self, state):
        # Mudar a cor visualmente para indicar que está desabilitado
        if state == 'disabled':
            self.btn_iniciar.config(state='disabled', bg="#95a5a6", cursor="arrow")
            self.btn_importar.config(state='disabled', bg="#95a5a6", cursor="arrow")
        else:
            self.btn_iniciar.config(state='normal', bg=self.colors["success"], cursor="hand2")
            self.btn_importar.config(state='normal', bg=self.colors["accent"], cursor="hand2")

    def show_error(self, title, message):
        messagebox.showerror(title, message)
        
    def show_success(self, title, message):
        messagebox.showinfo(title, message)