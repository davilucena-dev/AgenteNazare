import os
import json
import subprocess
import shutil

THEME_DIR = os.path.expanduser("~/.config/opencode/themes")
AGENT_DIR = os.path.expanduser("~/.config/opencode/agents")
TUI_JSON  = os.path.expanduser("~/.config/opencode/tui.json")
OPENCODE_CFG = os.path.expanduser("~/.config/opencode/config.json")

OPENCODE_BIN = None

JOKES_INSTALL = [
    "📈 Consultando matrizes de insumo-produto...",
    "📊 Calibrando coeficientes técnicos...",
    "📚 Indexando microdados RAIS e CAGED...",
    "🔧 Preparando motor de cálculo regional...",
]

_joke_index = 0

def next_joke():
    global _joke_index
    joke = JOKES_INSTALL[_joke_index % len(JOKES_INSTALL)]
    _joke_index += 1
    return joke


def run(cmd, check=True, **kw):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result


def find_opencode_binary():
    global OPENCODE_BIN

    _candidates = [
        os.path.expanduser("~/.local/bin/opencode"),
        os.path.expanduser("~/bin/opencode"),
        "/root/.local/bin/opencode",
        "/root/bin/opencode",
        "/usr/local/bin/opencode",
        "/usr/bin/opencode",
    ]
    _found = next((p for p in _candidates if os.path.isfile(p)), None)

    if _found is None:
        result = subprocess.run(
            ["find", "/root", "/home", "/usr/local", "-name", "opencode", "-type", "f"],
            capture_output=True, text=True
        )
        hits = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        _found = hits[0] if hits else None

    if _found:
        OPENCODE_BIN = _found
        _bin_dir = os.path.dirname(_found)
        if _bin_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _bin_dir + ":" + os.environ["PATH"]
        os.environ["OPENCODE_BIN"] = _found
        print(f"✅ opencode encontrado: {_found}")
        try:
            subprocess.run([_found, "--version"])
        except Exception:
            pass
    else:
        print("❌ opencode NÃO encontrado.")

    return _found


def install_opencode():
    print(f"\n{next_joke()}")
    print("📦 Instalando OpenCode...")
    run("curl -fsSL https://opencode.ai/install | bash", check=True)

    print(f"\n{next_joke()}")
    print("📦 Instalando uv...")
    run("curl -LsSf https://astral.sh/uv/install.sh | sh", check=False)

    print(f"\n{next_joke()}")
    print("📦 Instalando ferramentas auxiliares...")
    run("apt-get update -qq && apt-get install -y -qq xclip xsel", check=False)

    print("📦 Instalando dependências de Economia e Dados...")
    run(
        "pip install "
        "pandas numpy scipy statsmodels geopandas sidrapy ipeadatapy "
        "google-api-python-client google-auth-httplib2 gspread openpyxl --quiet",
        check=False,
    )

    find_opencode_binary()
    print("✅ OpenCode instalado.")


def create_directories():
    for d in [THEME_DIR, AGENT_DIR]:
        os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.dirname(OPENCODE_CFG), exist_ok=True)


def setup_theme():
    """Tema AgenteNazaré — verde institucional (crescimento/dados)."""
    theme = {
        "$schema": "https://opencode.ai/theme.json",
        "defs": {
            "bg0":        "#090b0a",
            "bg1":        "#0e130e",
            "bg2":        "#162016",
            "bg3":        "#203020",
            "bg4":        "#2c402c",
            "fg0":        "#e8f0e8",
            "fg1":        "#849984",
            "fg2":        "#425542",
            "fg3":        "#284028",
            "green":      "#4caf50",
            "greenDim":   "#1b5e20",
            "greenGlow":  "#2e7d32",
            "amber":      "#e8b84b",
            "red":        "#e07070",
            "blue":       "#5b8cdb",
            "cyan":       "#56d8cc",
            "silver":     "#b0d4bc",
            "purple":     "#b4b0e0",
            "synKeyword": "#4caf50",
            "synString":  "#81c784",
            "synComment": "#425542",
            "synNumber":  "#e8b84b",
            "synFunction":"#66bb6a",
            "synType":    "#b4b0e0",
            "synOp":      "#849984",
        },
        "theme": {
            "primary":            {"dark": "green",    "light": "greenDim"},
            "secondary":          {"dark": "cyan",     "light": "cyan"},
            "accent":             {"dark": "silver",   "light": "silver"},
            "error":              {"dark": "red",      "light": "red"},
            "warning":            {"dark": "amber",    "light": "amber"},
            "success":            {"dark": "green",    "light": "green"},
            "info":               {"dark": "blue",     "light": "blue"},
            "text":               {"dark": "fg0",      "light": "fg0"},
            "textMuted":          {"dark": "fg1",      "light": "fg1"},
            "background":         {"dark": "bg0",      "light": "bg0"},
            "backgroundPanel":    {"dark": "bg1",      "light": "bg1"},
            "backgroundElement":  {"dark": "bg2",      "light": "bg2"},
            "border":             {"dark": "bg3",      "light": "bg3"},
            "borderActive":       {"dark": "bg4",      "light": "bg4"},
            "syntaxKeyword":      {"dark": "synKeyword","light":"synKeyword"},
            "syntaxString":       {"dark": "synString", "light":"synString"},
            "syntaxComment":      {"dark": "synComment","light":"synComment"},
            "syntaxNumber":       {"dark": "synNumber", "light":"synNumber"},
            "syntaxFunction":     {"dark": "synFunction","light":"synFunction"},
            "syntaxType":         {"dark": "synType",   "light":"synType"},
            "syntaxOperator":     {"dark": "synOp",     "light":"synOp"},
            "markdownHeading":    {"dark": "green",     "light":"green"},
            "markdownCode":       {"dark": "amber",     "light":"amber"},
        }
    }

    theme_path = os.path.join(THEME_DIR, "nazare.json")
    with open(theme_path, "w") as f:
        json.dump(theme, f, indent=2)

    tui = {"$schema": "https://opencode.ai/tui.json", "theme": "nazare"}
    with open(TUI_JSON, "w") as f:
        json.dump(tui, f, indent=2)

    print("✅ Tema AgenteNazaré configurado:", theme_path)


def setup_agent():
    """Escreve o system prompt da AgenteNazaré e define como agente padrão."""

    agent_md = """\
---
name: AgenteNazaré
description: Agente de pesquisa em Economia Regional, Matrizes Insumo-Produto (MIP) e modelos CGE. Gera scripts determinísticos e orquestra coleta de microdados oficiais.
color: "#4caf50"
---

## 1. Identidade e Missão

Você é a **AgenteNazaré**, especialista autônoma em Economia Regional, Matrizes de Insumo-Produto e Equilíbrio Geral Computável.

Sua missão é traduzir comandos de pesquisa em scripts rigorosos (Python/Stata), realizar coleta autônoma de microdados e aplicar métodos de regionalização.

**Regra de Ouro:** Reprodutibilidade absoluta. Você **nunca inventa números**, não cria resíduos artificiais para fechar matrizes e não preenche lacunas sem instrução. Se faltarem dados, pause e solicite ao usuário.

**Créditos de Desenvolvimento:**
- Criador: Davi Lucena da Silva
- Cargo: Doutorando em Economia pela UFV
- Contato: davilucenas99@gmail.com | 88998642605

---

## 2. Ambiente de Trabalho

- **Diretório raiz:** `/content/drive/My Drive/AgenteNazaré/`
- **Estrutura de diretórios:**
    - `Dados_Brutos/`: Microdados (RAIS, CAGED, contas regionais) e APIs.
    - `Scripts/`: Códigos de automação (.py, .do) rastreáveis.
    - `Matrizes/`: Tabelas de recursos/usos e matrizes regionalizadas.
    - `Resultados/`: Multiplicadores, tabelas e visualizações.

---

## 3. Diretrizes de Ingestão de Dados

Você tem acesso irrestrito para:
- **IBGE/SIDRA:** Contas regionais, PIA, PAM, Matrizes de insumo-produto.
- **MTE (PDET):** Microdados RAIS/CAGED para massa salarial e emprego.
- **IPEADATA:** Séries históricas e deflatores.
- **Comex Stat:** Dados de comércio exterior.

*Rigor:* Todo passo de limpeza deve ser codificado. Nunca crie *proxies* não autorizados.

---

## 4. Procedimentos Analíticos

- **Regionalização:** Aplicação de Quocientes Locacionais (QL).
- **Balanceamento:** Métodos RAS ou Entropia Cruzada. Proibido forçar fechamento artificial que viole restrições teóricas.
- **Álgebra Linear:** Inversa de Leontief $L=(I-A)^{-1}$. Se não houver dados de fechamento para famílias, declare incapacidade analítica.
- **Simulações CGE:** Fiel aos parâmetros de choque. Toda correlação espacial exige base estatística robusta.

---

## 5. Exemplo de Interação

**Usuário:** "Calcule a inversa de Leontief da matriz regionalizada."

**AgenteNazaré:**
> 1. Validando singularidade da matriz (I - A)...
> 2. Calculando inversa...
> 3. Extraindo multiplicadores de produção.
>
> [📄 Arquivo Gerado] multiplicadores_setoriais_DDMMAAAA.csv — salvo em AgenteNazaré/Resultados/

---
*AgenteNazaré · Automação Rigorosa em Economia Regional*
"""

    agent_path = os.path.join(AGENT_DIR, "nazare.md")
    with open(agent_path, "w", encoding="utf-8") as f:
        f.write(agent_md)

    try:
        with open(OPENCODE_CFG) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}

    cfg["default_agent"] = "nazare"

    with open(OPENCODE_CFG, "w") as f:
        json.dump(cfg, f, indent=2)

    print("✅ AgenteNazaré configurada:", agent_path)


def run_all():
    install_opencode()
    create_directories()
    setup_theme()
    setup_agent()
    print("\n🎉 Dependências e configurações da AgenteNazaré concluídas!")


if __name__ == "__main__":
    run_all()