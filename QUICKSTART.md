# Quick Start - Acquaplan Tagger

Comece em 5 minutos!

## 1. Instalar

```bash
cd acquaplan-tagger
./scripts/install.sh
```

Aguarde 10-30 minutos (download do modelo).

## 2. Testar

```bash
source venv/bin/activate
python notebooks/test_notebook.py single foto.jpg
```

## 3. Processar Lightroom

```bash
# Teste (não grava)
python src/lightroom_tagger.py /pasta/raws --dry-run

# Produção
python src/lightroom_tagger.py /pasta/raws

# No Lightroom: Library → Metadata → Read Metadata
```

## 4. Processar Google Drive

```bash
# Configure credenciais primeiro (ver GUIA_USO.md)

python src/drive_tagger.py FOLDER_ID \
  --credentials credentials/service-account.json
```

## 5. Ver Resultados

```bash
# Estatísticas
python src/manifest_tools.py stats

# Exportar CSV
python src/manifest_tools.py export-analysis --output analise.csv
```

---

## Comandos Essenciais

### Lightroom

```bash
# Pasta completa
python src/lightroom_tagger.py /caminho/pasta

# Com opções
python src/lightroom_tagger.py /caminho/pasta \
  --dry-run \
  --extensions .CR3 .NEF \
  --manifest custom_manifest.jsonl
```

### Google Drive

```bash
# Pasta única
python src/drive_tagger.py FOLDER_ID \
  --credentials service-account.json

# Reprocessar tudo
python src/drive_tagger.py FOLDER_ID \
  --credentials service-account.json \
  --reprocess
```

### Análise

```bash
# Estatísticas gerais
python src/manifest_tools.py stats

# Exportar CSV
python src/manifest_tools.py export-analysis \
  --output analise.csv

# Filtrar
python src/manifest_tools.py filter \
  --habitat manguezal \
  --output manguezal.jsonl
```

---

## Estrutura de Saída

### XMP Sidecar (Projeto A)

```
foto.CR3
foto.CR3.xmp  ← Criado automaticamente
```

Conteúdo do XMP:
- Title
- Description (completa)
- Keywords (30-80)
- Subject
- Campos customizados (Habitat, etc.)

### Description do Drive (Projeto B)

Campo "Description" do arquivo contém:

```
[Descrição longa da imagem]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌿 HABITAT: manguezal
   Confiança: 92%
   [Evidências visuais]

🔬 ESPÉCIES IDENTIFICADAS:
   • Mangue-vermelho (Rhizophora mangle)
     Confiança: 88%
     [Evidências]

🏷️ PALAVRAS-CHAVE:
   bioma:manguezal, fauna:caranguejo-uçá, ...
```

---

## Troubleshooting Rápido

**Ollama não conecta**
```bash
ollama serve  # Em outra janela
```

**Modelo não encontrado**
```bash
ollama pull qwen2-vl:7b
```

**Import error**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Muito lento**
- Normal: 3-5 seg/imagem
- Se > 10 seg: Verificar temperatura do Mac
- Considere batch overnight para >100 fotos

---

**Documentação completa**: Ver `README.md` e `GUIA_USO.md`
