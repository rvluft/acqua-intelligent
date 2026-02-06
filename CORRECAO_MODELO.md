# ⚠️ CORREÇÃO URGENTE - Modelo de Visão

## Problema

O modelo `qwen2-vl:7b` não está disponível no Ollama.

## Solução Rápida

Execute estes comandos no terminal (dentro da pasta `acquaplan-tagger`):

```bash
# Baixar modelo correto (Llama 3.2 Vision 11B)
ollama pull llama3.2-vision:11b
```

**Tempo**: 15-40 minutos (download de ~7-8 GB)

---

## Alternativas (se quiser modelo menor/mais rápido)

```bash
# Opção 2: Llama 3.2 Vision padrão (~7B, mais rápido)
ollama pull llama3.2-vision

# Opção 3: LLaVA 13B (alternativa robusta)
ollama pull llava:13b

# Opção 4: LLaVA 7B (mais rápido, menor qualidade)
ollama pull llava:7b
```

---

## Após o Download

O sistema já foi atualizado para usar `llama3.2-vision:11b` por padrão.

**Testar**:
```bash
source venv/bin/activate
python scripts/verify_install.py
```

---

## Comparação de Modelos

| Modelo | Tamanho | RAM Necessária | Velocidade | Qualidade |
|--------|---------|----------------|------------|-----------|
| llama3.2-vision:11b | ~8 GB | 12-16 GB | 3-5 seg | ⭐⭐⭐⭐⭐ |
| llama3.2-vision | ~5 GB | 8-12 GB | 2-4 seg | ⭐⭐⭐⭐ |
| llava:13b | ~8 GB | 12-16 GB | 4-6 seg | ⭐⭐⭐⭐ |
| llava:7b | ~5 GB | 8-10 GB | 2-3 seg | ⭐⭐⭐ |

**Para M2 Max 32GB**: Use `llama3.2-vision:11b` (melhor qualidade)

---

## Se Quiser Trocar de Modelo

Edite `config/acquaplan_config.py`:

```python
class Config:
    # Trocar aqui:
    VISION_MODEL = "llama3.2-vision:11b"  # ou outro modelo
```

---

## Verificar Modelos Disponíveis

```bash
# Listar modelos instalados
ollama list

# Testar modelo
ollama run llama3.2-vision:11b "Olá"
```

---

## Status Atual

✅ Sistema atualizado para usar `llama3.2-vision:11b`  
✅ Todos os arquivos corrigidos  
⏳ Aguardando download do modelo  

**Próximo passo**: Após o download, execute:
```bash
python scripts/verify_install.py
```
