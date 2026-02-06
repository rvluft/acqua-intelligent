"""
Pipeline de Visão Computacional para Acquaplan
Usa Qwen2-VL via Ollama com Metal acceleration
"""

import ollama
import json
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import sys

# Add config to path
sys.path.append(str(Path(__file__).parent.parent))
from config.acquaplan_config import (
    EXTRACTION_PROMPT_TEMPLATE,
    NORMALIZATION_PROMPT_TEMPLATE,
    Config,
    Habitat,
    AcquaplanMetadata,
    SpeciesCandidate,
    LocationGuess
)


class VisionPipeline:
    """Pipeline completo de análise de imagem"""
    
    def __init__(self, model: str = None):
        self.model = model or Config.VISION_MODEL
        self._verify_ollama()
    
    def _verify_ollama(self):
        """Verifica se Ollama está rodando e modelo disponível"""
        try:
            models = ollama.list()
            
            # A API do Ollama retorna formato diferente dependendo da versão
            # Tentar ambos os formatos
            model_names = []
            if isinstance(models, dict) and 'models' in models:
                # Formato novo: {'models': [{'model': 'name:tag', ...}, ...]}
                for m in models['models']:
                    if isinstance(m, dict):
                        # Tentar 'model' primeiro, depois 'name'
                        name = m.get('model') or m.get('name', '')
                        if name:
                            model_names.append(name)
            elif isinstance(models, list):
                # Formato antigo: [{'name': 'model:tag', ...}, ...]
                model_names = [m.get('name', '') for m in models if isinstance(m, dict)]
            
            # Verificar se modelo está instalado
            # Aceitar match parcial (ex: 'llama3.2-vision' em 'llama3.2-vision:11b')
            model_found = any(
                self.model in name or name.startswith(self.model.split(':')[0])
                for name in model_names
            )
            
            if not model_found:
                print(f"⚠️  Modelo {self.model} não encontrado.")
                print(f"📥 Baixando modelo... (isso pode demorar alguns minutos)")
                ollama.pull(self.model)
                print(f"✅ Modelo {self.model} instalado com sucesso!")
        except Exception as e:
            raise RuntimeError(
                f"❌ Erro ao conectar com Ollama: {e}\n"
                f"Certifique-se que Ollama está instalado e rodando:\n"
                f"  brew install ollama\n"
                f"  ollama serve"
            )
    
    def process_image(self, image_path: str, file_id: str = None, source: str = "lightroom") -> AcquaplanMetadata:
        """
        Processa uma imagem completa (Pass 1 + Pass 2)
        
        Args:
            image_path: Caminho para a imagem
            file_id: ID único (path ou Drive ID)
            source: Origem (lightroom/drive/colaborador)
        
        Returns:
            AcquaplanMetadata completo
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")
        
        print(f"  🔍 Pass 1: Extração visual...")
        raw_data = self.pass1_extraction(str(image_path))
        
        print(f"  🧹 Pass 2: Normalização...")
        normalized = self.pass2_normalization(raw_data)
        
        print(f"  📦 Construindo metadados...")
        metadata = self._build_metadata(
            raw_data=raw_data,
            normalized=normalized,
            file_id=file_id or str(image_path),
            source=source,
            filename=image_path.name
        )
        
        return metadata
    
    def pass1_extraction(self, image_path: str) -> Dict:
        """
        Pass 1: Extração bruta de informações da imagem
        
        Returns:
            Dict com dados brutos do modelo
        """
        # Preparar prompt
        habitats_list = ", ".join([h.value for h in Habitat])
        
        # Prompt científico detalhado
        prompt = f"""Você é um ecólogo marinho brasileiro especializado em ecossistemas costeiros.

Analise esta imagem CIENTIFICAMENTE e retorne JSON VÁLIDO.

HABITATS VÁLIDOS: {habitats_list}

Instruções CRÍTICAS:
1. Identifique elementos VISÍVEIS na imagem (não invente)
2. Para espécies: seja CONSERVADOR - se não tiver certeza, use nível taxonômico superior
3. Arqueologia: APENAS se houver evidência CLARA de acúmulo de conchas ou estruturas elevadas
4. Keywords: MÍNIMO 30 palavras (inclua cores, elementos, texturas, condições)

RETORNE APENAS ESTE JSON (sem markdown, sem texto extra):

{{
  "scene_summary": "Descrição objetiva em 2-3 frases do que REALMENTE aparece na imagem",
  
  "habitat_guess": "O MAIS ESPECÍFICO dos habitats da lista (ex: se vê manguezal, não diga praia)",
  "habitat_confidence": 0.0-1.0,
  "habitat_evidence": "Elementos VISÍVEIS: tipo de vegetação, substrato, presença de água, maré, etc",
  
  "species_candidates": [
    {{
      "name_pt": "Nome popular EM PORTUGUÊS (se não souber, deixe genérico como 'ave não identificada')",
      "name_scientific": "Gênero species (se tiver certeza) OU 'ordem Ordem' OU 'classe Classe'",
      "confidence": 0.0-1.0,
      "evidence": "Características morfológicas VISÍVEIS (cor, forma, tamanho, estruturas)",
      "taxonomy_level": "species|genus|family|order|class"
    }}
  ],
  
  "archaeology_flags": [],
  "archaeology_evidence": "",
  
  "activities": ["pesca_artesanal, maricultura, etc - APENAS se claramente visível"],
  
  "technical_quality": "sharp|slightly_blurred|blurred|underexposed|overexposed",
  
  "keywords_raw": [
    "MÍNIMO 30 KEYWORDS variadas incluindo:",
    "- Cores dominantes: azul_claro, verde_escuro, marrom",
    "- Elementos: água, vegetação, areia, rochas, embarcação",
    "- Texturas: liso, rugoso, ondulado",
    "- Condições: céu_claro, nublado, maré_baixa, maré_alta",
    "- Atividades: pesca, turismo, navegação",
    "- Técnica: aérea, close-up, panorâmica, HDR"
  ]
}}

IMPORTANTE:
- Se não identificar espécie com confiança >50%, NÃO invente
- Se a imagem mostra manguezal, NÃO classifique como "praia"
- Keywords devem ser RICAS e DESCRITIVAS (30-80)
- Use acentuação correta em português

RESPONDA APENAS O JSON:
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_path]
                }],
                options={
                    'temperature': 0.3,  # Aumentar um pouco para mais criatividade nas keywords
                    'num_predict': 3072,  # Mais tokens para resposta completa
                    'top_p': 0.9,
                    'top_k': 40,
                },
                format='json'  # Forçar formato JSON
            )
            
            # Extrair JSON da resposta
            raw_text = response['message']['content']
            json_data = self._extract_json(raw_text)
            
            return json_data
            
        except Exception as e:
            raise RuntimeError(f"Erro no Pass 1 (extração): {e}")
    
    def pass2_normalization(self, raw_data: Dict) -> Dict:
        """
        Pass 2: Normaliza e refina os dados brutos
        
        Args:
            raw_data: Saída do pass1_extraction
        
        Returns:
            Dict com dados normalizados
        """
        # Prompt detalhado para normalização
        prompt = f"""Você é um especialista em catalogação científica de imagens.

Refine estes metadados para um banco de imagens de ecologia costeira:

DADOS BRUTOS:
{json.dumps(raw_data, indent=2, ensure_ascii=False)}

TAREFAS:
1. Criar título conciso e descritivo (5-8 palavras)
2. Descrição curta impactante (1 frase, 20-30 palavras)
3. Descrição longa detalhada (2-4 frases, 60-100 palavras)
4. Normalizar keywords para 40-80 termos hierárquicos

CATEGORIAS DE KEYWORDS (usar formato categoria:valor):
- bioma: manguezal, restinga, mata_atlantica, dunas, praia, costao_rochoso, estuario
- geomorfologia: canal_de_mare, baia, ilha, peninsula, laguna
- fauna: [nome_cientifico], [nome_popular]
- flora: [nome_cientifico], [nome_popular]
- atividade: pesca_artesanal, maricultura, turismo, pesquisa_cientifica
- clima: ceu_claro, nublado, mare_alta, mare_baixa, sol, chuva
- tecnica: aerea, panoramica, close-up, macro, HDR, subaquatica
- conservacao: area_preservada, impacto_antropico, poluicao
- cores: azul_claro, verde_escuro, marrom, cinza, branco
- elementos: agua, vegetacao, areia, rocha, embarcacao, construcao

RETORNE APENAS JSON:
{{
  "title": "Título descritivo de 5-8 palavras",
  "description_short": "1 frase impactante de 20-30 palavras descrevendo o essencial",
  "description_long": "2-4 frases detalhadas de 60-100 palavras com contexto ecológico e elementos notáveis",
  "keywords_normalized": [
    "40-80 keywords HIERÁRQUICAS no formato categoria:valor",
    "Exemplo: bioma:manguezal",
    "Exemplo: fauna:rhizophora_mangle",
    "Exemplo: geomorfologia:estuario",
    "Exemplo: clima:mare_baixa",
    "Exemplo: tecnica:fotografia_aerea",
    "Inclua TODAS as categorias relevantes",
    "Use acentuação correta"
  ]
}}

IMPORTANTE:
- Use acentuação correta em português (não use códigos como Ã¡)
- Keywords devem ser RICAS (mínimo 40)
- Balance categorias diferentes
- Remova duplicatas

APENAS O JSON:
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.4,  # Um pouco mais criativo para keywords variadas
                    'num_predict': 2048,
                    'top_p': 0.9,
                },
                format='json'  # Forçar JSON
            )
            
            raw_text = response['message']['content']
            normalized = self._extract_json(raw_text)
            
            return normalized
            
        except Exception as e:
            raise RuntimeError(f"Erro no Pass 2 (normalização): {e}")
    
    def _extract_json(self, text: str) -> Dict:
        """Extrai JSON de texto que pode conter markdown ou texto extra"""
        
        # Primeiro: tentar parsear direto (caso ideal)
        try:
            return json.loads(text.strip())
        except:
            pass
        
        # Remover markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Tentar novamente após remover markdown
        try:
            return json.loads(text.strip())
        except:
            pass
        
        # Buscar objeto JSON no texto
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Buscar array JSON
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Se chegou aqui, não encontrou JSON válido
        raise ValueError(f"Nenhum JSON válido encontrado na resposta: {text[:200]}")
    
    def _build_metadata(
        self,
        raw_data: Dict,
        normalized: Dict,
        file_id: str,
        source: str,
        filename: str
    ) -> AcquaplanMetadata:
        """Constrói objeto AcquaplanMetadata a partir dos dados processados"""
        
        # Processar candidatos de espécies
        species_candidates = []
        for sp in raw_data.get('species_candidates', []):
            species_candidates.append(SpeciesCandidate(
                name_pt=sp.get('name_pt', ''),
                name_scientific=sp.get('name_scientific', ''),
                confidence=float(sp.get('confidence', 0.0)),
                evidence=sp.get('evidence', ''),
                taxonomy_level=sp.get('taxonomy_level', 'species')
            ))
        
        # Location guess (se houver)
        location_guess = None
        if raw_data.get('location_guess'):
            loc = raw_data['location_guess']
            if isinstance(loc, dict):
                location_guess = LocationGuess(
                    description=loc.get('description', ''),
                    confidence=float(loc.get('confidence', 0.0)),
                    evidence=loc.get('evidence', '')
                )
        
        # Construir metadata
        metadata = AcquaplanMetadata(
            file_id=file_id,
            source=source,
            original_filename=filename,
            title=normalized.get('title', ''),
            description_short=normalized.get('description_short', ''),
            description_long=normalized.get('description_long', ''),
            habitat_guess=raw_data.get('habitat_guess', ''),
            habitat_confidence=float(raw_data.get('habitat_confidence', 0.0)),
            habitat_evidence=raw_data.get('habitat_evidence', ''),
            species_candidates=species_candidates,
            archaeology_flags=raw_data.get('archaeology_flags', []),
            archaeology_evidence=raw_data.get('archaeology_evidence', ''),
            keywords=normalized.get('keywords_normalized', []),
            location_guess=location_guess,
            activities=raw_data.get('activities', []),
            technical_quality=raw_data.get('technical_quality', ''),
            processing_timestamp=datetime.now().isoformat()
        )
        
        return metadata
    
    def batch_process(
        self,
        image_paths: list,
        source: str = "lightroom",
        progress_callback: callable = None
    ) -> list:
        """
        Processa múltiplas imagens em batch
        
        Args:
            image_paths: Lista de caminhos de imagem
            source: Origem dos arquivos
            progress_callback: Função chamada após cada imagem (opcional)
        
        Returns:
            Lista de AcquaplanMetadata
        """
        results = []
        total = len(image_paths)
        
        for idx, img_path in enumerate(image_paths, 1):
            print(f"\n[{idx}/{total}] {Path(img_path).name}")
            
            try:
                metadata = self.process_image(img_path, source=source)
                results.append(metadata)
                
                if progress_callback:
                    progress_callback(idx, total, metadata)
                
            except Exception as e:
                print(f"  ❌ Erro: {e}")
                continue
        
        return results


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def test_pipeline(image_path: str):
    """Testa o pipeline com uma imagem"""
    pipeline = VisionPipeline()
    
    print(f"🧪 Testando pipeline com: {image_path}\n")
    
    metadata = pipeline.process_image(image_path)
    
    print("\n" + "="*80)
    print("RESULTADO:")
    print("="*80)
    print(f"\n📝 Título: {metadata.title}")
    print(f"\n📄 Descrição curta:\n{metadata.description_short}")
    print(f"\n📖 Descrição longa:\n{metadata.description_long}")
    print(f"\n🌿 Habitat: {metadata.habitat_guess} ({metadata.habitat_confidence:.1%})")
    print(f"   Evidência: {metadata.habitat_evidence}")
    
    if metadata.species_candidates:
        print(f"\n🔬 Espécies identificadas:")
        for sp in metadata.species_candidates:
            print(f"   - {sp.name_pt} ({sp.name_scientific})")
            print(f"     Confiança: {sp.confidence:.1%} | {sp.evidence}")
    
    if metadata.archaeology_flags:
        print(f"\n🏛️  Arqueologia: {', '.join(metadata.archaeology_flags)}")
        print(f"   {metadata.archaeology_evidence}")
    
    print(f"\n🏷️  Keywords ({len(metadata.keywords)}):")
    print(f"   {', '.join(metadata.keywords[:20])}")
    if len(metadata.keywords) > 20:
        print(f"   ... e mais {len(metadata.keywords) - 20}")
    
    print("\n" + "="*80)
    
    return metadata


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python vision_pipeline.py <imagem.jpg>")
        sys.exit(1)
    
    test_pipeline(sys.argv[1])
