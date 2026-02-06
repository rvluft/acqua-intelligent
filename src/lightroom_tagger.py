"""
PROJETO A - Lightroom Tagger
Tagueia arquivos RAW via XMP sidecars
"""

import subprocess
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config.acquaplan_config import Config, AcquaplanMetadata
from src.vision_pipeline import VisionPipeline


class LightroomTagger:
    """
    Processa fotos do Lightroom e grava metadados em XMP sidecars
    """
    
    def __init__(
        self,
        catalog_path: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        dry_run: bool = False
    ):
        self.catalog_path = catalog_path
        self.manifest_path = manifest_path or Path.home() / Config.MANIFEST_FILENAME
        self.dry_run = dry_run
        self.pipeline = VisionPipeline()
        self.processed_cache = self._load_cache()
    
    def _load_cache(self) -> set:
        """Carrega cache de arquivos já processados"""
        cache_path = self.manifest_path.parent / Config.PROCESSED_CACHE
        
        if cache_path.exists():
            with open(cache_path) as f:
                data = json.load(f)
                return set(data.get('processed_files', []))
        
        return set()
    
    def _save_cache(self):
        """Salva cache de arquivos processados"""
        cache_path = self.manifest_path.parent / Config.PROCESSED_CACHE
        
        with open(cache_path, 'w') as f:
            json.dump({
                'processed_files': list(self.processed_cache),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
    
    def process_folder(
        self,
        folder_path: Path,
        extensions: List[str] = None,
        skip_processed: bool = True
    ) -> List[AcquaplanMetadata]:
        """
        Processa todos os RAWs de uma pasta
        
        Args:
            folder_path: Pasta contendo RAWs
            extensions: Extensões para processar (padrão: CR3, CR2, NEF, ARW)
            skip_processed: Pular arquivos já processados
        
        Returns:
            Lista de metadados processados
        """
        if extensions is None:
            extensions = ['.CR3', '.CR2', '.NEF', '.ARW', '.DNG', '.RAF']
        
        folder_path = Path(folder_path)
        
        # Buscar arquivos
        photo_files = []
        for ext in extensions:
            photo_files.extend(folder_path.glob(f"*{ext}"))
            photo_files.extend(folder_path.glob(f"*{ext.lower()}"))
        
        if not photo_files:
            print(f"⚠️  Nenhum arquivo RAW encontrado em {folder_path}")
            return []
        
        print(f"📁 Encontrados {len(photo_files)} arquivos RAW")
        
        # Filtrar já processados
        if skip_processed:
            to_process = [
                f for f in photo_files
                if str(f) not in self.processed_cache
            ]
            
            if len(to_process) < len(photo_files):
                skipped = len(photo_files) - len(to_process)
                print(f"⏭️  Pulando {skipped} arquivos já processados")
        else:
            to_process = photo_files
        
        if not to_process:
            print("✅ Todos os arquivos já foram processados!")
            return []
        
        print(f"🚀 Processando {len(to_process)} arquivos...\n")
        
        # Processar
        results = []
        for idx, photo_path in enumerate(to_process, 1):
            print(f"[{idx}/{len(to_process)}] {photo_path.name}")
            
            try:
                metadata = self.pipeline.process_image(
                    str(photo_path),
                    file_id=str(photo_path),
                    source="lightroom"
                )
                
                # Gravar XMP sidecar
                if not self.dry_run:
                    self._write_xmp_sidecar(photo_path, metadata)
                    self._append_to_manifest(photo_path, metadata)
                    self.processed_cache.add(str(photo_path))
                else:
                    print(f"  🔍 [DRY RUN] Não gravando arquivos")
                
                results.append(metadata)
                print(f"  ✅ Concluído\n")
                
            except Exception as e:
                print(f"  ❌ Erro: {e}\n")
                continue
        
        # Salvar cache
        if not self.dry_run:
            self._save_cache()
        
        print("\n" + "="*80)
        print(f"✅ Processamento concluído: {len(results)}/{len(to_process)} arquivos")
        print(f"📄 Manifest: {self.manifest_path}")
        
        if not self.dry_run:
            print(f"\n💡 Próximo passo no Lightroom:")
            print(f"   Library → Metadata → Read Metadata from Files")
        
        return results
    
    def _write_xmp_sidecar(self, photo_path: Path, metadata: AcquaplanMetadata):
        """
        Grava XMP sidecar usando ExifTool
        
        Cria arquivo .xmp ao lado do RAW com todos os metadados
        """
        # Construir descrição completa para XMP
        description_parts = [metadata.description_long, ""]
        
        # Adicionar informações estruturadas
        description_parts.append(f"Habitat: {metadata.habitat_guess} (confiança: {metadata.habitat_confidence:.0%})")
        description_parts.append(f"Evidência: {metadata.habitat_evidence}")
        
        if metadata.species_candidates:
            description_parts.append("")
            description_parts.append("Espécies identificadas:")
            for sp in metadata.species_candidates[:3]:  # Top 3
                description_parts.append(
                    f"  • {sp.name_pt} ({sp.name_scientific}) - {sp.confidence:.0%}"
                )
        
        if metadata.archaeology_flags:
            description_parts.append("")
            description_parts.append(f"Arqueologia: {', '.join(metadata.archaeology_flags)}")
            if metadata.archaeology_evidence:
                description_parts.append(f"  {metadata.archaeology_evidence}")
        
        if metadata.activities:
            description_parts.append("")
            description_parts.append(f"Atividades: {', '.join(metadata.activities)}")
        
        description_full = "\n".join(description_parts)
        
        # Construir comando ExifTool
        cmd = ['exiftool'] + Config.EXIFTOOL_COMMON_ARGS + [
            f'-XMP-dc:Title={metadata.title}',
            f'-XMP-dc:Description={description_full}',
            f'-IPTC:Caption-Abstract={metadata.description_short}',
            f'-IPTC:Headline={metadata.title}',
        ]
        
        # Adicionar keywords
        for kw in metadata.keywords:
            cmd.append(f'-XMP-dc:Subject+={kw}')
            cmd.append(f'-IPTC:Keywords+={kw}')
        
        # Adicionar metadados customizados em XMP
        cmd.extend([
            f'-XMP-acquaplan:Habitat={metadata.habitat_guess}',
            f'-XMP-acquaplan:HabitatConfidence={metadata.habitat_confidence}',
            f'-XMP-acquaplan:ProcessingTimestamp={metadata.processing_timestamp}',
        ])
        
        # Arquivo alvo
        cmd.append(str(photo_path))
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Verificar se XMP foi criado
            xmp_path = photo_path.with_suffix(photo_path.suffix + '.xmp')
            if xmp_path.exists():
                print(f"  📝 XMP sidecar criado: {xmp_path.name}")
            else:
                print(f"  ⚠️  XMP não encontrado (metadados podem estar no RAW)")
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erro ao gravar XMP: {e.stderr}")
    
    def _append_to_manifest(self, photo_path: Path, metadata: AcquaplanMetadata):
        """Adiciona entrada ao manifest JSONL"""
        entry = {
            'file_path': str(photo_path),
            'metadata': metadata.to_dict(),
            'project': 'lightroom',
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.manifest_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def read_lightroom_catalog(self, collection_name: str = None) -> List[Path]:
        """
        Lê arquivos de uma coleção do Lightroom Classic
        
        NOTA: Requer acesso ao banco SQLite do Lightroom
        Esta é uma implementação básica - pode precisar ajustes
        
        Args:
            collection_name: Nome da coleção (None = todas as fotos)
        
        Returns:
            Lista de paths absolutos
        """
        if not self.catalog_path or not self.catalog_path.exists():
            raise ValueError("catalog_path não configurado ou inválido")
        
        # Lightroom usa SQLite
        conn = sqlite3.connect(str(self.catalog_path))
        cursor = conn.cursor()
        
        try:
            if collection_name:
                # Buscar por coleção específica
                query = """
                    SELECT af.absolutePath || '/' || rf.baseName || '.' || rf.extension
                    FROM Adobe_images ai
                    JOIN AgLibraryFile rf ON ai.rootFile = rf.id_local
                    JOIN AgLibraryFolder af ON rf.folder = af.id_local
                    JOIN AgLibraryCollectionImage aci ON ai.id_local = aci.image
                    JOIN AgLibraryCollection ac ON aci.collection = ac.id_local
                    WHERE ac.name = ?
                """
                cursor.execute(query, (collection_name,))
            else:
                # Todas as fotos
                query = """
                    SELECT af.absolutePath || '/' || rf.baseName || '.' || rf.extension
                    FROM Adobe_images ai
                    JOIN AgLibraryFile rf ON ai.rootFile = rf.id_local
                    JOIN AgLibraryFolder af ON rf.folder = af.id_local
                """
                cursor.execute(query)
            
            paths = [Path(row[0]) for row in cursor.fetchall()]
            return paths
            
        finally:
            conn.close()


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Acquaplan Lightroom Tagger - Projeto A"
    )
    parser.add_argument(
        'folder',
        type=Path,
        help='Pasta contendo arquivos RAW'
    )
    parser.add_argument(
        '--manifest',
        type=Path,
        default=Path.home() / Config.MANIFEST_FILENAME,
        help='Caminho do arquivo manifest.jsonl'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Executa sem gravar arquivos (apenas teste)'
    )
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocessa arquivos já processados'
    )
    parser.add_argument(
        '--extensions',
        nargs='+',
        default=['.CR3', '.CR2', '.NEF', '.ARW'],
        help='Extensões de arquivo para processar'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("ACQUAPLAN LIGHTROOM TAGGER - PROJETO A")
    print("="*80)
    print(f"📁 Pasta: {args.folder}")
    print(f"📄 Manifest: {args.manifest}")
    print(f"🔧 Modo: {'DRY RUN' if args.dry_run else 'PRODUÇÃO'}")
    print("="*80 + "\n")
    
    tagger = LightroomTagger(
        manifest_path=args.manifest,
        dry_run=args.dry_run
    )
    
    results = tagger.process_folder(
        args.folder,
        extensions=args.extensions,
        skip_processed=not args.reprocess
    )
    
    print(f"\n🎉 Concluído! {len(results)} arquivos processados.")


if __name__ == "__main__":
    main()
