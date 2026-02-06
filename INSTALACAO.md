# 🎉 ACQUAPLAN INTELLIGENT TAGGER - INSTALAÇÃO FINAL

Sistema completo de tagueamento inteligente para acervos fotográficos científicos.

## 📦 CONTEÚDO DO PACOTE

Você recebeu: **acquaplan-tagger.tar.gz** (~32 KB compactado)

Este pacote contém:
- ✅ 15 arquivos Python e scripts
- ✅ 5 documentações completas
- ✅ Pipeline de IA completo (2 passes)
- ✅ Projeto A (Lightroom → XMP)
- ✅ Projeto B (Google Drive → Description)
- ✅ Ferramentas de análise e exportação
- ✅ Scripts de instalação automatizados

---

## 🚀 INSTALAÇÃO NO MAC M2 MAX

### Passo 1: Extrair o arquivo

```bash
# No terminal, vá para a pasta onde baixou o arquivo
cd ~/Downloads

# Extrair
tar -xzf acquaplan-tagger.tar.gz

# Entrar na pasta
cd acquaplan-tagger
```

### Passo 2: Executar instalação automatizada

```bash
# Tornar script executável (se necessário)
chmod +x scripts/install.sh

# Rodar instalação
./scripts/install.sh
```

**O script vai:**
1. ✅ Verificar Homebrew
2. ✅ Instalar Ollama
3. ✅ Baixar modelo Qwen2-VL (4-5 GB, pode demorar 10-30 min)
4. ✅ Configurar Python + dependências
5. ✅ Instalar ExifTool
6. ✅ Criar estrutura de diretórios

**⏱️ Tempo total**: 15-40 minutos (depende da conexão)

### Passo 3: Verificar instalação

```bash
# Rodar verificação
python3 scripts/verify_install.py
```

Deve mostrar todos os componentes com ✓ verde.

### Passo 4: Primeiro teste

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Testar com uma foto sua
python notebooks/test_notebook.py single /caminho/para/foto.jpg
```

**Resultado esperado**: Sistema analisa a foto e exibe:
- Título gerado
- Descrições (curta e longa)
- Habitat identificado
- Espécies (se houver)
- 30-80 keywords

---

## 📚 DOCUMENTAÇÃO

Dentro do pacote você encontra:

1. **QUICKSTART.md** → Início rápido (5 minutos)
2. **README.md** → Visão geral completa
3. **GUIA_USO.md** → Tutorial passo-a-passo detalhado
4. **ESTRUTURA.md** → Organização do projeto

**Leia primeiro**: `QUICKSTART.md`

---

## 🎯 CASOS DE USO

### Caso 1: Processar pasta do Lightroom

```bash
source venv/bin/activate

# Teste (dry run)
python src/lightroom_tagger.py /caminho/pasta/raws --dry-run

# Produção
python src/lightroom_tagger.py /caminho/pasta/raws

# No Lightroom: Library → Metadata → Read Metadata from Files
```

### Caso 2: Processar pasta do Google Drive

```bash
# Configurar credenciais primeiro (ver GUIA_USO.md)

python src/drive_tagger.py FOLDER_ID \
  --credentials credentials/service-account.json
```

### Caso 3: Analisar resultados

```bash
# Estatísticas
python src/manifest_tools.py stats

# Exportar para Excel
python src/manifest_tools.py export-analysis --output analise.csv
```

---

## ⚙️ ESPECIFICAÇÕES TÉCNICAS

**Modelo de IA**: Qwen2-VL 7B (via Ollama)
**Aceleração**: Apple Metal (GPU integrada)
**Velocidade**: 3-5 segundos/imagem
**Capacidade**: 720-1.200 imagens/hora
**RAM necessária**: 8-12 GB durante processamento
**Espaço em disco**: 
- Sistema: ~50 MB
- Modelo: ~5 GB
- Manifest (8.000 fotos): ~40 MB

---

## 🎓 QUALIDADE ESPERADA

### ✅ Alta Precisão (>80%)
- Classificação de habitats (manguezal, restinga, etc.)
- Elementos visuais óbvios
- Keywords descritivas

### ⚠️ Precisão Média (50-80%)
- Identificação de espécies (close-ups)
- Detecção de sambaquis (evidência clara)
- Classificação taxonômica (gênero/família)

### 💡 Uso Recomendado
- Sempre revisar identificações de espécies
- Validar flags arqueológicas com especialista
- Usar como ferramenta de triagem, não substituição de expertise

---

## 🔧 TROUBLESHOOTING

### Problema: Ollama não conecta
```bash
# Em outra janela do terminal:
ollama serve
```

### Problema: Modelo não encontrado
```bash
ollama pull qwen2-vl:7b
```

### Problema: Import error
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problema: Processamento lento
- Normal: 3-5 seg/imagem
- Se > 10 seg: Verificar temperatura do Mac
- Considere batch overnight para >100 fotos

---

## 📞 SUPORTE

1. **Documentação completa**: Leia `GUIA_USO.md`
2. **Verificar instalação**: `python scripts/verify_install.py`
3. **Problemas comuns**: Ver seção Troubleshooting acima

---

## 🏗️ ARQUITETURA DO SISTEMA

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

---

## ✅ CHECKLIST RÁPIDO

- [ ] Extrair `acquaplan-tagger.tar.gz`
- [ ] Executar `./scripts/install.sh`
- [ ] Aguardar download do modelo (10-30 min)
- [ ] Rodar `python scripts/verify_install.py`
- [ ] Testar com uma foto
- [ ] Ler `QUICKSTART.md`
- [ ] Processar primeira pasta

---

## 📝 PRÓXIMOS PASSOS

1. **Hoje**: Instalar e testar com 5-10 fotos
2. **Esta semana**: Processar primeira missão completa
3. **Este mês**: Integrar ao workflow regular
4. **Longo prazo**: Processar acervo completo (8.000+ fotos)

---

**Sistema desenvolvido para**: Mac Studio M2 Max (32 GB RAM)  
**Versão**: 1.0.0  
**Data**: Janeiro 2026  
**Uso**: Acervo fotográfico científico Acquaplan

---

🎉 **BOA SORTE COM O PROCESSAMENTO!** 🎉

Qualquer dúvida, consulte a documentação completa dentro do pacote.
