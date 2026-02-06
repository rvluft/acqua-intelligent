#!/bin/bash

# ============================================================================
# ACQUAPLAN TAGGER - Script de Instalação
# Para Mac com Apple Silicon (M2 Max)
# ============================================================================

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║         ACQUAPLAN INTELLIGENT TAGGER - Instalação Automatizada               ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funções helper
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# ============================================================================
# 1. Verificar sistema
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Verificando sistema..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar se é Mac
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "Este script é para macOS. Sistema detectado: $OSTYPE"
    exit 1
fi

log_info "Sistema: macOS $(sw_vers -productVersion)"

# Verificar arquitetura
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    log_warn "Arquitetura detectada: $ARCH (esperado: arm64 para M2 Max)"
    log_warn "O sistema ainda funcionará, mas pode não ter otimização Metal"
fi

# Verificar Homebrew
if ! command -v brew &> /dev/null; then
    log_error "Homebrew não encontrado!"
    echo "Instale com:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi

log_info "Homebrew: $(brew --version | head -n1)"

# ============================================================================
# 2. Instalar Ollama
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Instalando Ollama..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v ollama &> /dev/null; then
    log_info "Ollama já instalado: $(ollama --version)"
else
    echo "Instalando Ollama via Homebrew..."
    brew install ollama
    log_info "Ollama instalado com sucesso"
fi

# Verificar se Ollama está rodando
if ! pgrep -x "ollama" > /dev/null; then
    log_warn "Ollama não está rodando"
    echo "Iniciando Ollama em background..."
    ollama serve &
    sleep 3
    log_info "Ollama iniciado"
else
    log_info "Ollama já está rodando"
fi

# ============================================================================
# 3. Baixar modelo Llama 3.2 Vision
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Baixando modelo de visão Llama 3.2 Vision (11B)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_warn "Este download pode demorar 10-40 minutos dependendo da conexão"
log_warn "Tamanho aproximado: 7-8 GB"

if ollama list | grep -q "llama3.2-vision:11b"; then
    log_info "Modelo llama3.2-vision:11b já está instalado"
else
    echo "Baixando modelo..."
    ollama pull llama3.2-vision:11b
    log_info "Modelo baixado com sucesso"
fi

# ============================================================================
# 4. Instalar Python e dependências
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Configurando ambiente Python..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar Python 3
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 não encontrado!"
    echo "Instale com: brew install python@3.11"
    exit 1
fi

log_info "Python: $(python3 --version)"

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual Python..."
    python3 -m venv venv
    log_info "Ambiente virtual criado"
else
    log_info "Ambiente virtual já existe"
fi

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências Python..."
pip install --upgrade pip > /dev/null 2>&1

# Dependências core
pip install ollama pillow > /dev/null 2>&1
log_info "Instalado: ollama, pillow"

# ExifTool (via Homebrew, não Python)
if ! command -v exiftool &> /dev/null; then
    echo "Instalando ExifTool..."
    brew install exiftool
    log_info "ExifTool instalado"
else
    log_info "ExifTool já instalado: $(exiftool -ver)"
fi

# Google API (opcional)
echo ""
read -p "Instalar Google Drive API? (s/N): " install_google
if [[ $install_google =~ ^[Ss]$ ]]; then
    pip install google-api-python-client google-auth > /dev/null 2>&1
    log_info "Google Drive API instalada"
else
    log_warn "Google Drive API não instalada (Projeto B ficará indisponível)"
fi

# ============================================================================
# 5. Configurar estrutura de diretórios
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Configurando diretórios de trabalho..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Criar diretórios de dados
mkdir -p data/test_images
mkdir -p data/manifests
mkdir -p data/exports

log_info "Estrutura de diretórios criada"

# ============================================================================
# 6. Verificação final
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Verificação final..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Testar Ollama
if ollama list | grep -q "qwen2-vl:7b"; then
    log_info "Modelo Qwen2-VL disponível"
else
    log_error "Modelo Qwen2-VL não encontrado"
fi

# Testar Python imports
python3 -c "import ollama; from PIL import Image" 2>/dev/null && \
    log_info "Bibliotecas Python OK" || \
    log_error "Erro ao importar bibliotecas Python"

# Testar ExifTool
exiftool -ver > /dev/null 2>&1 && \
    log_info "ExifTool OK" || \
    log_error "ExifTool não funcional"

# ============================================================================
# 7. Próximos passos
# ============================================================================

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                           INSTALAÇÃO CONCLUÍDA! ✓                            ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 PRÓXIMOS PASSOS:"
echo ""
echo "1. Ativar ambiente virtual:"
echo "   source venv/bin/activate"
echo ""
echo "2. Testar com uma imagem:"
echo "   python notebooks/test_notebook.py single <caminho/imagem.jpg>"
echo ""
echo "3. Processar pasta do Lightroom:"
echo "   python src/lightroom_tagger.py /caminho/pasta/raws --dry-run"
echo ""
echo "4. Ver estatísticas:"
echo "   python src/manifest_tools.py stats"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 DOCUMENTAÇÃO:"
echo "   - README.md: Visão geral do sistema"
echo "   - GUIA_USO.md: Tutorial passo-a-passo"
echo ""
echo "❓ PROBLEMAS?"
echo "   1. Certifique-se que Ollama está rodando: ollama serve"
echo "   2. Verifique ambiente virtual: source venv/bin/activate"
echo "   3. Teste modelo: ollama run qwen2-vl:7b \"Olá\""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
