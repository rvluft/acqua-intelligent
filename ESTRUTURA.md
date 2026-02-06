# Estrutura do Projeto - Acquaplan Tagger

```
acquaplan-tagger/
│
├── 📄 README.md                      # Documentação principal
├── 📄 GUIA_USO.md                    # Tutorial passo-a-passo detalhado
├── 📄 QUICKSTART.md                  # Início rápido em 5 minutos
├── 📄 requirements.txt               # Dependências Python
├── 📄 .gitignore                     # Arquivos ignorados pelo Git
│
├── 📁 config/                        # Configurações do sistema
│   ├── __init__.py
│   └── acquaplan_config.py          # ⭐ Vocabulários, schemas, prompts
│
├── 📁 src/                           # Código principal
│   ├── __init__.py
│   ├── vision_pipeline.py           # ⭐ Pipeline de IA (Pass 1 + Pass 2)
│   ├── lightroom_tagger.py          # ⭐ PROJETO A - RAWs → XMP
│   ├── drive_tagger.py              # ⭐ PROJETO B - Drive → Description
│   └── manifest_tools.py            # ⭐ Análise e exportação
│
├── 📁 scripts/                       # Scripts auxiliares
│   ├── install.sh                   # ⭐ Instalação automatizada
│   ├── verify_install.py            # ⭐ Verificar instalação
│   └── batch_example.sh             # Exemplo de batch processing
│
├── 📁 notebooks/                     # Testes e demos
│   └── test_notebook.py             # ⭐ Interface de teste
│
├── 📁 data/                          # Dados e cache
│   ├── test_images/                 # Imagens para teste
│   ├── manifests/                   # Backups de manifests
│   └── exports/                     # CSVs exportados
│
├── 📁 credentials/                   # Credenciais (NÃO versionar)
│   ├── .gitkeep
│   └── service-account.json.example # Template para Google Drive
│
└── 📁 logs/                          # Logs de execução
    └── (criado automaticamente)
```

## Arquivos Principais (⭐)

### Core do Sistema

**config/acquaplan_config.py**
- Vocabulários controlados (habitats, arqueologia, atividades)
- Schema de metadados (AcquaplanMetadata)
- Prompts para IA (extração e normalização)
- Configurações técnicas

**src/vision_pipeline.py**
- Pipeline completo de processamento
- Pass 1: Extração visual (Qwen2-VL)
- Pass 2: Normalização e keywords
- Batch processing

### Projetos

**src/lightroom_tagger.py** (PROJETO A)
- Processa arquivos RAW
- Grava XMP sidecars
- Cache de processados
- Suporte a coleções do Lightroom

**src/drive_tagger.py** (PROJETO B)
- Processa arquivos no Google Drive
- Atualiza campo Description
- Google Drive API integration
- Suporte a múltiplas pastas

**src/manifest_tools.py**
- Estatísticas do manifest
- Exportação para CSV/Excel
- Filtros (habitat, espécie, arqueologia)
- Exportação para ExifTool batch

### Instalação e Testes

**scripts/install.sh**
- Instalação automatizada completa
- Verifica dependências
- Baixa modelo Qwen2-VL
- Configura ambiente Python

**scripts/verify_install.py**
- Verifica todos os componentes
- Testa conexão com Ollama
- Valida estrutura de diretórios
- Diagnóstico de problemas

**notebooks/test_notebook.py**
- Interface de teste interativa
- Teste de imagem única
- Teste de batch
- Teste de workflow completo

## Fluxo de Dados

```
ENTRADA                     PROCESSAMENTO              SAÍDA
────────                    ─────────────              ─────

RAWs (Lightroom)           ┌──────────────┐           XMP sidecars
    │                      │              │               │
    └──────────────────────▶ Vision       │               │
                           │ Pipeline     │               │
JPEGs (Drive)              │ (Qwen2-VL)   │               ├──▶ Lightroom
    │                      │              │               │    (Read Metadata)
    └──────────────────────▶              ├───────────────┤
                           └──────────────┘               │
                                  │                       │
                                  ▼                       │
                           manifest.jsonl                 │
                                  │                       │
                                  ├───────────────────────┤
                                  │                       │
                                  ▼                       ▼
                           Estatísticas            Drive Description
                           CSV/Excel               (campo do arquivo)
                           Filtros
```

## Manifest (manifest.jsonl)

Arquivo central que armazena todos os metadados processados:

```jsonl
{"file_path": "...", "metadata": {...}, "project": "lightroom", "timestamp": "..."}
{"file_id": "...", "metadata": {...}, "project": "drive", "timestamp": "..."}
...
```

Cada linha = 1 imagem processada
Formato: JSONL (JSON Lines)
Pode ter milhares de linhas

## Tamanhos Aproximados

```
Sistema completo:          ~50 MB
Modelo Qwen2-VL:           ~5 GB
Manifest (1000 imagens):   ~5 MB
Manifest (8000 imagens):   ~40 MB
XMP sidecar típico:        ~5-10 KB
```

## Próximos Passos

1. **Instalar**: `./scripts/install.sh`
2. **Verificar**: `python scripts/verify_install.py`
3. **Testar**: Ver `QUICKSTART.md`
4. **Usar**: Ver `GUIA_USO.md`

---

**Versão**: 1.0.0  
**Atualizado**: Janeiro 2026
