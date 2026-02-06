"""
PROJETO B - Google Drive Tagger
Atualiza descrições de arquivos no Google Drive
"""

import json
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import sys

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️  Google API não instalada. Instale com: pip install google-api-python-client google-auth")

sys.path.append(str(Path(__file__).parent.parent))
from config.acquaplan_config import Config, AcquaplanMetadata
from src.vision_pipeline import VisionPipeline


class DriveTagger:
    """
    Processa imagens do Google Drive e atualiza suas descrições
    """
    
    def __init__(
        self,
        credentials_path: Path,
        manifest_path: Optional[Path] = None,
        dry_run: bool = False
    ):
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google API libraries não instaladas")
        
        self.credentials_path = Path(credentials_path)
        self.manifest_path = manifest_path or Path.home() / Config.MANIFEST_FILENAME
        self.dry_run = dry_run
        self.pipeline = VisionPipeline()
        
        # Autenticar
        self.service = self._authenticate()
        self.processed_cache = self._load_cache()
    
    def _authenticate(self):
        """Autentica com Google Drive API"""
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Arquivo de credenciais não encontrado: {self.credentials_path}\n"
                f"Crie uma Service Account no Google Cloud Console:\n"
                f"https://console.cloud.google.com/apis/credentials"
            )
        
        creds = service_account.Credentials.from_service_account_file(
            str(self.credentials_path),
            scopes=Config.DRIVE_SCOPES
        )
        
        return build('drive', 'v3', credentials=creds)
    
    def _load_cache(self) -> set:
        """Carrega cache de arquivos já processados"""
        cache_path = self.manifest_path.parent / f"drive_{Config.PROCESSED_CACHE}"
        
        if cache_path.exists():
            with open(cache_path) as f:
                data = json.load(f)
                return set(data.get('processed_files', []))
        
        return set()
    
    def _save_cache(self):
        """Salva cache de arquivos processados"""
        cache_path = self.manifest_path.parent / f"drive_{Config.PROCESSED_CACHE}"
        
        with open(cache_path, 'w') as f:
            json.dump({
                'processed_files': list(self.processed_cache),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
    
    def process_folder(
        self,
        folder_id: str,
        skip_processed: bool = True,
        min_description_length: int = 100
    ) -> List[AcquaplanMetadata]:
        """
        Processa todos os arquivos de imagem de uma pasta do Drive
        
        Args:
            folder_id: ID da pasta no Google Drive
            skip_processed: Pular arquivos já processados
            min_description_length: Tamanho mínimo de descrição para pular
        
        Returns:
            Lista de metadados processados
        """
        print(f"📂 Listando arquivos da pasta {folder_id}...")
        
        # Listar arquivos de imagem
        files = self._list_image_files(folder_id)
        
        if not files:
            print(f"⚠️  Nenhuma imagem encontrada na pasta")
            return []
        
        print(f"📁 Encontrados {len(files)} arquivos de imagem")
        
        # Filtrar arquivos a processar
        to_process = []
        for file in files:
            file_id = file['id']
            current_desc = file.get('description', '')
            
            # Pular se já processado
            if skip_processed and file_id in self.processed_cache:
                continue
            
            # Pular se já tem descrição rica
            if current_desc and len(current_desc) >= min_description_length:
                print(f"⏭️  Pulando {file['name']} (já tem descrição rica)")
                continue
            
            to_process.append(file)
        
        if not to_process:
            print("✅ Todos os arquivos já foram processados!")
            return []
        
        print(f"🚀 Processando {len(to_process)} arquivos...\n")
        
        # Processar cada arquivo
        results = []
        for idx, file in enumerate(to_process, 1):
            print(f"[{idx}/{len(to_process)}] {file['name']}")
            
            try:
                # Baixar arquivo temporariamente
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    tmp_path = Path(tmp_file.name)
                    self._download_file(file['id'], tmp_path)
                    
                    # Processar com IA
                    metadata = self.pipeline.process_image(
                        str(tmp_path),
                        file_id=file['id'],
                        source="drive"
                    )
                    
                    # Atualizar descrição no Drive
                    if not self.dry_run:
                        drive_description = self._format_for_drive(metadata)
                        self._update_file_description(file['id'], drive_description)
                        self._append_to_manifest(file, metadata)
                        self.processed_cache.add(file['id'])
                    else:
                        print(f"  🔍 [DRY RUN] Não atualizando Drive")
                    
                    results.append(metadata)
                    print(f"  ✅ Concluído\n")
                    
                    # Limpar arquivo temporário
                    tmp_path.unlink()
                    
            except Exception as e:
                print(f"  ❌ Erro: {e}\n")
                continue
        
        # Salvar cache
        if not self.dry_run:
            self._save_cache()
        
        print("\n" + "="*80)
        print(f"✅ Processamento concluído: {len(results)}/{len(to_process)} arquivos")
        print(f"📄 Manifest: {self.manifest_path}")
        
        return results
    
    def _list_image_files(self, folder_id: str) -> List[Dict]:
        """Lista todos os arquivos de imagem de uma pasta"""
        query = f"'{folder_id}' in parents and (mimeType contains 'image/jpeg' or mimeType contains 'image/png' or mimeType contains 'image/tiff')"
        
        files = []
        page_token = None
        
        while True:
            response = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, description, mimeType, createdTime)",
                pageSize=Config.DRIVE_BATCH_SIZE,
                pageToken=page_token
            ).execute()
            
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            
            if not page_token:
                break
        
        return files
    
    def _download_file(self, file_id: str, output_path: Path):
        """Baixa arquivo do Drive"""
        request = self.service.files().get_media(fileId=file_id)
        
        with open(output_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            
            while not done:
                status, done = downloader.next_chunk()
    
    def _update_file_description(self, file_id: str, description: str):
        """Atualiza descrição de um arquivo no Drive"""
        self.service.files().update(
            fileId=file_id,
            body={'description': description}
        ).execute()
        
        print(f"  📝 Descrição do Drive atualizada")
    
    def _format_for_drive(self, metadata: AcquaplanMetadata) -> str:
        """
        Formata descrição human-friendly para o campo Description do Drive
        
        Retorna texto estruturado e legível
        """
        lines = [
            metadata.description_long,
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        # Habitat
        lines.append(f"🌿 HABITAT: {metadata.habitat_guess}")
        lines.append(f"   Confiança: {metadata.habitat_confidence:.0%}")
        lines.append(f"   {metadata.habitat_evidence}")
        lines.append("")
        
        # Espécies
        if metadata.species_candidates:
            lines.append("🔬 ESPÉCIES IDENTIFICADAS:")
            for sp in metadata.species_candidates[:3]:  # Top 3
                lines.append(f"   • {sp.name_pt}")
                if sp.name_scientific:
                    lines.append(f"     ({sp.name_scientific})")
                lines.append(f"     Confiança: {sp.confidence:.0%}")
                lines.append(f"     {sp.evidence}")
                lines.append("")
        
        # Arqueologia
        if metadata.archaeology_flags:
            lines.append("🏛️  ARQUEOLOGIA:")
            lines.append(f"   {', '.join(metadata.archaeology_flags)}")
            if metadata.archaeology_evidence:
                lines.append(f"   {metadata.archaeology_evidence}")
            lines.append("")
        
        # Atividades
        if metadata.activities:
            lines.append("👥 ATIVIDADES OBSERVADAS:")
            lines.append(f"   {', '.join(metadata.activities)}")
            lines.append("")
        
        # Keywords (top 25)
        lines.append("🏷️  PALAVRAS-CHAVE:")
        keywords_display = metadata.keywords[:25]
        # Quebrar em linhas de ~80 chars
        current_line = "   "
        for kw in keywords_display:
            if len(current_line + kw) > 77:
                lines.append(current_line.rstrip(', '))
                current_line = "   "
            current_line += kw + ", "
        
        if current_line.strip():
            lines.append(current_line.rstrip(', '))
        
        if len(metadata.keywords) > 25:
            lines.append(f"   ... e mais {len(metadata.keywords) - 25} keywords")
        
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"Processado automaticamente em {metadata.processing_timestamp}")
        lines.append("Sistema: Acquaplan Intelligent Tagger v1.0")
        
        return "\n".join(lines)
    
    def _append_to_manifest(self, file_info: Dict, metadata: AcquaplanMetadata):
        """Adiciona entrada ao manifest JSONL"""
        entry = {
            'file_id': file_info['id'],
            'file_name': file_info['name'],
            'metadata': metadata.to_dict(),
            'project': 'drive',
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.manifest_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def process_multiple_folders(
        self,
        folder_ids: List[str],
        skip_processed: bool = True
    ) -> Dict[str, List[AcquaplanMetadata]]:
        """
        Processa múltiplas pastas do Drive
        
        Args:
            folder_ids: Lista de IDs de pastas
            skip_processed: Pular arquivos já processados
        
        Returns:
            Dict com folder_id como chave e lista de metadados
        """
        all_results = {}
        
        for idx, folder_id in enumerate(folder_ids, 1):
            print(f"\n{'='*80}")
            print(f"PASTA {idx}/{len(folder_ids)}: {folder_id}")
            print('='*80 + '\n')
            
            results = self.process_folder(folder_id, skip_processed)
            all_results[folder_id] = results
        
        return all_results


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Acquaplan Google Drive Tagger - Projeto B"
    )
    parser.add_argument(
        'folder_id',
        help='ID da pasta no Google Drive'
    )
    parser.add_argument(
        '--credentials',
        type=Path,
        required=True,
        help='Caminho para arquivo de credenciais da Service Account'
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
        help='Executa sem atualizar Drive (apenas teste)'
    )
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocessa arquivos já processados'
    )
    parser.add_argument(
        '--min-description',
        type=int,
        default=100,
        help='Tamanho mínimo de descrição para pular arquivo'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("ACQUAPLAN GOOGLE DRIVE TAGGER - PROJETO B")
    print("="*80)
    print(f"📂 Pasta ID: {args.folder_id}")
    print(f"🔑 Credentials: {args.credentials}")
    print(f"📄 Manifest: {args.manifest}")
    print(f"🔧 Modo: {'DRY RUN' if args.dry_run else 'PRODUÇÃO'}")
    print("="*80 + "\n")
    
    tagger = DriveTagger(
        credentials_path=args.credentials,
        manifest_path=args.manifest,
        dry_run=args.dry_run
    )
    
    results = tagger.process_folder(
        args.folder_id,
        skip_processed=not args.reprocess,
        min_description_length=args.min_description
    )
    
    print(f"\n🎉 Concluído! {len(results)} arquivos processados.")


if __name__ == "__main__":
    main()
