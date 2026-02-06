# Guia de Uso - Acquaplan Intelligent Tagger

Guia completo passo-a-passo para operar o sistema em produção.

## 📋 Índice

1. [Configuração Inicial](#1-configuração-inicial)
2. [Workflow Lightroom (Projeto A)](#2-workflow-lightroom-projeto-a)
3. [Workflow Google Drive (Projeto B)](#3-workflow-google-drive-projeto-b)
4. [Análise e Exportação](#4-análise-e-exportação)
5. [Casos de Uso Avançados](#5-casos-de-uso-avançados)
6. [Manutenção](#6-manutenção)

---

## 1. Configuração Inicial

### 1.1 Primeira Execução

Após instalar, teste o sistema:

```bash
# Ativar ambiente
cd acquaplan-tagger
source venv/bin/activate

# Verificar Ollama
ollama list

# Deve mostrar:
# NAME              ID              SIZE    MODIFIED
# qwen2-vl:7b       abc123...       4.5 GB  X hours ago

# Se o modelo não estiver listado:
ollama pull qwen2-vl:7b
```

### 1.2 Teste Básico

```bash
# Baixe uma foto de teste ou use uma sua
python notebooks/test_notebook.py single /caminho/para/teste.jpg
```

**Resultado esperado**: O sistema deve exibir:
- Título
- Descrições (curta e longa)
- Habitat identificado
- Espécies (se houver)
- Keywords

Se tudo funcionar, você está pronto!

---

## 2. Workflow Lightroom (Projeto A)

### 2.1 Preparação no Lightroom

**Antes de processar**, organize suas fotos:

1. **Importar RAWs** para o Lightroom
2. **Criar coleção** para a missão
   - Exemplo: `2024_Missao_Laguna_Julho`
3. **Fazer curadoria**:
   - Marcar picks (P)
   - Aplicar flags
   - Dar estrelas (rating)
4. **Selecionar** apenas as fotos que quer processar

### 2.2 Processar Fotos

```bash
# Dry run (teste sem gravar)
python src/lightroom_tagger.py \
  /Volumes/Photos/2024/Missao_Laguna \
  --dry-run

# Verificar resultados no terminal
# Se OK, rodar em produção:

python src/lightroom_tagger.py \
  /Volumes/Photos/2024/Missao_Laguna
```

**O que acontece**:
1. Sistema busca todos os RAWs (.CR3, .CR2, .NEF, etc.)
2. Pula arquivos já processados (verifica cache)
3. Para cada foto:
   - Analisa com IA (3-5 segundos)
   - Gera metadados completos
   - Cria arquivo `.xmp` ao lado do RAW
   - Salva no manifest

### 2.3 Importar Metadados no Lightroom

```
Lightroom Classic
↓
Library
↓
Metadata
↓
Read Metadata from Files
```

**Aguarde**: Lightroom vai ler os XMP e popular:
- Título
- Descrição
- Keywords
- Campos IPTC

### 2.4 Exportar JPEGs

Agora que os RAWs têm metadados:

```
Export → JPEG
[✓] Include keywords
[✓] Write keywords as Lightroom Hierarchy
```

**Resultado**: JPEGs exportados já incluem todos os metadados!

### 2.5 Verificação

No Lightroom, verifique uma foto processada:

```
Metadata → IPTC
```

Deve conter:
- ✅ Title
- ✅ Caption
- ✅ Keywords (30-80)

---

## 3. Workflow Google Drive (Projeto B)

### 3.1 Configurar Credenciais

**Apenas primeira vez**:

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto novo
3. Ative a **Google Drive API**
4. Crie **Service Account**:
   - IAM & Admin → Service Accounts → Create
   - Nome: `acquaplan-tagger`
   - Role: Nenhuma (não precisa)
5. Crie chave JSON:
   - Clique na Service Account
   - Keys → Add Key → Create new key → JSON
6. Baixe o JSON para `acquaplan-tagger/credentials/service-account.json`

### 3.2 Compartilhar Pasta do Drive

1. Vá na pasta do Drive que quer processar
2. Compartilhe com o email da Service Account
   - Email está no JSON: `client_email`
   - Permissão: **Editor**

### 3.3 Obter ID da Pasta

Na URL da pasta do Drive:

```
https://drive.google.com/drive/folders/1A2B3C4D5E6F...
                                        └─────────┘
                                        Este é o ID
```

### 3.4 Processar Pasta

```bash
# Dry run
python src/drive_tagger.py 1A2B3C4D5E6F \
  --credentials credentials/service-account.json \
  --dry-run

# Produção
python src/drive_tagger.py 1A2B3C4D5E6F \
  --credentials credentials/service-account.json
```

**O que acontece**:
1. Lista todos os JPEGs/PNGs da pasta
2. Pula arquivos com descrição > 100 chars
3. Pula arquivos já processados
4. Para cada arquivo:
   - Baixa temporariamente
   - Analisa com IA
   - Atualiza campo `description` no Drive
   - Salva no manifest

### 3.5 Verificar no Drive

Abra um arquivo processado no Drive:

```
Clique com direito → Ver detalhes → Descrição
```

Deve conter:
- ✅ Descrição longa
- ✅ Habitat + confiança
- ✅ Espécies identificadas
- ✅ Keywords principais
- ✅ Timestamp de processamento

---

## 4. Análise e Exportação

### 4.1 Estatísticas Gerais

```bash
python src/manifest_tools.py stats
```

**Saída**:
- Total de entradas
- Distribuição por projeto (Lightroom/Drive)
- Habitats mais comuns
- Espécies mais identificadas
- Keywords mais usadas
- Período de processamento

### 4.2 Exportar para Excel/CSV

```bash
# CSV para análise
python src/manifest_tools.py export-analysis \
  --output data/exports/analise_completa.csv

# Abrir no Excel para análise estatística
```

**Campos no CSV**:
- `file_id`: Identificador único
- `habitat`: Habitat classificado
- `habitat_confidence`: Confiança (0-1)
- `species_count`: Número de espécies identificadas
- `top_species`: Espécie mais provável
- `keywords_count`: Total de keywords

### 4.3 Exportar para ExifTool

Se quiser aplicar metadados em lote:

```bash
python src/manifest_tools.py export-exiftool \
  --output data/exports/batch_exiftool.csv \
  --project lightroom

# Depois usar:
exiftool -csv="batch_exiftool.csv" /pasta/destino/
```

### 4.4 Filtrar por Critérios

**Por habitat**:
```bash
python src/manifest_tools.py filter \
  --habitat manguezal \
  --output data/exports/apenas_manguezal.jsonl
```

**Por espécie**:
```bash
python src/manifest_tools.py filter \
  --species "caranguejo-uçá" \
  --output data/exports/ucides_cordatus.jsonl
```

**Flags arqueológicas**:
```bash
python src/manifest_tools.py filter \
  --archaeology \
  --output data/exports/possivel_sambaqui.jsonl
```

---

## 5. Casos de Uso Avançados

### 5.1 Processar Apenas Fotos Novas

O sistema já faz isso automaticamente via cache. Para forçar reprocessamento:

```bash
python src/lightroom_tagger.py /pasta \
  --reprocess
```

### 5.2 Processar Múltiplas Pastas do Drive

Crie um script:

```bash
#!/bin/bash
# processar_todas_missoes.sh

FOLDERS=(
  "1A2B3C4D5E6F"  # Missão Jan/2024
  "7G8H9I0J1K2L"  # Missão Fev/2024
  "3M4N5O6P7Q8R"  # Missão Mar/2024
)

for FOLDER in "${FOLDERS[@]}"; do
  python src/drive_tagger.py "$FOLDER" \
    --credentials credentials/service-account.json
done
```

### 5.3 Processar Overnight (8.000 fotos)

```bash
# Rodar em background com log
nohup python src/lightroom_tagger.py /pasta/raws \
  > logs/processamento_$(date +%Y%m%d).log 2>&1 &

# Verificar progresso
tail -f logs/processamento_20260104.log
```

### 5.4 Integração com Scripts Lightroom

Se quiser automatizar a exportação de coleções específicas:

```applescript
-- exportar_picks.applescript
tell application "Adobe Lightroom Classic"
    tell active catalog
        set theCollection to collection "2024_Missao_Laguna"
        -- Exportar apenas picks
    end tell
end tell
```

---

## 6. Manutenção

### 6.1 Limpar Cache

```bash
# Limpar cache de arquivos processados
rm data/processed_files.json
rm data/drive_processed_files.json

# Próximo processamento vai recomeçar do zero
```

### 6.2 Atualizar Modelo

```bash
# Verificar versões disponíveis
ollama list

# Atualizar
ollama pull qwen2-vl:7b
```

### 6.3 Backup do Manifest

```bash
# Backup diário (adicionar ao cron)
cp ~/acquaplan_manifest.jsonl \
   ~/Backups/manifest_$(date +%Y%m%d).jsonl
```

### 6.4 Monitorar Espaço em Disco

O modelo ocupa ~5 GB, mas os manifests crescem:

```bash
# Ver tamanho do manifest
du -h ~/acquaplan_manifest.jsonl

# Comprimir manifests antigos
gzip data/manifests/manifest_2024*.jsonl
```

### 6.5 Performance

Se o processamento ficar lento:

1. **Verificar RAM**:
   ```bash
   top
   # Qwen2-VL deve usar 6-8 GB
   ```

2. **Verificar temperatura** (M2 Max):
   ```bash
   sudo powermetrics --samplers smc
   ```

3. **Reduzir batch size** se necessário:
   Edite `config/acquaplan_config.py`:
   ```python
   BATCH_SIZE = 5  # Reduzir de 10 para 5
   ```

---

## 💡 Dicas Pro

### Otimizar Workflow

1. **Curadoria primeiro**: Processe apenas fotos aprovadas
2. **Batch por missão**: Processe missão completa de uma vez
3. **Verify metadata**: Sempre `Read Metadata` no LR antes de exportar
4. **Backup regular**: Manifest contém todo histórico

### Keywords Hierárquicas

O sistema gera keywords no formato `categoria:valor`:

```
bioma:manguezal
fauna:caranguejo-uçá
atividade:pesca_artesanal
geomorfologia:estuário
clima:maré_baixa
```

No Lightroom, isso permite **buscar por categoria**:
- `bioma:*` → Todos os biomas
- `fauna:*` → Toda a fauna

### Qualidade vs. Velocidade

Para máxima qualidade (mais lento):
```python
# Em vision_pipeline.py
options={
    'temperature': 0.1,  # Mais conservador
    'num_predict': 2048,  # Mais tokens
}
```

Para máxima velocidade:
```python
options={
    'temperature': 0.5,
    'num_predict': 512,
}
```

---

## ❓ FAQ

**P: Posso processar vídeos?**  
R: Não nesta versão. Apenas imagens estáticas.

**P: Funciona offline?**  
R: Sim! Projeto A (Lightroom) é 100% offline. Projeto B precisa de internet apenas para acessar Drive API.

**P: Posso usar outro modelo?**  
R: Sim. Edite `Config.VISION_MODEL` em `acquaplan_config.py`. Teste com `ollama list`.

**P: E se eu não usar Lightroom?**  
R: Você pode adaptar para ler de pastas direto. O core é o `vision_pipeline.py`.

**P: Quanto custa?**  
R: Zero. Tudo roda localmente, sem APIs pagas.

**P: Preciso de GPU?**  
R: Não! M2 Max usa aceleração Metal (GPU integrada).

---

**Precisa de ajuda?** Verifique `README.md` ou revise o código em `src/`.
