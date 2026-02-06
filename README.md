# Acquaplan Intelligent Tagger

Sistema **self-hosted** de tagueamento inteligente para acervos fotográficos científicos de ecologia costeira, usando IA rodando localmente no Mac M2 Max.

## 🎯 Objetivo

Processar milhares de fotos de missões de campo (manguezais, restingas, costões rochosos, etc.) e gerar automaticamente:

- **Descrições detalhadas e científicas**
- **Classificação de habitats/biomas** (manguezal, restinga, Mata Atlântica, etc.)
- **Identificação de espécies** (fauna e flora costeira)
- **Detecção de sítios arqueológicos** (sambaquis, depósitos antrópicos)
- **Keywords hierárquicas** (30-80 por imagem)

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────┐
│   NÚCLEO DE IA (Qwen2-VL 7B via Ollama)     │
│   Roda localmente com aceleração Metal      │
│   → Pass 1: Extração visual                 │
│   → Pass 2: Normalização e vocabulário      │
└─────────────────────────────────────────────┘
                    ↓
          manifest.jsonl (único)
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
  PROJETO A                PROJETO B
  Lightroom               Google Drive
  RAWs → XMP              JPEGs → Description
  ExifTool                API Drive
```

### Dois Projetos Paralelos

**Projeto A - Lightroom (RAW-first tagging)**
- Lê: Arquivos RAW do Lightroom
- Grava: XMP sidecars + keywords
- Objetivo: Taguear na origem, exports herdam metadados

**Projeto B - Google Drive (Distribution metadata)**
- Lê: JPEGs/TIFFs exportados no Drive
- Grava: Campo `description` do Google Drive
- Objetivo: Metadados onde o público acessa

## 🚀 Instalação Rápida

### Pré-requisitos
- **Mac com Apple Silicon** (M2 Max recomendado)
- **macOS 12+**
- **32 GB RAM** (mínimo 16 GB)
- **15 GB espaço livre** (para modelo)

### Instalação Automatizada

```bash
cd acquaplan-tagger
chmod +x scripts/install.sh
./scripts/install.sh
```

O script instala:
- ✅ Ollama (gerenciador de modelos)
- ✅ Qwen2-VL 7B (modelo de visão)
- ✅ Python 3 + dependências
- ✅ ExifTool
- ✅ Google Drive API (opcional)

### Instalação Manual

```bash
# 1. Instalar Ollama
brew install ollama
ollama serve  # Rodar em outra janela

# 2. Baixar modelo (4-5 GB)
ollama pull qwen2-vl:7b

# 3. Instalar dependências Python
python3 -m venv venv
source venv/bin/activate
pip install ollama pillow

# 4. Instalar ExifTool
brew install exiftool

# 5. (Opcional) Google Drive API
pip install google-api-python-client google-auth
```

## 📖 Uso Básico

### 1. Testar com uma imagem

```bash
source venv/bin/activate
python notebooks/test_notebook.py single foto.jpg
```

### 2. Processar pasta do Lightroom (Projeto A)

```bash
# Dry run (apenas testa, não grava)
python src/lightroom_tagger.py /caminho/pasta/raws --dry-run

# Produção (grava XMP sidecars)
python src/lightroom_tagger.py /caminho/pasta/raws

# Depois no Lightroom:
# Library → Metadata → Read Metadata from Files
```

### 3. Processar pasta do Google Drive (Projeto B)

```bash
# Configurar credenciais primeiro (ver GUIA_USO.md)

python src/drive_tagger.py FOLDER_ID \
  --credentials service-account.json \
  --dry-run
```

### 4. Analisar resultados

```bash
# Estatísticas gerais
python src/manifest_tools.py stats

# Exportar para análise
python src/manifest_tools.py export-analysis \
  --output analysis.csv

# Filtrar por habitat
python src/manifest_tools.py filter \
  --habitat manguezal \
  --output manguezal_manifest.jsonl
```

## 📊 Performance

No **M2 Max (32 GB RAM)**:

- **Velocidade**: 3-5 segundos/imagem
- **Throughput**: ~720-1.200 imagens/hora
- **8.000 fotos**: 10-14 horas de processamento contínuo
- **Batch overnight**: Perfeitamente viável

## 🗂️ Estrutura do Projeto

```
acquaplan-tagger/
├── config/
│   └── acquaplan_config.py      # Vocabulários e schemas
├── src/
│   ├── vision_pipeline.py       # Pipeline de IA (Pass 1 + 2)
│   ├── lightroom_tagger.py      # Projeto A (RAWs)
│   ├── drive_tagger.py          # Projeto B (Drive)
│   └── manifest_tools.py        # Análise e exportação
├── notebooks/
│   └── test_notebook.py         # Testes e demos
├── scripts/
│   └── install.sh               # Instalação automatizada
├── data/                        # Manifests e cache
└── README.md
```

## 📝 Schema de Metadados

```python
{
  "title": "Manguezal com Rhizophora na Baía de Babitonga",
  "description_short": "Vista aérea de manguezal...",
  "description_long": "Manguezal em pleno desenvolvimento...",
  
  "habitat_guess": "manguezal",
  "habitat_confidence": 0.92,
  "habitat_evidence": "Rhizophora visível, maré baixa...",
  
  "species_candidates": [
    {
      "name_pt": "Mangue-vermelho",
      "name_scientific": "Rhizophora mangle",
      "confidence": 0.88,
      "evidence": "Raízes escora características...",
      "taxonomy_level": "species"
    }
  ],
  
  "archaeology_flags": ["possible_sambaqui"],
  "archaeology_evidence": "Acúmulo elevado de conchas...",
  
  "keywords": [
    "bioma:manguezal",
    "fauna:ucides_cordatus",
    "geomorfologia:estuario",
    "clima:maré_baixa",
    "tecnica:fotografia_aerea"
  ]
}
```

## 🎓 Qualidade Esperada

### ✅ Alta Precisão (>80%)
- Classificação de habitats/biomas
- Detecção de elementos visuais óbvios
- Keywords descritivas gerais

### ⚠️ Precisão Média (50-80%)
- Identificação de espécies (close-ups)
- Detecção de sambaquis (evidência clara)
- Classificação taxonômica (gênero/família)

### ⚠️ Uso com Curadoria
- Espécies em fotos distantes/parciais
- Arqueologia sem evidência forte
- Localização geográfica precisa

## 🔧 Troubleshooting

### Ollama não conecta
```bash
# Verificar se está rodando
ps aux | grep ollama

# Iniciar manualmente
ollama serve
```

### Modelo não encontrado
```bash
# Listar modelos instalados
ollama list

# Baixar novamente
ollama pull qwen2-vl:7b
```

### Erro de importação Python
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Reinstalar dependências
pip install -r requirements.txt
```

## 📚 Documentação

- **README.md** (este arquivo): Visão geral
- **GUIA_USO.md**: Tutorial detalhado passo-a-passo
- **config/acquaplan_config.py**: Vocabulários e configurações

## 🤝 Contribuindo

Este sistema foi desenvolvido especificamente para o acervo Acquaplan, mas pode ser adaptado para outros projetos de fotografia científica.

### Customização

1. **Vocabulários**: Edite `config/acquaplan_config.py`
2. **Prompts**: Ajuste templates em `config/acquaplan_config.py`
3. **Pipeline**: Modifique `src/vision_pipeline.py`

## 📄 Licença

Uso interno Acquaplan. Código fornecido "as-is" para fins de pesquisa científica.

---

**Versão**: 1.0.0  
**Última atualização**: Janeiro 2026  
**Desenvolvido para**: Mac Studio M2 Max (32 GB)
