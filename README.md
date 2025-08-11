# Scraper de Oportunidades Petronect

Este script automatiza a busca por códigos de oportunidade no portal de licitações da Petronect, realiza o download dos arquivos anexos e os organiza em pastas locais.

## O que o script faz?
- Navega até o portal de licitações públicas da Petronect.
- Busca por um ou mais códigos de oportunidade, paginando se necessário.
- Para cada código encontrado, cria uma pasta com um nome descritivo (código, objeto, data).
- Baixa todos os arquivos anexos da oportunidade para a pasta correspondente.
- Descompacta arquivos `.zip` que foram baixados.
- Verifica se uma oportunidade já foi baixada (se a pasta já existe) e a ignora para não repetir o trabalho.

## Pré-requisitos

Antes de começar, garanta que você tenha os seguintes softwares instalados:

- **Python 3.7 ou superior**
- **Navegador Google Chrome**

## Instalação

Siga os passos abaixo para configurar o ambiente e instalar as dependências do projeto.

1.  **Clone o repositório ou salve o script**
    Baixe o arquivo `.py` para uma pasta de sua escolha em seu computador.

2.  **Abra o Terminal**
    Navegue através do seu terminal (Prompt de Comando, PowerShell, etc.) até a pasta onde você salvou o script.

3.  **Instale as bibliotecas Python**
    Execute o comando abaixo para instalar todas as bibliotecas necessárias de uma só vez:
    ```bash
    pip install pandas selenium webdriver-manager beautifulsoup4 requests openpyxl
    ```

## Como Usar

1.  Com o terminal aberto na pasta correta, execute o script com o seguinte comando:
    ```bash
    python nome_do_seu_script.py
    ```
2.  O script irá pedir para você escolher o modo de operação:
    * **Modo 1: Buscar um código individual**
        - Digite `1` e pressione Enter.
        - Em seguida, digite o código da oportunidade que deseja buscar.

    * **Modo 2: Processar um arquivo com múltiplos códigos**
        - Digite `2` e pressione Enter.
        - Forneça o caminho completo para o seu arquivo (`.csv` ou `.xlsx`).
        - **Importante:** O arquivo precisa ter uma coluna com o cabeçalho **`oportunidade`**, contendo a lista dos códigos a serem processados.

3.  Aguarde o script finalizar. Ele irá abrir uma janela do Google Chrome para realizar a automação e exibirá o progresso no terminal.

## Estrutura de Saída

Para cada oportunidade processada com sucesso, uma nova pasta será criada no mesmo diretório do script. O nome da pasta seguirá o formato:

`[CódigoDaOportunidade]_[ObjetoDaOportunidade]_[DataDeFim]`

**Exemplo:** `7770012345_AQUISICAO DE VALVULAS_30_09_2025`
