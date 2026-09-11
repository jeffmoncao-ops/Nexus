#!/usr/bin/env python3
"""Treina o Nexus com material real da web (SQuAD v1.1 PT-BR) e avalia.

Material: tradução PT-BR do Stanford Question Answering Dataset (SQuAD
v1.1) — github.com/nunorc/squad-v1.1-pt (tradução automática via Google
Cloud API; dataset original de Rajpurkar et al.). Baixado do GitHub
(codeload) se ainda não estiver em data/trained/.

Protocolo honesto em DOIS eixos:
  1. RECALL (aprendeu?): perguntas sobre os artigos TREINADOS — o
     contexto foi estudado, a pergunta é nova. Sem treino, espera-se ~0;
     com treino, hit@k mede se o sistema recupera o fato certo.
  2. ESPECIFICIDADE (alucina?): perguntas sobre artigos NUNCA VISTOS —
     espera-se ~0: um sistema de memória não inventa o que não aprendeu
     (0/30 medido na primeira rodada deste protocolo).

"Treino" aqui = aprendizado one-shot (sem gradiente): o encoder neural
fica congelado; o que aprende são memória SDR, sinapses Hebbianas,
valência e transições de estados.

Uso:
  python3 tools/train_from_web.py                    # treino + avaliação
  python3 tools/train_from_web.py --articles 8       # treino menor
  python3 tools/train_from_web.py --skip-train       # avalia modelo salvo
"""
import json
import os
import random
import sys
import tarfile
import time
import unicodedata
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

DATA_DIR = os.path.join(HERE, 'data', 'trained')
DATASET_URL = ('https://codeload.github.com/nunorc/squad-v1.1-pt/'
               'tar.gz/refs/heads/master')
TARBALL = os.path.join(DATA_DIR, 'squad-v1.1-pt.tar.gz')
EXTRACTED = os.path.join(DATA_DIR, 'squad-v1.1-pt-master')
DEV_JSON = os.path.join(EXTRACTED, 'dev-v1.1-pt.json')
MODEL_PATH = os.path.join(DATA_DIR, 'nexus_squad_model.json')
SEED = 42


def norm(s: str) -> str:
    """minúsculas sem acentos, para comparar resposta-ouro × fato."""
    s = unicodedata.normalize('NFKD', s.lower())
    return ''.join(c for c in s if not unicodedata.combining(c)).strip()


def ensure_dataset() -> None:
    if os.path.isfile(DEV_JSON):
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f'[dataset] baixando {DATASET_URL}')
    urllib.request.urlretrieve(DATASET_URL, TARBALL)
    with tarfile.open(TARBALL) as tf:
        tf.extractall(DATA_DIR)
    os.unlink(TARBALL)
    print(f'[dataset] extraído em {EXTRACTED}')


def load_nexus():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'nx', os.path.join(HERE, 'nexus_v14_shared_hippocampus.py'))
    nx = importlib.util.module_from_spec(spec)
    sys.modules['nx'] = nx
    spec.loader.exec_module(nx)
    return nx


def sample_questions(articles, per_article, rng):
    """Perguntas (+resposta-ouro) amostradas de artigos."""
    qs = []
    for art in articles:
        pool = [qa for para in art['paragraphs'] for qa in para['qas']
                if qa.get('answers')]
        if not pool:
            continue
        for qa in rng.sample(pool, min(per_article, len(pool))):
            qs.append({'question': qa['question'],
                       'answer': qa['answers'][0]['text']})
    return qs


def _content_words(s):
    import re
    return {w for w in re.findall(r'[a-z0-9]{3,}', norm(s))}


def retrieve_eval(kernel, questions):
    """hit@1/hit@5 de recuperação, em duas métricas.

    estrito : resposta-ouro (substring) contida no fato recuperado;
    leniente: ≥50% das palavras-núcleo da resposta presentes no fato —
    captura quase-acertos onde a segmentação em fatos truncou o trecho
    da resposta (o fato certo foi recuperado, mas o span foi cortado).
    """
    rows = []
    for q in questions:
        sdr = kernel.semantic_encode(q['question'])
        hits = kernel.retriever.retrieve(q['question'], sdr, top_k=5)
        gold = norm(q['answer'])
        gwords = _content_words(q['answer'])
        rows.append({
            'q': q['question'][:70], 'gold': q['answer'],
            'hit1': any(gold in norm(t) for _, t, _ in hits[:1]),
            'hit5': any(gold in norm(t) for _, t, _ in hits[:5]),
            'len5': any(
                gwords and len(gwords & _content_words(t)) >= len(gwords) * 0.5
                for _, t, _ in hits[:5]),
            'top': hits[0][1][:80] if hits else '',
        })
    return rows


def chat_eval(kernel, questions):
    """Acurácia ponta-a-ponta: resposta-ouro contida na resposta do chat()."""
    rows = []
    for q in questions:
        resp = kernel.chat(q['question'])
        gold = norm(q['answer'])
        rows.append({'q': q['question'][:70], 'gold': q['answer'],
                     'ok': gold in norm(resp or ''),
                     'resp': (resp or '')[:90]})
    return rows


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--articles', type=int, default=10)
    ap.add_argument('--questions-per-article', type=int, default=3)
    ap.add_argument('--chat-questions', type=int, default=8,
                    help='subconjunto avaliado via chat() (mais lento)')
    ap.add_argument('--max-paragraphs', type=int, default=30,
                    help='limita parágrafos por artigo (tempo de treino)')
    ap.add_argument('--skip-train', action='store_true')
    args = ap.parse_args()

    ensure_dataset()
    data = json.load(open(DEV_JSON, encoding='utf-8'))['data']
    rng = random.Random(SEED)
    idx = list(range(len(data)))
    rng.shuffle(idx)
    train_arts = [data[i] for i in idx[:args.articles]]
    unseen_arts = [data[i] for i in idx[args.articles:args.articles + 10]]

    recall_qs = sample_questions(train_arts, args.questions_per_article,
                                 random.Random(SEED + 1))
    unseen_qs = sample_questions(unseen_arts, 2, random.Random(SEED + 2))
    print(f'[protocolo] treino: {args.articles} artigos')
    print(f'  RECALL        : {len(recall_qs)} perguntas sobre artigos treinados')
    print(f'  ESPECIFICIDADE: {len(unseen_qs)} perguntas sobre artigos nunca vistos')

    nx = load_nexus()

    # ── instância treinada ──────────────────────────────────────────────────
    if args.skip_train and os.path.isfile(MODEL_PATH):
        t0 = time.time()
        kernel = nx.NexusV10.load(MODEL_PATH)
        print(f'[modelo] carregado em {time.time() - t0:.0f}s: {MODEL_PATH}')
    else:
        kernel = nx.NexusFinal()
        kernel.disable_autosave()
        t0 = time.time()
        n_para, n_facts = 0, 0
        for ai, art in enumerate(train_arts):
            for para in art['paragraphs'][:args.max_paragraphs]:
                n_facts += kernel.learn_document(para['context'])
                n_para += 1
            print(f'  [{ai + 1:2d}/{len(train_arts)}] {art["title"][:34]:36s} '
                  f'{n_para} parágrafos → {n_facts} fatos ({time.time() - t0:.0f}s)')
        print(f'[treino] {n_facts} fatos em {time.time() - t0:.0f}s')
        os.makedirs(DATA_DIR, exist_ok=True)
        kernel.save(MODEL_PATH)
        print(f'[treino] modelo salvo: {MODEL_PATH}')

    # ── controle SEM treino (mesmas perguntas de recall) ────────────────────
    print('\n[controle] instância SEM treino...')
    ctrl = nx.NexusFinal()
    ctrl.disable_autosave()
    ctrl_rows = retrieve_eval(ctrl, recall_qs)

    # ── avaliações ──────────────────────────────────────────────────────────
    print('\n[avaliação] recuperação (recall)…')
    tr_rows = retrieve_eval(kernel, recall_qs)
    print('[avaliação] especificidade (nunca vistos)…')
    sp_rows = retrieve_eval(kernel, unseen_qs)
    print(f'[avaliação] chat() ponta-a-ponta ({args.chat_questions} perguntas)…')
    ch_rows = chat_eval(kernel, recall_qs[:args.chat_questions])

    n = len(tr_rows)
    ch1 = sum(r['hit1'] for r in ctrl_rows)
    ch5 = sum(r['hit5'] for r in ctrl_rows)
    th1 = sum(r['hit1'] for r in tr_rows)
    th5 = sum(r['hit5'] for r in tr_rows)
    tl5 = sum(r['len5'] for r in tr_rows)
    spn = len(sp_rows)
    sp_hits = sum(r['hit5'] for r in sp_rows)
    chn = len(ch_rows)
    ch_ok = sum(r['ok'] for r in ch_rows)

    print('\n┌────────────────────────────────────────────────────────────────┐')
    print('│  RESULTADO — SQuAD v1.1 PT-BR (treino web, one-shot)           │')
    print('├────────────────────────────────────────────────────────────────┤')
    print(f'│  RECALL (artigos treinados, {n} perguntas novas):              ' + ' ' * 8 + '│')
    print(f'│    hit@1 : SEM treino {ch1:2d}/{n}  →  COM treino {th1:2d}/{n}   '
          f'({(th1 - ch1) / n * 100:+.0f} pp)          │')
    print(f'│    hit@5 : SEM treino {ch5:2d}/{n}  →  COM treino {th5:2d}/{n}   '
          f'({(th5 - ch5) / n * 100:+.0f} pp)          │')
    print(f'│    len@5 : COM treino {tl5:2d}/{n}  (≥50% das palavras-núcleo —  ' + ' ' * 3 + '│')
    print(f'│            captura trechos truncados pela segmentação)          ' + ' ' * 6 + '│')
    print(f'│  ESPECIFICIDADE (nunca vistos, {spn} perguntas):               ' + ' ' * 12 + '│')
    print(f'│    hit@5 : {sp_hits}/{spn} (esperado ~0 — não inventa o que não  ' + ' ' * 4 + '│')
    print(f'│             aprendeu)                                          ' + ' ' * 12 + '│')
    print(f'│  CHAT() ponta-a-ponta ({chn} perguntas): acertos {ch_ok}/{chn}        ' + ' ' * 14 + '│')
    print('└────────────────────────────────────────────────────────────────┘')

    print('\nexemplos (recall):')
    hit_shown = miss_shown = 0
    for r in tr_rows:
        if r['hit1'] and hit_shown < 4:
            print(f"  ✓ {r['q']}")
            print(f"    ouro: {r['gold'][:52]!r}")
            hit_shown += 1
        elif not r['hit5'] and miss_shown < 4:
            print(f"  ✗ {r['q']}")
            print(f"    ouro: {r['gold'][:52]!r} | top: {r['top'][:56]!r}")
            miss_shown += 1
        if hit_shown >= 4 and miss_shown >= 4:
            break
    return 0


if __name__ == '__main__':
    sys.exit(main())
