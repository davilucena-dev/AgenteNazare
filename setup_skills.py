import os
import shutil
import subprocess
import time

# Tenta importar o tqdm otimizado para Colab (notebook), senão usa o padrão
try:
    from tqdm.notebook import tqdm
except ImportError:
    from tqdm import tqdm

SKILLS_DIR = os.path.expanduser("~/.agents/skills")

# Skills externas (vazio por enquanto, mas a barra já vai contabilizar se você adicionar)
REMOTE_SKILLS = [
    ("https://github.com/davilucena-dev/Skill-regionalizacao-mip.git", "regionalizacao-mip"),
    ("https://github.com/davilucena-dev/Skill_estimacao-impacto-economico.git", "estimacao-impacto-economico"),
]

def create_local_skills_with_progress(pbar):
    """Cria as skills locais e atualiza a barra de progresso."""
    os.makedirs(SKILLS_DIR, exist_ok=True)

    # 1. Skill: gestao-drive-nazare
    pbar.set_description("📈 Instalando: gestao-drive-nazare")
    skill_drive_dir = os.path.join(SKILLS_DIR, "gestao-drive-nazare")
    os.makedirs(skill_drive_dir, exist_ok=True)
    with open(os.path.join(skill_drive_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("# Skill: Gestão do Drive\nPermite criar estrutura de pastas: Dados_Brutos, Scripts, Matrizes, Resultados.")
    time.sleep(0.5) # Pausa leve apenas para o visual da barra no Colab
    pbar.update(1)

    # 2. Skill: extracao-dados-oficiais
    pbar.set_description("📊 Instalando: extracao-dados")
    extracao_dir = os.path.join(SKILLS_DIR, "extracao-dados-oficiais")
    os.makedirs(extracao_dir, exist_ok=True)
    with open(os.path.join(extracao_dir, "scraping_core.py"), "w") as f:
        f.write("import sidrapy\nimport ipeadatapy as ipa")
    time.sleep(0.5)
    pbar.update(1)

    # 3. Skill: algebra-matrizes
    pbar.set_description("📐 Instalando: algebra-matrizes")
    algebra_dir = os.path.join(SKILLS_DIR, "algebra-matrizes")
    os.makedirs(algebra_dir, exist_ok=True)
    with open(os.path.join(algebra_dir, "matrizes_core.py"), "w") as f:
        f.write("import numpy as np")
    time.sleep(0.5)
    pbar.update(1)

    # 4. Skill: geracao-scripts
    pbar.set_description("⚙️ Instalando: geracao-scripts")
    scripts_dir = os.path.join(SKILLS_DIR, "geracao-scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    with open(os.path.join(scripts_dir, "SKILL.md"), "w") as f:
        f.write("# Skill: Geração de Scripts\nFocado em exportar resultados para .py ou .do com semente fixa.")
    time.sleep(0.5)
    pbar.update(1)


def install_skills():
    os.chdir("/tmp")
    print("\n🔧 Iniciando o motor da AgenteNazaré...\n")

    # Quantidade total de passos: 4 locais + quantidade de skills remotas
    total_skills = 4 + len(REMOTE_SKILLS)
    
    # Inicia a barra de progresso (verde para combinar com o tema)
    with tqdm(total=total_skills, desc="Iniciando...", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]", colour='green') as pbar:
        
        # Instala as locais
        create_local_skills_with_progress(pbar)

        # Instala as remotas (se existirem)
        for repo_url, name in REMOTE_SKILLS:
            pbar.set_description(f"🌐 Baixando: {name}")
            tmp = f"/tmp/skill_{name}"
            if os.path.exists(tmp):
                shutil.rmtree(tmp)
            
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, tmp],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                dest = os.path.join(SKILLS_DIR, name)
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(tmp, dest, dirs_exist_ok=True)
            
            time.sleep(0.5)
            pbar.update(1)

    print("\n🎉 Todas as skills da AgenteNazaré foram carregadas com sucesso!")

if __name__ == "__main__":
    install_skills()
