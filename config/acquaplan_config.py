"""
Configuração central do sistema Acquaplan Tagger
Vocabulários controlados e schemas
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

# ============================================================================
# VOCABULÁRIOS CONTROLADOS
# ============================================================================

class Habitat(str, Enum):
    """Habitats costeiros brasileiros"""
    MANGUEZAL = "manguezal"
    RESTINGA = "restinga"
    MATA_ATLANTICA = "mata_atlantica"
    DUNAS = "dunas"
    PRAIA = "praia"
    COSTAO_ROCHOSO = "costao_rochoso"
    ESTUARIO = "estuario"
    LAGUNA = "laguna"
    AREA_URBANA = "area_urbana"
    RIO = "rio"
    SERRA = "serra"
    ILHAS = "ilhas"
    BAIA = "baia"
    AMBIENTE_MARINHO = "ambiente_marinho"

HABITAT_KEYWORDS_MAP = {
    Habitat.MANGUEZAL: ["mangrove", "rhizophora", "avicennia", "laguncularia", "raízes_aéreas", "maré"],
    Habitat.RESTINGA: ["sandy_vegetation", "vegetation_coastal", "dunes_vegetation", "beach_ridge"],
    Habitat.MATA_ATLANTICA: ["atlantic_forest", "rainforest", "tropical_forest", "floresta"],
    Habitat.DUNAS: ["sand_dunes", "coastal_dunes", "areia", "vegetação_dunar"],
    Habitat.PRAIA: ["beach", "shore", "shoreline", "sand", "waves", "surf"],
    Habitat.COSTAO_ROCHOSO: ["rocky_shore", "intertidal", "tide_pools", "rocks", "algae"],
    Habitat.ESTUARIO: ["estuary", "river_mouth", "brackish_water", "foz"],
    Habitat.LAGUNA: ["lagoon", "coastal_lagoon", "shallow_water"],
    Habitat.AREA_URBANA: ["urban", "city", "buildings", "infrastructure", "port"],
    Habitat.RIO: ["river", "stream", "freshwater", "riparian"],
    Habitat.SERRA: ["mountain", "highland", "slope", "elevation"],
}

class ArchaeologyFlag(str, Enum):
    """Indicadores arqueológicos"""
    POSSIBLE_SAMBAQUI = "possible_sambaqui"
    SHELL_MOUND = "shell_mound"
    SHELL_ACCUMULATION = "shell_accumulation"
    CERAMIC_FRAGMENT = "ceramic_fragment"
    LITHIC_MATERIAL = "lithic_material"
    ANTHROPOGENIC_DEPOSIT = "anthropogenic_deposit"
    SHELL_MIDDENS = "shell_middens"
    ARCHAEOLOGICAL_SITE = "archaeological_site"

class ActivityType(str, Enum):
    """Tipos de atividades humanas"""
    PESCA_ARTESANAL = "pesca_artesanal"
    PESCA_INDUSTRIAL = "pesca_industrial"
    MARICULTURA = "maricultura"
    PESQUISA_CIENTIFICA = "pesquisa_cientifica"
    TURISMO = "turismo"
    NAVEGACAO = "navegacao"
    CONSTRUCAO = "construcao"
    DESMATAMENTO = "desmatamento"
    RECUPERACAO_AMBIENTAL = "recuperacao_ambiental"

# ============================================================================
# SCHEMAS DE DADOS
# ============================================================================

@dataclass
class SpeciesCandidate:
    """Candidato a identificação de espécie"""
    name_pt: str
    name_scientific: str
    confidence: float  # 0.0 - 1.0
    evidence: str
    taxonomy_level: str = "species"  # species, genus, family, order

    def to_dict(self) -> Dict:
        return {
            'name_pt': self.name_pt,
            'name_scientific': self.name_scientific,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'taxonomy_level': self.taxonomy_level
        }

@dataclass
class LocationGuess:
    """Localização estimada com confiança"""
    description: str
    confidence: float
    evidence: str
    coordinates: Optional[tuple] = None  # (lat, lon)

@dataclass
class AcquaplanMetadata:
    """Schema completo de metadados Acquaplan"""
    
    # Identificação
    file_id: str
    source: str  # "lightroom" | "drive" | "colaborador"
    original_filename: str
    
    # Descrições (multi-nível)
    title: str
    description_short: str  # 1 frase impactante
    description_long: str   # 2-5 frases detalhadas
    
    # Classificação ecológica
    habitat_guess: str
    habitat_confidence: float
    habitat_evidence: str
    
    # Espécies identificadas
    species_candidates: List[SpeciesCandidate] = field(default_factory=list)
    
    # Arqueologia
    archaeology_flags: List[str] = field(default_factory=list)
    archaeology_evidence: str = ""
    
    # Keywords estruturadas (hierárquicas)
    keywords: List[str] = field(default_factory=list)
    
    # Localização (opcional)
    location_guess: Optional[LocationGuess] = None
    
    # Atividades humanas observadas
    activities: List[str] = field(default_factory=list)
    
    # Qualidade da imagem
    technical_quality: str = ""  # sharp, blurred, underexposed, overexposed
    
    # Timestamps
    processing_timestamp: str = ""
    
    def to_dict(self) -> Dict:
        """Converte para dicionário serializável"""
        return {
            'file_id': self.file_id,
            'source': self.source,
            'original_filename': self.original_filename,
            'title': self.title,
            'description_short': self.description_short,
            'description_long': self.description_long,
            'habitat_guess': self.habitat_guess,
            'habitat_confidence': self.habitat_confidence,
            'habitat_evidence': self.habitat_evidence,
            'species_candidates': [s.to_dict() for s in self.species_candidates],
            'archaeology_flags': self.archaeology_flags,
            'archaeology_evidence': self.archaeology_evidence,
            'keywords': self.keywords,
            'location_guess': self.location_guess.__dict__ if self.location_guess else None,
            'activities': self.activities,
            'technical_quality': self.technical_quality,
            'processing_timestamp': self.processing_timestamp
        }

# ============================================================================
# HIERARQUIA DE KEYWORDS
# ============================================================================

KEYWORD_CATEGORIES = {
    'bioma': ['manguezal', 'restinga', 'mata_atlantica', 'dunas', 'praia', 'costao_rochoso'],
    'fauna': ['ave', 'peixe', 'crustaceo', 'molusco', 'reptil', 'mamifero', 'inseto'],
    'flora': ['arvore', 'arbusto', 'herbácea', 'alga', 'planta_aquatica', 'bromélia'],
    'atividade': ['pesca', 'maricultura', 'pesquisa', 'turismo', 'navegacao'],
    'arqueologia': ['sambaqui', 'cerâmica', 'lítico', 'concha'],
    'geomorfologia': ['duna', 'praia', 'estuário', 'ilha', 'canal', 'baía'],
    'impacto': ['poluicao', 'desmatamento', 'erosao', 'assoreamento', 'eutrofização'],
    'clima': ['sol', 'nublado', 'chuva', 'maré_alta', 'maré_baixa'],
    'técnica': ['aérea', 'subaquática', 'macro', 'panorâmica', 'close-up']
}

# ============================================================================
# PROMPTS BASE
# ============================================================================

EXTRACTION_PROMPT_TEMPLATE = """Você é um especialista em ecologia costeira e marinha brasileira, com conhecimento em:
- Ecossistemas costeiros (manguezais, restingas, costões rochosos)
- Fauna e flora regional
- Arqueologia costeira (sambaquis, sítios pré-coloniais)
- Geomorfologia costeira

Analise esta imagem com RIGOR CIENTÍFICO e retorne APENAS um JSON válido.

HABITATS VÁLIDOS: {habitats}

ESTRUTURA OBRIGATÓRIA:
{{
  "scene_summary": "Descrição factual e objetiva em 2-3 frases. Seja específico sobre elementos visíveis.",
  
  "habitat_guess": "Escolha UM habitat da lista acima. Seja o MAIS ESPECÍFICO possível.",
  "habitat_confidence": 0.0-1.0,
  "habitat_evidence": "Liste elementos visuais concretos que justificam sua classificação",
  
  "species_candidates": [
    {{
      "name_pt": "Nome popular em português",
      "name_scientific": "Gênero species (se identificável) ou 'família Familidae' ou 'ordem Ordem'",
      "confidence": 0.0-1.0,
      "evidence": "Características morfológicas visíveis (cor, forma, tamanho, estruturas)",
      "taxonomy_level": "species|genus|family|order"
    }}
  ],
  
  "archaeology_flags": ["APENAS se houver evidência clara: possible_sambaqui, shell_accumulation, etc."],
  "archaeology_evidence": "Descreva evidências se houver, senão deixe vazio",
  
  "activities": ["Atividades humanas visíveis: pesca_artesanal, maricultura, etc."],
  
  "technical_quality": "sharp|slightly_blurred|blurred|underexposed|overexposed|good_exposure",
  
  "keywords_raw": [
    "30-80 palavras-chave descritivas",
    "Inclua: cores dominantes, texturas, elementos, condições climáticas",
    "Use formato: categoria:valor quando apropriado",
    "Exemplo: fauna:caranguejo, cor:verde, clima:nublado, tecnica:aerea"
  ]
}}

REGRAS CRÍTICAS:
1. Para espécies: seja CONSERVADOR. Se não tiver certeza razoável, use nível taxonômico superior (gênero/família)
2. Para sambaquis: só marque se houver FORTE evidência (acúmulo visível de conchas, elevação, estratificação)
3. Para habitat: considere vegetação, substrato, presença de água, maré
4. Keywords: balance termos técnicos e descritivos
5. NUNCA invente informações. Se não souber, indique baixa confiança
"""

NORMALIZATION_PROMPT_TEMPLATE = """Você receberá dados brutos de análise de uma imagem científica.
Sua tarefa: refinar e normalizar os metadados seguindo padrões Acquaplan.

DADOS BRUTOS:
{raw_data}

REFINE E RETORNE JSON:
{{
  "title": "Título conciso, 5-8 palavras, estilo: 'Manguezal com Rhizophora na Baía de Babitonga'",
  
  "description_short": "1 frase impactante que captura a essência da imagem (20-30 palavras)",
  
  "description_long": "2-4 frases detalhadas. Inclua contexto ecológico, elementos notáveis, condições observadas (60-100 palavras)",
  
  "keywords_normalized": [
    "30-80 keywords normalizadas",
    "Use hierarquia: bioma:manguezal, fauna:caranguejo-uçá, geomorfologia:estuário",
    "Inclua termos em português E científicos quando relevante",
    "Balanceie categorias: ecologia, atividades, localização, técnica",
    "Remova duplicatas e variações redundantes",
    "Ordene por relevância"
  ]
}}

EXEMPLOS DE KEYWORDS HIERÁRQUICAS:
- bioma:manguezal
- fauna:ucides_cordatus
- fauna:caranguejo-uçá
- atividade:pesca_artesanal
- geomorfologia:canal_de_maré
- clima:maré_baixa
- tecnica:fotografia_aerea
- conservacao:area_preservada

MANTENHA: toda informação científica dos dados brutos (espécies, evidências, confiança)
"""

# ============================================================================
# CONFIGURAÇÕES TÉCNICAS
# ============================================================================

class Config:
    """Configurações do sistema"""
    
    # Modelo de visão
    # Modelos recomendados (em ordem de preferência):
    # - llama3.2-vision:11b (melhor qualidade, requer 32GB RAM)
    # - llama3.2-vision (padrão, ~7B)
    # - llava:13b (alternativa robusta)
    # - llava:7b (mais rápido)
    VISION_MODEL = "llama3.2-vision:11b"
    
    # Limites
    MAX_KEYWORDS = 80
    MIN_KEYWORDS = 30
    
    # Confiança mínima para tags
    MIN_HABITAT_CONFIDENCE = 0.6
    MIN_SPECIES_CONFIDENCE = 0.5
    MIN_ARCHAEOLOGY_CONFIDENCE = 0.7
    
    # Paths
    MANIFEST_FILENAME = "acquaplan_manifest.jsonl"
    PROCESSED_CACHE = "processed_files.json"
    
    # Batch processing
    BATCH_SIZE = 10
    RETRY_ATTEMPTS = 3
    
    # ExifTool
    EXIFTOOL_COMMON_ARGS = [
        '-overwrite_original',
        '-charset', 'utf8',
        '-codedcharacterset=utf8'
    ]
    
    # Google Drive
    DRIVE_BATCH_SIZE = 50
    DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive']
