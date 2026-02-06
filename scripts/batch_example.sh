#!/bin/bash

# ============================================================================
# EXEMPLO: Processar múltiplas missões em batch
# ============================================================================

# Este é um script de exemplo mostrando como processar várias pastas
# de uma vez, tanto no Lightroom quanto no Drive

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║              PROCESSAMENTO EM LOTE - EXEMPLO                                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Ativar ambiente virtual
source venv/bin/activate

# Paths
MANIFEST_PATH="$HOME/acquaplan_manifest.jsonl"
CREDENTIALS="credentials/service-account.json"

# ============================================================================
# PROJETO A - LIGHTROOM
# ============================================================================

echo -e "${GREEN}━━━ PROJETO A: LIGHTROOM ━━━${NC}"
echo ""

# Array de pastas com RAWs
LIGHTROOM_FOLDERS=(
    "/Volumes/Photos/2024/Janeiro_Missao_Laguna"
    "/Volumes/Photos/2024/Fevereiro_Missao_Floripa"
    "/Volumes/Photos/2024/Marco_Missao_Babitonga"
)

for FOLDER in "${LIGHTROOM_FOLDERS[@]}"; do
    if [ -d "$FOLDER" ]; then
        echo -e "${YELLOW}Processando:${NC} $FOLDER"
        
        python src/lightroom_tagger.py "$FOLDER" \
            --manifest "$MANIFEST_PATH"
        
        echo ""
    else
        echo -e "${YELLOW}⚠️  Pasta não encontrada:${NC} $FOLDER"
        echo ""
    fi
done

# ============================================================================
# PROJETO B - GOOGLE DRIVE
# ============================================================================

echo -e "${GREEN}━━━ PROJETO B: GOOGLE DRIVE ━━━${NC}"
echo ""

# Array de IDs de pastas do Drive
DRIVE_FOLDERS=(
    "1A2B3C4D5E6F7G8H"  # Missão Janeiro 2024
    "9I0J1K2L3M4N5O6P"  # Missão Fevereiro 2024
    "7Q8R9S0T1U2V3W4X"  # Missão Março 2024
)

# Verificar se credenciais existem
if [ ! -f "$CREDENTIALS" ]; then
    echo -e "${YELLOW}⚠️  Credenciais não encontradas: $CREDENTIALS${NC}"
    echo "Pulando Projeto B"
else
    for FOLDER_ID in "${DRIVE_FOLDERS[@]}"; do
        echo -e "${YELLOW}Processando pasta Drive:${NC} $FOLDER_ID"
        
        python src/drive_tagger.py "$FOLDER_ID" \
            --credentials "$CREDENTIALS" \
            --manifest "$MANIFEST_PATH"
        
        echo ""
    done
fi

# ============================================================================
# ESTATÍSTICAS FINAIS
# ============================================================================

echo -e "${GREEN}━━━ ESTATÍSTICAS FINAIS ━━━${NC}"
echo ""

python src/manifest_tools.py stats --manifest "$MANIFEST_PATH"

# ============================================================================
# EXPORTAR RESULTADOS
# ============================================================================

echo ""
echo -e "${GREEN}━━━ EXPORTANDO RESULTADOS ━━━${NC}"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# CSV para análise
python src/manifest_tools.py export-analysis \
    --manifest "$MANIFEST_PATH" \
    --output "data/exports/analise_${TIMESTAMP}.csv"

echo ""
echo -e "${GREEN}✓${NC} Exportado: data/exports/analise_${TIMESTAMP}.csv"

# Backup do manifest
cp "$MANIFEST_PATH" "data/manifests/manifest_backup_${TIMESTAMP}.jsonl"
echo -e "${GREEN}✓${NC} Backup: data/manifests/manifest_backup_${TIMESTAMP}.jsonl"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                         PROCESSAMENTO CONCLUÍDO                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
