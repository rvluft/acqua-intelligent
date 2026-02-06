#!/usr/bin/env python3
"""
Script de verificação da instalação do Acquaplan Tagger
Testa todos os componentes antes de começar a usar
"""

import sys
import subprocess
from pathlib import Path

# Cores para terminal
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*80}{NC}")
    print(f"{BLUE}{text.center(80)}{NC}")
    print(f"{BLUE}{'='*80}{NC}\n")

def check_item(name, condition, error_msg=""):
    """Verifica um item e imprime resultado"""
    if condition:
        print(f"{GREEN}✓{NC} {name}")
        return True
    else:
        print(f"{RED}✗{NC} {name}")
        if error_msg:
            print(f"  {YELLOW}→{NC} {error_msg}")
        return False

def run_command(cmd, capture=True):
    """Executa comando e retorna saída"""
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0, result.stdout.strip()
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, ""
    except:
        return False, ""

def main():
    print_header("ACQUAPLAN TAGGER - VERIFICAÇÃO DE INSTALAÇÃO")
    
    all_ok = True
    
    # ========================================================================
    # 1. Sistema Operacional
    # ========================================================================
    print_header("1. Sistema Operacional")
    
    success, os_info = run_command("uname -s")
    all_ok &= check_item(
        f"Sistema: {os_info}",
        "Darwin" in os_info,
        "Este sistema é otimizado para macOS"
    )
    
    success, arch = run_command("uname -m")
    all_ok &= check_item(
        f"Arquitetura: {arch}",
        success,
        "arm64 (Apple Silicon) tem melhor performance"
    )
    
    # ========================================================================
    # 2. Homebrew
    # ========================================================================
    print_header("2. Homebrew")
    
    success, brew_version = run_command("brew --version")
    all_ok &= check_item(
        "Homebrew instalado",
        success,
        "Instale com: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    )
    
    # ========================================================================
    # 3. Ollama
    # ========================================================================
    print_header("3. Ollama")
    
    success, _ = run_command("which ollama")
    all_ok &= check_item(
        "Ollama instalado",
        success,
        "Instale com: brew install ollama"
    )
    
    success, _ = run_command("pgrep ollama")
    check_item(
        "Ollama rodando",
        success,
        "Inicie com: ollama serve (em outra janela)"
    )
    
    success, models_output = run_command("ollama list")
    has_model = "llama3.2-vision" in models_output or "llava" in models_output
    all_ok &= check_item(
        "Modelo de visão instalado",
        has_model,
        "Baixe com: ollama pull llama3.2-vision:11b (recomendado) ou ollama pull llava:13b"
    )
    
    # ========================================================================
    # 4. Python
    # ========================================================================
    print_header("4. Python")
    
    success, py_version = run_command("python3 --version")
    all_ok &= check_item(
        f"Python: {py_version}",
        success and "Python 3" in py_version,
        "Instale com: brew install python@3.11"
    )
    
    # Verificar ambiente virtual
    venv_path = Path("venv")
    check_item(
        "Ambiente virtual criado",
        venv_path.exists(),
        "Crie com: python3 -m venv venv"
    )
    
    # ========================================================================
    # 5. Dependências Python
    # ========================================================================
    print_header("5. Dependências Python")
    
    try:
        import ollama
        check_item("ollama (Python)", True)
    except ImportError:
        all_ok &= check_item(
            "ollama (Python)",
            False,
            "Instale com: pip install ollama"
        )
    
    try:
        from PIL import Image
        check_item("Pillow", True)
    except ImportError:
        all_ok &= check_item(
            "Pillow",
            False,
            "Instale com: pip install pillow"
        )
    
    try:
        from google.oauth2 import service_account
        check_item("Google API (opcional)", True)
    except ImportError:
        check_item(
            "Google API (opcional)",
            False,
            "Opcional para Projeto B. Instale com: pip install google-api-python-client google-auth"
        )
    
    # ========================================================================
    # 6. ExifTool
    # ========================================================================
    print_header("6. ExifTool")
    
    success, exif_version = run_command("exiftool -ver")
    all_ok &= check_item(
        f"ExifTool: {exif_version}",
        success,
        "Instale com: brew install exiftool"
    )
    
    # ========================================================================
    # 7. Estrutura de Diretórios
    # ========================================================================
    print_header("7. Estrutura de Diretórios")
    
    dirs_to_check = [
        "src",
        "config",
        "scripts",
        "notebooks",
        "data",
        "data/test_images",
        "data/manifests",
        "data/exports",
        "credentials"
    ]
    
    for dir_name in dirs_to_check:
        dir_path = Path(dir_name)
        check_item(
            f"Diretório: {dir_name}",
            dir_path.exists() and dir_path.is_dir()
        )
    
    # ========================================================================
    # 8. Arquivos Principais
    # ========================================================================
    print_header("8. Arquivos Principais")
    
    files_to_check = [
        "src/vision_pipeline.py",
        "src/lightroom_tagger.py",
        "src/drive_tagger.py",
        "src/manifest_tools.py",
        "config/acquaplan_config.py",
        "notebooks/test_notebook.py",
        "README.md",
        "GUIA_USO.md",
        "QUICKSTART.md"
    ]
    
    for file_name in files_to_check:
        file_path = Path(file_name)
        check_item(
            f"Arquivo: {file_name}",
            file_path.exists() and file_path.is_file()
        )
    
    # ========================================================================
    # 9. Teste Rápido
    # ========================================================================
    print_header("9. Teste Rápido (opcional)")
    
    print(f"{YELLOW}Deseja testar a conexão com Ollama?{NC} (s/N): ", end="")
    response = input().strip().lower()
    
    if response == 's':
        print("\nTestando conexão com modelo...")
        try:
            import ollama
            response = ollama.chat(
                model='llama3.2-vision:11b',
                messages=[{
                    'role': 'user',
                    'content': 'Responda apenas "OK"'
                }]
            )
            check_item(
                "Comunicação com Llama 3.2 Vision",
                True,
                f"Resposta: {response['message']['content']}"
            )
        except Exception as e:
            check_item(
                "Comunicação com Llama 3.2 Vision",
                False,
                f"Erro: {e}"
            )
    
    # ========================================================================
    # Resultado Final
    # ========================================================================
    print_header("RESULTADO DA VERIFICAÇÃO")
    
    if all_ok:
        print(f"{GREEN}✓ TUDO OK!{NC}")
        print("\nVocê pode começar a usar o sistema:")
        print(f"\n  1. Ative o ambiente virtual:")
        print(f"     {BLUE}source venv/bin/activate{NC}")
        print(f"\n  2. Teste com uma imagem:")
        print(f"     {BLUE}python notebooks/test_notebook.py single foto.jpg{NC}")
        print(f"\n  3. Veja o Quick Start:")
        print(f"     {BLUE}cat QUICKSTART.md{NC}")
    else:
        print(f"{RED}✗ ALGUNS COMPONENTES FALTANDO{NC}")
        print("\nRevise os itens marcados com ✗ acima e siga as instruções.")
        print(f"\nPara reinstalar tudo:")
        print(f"  {BLUE}./scripts/install.sh{NC}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
