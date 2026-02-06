#!/bin/bash

# ============================================================================
# PATCH - Correção de Modelo de Visão
# ============================================================================

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    PATCH - MODELO DE VISÃO CORRETO                           ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}O modelo qwen2-vl:7b não está disponível no Ollama.${NC}"
echo ""
echo "Modelos de visão disponíveis e recomendados:"
echo "  1. llama3.2-vision:11b (RECOMENDADO - melhor qualidade)"
echo "  2. llama3.2-vision (versão padrão ~7B)"
echo "  3. llava:13b (alternativa robusta)"
echo "  4. llava:7b (mais rápido, menor qualidade)"
echo ""
echo "Para o M2 Max com 32 GB, recomendo: llama3.2-vision:11b"
echo ""

read -p "Qual modelo deseja usar? [1-4, padrão=1]: " choice

case $choice in
    2)
        MODEL="llama3.2-vision"
        ;;
    3)
        MODEL="llava:13b"
        ;;
    4)
        MODEL="llava:7b"
        ;;
    *)
        MODEL="llama3.2-vision:11b"
        ;;
esac

echo ""
echo -e "${GREEN}Modelo selecionado: $MODEL${NC}"
echo ""

# Atualizar arquivo de configuração
CONFIG_FILE="config/acquaplan_config.py"

if [ -f "$CONFIG_FILE" ]; then
    echo "Atualizando config/acquaplan_config.py..."
    
    # Backup
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"
    
    # Substituir modelo
    sed -i.bak "s/VISION_MODEL = \"qwen2-vl:7b\"/VISION_MODEL = \"$MODEL\"/" "$CONFIG_FILE"
    
    echo -e "${GREEN}✓${NC} Configuração atualizada"
    echo ""
else
    echo -e "${YELLOW}⚠${NC} Arquivo de configuração não encontrado"
    echo "Execute este script da raiz do projeto acquaplan-tagger/"
    exit 1
fi

# Baixar modelo
echo "Baixando modelo $MODEL..."
echo -e "${YELLOW}Isso pode demorar 10-40 minutos dependendo da conexão${NC}"
echo ""

ollama pull "$MODEL"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓${NC} Modelo $MODEL baixado com sucesso!"
    echo ""
    echo "Testando modelo..."
    ollama run "$MODEL" "Descreva esta imagem em uma frase." --verbose
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                         PATCH APLICADO COM SUCESSO                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Próximo passo:"
    echo "  python scripts/verify_install.py"
    
else
    echo ""
    echo -e "${YELLOW}✗${NC} Erro ao baixar modelo"
    echo ""
    echo "Tente manualmente:"
    echo "  ollama pull $MODEL"
fi
