#!/usr/bin/env python3
"""Instala o encoder semântico local do Nexus (MiniLM-L6-v2, 384d).

Baixa o pacote `gt-all-minilm-l6-v2` do PyPI (que empacota os pesos
safetensors + tokenizer do all-MiniLM-L6-v2, Apache 2.0) e extrai o
modelo para data/semantic/minilm-l6-v2/ — usado pelo
SemanticEncoderProvider (backend 'minilm-local') em numpy puro.

Requisitos: pip funcional (PyPI) + numpy + safetensors + tokenizers
  pip install numpy safetensors tokenizers

Alternativa com melhor qualidade PT-BR (requer internet aberta no 1º uso):
  pip install fastembed
  NEXUS_SEMANTIC_EMBEDDER=fastembed python3 nexus_v14_shared_hippocampus.py

Uso:
  python3 tools/bootstrap_encoder.py            # instala em data/semantic/
  python3 tools/bootstrap_encoder.py --force    # reinstala se já existir
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'semantic', 'minilm-l6-v2')
PKG = 'gt-all-minilm-l6-v2'


def main() -> int:
    if os.path.isfile(os.path.join(MODEL_DIR, 'model.safetensors')):
        if '--force' not in sys.argv:
            print(f'[ok] encoder já instalado em {MODEL_DIR}')
            print('     (use --force para reinstalar)')
            return 0

    for mod in ('numpy', 'safetensors', 'tokenizers'):
        try:
            __import__(mod)
        except ImportError:
            print(f'[!] dependência ausente: {mod}')
            print(f'    instale com: pip install {mod}')
            return 1

    with tempfile.TemporaryDirectory() as tmp:
        print(f'[1/3] baixando {PKG} do PyPI (~90 MB)...')
        r = subprocess.run(
            [sys.executable, '-m', 'pip', 'download', PKG,
             '--no-deps', '-q', '-d', tmp],
            capture_output=True, text=True)
        wheels = [f for f in os.listdir(tmp) if f.endswith('.whl')]
        if r.returncode != 0 or not wheels:
            print('[x] falha no download:', r.stderr[-500:])
            return 1

        print('[2/3] extraindo modelo...')
        # o diretório interno do pacote usa UNDERSCORE (gt_all_minilm_l6_v2),
        # não o nome do pacote com traços
        prefixes = (f'{PKG}/model/', PKG.replace('-', '_') + '/model/')
        with zipfile.ZipFile(os.path.join(tmp, wheels[0])) as z:
            members = [n for n in z.namelist()
                       if n.startswith(prefixes) and not n.endswith('/')]
            if not members:
                print('[x] modelo não encontrado dentro do wheel')
                return 1
            os.makedirs(MODEL_DIR, exist_ok=True)
            for n in members:
                dest = os.path.join(MODEL_DIR, os.path.basename(n))
                with z.open(n) as f, open(dest, 'wb') as g:
                    shutil.copyfileobj(f, g)

    ok = (os.path.isfile(os.path.join(MODEL_DIR, 'model.safetensors'))
          and os.path.isfile(os.path.join(MODEL_DIR, 'tokenizer.json')))
    print(f"[3/3] {'✓ instalado' if ok else '✗ incompleto'}: {MODEL_DIR}")
    if ok:
        print('\nVerificação:')
        print('  python3 nexus_v14_shared_hippocampus.py --agent-demo')
        print('  (o cabeçalho deve mostrar: encoder: minilm-local)')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
