#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NEXUS V14 UNIFIED — PIPELINE DE INGESTÃO DE CONHECIMENTO                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Põe conhecimento DENTRO do kernel — até aqui o sistema só aprendia pelo chat
ou por um documento colado à mão. Este módulo lê corpus real (arquivos,
diretórios, JSONL, Wikipedia) e reporta o que entrou, o que foi duplicado e
qual ficou a cobertura de proveniência.

Fontes suportadas:

  --file ARQ              um arquivo de texto (.txt/.md/.rst) ou JSONL
  --dir DIR               diretório inteiro (busca recursiva)
  --glob 'docs/**/*.md'   padrão glob
  --wiki TÍTULO           resumo da Wikipedia pt (requer rede)
  --wiki-list ARQ         um título por linha
  --stdin                 texto vindo da entrada padrão

Comportamento:

  • Segmentação por sentenças + filtro de tamanho (a mesma usada por
    learn_document), com limpeza de artefatos markdown.
  • Deduplicação SDR do próprio kernel: fato repetido NÃO é reaprendido e é
    contabilizado como duplicado no relatório.
  • Proveniência por fato: origem = caminho do arquivo ou URL, confiança
    configurável via --confidence (padrão: 0.85 para arquivos, 0.80 Wikipedia).
  • --backfill marca fatos pré-existentes sem origem como 'legacy'.
  • Relatório final em JSON (--report) + resumo legível no terminal.

Exemplos:

    python nexus_ingest.py --file manual.txt
    python nexus_ingest.py --glob 'docs/**/*.md' --confidence 0.9 --report ing.json
    python nexus_ingest.py --wiki Fotossíntese --wiki Mitocôndria
    python nexus_ingest.py --file fatos.jsonl --jsonl
    python nexus_ingest.py --stdin < artigo.txt

JSONL: cada linha é um objeto com a chave "text" (ou "fact") e, opcionalmente,
"source", "confidence" e "evidence".
"""
from __future__ import annotations

import argparse
import glob as _glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

WIKI_URL = "https://pt.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKI_UA = "NexusV14-Ingest/1.0 (python-stdlib)"

# Segmentação de sentenças: ponto/interrogação/exclamação + quebra de parágrafo
_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|\n{2,}')
_MD_ARTIFACTS = re.compile(r'[*#`>|\[\]()]')


# ══════════════════════════════════════════════════════════════════════════════
# NÚCLEO DA INGESTÃO
# ══════════════════════════════════════════════════════════════════════════════

def split_facts(text: str, min_len: int = 20, max_len: int = 250) -> List[str]:
    """Texto bruto → lista de fatos atômicos (sentenças limpas e úteis)."""
    fatos: List[str] = []
    for bruto in _SENT_SPLIT.split(text or ''):
        s = _MD_ARTIFACTS.sub('', bruto or '').strip()
        s = re.sub(r'\s+', ' ', s)
        # Descarta ruído de markdown/tabelas e linhas sem conteúdo semântico
        if min_len <= len(s) <= max_len and len(re.findall(r'\w', s)) >= min_len * 0.6:
            fatos.append(s)
    return fatos


def _tamanho_store(kernel) -> Optional[int]:
    """Quantos fatos o kernel tem agora? (None se a API não existir)"""
    try:
        return len(kernel.cognitive.fact_store)
    except Exception:
        return None


def _learn_batch(kernel, fatos: Iterable[str], source: str, confidence: float,
                 evidence: str = '') -> Tuple[int, int]:
    """Aprende uma lista de fatos. Retorna (novos, duplicados)."""
    novos = dups = 0
    for fato in fatos:
        # Métrica autoritativa: o FactStore cresceu? (a mensagem do kernel é
        # secundária — nunca confiamos só no texto para decidir se aprendeu)
        antes = _tamanho_store(kernel)
        try:
            resultado = kernel.learn(fato, source=source, confidence=confidence,
                                     evidence=evidence)
        except TypeError:
            # Compatibilidade com kernels antigos (sem parâmetros de origem):
            # aprende e tenta registrar a proveniência pelo caminho disponível.
            resultado = kernel.learn(fato)
            store = getattr(kernel, 'provenance', None) or \
                getattr(getattr(kernel, 'cognitive', None), 'provenance', None)
            try:
                if store is not None:
                    store.record(fato, source=source, confidence=confidence,
                                 evidence=evidence)
            except Exception:
                pass
        depois = _tamanho_store(kernel)
        duplicado = str(resultado).lstrip().lower().startswith('[dedup]')
        if antes is not None and depois is not None:
            duplicado = duplicado or depois <= antes
        if duplicado:
            dups += 1
        else:
            novos += 1
    return novos, dups


def ingest_text(kernel, text: str, source: str = 'ingest',
                confidence: float = 0.85, evidence: str = '',
                min_len: int = 20, max_len: int = 250) -> Dict[str, Any]:
    """Ingere um bloco de texto. Devolve métricas da ingestão."""
    fatos = split_facts(text, min_len=min_len, max_len=max_len)
    novos, dups = _learn_batch(kernel, fatos, source, confidence, evidence)
    return _metricas(source, novos, dups, len(text or ''), len(fatos))


def ingest_file(kernel, path: str, confidence: float = 0.85,
                min_len: int = 20, max_len: int = 250) -> Dict[str, Any]:
    """Ingere um arquivo de texto (ou JSONL quando termina em .jsonl)."""
    if path.lower().endswith(('.jsonl', '.ndjson')):
        return ingest_jsonl(kernel, path)
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        texto = f.read()
    return ingest_text(kernel, texto, source='ingest', confidence=confidence,
                       evidence=os.path.relpath(path), min_len=min_len, max_len=max_len)


def ingest_jsonl(kernel, path: str) -> Dict[str, Any]:
    """Ingere JSONL: cada linha com {text|fact, source?, confidence?, evidence?}."""
    novos = dups = linhas = 0
    confs: List[float] = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            linhas += 1
            try:
                obj = json.loads(linha)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            fato = str(obj.get('text') or obj.get('fact') or '').strip()
            if len(fato) < 10:
                continue
            src = str(obj.get('source') or 'ingest')
            conf = float(obj.get('confidence', 0.85))
            ev = str(obj.get('evidence') or os.path.relpath(path))
            n, d = _learn_batch(kernel, [fato], src, conf, ev)
            novos += n
            dups += d
            confs.append(conf)
    m = _metricas('ingest_jsonl', novos, dups, 0, linhas)
    m['avg_confidence'] = round(sum(confs) / len(confs), 3) if confs else 0.0
    m['evidence'] = os.path.relpath(path)
    return m


def fetch_wiki_summary(title: str, timeout: int = 10) -> Dict[str, Any]:
    """Busca o resumo de um verbete na Wikipedia pt (stdlib, sem dependências)."""
    url = WIKI_URL.format(title=urllib.parse.quote(title))
    req = urllib.request.Request(url, headers={'User-Agent': WIKI_UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def ingest_wiki(kernel, titles: Iterable[str], confidence: float = 0.80,
                max_sentences: int = 8, fetch: Callable[[str], Dict[str, Any]] = None,
                min_len: int = 25, max_len: int = 300) -> List[Dict[str, Any]]:
    """
    Ingere resumos da Wikipedia.

    `fetch` é injetável: os testes passam um dublê e nunca tocam a rede.
    """
    fetch = fetch or fetch_wiki_summary
    out: List[Dict[str, Any]] = []
    for titulo in titles:
        titulo = titulo.strip()
        if not titulo:
            continue
        url = WIKI_URL.format(title=urllib.parse.quote(titulo))
        try:
            dados = fetch(titulo)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as exc:
            out.append({'source': 'wikipedia', 'title': titulo, 'error': f'{type(exc).__name__}: {exc}',
                        'new': 0, 'duplicates': 0, 'facts_found': 0, 'chars': 0,
                        'avg_confidence': confidence})
            continue
        resumo = (dados or {}).get('extract') or ''
        fatos = split_facts(resumo, min_len=min_len, max_len=max_sentences and max_len or max_len)[:max_sentences]
        novos, dups = _learn_batch(kernel, fatos, 'wikipedia', confidence, evidence=url)
        m = _metricas('wikipedia', novos, dups, len(resumo), len(fatos))
        m.update({'title': titulo, 'url': url,
                  'canonical': (dados or {}).get('title', titulo)})
        out.append(m)
    return out


def _metricas(source: str, novos: int, dups: int, chars: int, facts: int) -> Dict[str, Any]:
    return {'source': source, 'new': novos, 'duplicates': dups,
            'chars': chars, 'facts_found': facts}


def iter_files(dir_: str = None, pattern: str = None,
               exts: Tuple[str, ...] = ('.txt', '.md', '.rst', '.jsonl', '.ndjson', '.csv')) -> List[str]:
    """Resolve diretório/glob em uma lista ordenada de arquivos de texto."""
    arquivos: List[str] = []
    if dir_:
        for raiz, _dirs, nomes in os.walk(dir_):
            for nome in sorted(nomes):
                if nome.lower().endswith(exts):
                    arquivos.append(os.path.join(raiz, nome))
    if pattern:
        arquivos.extend(p for p in sorted(_glob.glob(pattern, recursive=True))
                        if os.path.isfile(p))
    return sorted(set(arquivos))


def build_report(resultados: List[Dict[str, Any]], kernel, duracao: float,
                 backfilled: int = 0) -> Dict[str, Any]:
    """Consolida as métricas de ingestão + estado de proveniência do kernel."""
    novos = sum(r.get('new', 0) for r in resultados)
    dups = sum(r.get('duplicates', 0) for r in resultados)
    erros = [r for r in resultados if r.get('error')]
    try:
        prov = kernel.provenance_report()
    except Exception:
        prov = {}
    return {
        'schema': 'nexus.ingest.report/1',
        'when': time.time(),
        'duration_s': round(duracao, 2),
        'totals': {
            'new_facts': novos,
            'duplicates_skipped': dups,
            'facts_seen': novos + dups,
            'errors': len(erros),
            'sources': len({r.get('source') for r in resultados}),
            'backfilled': backfilled,
        },
        'provenance': prov,
        'results': resultados,
    }


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def _imprimir_resumo(rep: Dict[str, Any], quieto: bool = False) -> None:
    t = rep['totals']
    print('─' * 68)
    print('  INGESTÃO NEXUS V14')
    print('─' * 68)
    for r in rep['results']:
        nome = r.get('evidence') or r.get('title') or r.get('source', '?')
        if r.get('error'):
            print(f'  ✗ {nome:44s} erro: {r["error"][:60]}')
        else:
            print(f'  ✓ {str(nome):44s} novos={r.get("new", 0):4d} '
                  f'dups={r.get("duplicates", 0):4d}')
    print('─' * 68)
    print(f'  fatos novos        : {t["new_facts"]}')
    print(f'  duplicados pulados : {t["duplicates_skipped"]}')
    print(f'  backfill (legacy)  : {t["backfilled"]}')
    prov = rep.get('provenance') or {}
    if prov:
        fontes = ', '.join(f'{k}={v["facts"]}' for k, v in prov.get('sources', {}).items())
        print(f'  proveniência       : {prov.get("tracked", 0)} fatos '
              f'({prov.get("coverage", 0):.0%} de cobertura) [{fontes}]')
    print(f'  tempo              : {rep["duration_s"]}s')
    st = rep.get('state') or {}
    if st:
        marca = 'carregado' if st.get('loaded') else 'novo'
        print(f'  estado             : {st.get("path")} ({marca})'
              + (' — salvo' if st.get('saved') else ''))
    if not quieto:
        print('─' * 68)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog='nexus_ingest.py',
        description='Alimenta o kernel Nexus V14 com corpus real (com dedup e proveniência).')
    ap.add_argument('--file', action='append', default=[], help='arquivo de texto/JSONL')
    ap.add_argument('--dir', help='diretório (busca recursiva)')
    ap.add_argument('--glob', dest='glob_pat', help="padrão glob, ex: 'docs/**/*.md'")
    ap.add_argument('--wiki', action='append', default=[], help='verbete da Wikipedia pt')
    ap.add_argument('--wiki-list', help='arquivo com um verbete por linha')
    ap.add_argument('--stdin', action='store_true', help='lê o texto da entrada padrão')
    ap.add_argument('--confidence', type=float, default=None,
                    help='confiança dos fatos (padrão: 0.85 arquivos, 0.80 wiki)')
    ap.add_argument('--min-len', type=int, default=20, help='tamanho mínimo do fato')
    ap.add_argument('--max-len', type=int, default=250, help='tamanho máximo do fato')
    ap.add_argument('--max-sentences', type=int, default=8,
                    help='sentenças por verbete da Wikipedia')
    ap.add_argument('--limit', type=int, default=None, help='máximo de arquivos/verbete')
    ap.add_argument('--backfill', action='store_true',
                    help="marca fatos existentes sem origem como 'legacy'")
    ap.add_argument('--provenance-db', default='nexus_provenance.db',
                    help='arquivo de proveniência (padrão: nexus_provenance.db)')
    ap.add_argument('--state', default='nexus_state.json',
                    help='estado do kernel a carregar/salvar (padrão: nexus_state.json)')
    ap.add_argument('--no-state', action='store_true',
                    help='não carrega nem salva o estado (kernel efêmero)')
    ap.add_argument('--report', help='salva o relatório JSON no caminho dado')
    ap.add_argument('--quiet', action='store_true', help='só o relatório JSON')
    args = ap.parse_args(argv)

    from nexus_core import NexusV14Unified
    kernel = NexusV14Unified()
    if args.provenance_db:
        kernel.cognitive.set_provenance_path(args.provenance_db)

    estado_carregado = False
    if not args.no_state and args.state and os.path.exists(args.state):
        estado_carregado = kernel.load_state(args.state)

    t0 = time.time()
    resultados: List[Dict[str, Any]] = []

    conf_arq = args.confidence if args.confidence is not None else 0.85
    arquivos = list(args.file) + iter_files(args.dir, args.glob_pat)
    if args.limit:
        arquivos = arquivos[:args.limit]
    for caminho in arquivos:
        if not os.path.exists(caminho):
            resultados.append({'source': 'file', 'evidence': caminho, 'new': 0,
                               'duplicates': 0, 'facts_found': 0, 'chars': 0,
                               'error': 'arquivo não encontrado'})
            continue
        try:
            m = ingest_file(kernel, caminho, confidence=conf_arq,
                            min_len=args.min_len, max_len=args.max_len)
            m['evidence'] = os.path.relpath(caminho)
            resultados.append(m)
        except Exception as exc:                                  # pragma: no cover
            resultados.append({'source': 'file', 'evidence': caminho, 'new': 0,
                               'duplicates': 0, 'facts_found': 0, 'chars': 0,
                               'error': f'{type(exc).__name__}: {exc}'})

    if args.stdin:
        texto = sys.stdin.read()
        resultados.append(ingest_text(kernel, texto, source='ingest',
                                      confidence=conf_arq, evidence='<stdin>',
                                      min_len=args.min_len, max_len=args.max_len))

    titulos = list(args.wiki)
    if args.wiki_list and os.path.exists(args.wiki_list):
        with open(args.wiki_list, encoding='utf-8') as f:
            titulos += [l.strip() for l in f if l.strip()]
    if args.limit and titulos:
        titulos = titulos[:args.limit]
    if titulos:
        conf_wiki = args.confidence if args.confidence is not None else 0.80
        resultados += ingest_wiki(kernel, titulos, confidence=conf_wiki,
                                  max_sentences=args.max_sentences,
                                  min_len=args.min_len, max_len=args.max_len)

    backfilled = 0
    if args.backfill:
        try:
            fatos = kernel.cognitive.fact_store.all_facts() \
                if hasattr(kernel.cognitive.fact_store, 'all_facts') else []
            backfilled = kernel.cognitive.provenance.backfill(fatos)
        except Exception as exc:
            print(f'[backfill] {type(exc).__name__}: {exc}', file=sys.stderr)

    rep = build_report(resultados, kernel, time.time() - t0, backfilled=backfilled)
    rep['state'] = {'path': None if args.no_state else args.state,
                    'loaded': estado_carregado, 'saved': False}
    if not args.no_state and args.state:
        rep['state']['saved'] = bool(kernel.save_state(args.state))
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
    if args.quiet:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        _imprimir_resumo(rep)
        if args.report:
            print(f'  relatório salvo em {args.report}')
    return 0 if rep['totals']['new_facts'] or rep['totals']['duplicates_skipped'] else 1


if __name__ == '__main__':
    sys.exit(main())
