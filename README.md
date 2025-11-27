# Scraper de Oportunidades Petronect

Este script automatiza a busca por códigos de oportunidade no portal de licitações da Petronect, realiza o download dos arquivos anexos e os organiza em pastas locais.

https://www.petronect.com.br/irj/go/km/docs/pccshrcontent/Site%20Content%20(Legacy)/Portal2018/pt/lista_licitacoes_publicadas_ft.html

## O que o script faz?
- Navega até o portal de licitações públicas da Petronect.
- Busca por um ou mais códigos de oportunidade.
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
    pip install -r requirements.txt
    ```

## Como Usar

1.  Com o terminal aberto na pasta correta, execute o script com o seguinte comando:
    ```bash
    python main.py
    ```
2.  Uma interface será aberta, permitindo importar um csv ou inserir manualmente os códigos:

    * **Processar um arquivo com múltiplos códigos**
        - CLique no botão de importar CSV e selecione seu arquivo
        - **Importante:** O arquivo precisa ter uma coluna com o cabeçalho **`oportunidade`**, contendo a lista dos códigos a serem processados.

3.  Aguarde o script finalizar. Ele irá abrir uma janela do Google Chrome para realizar a automação e exibirá o progresso no terminal.

## Estrutura de Saída

Para cada oportunidade processada com sucesso, uma nova pasta será criada no mesmo diretório do script. O nome da pasta seguirá o formato:

`[CódigoDaOportunidade]_[ObjetoDaOportunidade]_[DataDeFim]`

**Exemplo:** `7770012345_AQUISICAO DE VALVULAS_30_09_2025`
