"""
Ferramentas para trabalhar com o manifest.jsonl
Exportação para CSV, análise estatística, etc.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter, defaultdict
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config.acquaplan_config import Config


class ManifestTools:
    """Ferramentas para analisar e exportar o manifest"""
    
    def __init__(self, manifest_path: Path):
        self.manifest_path = Path(manifest_path)
        
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest não encontrado: {manifest_path}")
        
        self.entries = self._load_all()
    
    def _load_all(self) -> List[Dict]:
        """Carrega todas as entradas do manifest"""
        entries = []
        
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        return entries
    
    def stats(self) -> Dict:
        """Gera estatísticas do manifest"""
        
        total = len(self.entries)
        
        # Contadores
        projects = Counter(e.get('project', 'unknown') for e in self.entries)
        habitats = Counter(
            e['metadata']['habitat_guess'] 
            for e in self.entries 
            if 'habitat_guess' in e.get('metadata', {})
        )
        
        # Espécies mais comuns
        all_species = []
        for entry in self.entries:
            species_list = entry.get('metadata', {}).get('species_candidates', [])
            for sp in species_list:
                if isinstance(sp, dict) and sp.get('confidence', 0) > 0.7:
                    all_species.append(sp.get('name_scientific', sp.get('name_pt', '')))
        
        species_counts = Counter(all_species)
        
        # Arqueologia
        archaeology_count = sum(
            1 for e in self.entries
            if e.get('metadata', {}).get('archaeology_flags')
        )
        
        # Keywords mais comuns
        all_keywords = []
        for entry in self.entries:
            all_keywords.extend(entry.get('metadata', {}).get('keywords', []))
        
        keyword_counts = Counter(all_keywords)
        
        return {
            'total_entries': total,
            'by_project': dict(projects),
            'habitats': dict(habitats.most_common(10)),
            'top_species': dict(species_counts.most_common(10)),
            'archaeology_flags': archaeology_count,
            'top_keywords': dict(keyword_counts.most_common(30)),
            'date_range': {
                'first': min((e.get('timestamp', '') for e in self.entries), default=''),
                'last': max((e.get('timestamp', '') for e in self.entries), default='')
            }
        }
    
    def print_stats(self):
        """Imprime estatísticas formatadas"""
        stats = self.stats()
        
        print("="*80)
        print("ESTATÍSTICAS DO MANIFEST")
        print("="*80)
        print(f"\n📊 Total de entradas: {stats['total_entries']}")
        
        print(f"\n📁 Por projeto:")
        for project, count in stats['by_project'].items():
            print(f"   {project}: {count}")
        
        print(f"\n🌿 Habitats mais comuns:")
        for habitat, count in list(stats['habitats'].items())[:10]:
            pct = count / stats['total_entries'] * 100
            print(f"   {habitat}: {count} ({pct:.1f}%)")
        
        print(f"\n🔬 Espécies mais identificadas (confiança > 70%):")
        for species, count in list(stats['top_species'].items())[:10]:
            print(f"   {species}: {count}")
        
        print(f"\n🏛️  Flags arqueológicas: {stats['archaeology_flags']}")
        
        print(f"\n🏷️  Keywords mais usadas:")
        for kw, count in list(stats['top_keywords'].items())[:15]:
            print(f"   {kw}: {count}")
        
        print(f"\n📅 Período:")
        print(f"   Primeiro: {stats['date_range']['first']}")
        print(f"   Último: {stats['date_range']['last']}")
        
        print("\n" + "="*80)
    
    def to_csv_exiftool(self, output_path: Path, project: str = None):
        """
        Exporta para CSV compatível com ExifTool em batch
        
        Formato: SourceFile, XMP-dc:Title, XMP-dc:Description, etc.
        """
        entries_to_export = self.entries
        
        if project:
            entries_to_export = [
                e for e in self.entries 
                if e.get('project') == project
            ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'SourceFile',
                'XMP-dc:Title',
                'XMP-dc:Description',
                'IPTC:Caption-Abstract',
                'XMP-dc:Subject',
                'IPTC:Keywords'
            ])
            
            writer.writeheader()
            
            for entry in entries_to_export:
                meta = entry.get('metadata', {})
                
                # Construir descrição completa
                desc_parts = [meta.get('description_long', '')]
                desc_parts.append(f"\nHabitat: {meta.get('habitat_guess', '')} ({meta.get('habitat_confidence', 0):.0%})")
                
                # Keywords como string separada por ponto-e-vírgula
                keywords_str = ';'.join(meta.get('keywords', []))
                
                writer.writerow({
                    'SourceFile': entry.get('file_path', entry.get('file_id', '')),
                    'XMP-dc:Title': meta.get('title', ''),
                    'XMP-dc:Description': ''.join(desc_parts),
                    'IPTC:Caption-Abstract': meta.get('description_short', ''),
                    'XMP-dc:Subject': keywords_str,
                    'IPTC:Keywords': keywords_str
                })
        
        print(f"✅ CSV para ExifTool exportado: {output_path}")
        print(f"   {len(entries_to_export)} entradas")
        print(f"\n💡 Para aplicar em lote:")
        print(f"   exiftool -csv=\"{output_path}\" /pasta/com/fotos/")
    
    def to_csv_analysis(self, output_path: Path):
        """
        Exporta CSV para análise em Excel/Python
        
        Formato flat com uma linha por imagem
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'file_id',
                'filename',
                'project',
                'timestamp',
                'title',
                'description_short',
                'habitat',
                'habitat_confidence',
                'species_count',
                'top_species',
                'archaeology_flags',
                'keywords_count',
                'top_keywords'
            ])
            
            writer.writeheader()
            
            for entry in self.entries:
                meta = entry.get('metadata', {})
                
                # Top espécie
                species_list = meta.get('species_candidates', [])
                top_species = ''
                if species_list and isinstance(species_list, list):
                    top = species_list[0]
                    if isinstance(top, dict):
                        top_species = f"{top.get('name_pt', '')} ({top.get('confidence', 0):.0%})"
                
                # Top keywords
                keywords = meta.get('keywords', [])
                top_kw = ', '.join(keywords[:10])
                
                writer.writerow({
                    'file_id': entry.get('file_id', entry.get('file_path', '')),
                    'filename': entry.get('file_name', Path(entry.get('file_path', '')).name),
                    'project': entry.get('project', ''),
                    'timestamp': entry.get('timestamp', ''),
                    'title': meta.get('title', ''),
                    'description_short': meta.get('description_short', ''),
                    'habitat': meta.get('habitat_guess', ''),
                    'habitat_confidence': meta.get('habitat_confidence', 0),
                    'species_count': len(species_list),
                    'top_species': top_species,
                    'archaeology_flags': ', '.join(meta.get('archaeology_flags', [])),
                    'keywords_count': len(keywords),
                    'top_keywords': top_kw
                })
        
        print(f"✅ CSV para análise exportado: {output_path}")
    
    def filter_by_habitat(self, habitat: str) -> List[Dict]:
        """Retorna entradas de um habitat específico"""
        return [
            e for e in self.entries
            if e.get('metadata', {}).get('habitat_guess') == habitat
        ]
    
    def filter_by_species(self, species_name: str, min_confidence: float = 0.5) -> List[Dict]:
        """Retorna entradas com uma espécie específica"""
        results = []
        
        for entry in self.entries:
            species_list = entry.get('metadata', {}).get('species_candidates', [])
            
            for sp in species_list:
                if isinstance(sp, dict):
                    name_pt = sp.get('name_pt', '').lower()
                    name_sci = sp.get('name_scientific', '').lower()
                    confidence = sp.get('confidence', 0)
                    
                    if confidence >= min_confidence:
                        if species_name.lower() in name_pt or species_name.lower() in name_sci:
                            results.append(entry)
                            break
        
        return results
    
    def filter_by_archaeology(self) -> List[Dict]:
        """Retorna entradas com flags arqueológicas"""
        return [
            e for e in self.entries
            if e.get('metadata', {}).get('archaeology_flags')
        ]
    
    def export_filtered(self, entries: List[Dict], output_path: Path):
        """Exporta entradas filtradas para novo manifest"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✅ {len(entries)} entradas exportadas para {output_path}")


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ferramentas para análise do manifest Acquaplan"
    )
    parser.add_argument(
        '--manifest',
        type=Path,
        default=Path.home() / Config.MANIFEST_FILENAME,
        help='Caminho do manifest.jsonl'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comando')
    
    # Stats
    subparsers.add_parser('stats', help='Mostrar estatísticas')
    
    # Export ExifTool CSV
    export_exif = subparsers.add_parser('export-exiftool', help='Exportar CSV para ExifTool')
    export_exif.add_argument('--output', type=Path, required=True)
    export_exif.add_argument('--project', choices=['lightroom', 'drive'])
    
    # Export Analysis CSV
    export_analysis = subparsers.add_parser('export-analysis', help='Exportar CSV para análise')
    export_analysis.add_argument('--output', type=Path, required=True)
    
    # Filter
    filter_cmd = subparsers.add_parser('filter', help='Filtrar entradas')
    filter_cmd.add_argument('--habitat', help='Filtrar por habitat')
    filter_cmd.add_argument('--species', help='Filtrar por espécie')
    filter_cmd.add_argument('--archaeology', action='store_true', help='Apenas com flags arqueológicas')
    filter_cmd.add_argument('--output', type=Path, help='Salvar resultado filtrado')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Carregar manifest
    tools = ManifestTools(args.manifest)
    
    if args.command == 'stats':
        tools.print_stats()
    
    elif args.command == 'export-exiftool':
        tools.to_csv_exiftool(args.output, args.project)
    
    elif args.command == 'export-analysis':
        tools.to_csv_analysis(args.output)
    
    elif args.command == 'filter':
        results = []
        
        if args.habitat:
            results = tools.filter_by_habitat(args.habitat)
            print(f"🔍 Encontradas {len(results)} entradas com habitat '{args.habitat}'")
        
        elif args.species:
            results = tools.filter_by_species(args.species)
            print(f"🔍 Encontradas {len(results)} entradas com espécie '{args.species}'")
        
        elif args.archaeology:
            results = tools.filter_by_archaeology()
            print(f"🔍 Encontradas {len(results)} entradas com flags arqueológicas")
        
        if results and args.output:
            tools.export_filtered(results, args.output)


if __name__ == "__main__":
    main()
