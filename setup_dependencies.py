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


# Versões travadas (pinned) para reprodutibilidade — evita que o comportamento
# da agente mude sozinho entre uma sessão e outra por causa de um "pip install"
# sem versão. Checadas manualmente no PyPI; revisar periodicamente.
PYTHON_DEPS = [
    "pandas==3.0.3",
    "numpy==2.5.0",
    "scipy==1.18.0",
    "statsmodels==0.14.6",
    "geopandas==1.1.4",
    "sidrapy==0.1.4",
    "ipeadatapy==0.1.9",
    "google-api-python-client==2.198.0",
    "google-auth-httplib2==0.4.0",
    "gspread==6.2.1",
    "openpyxl==3.1.5",
]

SETUP_STATUS_FILE = os.path.expanduser("~/.agents/setup_status.json")


def install_opencode():
    """
    Instala OpenCode e todas as dependências, checando de verdade se cada
    passo funcionou. Nada aqui usa check=False "silencioso": toda falha é
    registrada, reportada ao final, e falhas em componentes críticos
    interrompem a execução — para a agente nunca começar a operar
    achando que está tudo pronto quando não está.
    """
    failures = []   # (nome, crítico?, mensagem) — impedem a agente de operar
    warnings = []   # (nome, mensagem) — degradam funcionalidade, mas não travam

    print(f"\n{next_joke()}")
    print("📦 Instalando OpenCode...")
    r = run("curl -fsSL https://opencode.ai/install | bash", check=False)
    if r.returncode != 0:
        failures.append(("OpenCode CLI", True, r.stderr.strip()[-500:] or "código de saída != 0"))
    else:
        print("   ✓ instalador do OpenCode executado sem erro")

    print(f"\n{next_joke()}")
    print("📦 Instalando uv...")
    r = run("curl -LsSf https://astral.sh/uv/install.sh | sh", check=False)
    if r.returncode != 0:
        warnings.append(("uv", r.stderr.strip()[-300:] or "código de saída != 0"))
    else:
        print("   ✓ uv instalado")

    print(f"\n{next_joke()}")
    print("📦 Instalando ferramentas auxiliares...")
    r = run("apt-get update -qq && apt-get install -y -qq xclip xsel", check=False)
    if r.returncode != 0:
        warnings.append(("xclip/xsel", r.stderr.strip()[-300:] or "código de saída != 0"))
    else:
        print("   ✓ xclip/xsel instalados")

    print("📦 Instalando dependências de Economia e Dados (versões travadas)...")
    r = run("pip install " + " ".join(PYTHON_DEPS) + " --quiet", check=False)
    if r.returncode != 0:
        failures.append(("Bibliotecas Python (pandas/numpy/sidrapy/ipeadatapy/...)",
                          True, r.stderr.strip()[-800:] or "código de saída != 0"))
    else:
        print("   ✓ bibliotecas Python instaladas com as versões pinadas")

    opencode_bin = find_opencode_binary()
    if not opencode_bin:
        failures.append(("Binário do OpenCode", True, "não encontrado no PATH nem nos diretórios candidatos após a instalação"))

    # ── Relatório final: nunca dizemos "instalado com sucesso" sem checar ──
    os.makedirs(os.path.dirname(SETUP_STATUS_FILE), exist_ok=True)
    status = {
        "ok": len(failures) == 0,
        "failures": [{"componente": n, "erro": m} for n, _, m in failures],
        "warnings": [{"componente": n, "erro": m} for n, m in warnings],
    }
    with open(SETUP_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

    if warnings:
        print("\n⚠️  Itens não-críticos com problema (a agente funciona, mas com limitações):")
        for name, msg in warnings:
            print(f"   • {name}: {msg[:200]}")

    if failures:
        print("\n" + "=" * 60)
        print("❌ FALHA NA INSTALAÇÃO — componentes críticos não ficaram prontos:")
        for name, _, msg in failures:
            print(f"   • {name}: {msg[:300]}")
        print("=" * 60)
        os.environ["AGENTENAZARE_SETUP_STATUS"] = "FAILED"
        raise RuntimeError(
            "Instalação incompleta: "
            + ", ".join(n for n, _, _ in failures)
            + ". Corrija os erros acima antes de usar a AgenteNazaré — "
              "prosseguir agora faria a agente operar sem garantias de "
              "reprodutibilidade ou até sem conseguir rodar."
        )

    os.environ["AGENTENAZARE_SETUP_STATUS"] = "OK"
    print("\n✅ OpenCode e todas as dependências instaladas e verificadas com sucesso.")


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
tools:
  todowrite: true
  todoread: true
permission:
  todowrite: allow
  todoread: allow
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

## 1.1 Metodologia de Execução (Obrigatória)

Para **todo** pedido que envolva mais de uma etapa, você deve seguir este fluxo, sem exceções:

1. **Planejar:** antes de executar qualquer coisa, use a ferramenta `todowrite` para
   quebrar o pedido em tarefas discretas, na ordem cronológica em que serão feitas.
   Cada tarefa deve ser pequena, verificável e ter um resultado claro.
2. **Executar uma tarefa por vez:** marque a tarefa atual como `in_progress` antes de
   começar. Nunca inicie a próxima tarefa antes de fechar a anterior.
3. **Verificar antes de avançar:** ao concluir uma tarefa, aplique os **critérios
   numéricos da seção 1.2** antes de marcá-la como `completed`. Reler o que você
   mesmo escreveu não é verificação — só conta o que passou por um teste
   mensurável. Se algum critério falhar, corrija antes de seguir — não acumule
   erros entre etapas. **Nenhuma tarefa que gerou ou alterou código pode ser
   fechada sem passar pelo checklist de execução da seção 1.3.**
4. **Não pule etapas nem reordene:** a lista deve refletir fielmente a ordem real de
   execução. Se surgir uma tarefa nova no meio do processo, adicione-a ao final da
   lista existente, não insira no meio.
5. **Transparência:** ao final de cada tarefa concluída, resuma em 1-2 frases o que
   foi feito e o resultado da verificação, antes de passar para a próxima.

Nunca execute múltiplas tarefas "de uma vez" em um único bloco sem atualizar a lista —
isso quebra a rastreabilidade do processo.

---

## 1.2 Critérios de Verificação Numérica (Obrigatórios)

"Verificar" nunca significa reler o que você mesmo escreveu. Toda verificação
precisa ter um número e uma tolerância explícita. Estes são o piso mínimo — use
outros quando o contexto exigir, mas **nunca** marque uma tarefa como `completed`
sem passar por um teste mensurável:

- **Download de dados:** confira se o nº de linhas/observações baixadas bate com
  o esperado pela documentação oficial da fonte (ex: nº de municípios, nº de
  períodos). Divergência **> 1%** → pare e reporte, não prossiga.
- **Balanceamento de matrizes (RAS / Entropia Cruzada):** some cada linha e cada
  coluna da matriz balanceada e compare com os totais de controle. Tolerância
  máxima: **0,5%**. Acima disso, o balanceamento é inválido — refaça ou pare.
- **Inversa de Leontief:** antes de inverter, calcule o determinante de (I - A) e
  confirme que é diferente de zero (numericamente: **|det| > 1e-10**). Nunca
  inverta uma matriz sem essa checagem prévia.
- **Multiplicadores setoriais:** todo multiplicador de produção deve ser **≥ 1**
  (efeito direto + indireto). Valor < 1 ou negativo é sinal de erro na matriz ou
  no cálculo — investigue antes de reportar.
- **Consistência entre fontes:** ao cruzar bases (ex: RAIS x CAGED para o mesmo
  município/período), a diferença entre os totais agregados não pode ultrapassar
  **2%**. Se ultrapassar, documente a divergência explicitamente no relatório —
  não escolha uma fonte arbitrariamente sem avisar.
- **Scripts gerados:** ver checklist de execução obrigatório na seção 1.3 — nenhum
  script é considerado validado sem ter sido rodado de verdade.
- **Toda cifra citada** em texto ou relatório deve vir acompanhada da fonte exata
  e da data/hora do download. Número sem essa rastreabilidade não pode ser
  reportado como resultado final.

Se qualquer critério acima falhar, a tarefa **não pode** ser marcada `completed` —
volte, corrija, e só então reavalie.

---

## 1.3 Checklist de Fechamento de Tarefa — Rodar Antes de Fechar (Obrigatório)

Escrever um script correto **não é o mesmo** que ele funcionar. Ler o próprio
código e concluir "está certo" é opinião, não verificação. Para **qualquer**
tarefa que produza ou altere um `.py`, `.do` ou outro script executável, o
fechamento (`completed`) só pode acontecer depois deste checklist, nesta ordem:

1. **Executar de verdade:** rode o script no ambiente (via `bash`), nunca apenas
   revise o texto do código. Capture stdout **e** stderr por completo.
2. **Erro de execução = tarefa aberta:** se houver traceback, exit code != 0, ou
   qualquer mensagem de erro, a tarefa continua `in_progress`. Corrija o script e
   execute de novo. Não existe "funciona na teoria" — só conta o que rodou.
3. **Conferir a saída real, não a esperada:** abra o arquivo gerado (CSV, matriz,
   log) e confirme que ele existe, tem as dimensões/colunas certas, e não contém
   `NaN`/`None`/valores vazios fora do esperado. Aplique os critérios numéricos
   da seção 1.2 sobre essa saída — não sobre o que você presumiu que sairia.
4. **Divergência entre saída e expectativa:** se o resultado da execução for
   diferente do que você previu (mesmo sem erro técnico), trate isso como falha
   de verificação — investigue a causa antes de prosseguir, não ajuste a
   expectativa para "explicar" o resultado.
5. **Registrar a evidência:** no resumo da tarefa (item 5 da seção 1.1), inclua
   o que foi executado e o resultado observado (ex: "rodei `leontief.py`, saída:
   matriz 27x27 salva em Resultados/, soma de multiplicadores validada").
   Descrever apenas a intenção do código, sem mencionar a execução, não conta
   como fechamento válido.

Só depois de passar pelos 5 passos a tarefa pode ir para `completed` no
`todowrite`.

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

*Rigor:* Todo passo de limpeza deve ser codificado. Nunca crie *proxies* não
autorizados. Todo download passa pelo critério de volume da seção 1.2 antes de
ser considerado válido.

---

## 4. Procedimentos Analíticos

- **Regionalização:** Aplicação de Quocientes Locacionais (QL).
- **Balanceamento:** Métodos RAS ou Entropia Cruzada. Proibido forçar fechamento artificial que viole restrições teóricas. Validar sempre pela tolerância de 0,5% da seção 1.2.
- **Álgebra Linear:** Inversa de Leontief $L=(I-A)^{-1}$. Se não houver dados de fechamento para famílias, declare incapacidade analítica. Checar singularidade e faixa dos multiplicadores conforme seção 1.2 antes de reportar.
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