# 📈 AgenteNazaré Automação Rigorosa em Economia Regional

A **AgenteNazaré** é uma assistente de pesquisa e automação executada no Google Colab.
Focada em Economia Regional, Matrizes de Insumo Produto e Modelos de Equilíbrio Geral Computável,
ela traduz comandos em linguagem natural para scripts de Python ou Stata, orquestrando a coleta
de dados na internet, aplicando algoritmos de regionalização e gerando relatórios precisos.

***

## 🛡️ Vantagens

1. **100% Gratuita e Autônoma** Roda na infraestrutura do Google + API gratuita
2. **Reprodutibilidade Absoluta** Scripts gerados são determinísticos e fiéis aos dados empíricos
3. **Drive Integrado** Cria, acessa e edita pastas e arquivos automaticamente
4. **Baseada em Rigor Matemático** Sem invenção de dados ou resíduos artificiais apenas evidências

***

## 🚀 Como Iniciar

1. No menu superior, clique em **Ambiente de execução Executar tudo**
2. Aguarde 2 minutos enquanto as dependências são instaladas.
3. Clique no botão que irá aparecer e a AgenteNazaré abrirá em uma nova aba.
4. Na primeira vez, clique em **+ provedor IA** e insira sua chave gratuita.

***

## ℹ️ Informações Importantes

* **Navegador** Use preferencialmente o **Google Chrome**.
* **Internet** Conexão estável é obrigatória para ingestão de dados.
* **Google Drive** Os dados e rotinas ficam em Meu Drive/AgenteNazaré/.
* **Permissões** Conceda todas as permissões solicitadas pelo Colab.
* **Rigor Metodológico** A agente pausará a execução caso faltem parâmetros para o cálculo.

***

## 📁 Estrutura do Drive

Meu Drive/
└── AgenteNazaré/
    ├── Dados_Brutos/   dados coletados da internet
    ├── Matrizes/       dados e matrizes balanceadas
    ├── Scripts/        códigos gerados em Python e Stata
    └── Resultados/     planilhas de resultados, multiplicadores e simulações CGE

***

## 💬 Exemplos de comandos para o chat

"Baixe os microdados da RAIS e CAGED para obter a massa salarial por município."

"Calcule a inversa de Leontief e extraia os multiplicadores de produção, emprego e renda."

"Aplique o método de Entropia Cruzada para regionalizar a matriz, sem violar as restrições de convergência."

"Gere o script em Stata para simular o choque econômico de demanda."

"Crie uma visualização com base na matriz de pesos espaciais."

***

## Célula de execução

```python
import os, sys, subprocess, shutil

REPO_URL = "[https://github.com/davilucena-dev/AgenteNazare.git](https://github.com/davilucena-dev/AgenteNazare.git)"
WORK_DIR = "/tmp/agentenazare"

print("⏳ Carregando a AgenteNazaré...")

if os.path.exists(WORK_DIR):
    shutil.rmtree(WORK_DIR)

print("📥 Baixando arquivos...")
subprocess.run(["git", "clone", "--depth", "1", REPO_URL, WORK_DIR], capture_output=True)

os.chdir(WORK_DIR)
sys.path.insert(0, WORK_DIR)

from main import run
run()