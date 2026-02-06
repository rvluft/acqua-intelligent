"""
NOTEBOOK DE TESTE - Acquaplan Tagger
Teste o sistema com fotos de exemplo
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from vision_pipeline import VisionPipeline
from lightroom_tagger import LightroomTagger
import json


def test_single_image(image_path: str):
    """
    Teste básico: processa uma imagem e mostra o resultado
    """
    print("="*80)
    print("TESTE 1: PROCESSAMENTO DE IMAGEM ÚNICA")
    print("="*80)
    
    pipeline = VisionPipeline()
    
    print(f"\n📸 Processando: {image_path}")
    
    try:
        metadata = pipeline.process_image(image_path)
        
        print("\n✅ SUCESSO!\n")
        print("="*80)
        print("METADADOS GERADOS:")
        print("="*80)
        
        print(f"\n📝 Título:")
        print(f"   {metadata.title}")
        
        print(f"\n📄 Descrição curta:")
        print(f"   {metadata.description_short}")
        
        print(f"\n📖 Descrição longa:")
        for line in metadata.description_long.split('. '):
            if line.strip():
                print(f"   {line.strip()}.")
        
        print(f"\n🌿 Habitat:")
        print(f"   Classificação: {metadata.habitat_guess}")
        print(f"   Confiança: {metadata.habitat_confidence:.1%}")
        print(f"   Evidência: {metadata.habitat_evidence}")
        
        if metadata.species_candidates:
            print(f"\n🔬 Espécies identificadas ({len(metadata.species_candidates)}):")
            for idx, sp in enumerate(metadata.species_candidates, 1):
                print(f"\n   {idx}. {sp.name_pt}")
                if sp.name_scientific:
                    print(f"      Nome científico: {sp.name_scientific}")
                print(f"      Nível taxonômico: {sp.taxonomy_level}")
                print(f"      Confiança: {sp.confidence:.1%}")
                print(f"      Evidência: {sp.evidence}")
        
        if metadata.archaeology_flags:
            print(f"\n🏛️  Arqueologia:")
            print(f"   Flags: {', '.join(metadata.archaeology_flags)}")
            if metadata.archaeology_evidence:
                print(f"   Evidência: {metadata.archaeology_evidence}")
        
        if metadata.activities:
            print(f"\n👥 Atividades humanas observadas:")
            for activity in metadata.activities:
                print(f"   • {activity}")
        
        print(f"\n🏷️  Keywords ({len(metadata.keywords)}):")
        
        # Agrupar por categoria
        categorized = {}
        uncategorized = []
        
        for kw in metadata.keywords:
            if ':' in kw:
                cat, val = kw.split(':', 1)
                if cat not in categorized:
                    categorized[cat] = []
                categorized[cat].append(val)
            else:
                uncategorized.append(kw)
        
        for cat, values in sorted(categorized.items()):
            print(f"\n   {cat.upper()}:")
            print(f"      {', '.join(values[:10])}")
            if len(values) > 10:
                print(f"      ... e mais {len(values) - 10}")
        
        if uncategorized:
            print(f"\n   GERAIS:")
            print(f"      {', '.join(uncategorized[:15])}")
            if len(uncategorized) > 15:
                print(f"      ... e mais {len(uncategorized) - 15}")
        
        print(f"\n⏱️  Processado em: {metadata.processing_timestamp}")
        
        print("\n" + "="*80)
        
        return metadata
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_batch_processing(folder_path: str, max_images: int = 3):
    """
    Teste de batch: processa múltiplas imagens de uma pasta
    """
    print("\n" + "="*80)
    print("TESTE 2: PROCESSAMENTO EM BATCH")
    print("="*80)
    
    folder = Path(folder_path)
    
    # Buscar imagens
    image_extensions = ['.jpg', '.jpeg', '.png', '.CR3', '.CR2', '.NEF']
    images = []
    
    for ext in image_extensions:
        images.extend(folder.glob(f"*{ext}"))
        images.extend(folder.glob(f"*{ext.upper()}"))
    
    if not images:
        print(f"⚠️  Nenhuma imagem encontrada em {folder_path}")
        return
    
    # Limitar quantidade
    images = images[:max_images]
    
    print(f"\n📁 Processando {len(images)} imagens de {folder_path}...")
    
    pipeline = VisionPipeline()
    
    results = []
    for idx, img_path in enumerate(images, 1):
        print(f"\n[{idx}/{len(images)}] {img_path.name}")
        print("-" * 40)
        
        try:
            metadata = pipeline.process_image(str(img_path))
            results.append({
                'file': img_path.name,
                'metadata': metadata
            })
            
            # Resumo rápido
            print(f"  ✅ {metadata.title}")
            print(f"  🌿 {metadata.habitat_guess} ({metadata.habitat_confidence:.0%})")
            if metadata.species_candidates:
                sp = metadata.species_candidates[0]
                print(f"  🔬 {sp.name_pt} ({sp.confidence:.0%})")
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            continue
    
    # Salvar resultados
    output_file = folder / 'test_batch_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(
            [{'file': r['file'], 'metadata': r['metadata'].to_dict()} for r in results],
            f,
            indent=2,
            ensure_ascii=False
        )
    
    print("\n" + "="*80)
    print(f"✅ Batch concluído: {len(results)}/{len(images)} imagens processadas")
    print(f"📄 Resultados salvos em: {output_file}")
    print("="*80)


def test_lightroom_workflow(folder_path: str, dry_run: bool = True):
    """
    Teste completo do workflow do Lightroom
    """
    print("\n" + "="*80)
    print("TESTE 3: WORKFLOW LIGHTROOM (DRY RUN)")
    print("="*80)
    
    tagger = LightroomTagger(
        manifest_path=Path(folder_path) / 'test_manifest.jsonl',
        dry_run=dry_run
    )
    
    print(f"\n📁 Processando pasta: {folder_path}")
    print(f"🔧 Modo: {'DRY RUN (não grava arquivos)' if dry_run else 'PRODUÇÃO'}")
    
    results = tagger.process_folder(
        Path(folder_path),
        extensions=['.jpg', '.jpeg', '.CR3', '.CR2'],
        skip_processed=False
    )
    
    if results:
        print(f"\n✅ Teste concluído com sucesso!")
        print(f"   {len(results)} arquivos processados")
        
        if dry_run:
            print(f"\n💡 Para executar de verdade:")
            print(f"   python lightroom_tagger.py {folder_path}")
    else:
        print(f"\n⚠️  Nenhum arquivo foi processado")


def interactive_menu():
    """Menu interativo para testes"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ACQUAPLAN TAGGER - NOTEBOOK DE TESTE                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

Escolha um teste:

1. Processar uma imagem única
2. Processar batch de imagens (máx 3)
3. Testar workflow Lightroom completo (dry run)
4. Sair

""")
    
    choice = input("Escolha (1-4): ").strip()
    
    if choice == '1':
        img_path = input("\nCaminho da imagem: ").strip()
        test_single_image(img_path)
    
    elif choice == '2':
        folder = input("\nCaminho da pasta: ").strip()
        test_batch_processing(folder)
    
    elif choice == '3':
        folder = input("\nCaminho da pasta com RAWs: ").strip()
        test_lightroom_workflow(folder)
    
    elif choice == '4':
        print("\n👋 Até logo!")
        return
    
    else:
        print("\n⚠️  Opção inválida")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Modo CLI
        if sys.argv[1] == 'single' and len(sys.argv) > 2:
            test_single_image(sys.argv[2])
        
        elif sys.argv[1] == 'batch' and len(sys.argv) > 2:
            test_batch_processing(sys.argv[2])
        
        elif sys.argv[1] == 'lightroom' and len(sys.argv) > 2:
            test_lightroom_workflow(sys.argv[2])
        
        else:
            print("Uso:")
            print("  python test_notebook.py single <imagem.jpg>")
            print("  python test_notebook.py batch <pasta>")
            print("  python test_notebook.py lightroom <pasta_com_raws>")
    
    else:
        # Modo interativo
        interactive_menu()
