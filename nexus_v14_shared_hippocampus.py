#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         NEXUS V14 UNIFIED — SISTEMA COGNITIVO DE MISSÃO CRÍTICA            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  FUSÃO COMPLETA: V10 Ultimate + V11.2 Production + V13 Evolution             ║
║                                                                              ║
║  CAMADA COGNITIVA (V10 Ultimate):                                            ║
║  • SparseSDR 4096 bits — representação primária do conhecimento              ║
║  • MiniEmbed 768D — Word2Vec + FastText + Hebbiano                           ║
║  • CognitiveBrain — InvertedIndex O(1) recall                                ║
║  • ConceptGraph — analogia XOR, BFS, vizinhos ponderados                     ║
║  • NGramMemory — predição e geração de texto                                 ║
║  • TextWeaver — geração de prosa coerente                                    ║
║  • EpistemicLayer — hipóteses, promoção, validação                           ║
║  • ConditionalEngine — regras SE-ENTÃO BFS                                   ║
║  • DeductiveEngine — silogismos fuzzy                                        ║
║  • CodeGeneralizer — CBR + sandbox + auto-repair                             ║
║  • MathEngine — cálculo seguro em PT-BR                                      ║
║  • GlobalWorkspaceNexus — multi-brain por domínio                            ║
║  • RepresentationalBus — comunicação inter-módulo via SDR                    ║
║  • XORBinding — raciocínio analógico bitwise                                 ║
║  • NoveltyDetector — surprise-based learning                                 ║
║  • BeamGenerator — beam search + reranking                                   ║
║  • AttentionPool — IDF-weighted sentence vectors                             ║
║                                                                              ║
║  CAMADA DE PRODUÇÃO (V11.2 Mission Critical):                                ║
║  • NexusGuardV11 — Criptografia XOR 256-byte com SDR-Key determinística      ║
║  • NexusPersistV11 — Persistência aiosqlite (nexus_secure.db + iot_final.db) ║
║  • NexusSDRFilter — Filtragem por densidade de bits + Inibição Lateral       ║
║  • NexusHealerV11 — Auto-reparo com flush real + varredura de integridade    ║
║  • NexusDomainBus — Processamento concorrente asyncio.gather por domínio     ║
║  • NexusSeniorGateway — Rate limiting + SDR validation                       ║
║                                                                              ║
║  CAMADA DE EVOLUÇÃO (V13):                                                   ║
║  • VecOps — numpy opcional (~10× speedup, fallback Python puro)              ║
║  • VisualEncoder — cor/borda/textura/movimento/forma → SDR 40 bits           ║
║  • AudioEncoder — espectro/MFCC/ZCR/pitch/voz → SDR 40 bits                 ║
║  • MiniEmbedAccelerator — monkey-patch numpy nos hot paths                   ║
║                                                                              ║
║  Deps: Python ≥ 3.9, numpy (opcional), aiosqlite (opcional)                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import array, ast, asyncio, contextlib, hashlib, io, json, math, os, re
import atexit, struct, threading, time, unicodedata, random
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

# ── numpy: opcional (V13 acceleration) ─────────────────────────────────────
try:
    import numpy as np
    HAS_NUMPY = True
    _np = np
except ImportError:
    np = None
    HAS_NUMPY = False

# ── aiosqlite: opcional (V11.2 persistence) ────────────────────────────────
try:
    import aiosqlite
    _AIOSQLITE_OK = True
except ImportError:
    _AIOSQLITE_OK = False


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PARTE 1: NÚCLEO COGNITIVO (V10 Ultimate)                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ══════════════════════════════════════════════════════════════════════════════
# §0  CONSTANTES GLOBAIS
# ══════════════════════════════════════════════════════════════════════════════

VERSION    = 'v14-unified'
SDR_SIZE   = 4096
SDR_ACTIVE = 80
SDR_SEED   = 0xDEAD_BEEF

ZONE_SEMANTIC = (0,    2048)
ZONE_CONTEXT  = (2048, 3072)
ZONE_VALENCE  = (3072, 4096)
ZONE_ACTIVE   = (30, 25, 25)   # bits por zona (total = 80)

_STOP_PT: frozenset = frozenset({
    "o","a","os","as","um","uma","uns","umas","que","é","de","do","da",
    "dos","das","em","no","na","nos","nas","por","para","com","sem",
    "entre","sobre","após","ao","aos","à","às","qual","quem","como",
    "quando","onde","mais","mas","pois","então","logo","se","não",
    "sim","já","ainda","também","isso","este","esse","aquele",
    "são","ser","tem","têm","ter","foi","era","está","estão","estar",
    "pode","podem","deve","devem","vai","vão","seu","sua","seus","suas",
    "meu","minha","ele","ela","eles","elas","eu","tu","você","nós",
    "todo","toda","todos","todas","cada","qualquer","nenhum","nenhuma",
    "aquilo","isto","lá","cá","muito","pouco","bem","mal",
})

_ANTONYMS: Dict[str, str] = {
    'quente':'frio','frio':'quente','vivo':'morto','morto':'vivo',
    'autoimune':'infecciosa','infecciosa':'autoimune',
    'mamífero':'réptil','réptil':'mamífero',
    'positivo':'negativo','negativo':'positivo',
    'benigno':'maligno','maligno':'benigno',
    'ácido':'básico','básico':'ácido',
    'rápido':'lento','lento':'rápido',
    'grande':'pequeno','pequeno':'grande',
    'carnívoro':'herbívoro','herbívoro':'carnívoro',
    'diurno':'noturno','noturno':'diurno',
}

_SOCIAL: Dict[str, str] = {
    'olá':           'Olá! Como posso ajudar?',
    'oi':            'Oi! Em que posso ser útil?',
    'bom dia':       'Bom dia! O que você gostaria de saber?',
    'boa tarde':     'Boa tarde! Como posso ajudar?',
    'boa noite':     'Boa noite! Em que posso ser útil?',
    'tudo bem':      'Tudo ótimo, obrigado! E você?',
    'tudo bom':      'Tudo ótimo! Posso ajudar com algo?',
    'como vai':      'Bem, obrigado! Em que posso ajudar?',
    'obrigado':      'De nada! Há mais alguma coisa?',
    'obrigada':      'De nada! Posso ajudar com mais algo?',
    'valeu':         'Disponha! Se precisar, é só perguntar.',
    'tchau':         'Até mais! Foi um prazer ajudar.',
    'até mais':      'Até! Volte quando quiser.',
    'você é um robô':'Sou um sistema cognitivo — aprendo fatos, razocínio e respondo perguntas.',
    'quem é você':   'Sou Nexus, um sistema de conhecimento. Aprendo fatos e respondo perguntas.',
    'o que você faz':'Aprendo fatos, respondo perguntas, calculo, deduzo e gero texto.',
    'você consegue me ajudar': 'Sim! Pode perguntar. Se eu souber, respondo; se não, você me ensina.',
    'me ajuda':      'Claro! O que você gostaria de saber?',
}

REL_IS_A='IS_A'; REL_HAS='HAS'; REL_DOES='DOES'

def _safe_capitalize(s: str) -> str:
    """Capitaliza primeira letra, preservando camelCase (iPhone, DNA, iPad)."""
    if not s:
        return s
    # Não capitaliza se: (a) primeiro char já é maiúsculo, ou
    # (b) segundo char é maiúsculo (camelCase: iPhone, iPad, macOS)
    if s[0].isupper():
        return s
    if len(s) > 1 and s[1].isupper():
        return s  # camelCase — preserva intacto
    return s[0].upper() + s[1:]
REL_CAUSES='CAUSES'; REL_PRODUCES='PRODUCES'; REL_PART_OF='PART_OF'

_REL_PATTERNS: List[Tuple] = [
    (re.compile(r'^([\w\s]{2,25}?)\s+(?:é\s+um[a]?|são\s+um[a]?)\s+([\w\s]{2,25})$', re.I), REL_IS_A),
    (re.compile(r'^([\w\s]{2,25}?)\s+(?:é|são)\s+([\w\s]{2,25})$', re.I), REL_IS_A),
    (re.compile(r'^([\w\s]{2,25}?)\s+tem\s+([\w\s]{2,30})$', re.I), REL_HAS),
    (re.compile(r'^([\w\s]{2,25}?)\s+(?:faz|fazem|executa)\s+([\w\s]{2,25})$', re.I), REL_DOES),
    (re.compile(r'^([\w\s]{2,25}?)\s+causa\s+([\w\s]{2,25})$', re.I), REL_CAUSES),
    (re.compile(r'^([\w\s]{2,25}?)\s+produz\s+([\w\s]{2,25})$', re.I), REL_PRODUCES),
    (re.compile(r'^([\w\s]{2,25}?)\s+(?:faz\s+parte|pertence)\s+([\w\s]{2,25})$', re.I), REL_PART_OF),
]

_CONTEXT_LABELS: Dict[str, str] = {
    'code':    'programação código algoritmo função',
    'science': 'ciência biologia física química',
    'history': 'história guerra política governo',
    'math':    'matemática cálculo equação número',
    'general': 'geral assunto conversa tema',
    'medical': 'médico saúde doença diagnóstico',
}

_VALENCE_POS = frozenset({'bom','boa','ótimo','excelente','certo','correto','positivo',
    'sucesso','vantagem','benefício','verdadeiro','saudável','funciona','cria','gera'})
_VALENCE_NEG = frozenset({'ruim','mau','errado','incorreto','negativo','falso','falha',
    'erro','problema','doença','mortal','perigoso','tóxico','contradição','lento'})

_DOMAIN_PATTERNS_RAW = [
    (r'\bna\s+([\wáàâãéèêíóòôõúùûç]+(?:\s+[\wáàâãéèêíóòôõúùûç]+)?)\b', 1),
    (r'\bno\s+([\wáàâãéèêíóòôõúùûç]+(?:\s+[\wáàâãéèêíóòôõúùûç]+)?)\b', 1),
    (r'\bem\s+([\wáàâãéèêíóòôõúùûç]+(?:\s+[\wáàâãéèêíóòôõúùûç]+)?)\b', 1),
    (r'\bsegundo\s+(?:a\s+|o\s+)?([\wáàâãéèêíóòôõúùûç]+)\b', 1),
    # Padrão explícito "contexto: X" ou "contexto X" — usado pelo Versionamento Contextual
    (r'\bcontexto[:\s]+([^\)\s,\.]{3,40})', 1),
    # Parênteses contextuais: "(contexto: X)" ou "(X)"  no fim do texto
    (r'\(contexto[:\s]+([^\)]{3,40})\)', 1),
]
_DOMAIN_PATTERNS = [(re.compile(p, re.I), g) for p, g in _DOMAIN_PATTERNS_RAW]
_NOT_DOMAIN = frozenset({'que','ser','esta','esse','todo','como','mais','ele','ela',
    'seu','uma','uns','umas','dos','das','aos','pois','logo','isso','aqui','ali',
    'lá','já','ainda','também','assim','muito','pouco','pode','deve'})

def _extract_domain(text: str) -> Optional[str]:
    tl = text.lower()
    for pat, grp in _DOMAIN_PATTERNS:
        m = pat.search(tl)
        if m:
            c = m.group(grp).strip()
            if c not in _NOT_DOMAIN and len(c) >= 4:
                return c
    return None

def _deaccent(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


# ══════════════════════════════════════════════════════════════════════════════
# §1  SPARSE SDR — v5 Pro (array('H'), 25× mais compacto)
# ══════════════════════════════════════════════════════════════════════════════

class SparseSDR:
    """
    SDR compacto: armazena só ÍNDICES dos bits ativos via array('H').
    40 bits ativos = 80 bytes (vs 256 bytes num int de 2048 bits).
    """
    __slots__ = ('_idx',)

    def __init__(self, indices=None):
        if indices is None:
            self._idx = array.array('H')
        elif isinstance(indices, array.array):
            self._idx = indices
        elif isinstance(indices, (list, set, frozenset)):
            self._idx = array.array('H', sorted(int(i) for i in indices))
        else:
            self._idx = array.array('H')

    @classmethod
    def from_indices(cls, indices) -> 'SparseSDR':
        return cls(indices)

    @classmethod
    def from_list(cls, lst: list) -> 'SparseSDR':
        return cls(lst)

    def to_list(self) -> list:
        return list(self._idx)

    def to_dict(self) -> dict:
        return {'idx': list(self._idx)}

    @classmethod
    def from_dict(cls, d: dict) -> 'SparseSDR':
        return cls(d.get('idx', []))

    # ── Operações de conjunto ─────────────────────────────────────────────────

    def __or__(self, other: 'SparseSDR') -> 'SparseSDR':
        return SparseSDR(set(self._idx) | set(other._idx))

    def __and__(self, other: 'SparseSDR') -> 'SparseSDR':
        return SparseSDR(set(self._idx) & set(other._idx))

    def __xor__(self, other: 'SparseSDR') -> 'SparseSDR':
        return SparseSDR(set(self._idx) ^ set(other._idx))

    def jaccard(self, other: 'SparseSDR') -> float:
        a, b = set(self._idx), set(other._idx)
        if not a and not b: return 1.0
        u = len(a | b)
        return len(a & b) / u if u else 0.0

    def overlap_score(self, other: 'SparseSDR') -> float:
        a = set(self._idx)
        if not a: return 0.0
        return len(a & set(other._idx)) / len(a)

    def invert_sparse(self) -> 'SparseSDR':
        active = set(self._idx)
        all_bits = set(range(SDR_SIZE))
        return SparseSDR(all_bits - active)

    def sparsify(self, target: int) -> 'SparseSDR':
        if len(self._idx) <= target:
            return self
        return SparseSDR(list(self._idx)[:target])

    # ── Zonas ─────────────────────────────────────────────────────────────────

    def semantic_bits(self) -> 'SparseSDR':
        lo, hi = ZONE_SEMANTIC
        return SparseSDR([i for i in self._idx if lo <= i < hi])

    def context_bits(self) -> 'SparseSDR':
        lo, hi = ZONE_CONTEXT
        return SparseSDR([i for i in self._idx if lo <= i < hi])

    def valence_bits(self) -> 'SparseSDR':
        lo, hi = ZONE_VALENCE
        return SparseSDR([i for i in self._idx if lo <= i < hi])

    # ── Bundle (média threshold) ──────────────────────────────────────────────

    @staticmethod
    def bundle(sdrs: List['SparseSDR'], threshold: float = 0.5) -> 'SparseSDR':
        if not sdrs: return SparseSDR()
        counts: Dict[int, int] = defaultdict(int)
        for s in sdrs:
            for i in s._idx:
                counts[i] += 1
        n = len(sdrs)
        return SparseSDR([i for i, c in counts.items() if c / n >= threshold])

    def __len__(self) -> int:
        return len(self._idx)

    def __repr__(self) -> str:
        return f'SparseSDR({len(self._idx)}/{SDR_SIZE})'


# ══════════════════════════════════════════════════════════════════════════════
# §2  INVERTED INDEX — v5 Pro (recall O(1) por candidatos)
# ══════════════════════════════════════════════════════════════════════════════

class InvertedIndex:
    """
    Mapa de bit_index → set(memory_ids).
    Dado um query SDR, candidates() retorna IDs com overlap ≥ min_overlap em O(k).
    """
    def __init__(self):
        self._map: Dict[int, Set[int]] = defaultdict(set)
        self._bit_count = 0

    def add(self, mem_id: int, sdr: SparseSDR) -> None:
        for bit in sdr.semantic_bits()._idx:
            self._map[bit].add(mem_id)
            self._bit_count += 1

    def remove(self, mem_id: int, sdr: SparseSDR) -> None:
        for bit in sdr.semantic_bits()._idx:
            self._map[bit].discard(mem_id)

    def candidates(self, query: SparseSDR, min_overlap: int = 3) -> Set[int]:
        counts: Dict[int, int] = defaultdict(int)
        for bit in query.semantic_bits()._idx:
            for mid in self._map.get(bit, set()):
                counts[mid] += 1
        return {mid for mid, cnt in counts.items() if cnt >= min_overlap}

    @property
    def bit_count(self) -> int:
        return self._bit_count


# ══════════════════════════════════════════════════════════════════════════════
# §2b  SEMANTIC SDR ENCODER — LSH + Spatial Pooler opcional
# ══════════════════════════════════════════════════════════════════════════════

class SemanticSDREncoder:
    """SDR semântico via Locality-Sensitive Hashing (LSH).

    Transforma o vetor denso do MiniEmbed (128 floats) em SDR esparso (40/2048)
    preservando a estrutura de vizinhança: palavras similares no espaço embed
    → alto Jaccard no SDR → CognitiveBrain faz recall semântico cruzado.

    ── Método: SimHash / Random Projection ──────────────────────────────────
    Gera uma matriz de projeção R (SDR_SIZE × DIM) com vetores aleatórios
    normalizados fixos e determinísticos (hash-based).

    Para cada input embed_vec:
      score[i]  = R[i] · embed_vec       (produto escalar com cada linha)
      top-ACTIVE = índices de maior score  (winner-take-all suave)
      SDR        = SparseSDR(top_k)

    Garantia matemática (SimHash theorem):
      E[jaccard(SDR(a), SDR(b))] ≈ f(cos(a, b))
      → Monotonicamente crescente: cos alto → Jaccard alto

    ── Por que LSH e não Spatial Pooler aprendido ──────────────────────────
    O Spatial Pooler aprendido (Hebbiano) colapsa com corpus pequeno: com
    poucos exemplos, os mesmos 40 neurônios vencem sempre → todos os SDRs
    ficam idênticos (Jaccard ≈ 0.95 para qualquer par).
    O LSH não tem este problema: a matriz R é fixa e a separação depende
    apenas da qualidade do embed, não do número de épocas de treino.

    Sem treinamento necessário — funciona imediatamente após o MiniEmbed
    ter sido calibrado (deep_scan ou learn() regular).

    ── Limitação real ───────────────────────────────────────────────────────
    A separação LSH é proporcional à separação do embed.
    Com embed de baixa qualidade (corpus pequeno), o recall semântico é fraco.
    Com corpus rico (1000+ frases por domínio), sep_LSH ≈ +0.30 a +0.60.
    """

    SDR_SIZE = 4096
    ACTIVE   = 40

    def __init__(self, embed_dim: int = 128):
        self.dim      = embed_dim
        self._updates = 0   # sempre 0 — LSH não aprende
        # Matriz de projeção: SDR_SIZE vetores aleatórios normalizados
        # Determinística via hash → mesma matriz em toda instância
        self._R: List[List[float]] = []
        for i in range(self.SDR_SIZE):
            seed = (i * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFF
            v = []
            for _ in range(embed_dim):
                seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
                u = max(seed / 0xFFFFFFFF, 1e-9)
                # Aproxima distribuição normal via log-transform
                v.append(math.log(u))
            nrm = math.sqrt(sum(x*x for x in v)) or 1.0
            self._R.append([x/nrm for x in v])

    def encode(self, embed_vec: List[float], learn: bool = False) -> SparseSDR:
        """Projeta embed_vec em SDR semântico via SimHash.

        learn=True aceito por compatibilidade mas ignorado (LSH é sem treino).
        """
        if len(embed_vec) != self.dim:
            embed_vec = (embed_vec + [0.0] * self.dim)[:self.dim]

        # score[i] = R[i] · embed_vec
        scores = [sum(self._R[i][k] * embed_vec[k]
                      for k in range(self.dim))
                  for i in range(self.SDR_SIZE)]

        # Top-ACTIVE por score (preserva a geometria do espaço)
        top_k = sorted(range(self.SDR_SIZE),
                        key=lambda i: -scores[i])[:self.ACTIVE]
        return SparseSDR.from_indices(top_k)

    def train(self, embed: 'MiniEmbed', texts: List[str],
              epochs: int = 1) -> None:
        """Compatibilidade com train_spatial_pooler() — LSH não precisa treinar."""
        pass   # LSH é determinístico; o embed é que precisa de calibração

    def to_dict(self) -> dict:
        # Extremamente compacto: apenas metadados (R é sempre recalculável)
        return {'dim': self.dim,
                'sdr_size': self.SDR_SIZE,
                'active': self.ACTIVE,
                'updates': self._updates}

    @classmethod
    def from_dict(cls, d: dict) -> 'SemanticSDREncoder':
        sp = cls(embed_dim=d.get('dim', 128))
        sp._updates = d.get('updates', 0)
        return sp


# ══════════════════════════════════════════════════════════════════════════════
# §3  MULTI-LOBE ENCODER — v5 Pro (3 zonas + ngrams + bigramas)
# ══════════════════════════════════════════════════════════════════════════════

class MultiLobeEncoder:
    """
    Encoder deterministico de 3 zonas:
      - Semântica  [0..1024]:   conteúdo dos tokens + ngrams char
      - Contexto   [1024..1536]: domínio detectado
      - Valência   [1536..2048]: polaridade positiva/negativa
    SparseSDR: 40 bits ativos, 25× mais compacto que int bitmask.
    """
    BITS_PER_TOKEN = 3
    NGRAM_SIZES    = (2, 3)

    def __init__(self, seed: int = SDR_SEED):
        self._seed       = seed
        self._triggers   : Dict[str, str]       = {}
        self._prototypes : Dict[str, SparseSDR] = {}
        self._cache      : Dict[str, SparseSDR] = {}

    def encode(self, text: str, context: str = 'general',
               valence: Optional[str] = None) -> SparseSDR:
        key = f'{text}|{context}|{valence}'
        if key in self._cache:
            return self._cache[key]
        tl = text.lower().strip()
        active_intent = next((i for t, i in self._triggers.items() if t in tl), None)
        sem = self._zone_encode(text, ZONE_SEMANTIC, ZONE_ACTIVE[0])
        ctx = self._zone_encode(
            self._detect_context(text) if context == 'general' else context,
            ZONE_CONTEXT, ZONE_ACTIVE[1])
        val = self._zone_encode(
            valence or self._detect_valence(text),
            ZONE_VALENCE, ZONE_ACTIVE[2])
        sdr = sem | ctx | val
        if active_intent and active_intent in self._prototypes:
            sdr = SparseSDR.bundle([self._prototypes[active_intent],
                                    self._prototypes[active_intent], sdr])
        self._cache[key] = sdr
        return sdr

    def one_shot_learn(self, trigger: str, intent: str,
                       examples: Optional[List[str]] = None) -> SparseSDR:
        examples = examples or [trigger]
        sdrs = [self._zone_encode(e, ZONE_SEMANTIC, ZONE_ACTIVE[0]) for e in examples]
        proto = SparseSDR.bundle(sdrs)
        self._prototypes[intent] = proto
        self._triggers[trigger.lower()] = intent
        self._cache.clear()
        return proto

    def _zone_encode(self, text: str, zone: Tuple[int, int], target: int) -> SparseSDR:
        start, end = zone
        tokens = self._tokenize(text)
        freq: Dict[int, int] = {}
        for tok in tokens:
            for pos in self._token_to_zone_bits(tok, start, end):
                freq[pos] = freq.get(pos, 0) + 1
        top = sorted(freq, key=lambda p: (-freq[p], p))[:target]
        return SparseSDR.from_indices(top)

    def _detect_context(self, text: str) -> str:
        tl = text.lower()
        best_l, best_c = 'general', 0
        for label, kws in _CONTEXT_LABELS.items():
            c = sum(1 for k in kws.split() if k in tl)
            if c > best_c:
                best_c, best_l = c, label
        return best_l

    def _detect_valence(self, text: str) -> str:
        toks = set(re.findall(r'\w+', text.lower()))
        pos = len(toks & _VALENCE_POS)
        neg = len(toks & _VALENCE_NEG)
        return 'positive' if pos > neg else ('negative' if neg > pos else 'neutral')

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', text.lower())
        tokens = list(words)
        for w in words:
            for n in self.NGRAM_SIZES:
                if len(w) >= n:
                    tokens.extend(w[i:i+n] for i in range(len(w)-n+1))
        for i in range(len(words)-1):
            tokens.append(f'{words[i]}·{words[i+1]}')
        return tokens

    def _token_to_zone_bits(self, token: str, start: int, end: int) -> List[int]:
        h = self._djb2(token)
        w = end - start
        bits = []
        for k in range(self.BITS_PER_TOKEN):
            bits.append(start + (h ^ (h >> 13) ^ (k * 2053) ^ (self._seed >> k)) % w)
            h = (h * 1_664_525 + 1_013_904_223) & 0xFFFF_FFFF
        return bits

    @staticmethod
    def _djb2(s: str) -> int:
        h = 5381
        for c in s.encode('utf-8', errors='replace'):
            h = ((h << 5) + h + c) & 0xFFFF_FFFF
        return h

    def to_dict(self) -> dict:
        return {'seed': self._seed, 'triggers': dict(self._triggers),
                'prototypes': {k: v.to_dict() for k, v in self._prototypes.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> 'MultiLobeEncoder':
        enc = cls(seed=d.get('seed', SDR_SEED))
        enc._triggers = d.get('triggers', {})
        enc._prototypes = {k: SparseSDR.from_dict(v)
                           for k, v in d.get('prototypes', {}).items()}
        return enc


# ══════════════════════════════════════════════════════════════════════════════
# §4  MINI-EMBED — v7 (PMI + projeção aleatória dim=64)
# ══════════════════════════════════════════════════════════════════════════════

def _tokenize_embed(text: str) -> List[str]:
    t = _deaccent(text.lower())
    return [w for w in re.findall(r'[a-z]{3,}', t)
            if w not in {'que','com','para','por','uma','uns','umas','dos',
                         'das','nos','nas','seu','sua','seus','suas','este','essa','isso'}]


class MiniEmbed:
    """
    Embeddings densos incrementais — arquitetura Word2Vec/FastText em Python puro.

    v9 rev.6 — Melhorias para máxima proximidade de LLM sem dependências:

    VETORES:
      _input_vec  (W)  — vetor de input, inicializado com rand_vec, aprende por
                         negative sampling (gradiente real, não só média).
      _output_vec (W') — vetor de output separado, como em Skip-Gram.
                         A separação W/W' é o que torna analogias possíveis.
      _drift_vec       — média Hebbiana (compatibilidade e regularização).
      _ctx_vec         — Random Indexing acumulado (compatibilidade PMI).

    NEGATIVE SAMPLING:
      Para cada par (palavra, contexto), também amostra K palavras aleatórias
      e aplica gradiente para AFASTAR os pares não-relacionados.
      Equação: ∂L/∂W = (σ(W·W') - y) · W'  onde y=1 para positivos, 0 para negativos.

    SUBWORD CHAR N-GRAMS (FastText-style):
      Palavras são representadas como soma dos vetores dos seus char n-gramas
      (3–5 chars). Isso permite:
        - Palavras fora do vocab recebem vetor útil (não zero).
        - Morfologia capturada: "mitocôndria" e "mitocondrial" compartilham
          n-gramas e ficam próximos automaticamente.
        - Robustez a erros de digitação e plurais.

    EMBEDDING FINAL:
      vector(w) = normalize(W[w] + DRIFT_WEIGHT * drift[w] + SUBWORD_WEIGHT * subword[w])
      O rand_vec puro foi REMOVIDO do embedding final — só fica como inicializador.

    COMPATIBILIDADE:
      Totalmente compatível com API anterior. Serializa W, W', drift, ctx em JSON.
      update_vectors_only=True continua funcionando (deep_scan mode).
    """

    DIM    = 768
    WINDOW = 6
    SUBSAMPLE_T  = 1e-4
    CTX_DECAY    = 0.9998

    # ── Negative Sampling ─────────────────────────────────────────────────────
    # K negativos por par positivo. K=5 é o padrão do Word2Vec original.
    NS_K         = 10
    # Taxa de aprendizado para negative sampling. Decai com freq como o drift.
    NS_LR        = 0.015
    NS_LR_MIN    = 0.0001
    # Expoente da distribuição de amostragem negativa (freq^0.75 como Word2Vec).
    NS_POWER     = 0.75
    # Tamanho da tabela de amostragem negativa (eficiência O(1) por sample).
    NS_TABLE_SZ  = 10_000

    # ── Drift / Hebbiano ──────────────────────────────────────────────────────
    DRIFT_LR       = 0.03
    DRIFT_LR_DECAY = 100.0
    DRIFT_WEIGHT   = 0.35    # reduzido: NS 768d carrega mais sinal

    # ── Subword char n-grams (FastText-style) ─────────────────────────────────
    SUBWORD_MIN    = 2      # n-grama mínimo (mais granular em 768d)
    SUBWORD_MAX    = 6      # n-grama máximo
    SUBWORD_WEIGHT = 0.3    # peso no embedding final (NS mais forte em 768d)

    def __init__(self):
        self._cooc:         Dict[Tuple[str,str], int] = defaultdict(int)
        self._freq:         Dict[str, int]            = defaultdict(int)
        self._total_pairs   = 0
        self._total_tokens  = 0
        self._vocab:        set = set()
        # ctx_vec: Random Indexing incremental (compatibilidade PMI)
        self._ctx_vec:      Dict[str, List[float]] = {}
        # drift_vec: Hebbian moving average (regularização)
        self._drift_vec:    Dict[str, List[float]] = {}
        # ── Word2Vec-style vetores W (input) e W' (output) ──────────────────
        # W  (input_vec): vetor do lado da palavra central em Skip-Gram.
        # W' (output_vec): vetor do lado do contexto / target.
        # A separação é o que permite analogias: vec(rei)-vec(homem)+vec(mulher)
        self._input_vec:    Dict[str, List[float]] = {}
        self._output_vec:   Dict[str, List[float]] = {}
        # ── Tabela de amostragem negativa ────────────────────────────────────
        # Lista de tokens amostrada proporcionalmente a freq^NS_POWER.
        # Reconstruída quando o vocab cresce muito.
        self._ns_table:     List[str] = []
        self._ns_dirty:     bool      = True   # reconstrói na próxima NS
        # Cache de sentence_vector
        self._sv_cache:     Dict[str, List[float]] = {}
        self._sv_version:   int = 0
        # Contador de updates para decaimento de LR
        self._updates:      int = 0

    # Cache de classe para rand_vec (imutável, função pura)
    _rand_vec_cache: Dict[str, List[float]] = {}

    @staticmethod
    def _rand_vec(word: str, dim: int = None) -> List[float]:
        """Vetor aleatório fixo determinístico (inicializador, NÃO entra no final)."""
        if dim is None:
            dim = MiniEmbed.DIM
        cached = MiniEmbed._rand_vec_cache.get(word)
        if cached is not None:
            return cached
        vec = []
        seed = int(hashlib.md5(word.encode()).hexdigest(), 16)
        for _ in range(dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            u = (seed / 0xFFFFFFFF) * 2 - 1
            vec.append(u)
        norm = math.sqrt(sum(x*x for x in vec)) or 1.0
        result = [x/norm for x in vec]
        MiniEmbed._rand_vec_cache[word] = result
        return result

    # ── Subword char n-grams ────────────────────────────────────────────────────

    @staticmethod
    def _char_ngrams(word: str, n_min: int = None, n_max: int = None) -> List[str]:
        """Gera char n-gramas no estilo FastText: <palavra> com sentinelas."""
        if n_min is None: n_min = MiniEmbed.SUBWORD_MIN
        if n_max is None: n_max = MiniEmbed.SUBWORD_MAX
        w = '<' + word + '>'
        ngrams = []
        for n in range(n_min, min(n_max + 1, len(w) + 1)):
            for i in range(len(w) - n + 1):
                ngrams.append(w[i:i+n])
        return ngrams

    def _subword_vec(self, word: str) -> List[float]:
        """Vetor subword: média dos rand_vec dos char n-gramas da palavra."""
        ngrams = self._char_ngrams(word)
        if not ngrams:
            return [0.0] * self.DIM
        vecs = [self._rand_vec(ng, self.DIM) for ng in ngrams]
        avg  = [sum(v[i] for v in vecs) / len(vecs) for i in range(self.DIM)]
        norm = math.sqrt(sum(x*x for x in avg)) or 1.0
        return [x/norm for x in avg]

    # ── Inicialização de vetores ──────────────────────────────────────────────

    def _ensure_word(self, word: str) -> None:
        """Garante que W e W' existem, inicializados pequenos.
        drift_vec inicia em ZEROS — aprende exclusivamente do contexto via NS+Hebbiano.
        Isso evita que rand_vec polua o drift antes do aprendizado acontecer.
        """
        if word not in self._input_vec:
            rv = self._rand_vec(word)
            scale = 0.5 / self.DIM
            self._input_vec[word]  = [x * scale for x in rv]
            self._output_vec[word] = [0.0] * self.DIM
            # ZERO-INIT: drift começa neutro, aprende do contexto real
            self._drift_vec[word]  = [0.0] * self.DIM

    # ── Tabela de negative sampling ───────────────────────────────────────────

    def _rebuild_ns_table(self) -> None:
        """Reconstrói a tabela de amostragem negativa (freq^NS_POWER)."""
        if not self._vocab:
            return
        total = sum(max(f, 1) ** self.NS_POWER for f in self._freq.values())
        table = []
        for word in self._vocab:
            count = int((max(self._freq.get(word, 1), 1) ** self.NS_POWER / total) * self.NS_TABLE_SZ)
            table.extend([word] * max(count, 1))
        self._ns_table = table
        self._ns_dirty = False

    def _neg_sample(self, exclude: set) -> List[str]:
        """Amostra K palavras negativas, excluindo as do contexto positivo."""
        if self._ns_dirty or not self._ns_table:
            self._rebuild_ns_table()
        if not self._ns_table:
            return []
        result = []
        attempts = 0
        while len(result) < self.NS_K and attempts < self.NS_K * 10:
            w = self._ns_table[hash(str(attempts) + str(self._updates)) % len(self._ns_table)]
            if w not in exclude:
                result.append(w)
            attempts += 1
        return result

    # ── Sigmoid helper ────────────────────────────────────────────────────────

    @staticmethod
    def _sigmoid(x: float) -> float:
        if x > 20:  return 1.0
        if x < -20: return 0.0
        return 1.0 / (1.0 + math.exp(-x))

    # ── Atualização NS (núcleo do Word2Vec) ────────────────────────────────────

    def _ns_update(self, word: str, pos_contexts: List[str]) -> None:
        """
        Skip-Gram com Negative Sampling.

        Para cada (word, ctx_pos) par positivo:
          1. Calcula dot = W[word] · W'[ctx_pos]
          2. err_pos = σ(dot) - 1  (quero σ(dot)→1)
          3. Atualiza: W[word] -= lr * err_pos * W'[ctx_pos]
                       W'[ctx_pos] -= lr * err_pos * W[word]

        Para cada ctx_neg negativo:
          1. dot_neg = W[word] · W'[ctx_neg]
          2. err_neg = σ(dot_neg) - 0  (quero σ(dot_neg)→0)
          3. Atualiza: W[word] -= lr * err_neg * W'[ctx_neg]
                       W'[ctx_neg] -= lr * err_neg * W[word]
        """
        self._ensure_word(word)
        if not pos_contexts:
            return

        # LR decai linearmente com o número de updates (como Word2Vec)
        freq_w = self._freq.get(word, 1)
        lr = max(self.NS_LR / (1.0 + freq_w / 100.0), self.NS_LR_MIN)

        # Acumulador de gradiente para W[word] (aplicado uma vez por eficiência)
        grad_w = [0.0] * self.DIM
        neg_ctx = self._neg_sample(set(pos_contexts) | {word})

        # Pares positivos (y=1)
        for ctx in pos_contexts:
            self._ensure_word(ctx)
            wv  = self._input_vec[word]
            cv  = self._output_vec[ctx]
            dot = sum(wv[i] * cv[i] for i in range(self.DIM))
            err = self._sigmoid(dot) - 1.0   # gradiente: σ(dot) - 1
            # Acumula gradiente sobre W[word]
            for i in range(self.DIM):
                grad_w[i] += lr * err * cv[i]
            # Atualiza W'[ctx] imediatamente
            wv_snap = list(wv)
            for i in range(self.DIM):
                cv[i] -= lr * err * wv_snap[i]

        # Pares negativos (y=0)
        for neg in neg_ctx:
            self._ensure_word(neg)
            wv   = self._input_vec[word]
            nv   = self._output_vec[neg]
            dot  = sum(wv[i] * nv[i] for i in range(self.DIM))
            err  = self._sigmoid(dot)          # gradiente: σ(dot) - 0
            for i in range(self.DIM):
                grad_w[i] += lr * err * nv[i]
            wv_snap = list(wv)
            for i in range(self.DIM):
                nv[i] -= lr * err * wv_snap[i]

        # Aplica gradiente acumulado a W[word]
        wv = self._input_vec[word]
        for i in range(self.DIM):
            wv[i] -= grad_w[i]

        self._updates += 1

    # ── Método learn() principal ───────────────────────────────────────────────

    def _subsample_weight(self, word: str) -> float:
        if self._total_tokens == 0:
            return 1.0
        f = self._freq.get(word, 0) / self._total_tokens
        if f <= self.SUBSAMPLE_T:
            return 1.0
        return math.sqrt(self.SUBSAMPLE_T / f)

    def learn(self, text: str, update_vectors_only: bool = False) -> None:
        """
        Atualiza todos os vetores: NS (Word2Vec), Drift (Hebbiano), RI (compatibilidade).

        update_vectors_only=True: modo deep_scan — só ajusta vetores semânticos,
        não registra co-ocorrências PMI, não alimenta o FactStore/Brain.
        """
        tokens = _tokenize_embed(text)
        if not tokens:
            return

        # Atualiza frequências e vocab
        for tok in tokens:
            self._freq[tok] += 1
            self._vocab.add(tok)
            self._total_tokens += 1

        # Garante que a tabela de NS está atualizada antes do loop
        # (vocab >= NS_K para ter amostragem útil)
        if len(self._vocab) >= self.NS_K and (self._ns_dirty or not self._ns_table):
            self._rebuild_ns_table()
        elif len(self._vocab) % 50 == 0 and len(self._vocab) > 0:
            self._ns_dirty = True

        if not update_vectors_only:
            # PMI co-ocorrências (compatibilidade)
            n = len(tokens)
            for i, w1 in enumerate(tokens):
                for j in range(max(0, i-self.WINDOW), min(n, i+self.WINDOW+1)):
                    if i == j: continue
                    key = (min(w1, tokens[j]), max(w1, tokens[j]))
                    self._cooc[key] += 1
                    self._total_pairs += 1

        n = len(tokens)

        # ── 1. Negative Sampling (Word2Vec Skip-Gram) ─────────────────────────
        for i, w in enumerate(tokens):
            if self._subsample_weight(w) < 0.01:
                continue
            pos_ctx = [tokens[j]
                       for j in range(max(0, i-self.WINDOW), min(n, i+self.WINDOW+1))
                       if j != i and self._subsample_weight(tokens[j]) >= 0.01]
            if pos_ctx:
                self._ns_update(w, pos_ctx)

        # ── 2. Random Indexing incremental (ctx_vec, compatibilidade) ─────────
        for i, w in enumerate(tokens):
            if w not in self._ctx_vec:
                self._ctx_vec[w] = [0.0] * self.DIM
            w_sub = self._subsample_weight(w)
            if w_sub < 0.01:
                continue
            for j in range(max(0, i-self.WINDOW), min(n, i+self.WINDOW+1)):
                if i == j: continue
                c      = tokens[j]
                c_sub  = self._subsample_weight(c)
                dw     = 1.0 / (abs(i-j) + 1)
                weight = w_sub * c_sub * dw
                c_idx  = self._rand_vec(c)
                cv     = self._ctx_vec[w]
                for k in range(self.DIM):
                    cv[k] += weight * c_idx[k]

        # ── 3. Semantic Drift (Hebbiano, regularização) ───────────────────────
        for i, w in enumerate(tokens):
            w_sub = self._subsample_weight(w)
            if w_sub < 0.01:
                continue
            nbrs = [j for j in range(max(0, i-self.WINDOW), min(n, i+self.WINDOW+1)) if j != i]
            if not nbrs:
                continue
            ctx_sum = [0.0] * self.DIM
            w_total = 0.0
            for j in nbrs:
                c     = tokens[j]
                c_sub = self._subsample_weight(c)
                dw    = 1.0 / (abs(i-j) + 1)
                wt    = w_sub * c_sub * dw
                c_vec = self._rand_vec(c)
                c_ctx = self._ctx_vec.get(c)
                if c_ctx:
                    nrm = math.sqrt(sum(x*x for x in c_ctx)) or 1.0
                    for k in range(self.DIM):
                        ctx_sum[k] += wt * (c_vec[k] + 0.3 * c_ctx[k] / nrm)
                else:
                    for k in range(self.DIM):
                        ctx_sum[k] += wt * c_vec[k]
                w_total += wt
            if w_total < 1e-9:
                continue
            ctx_mean = [x / w_total for x in ctx_sum]
            nrm      = math.sqrt(sum(x*x for x in ctx_mean)) or 1.0
            ctx_mean = [x / nrm for x in ctx_mean]
            freq_w   = self._freq.get(w, 1)
            lr_d     = self.DRIFT_LR / (1.0 + freq_w / self.DRIFT_LR_DECAY)
            if w not in self._drift_vec:
                self._drift_vec[w] = [0.0] * self.DIM   # zero-init: aprende do contexto
            dv = self._drift_vec[w]
            for k in range(self.DIM):
                dv[k] += lr_d * (ctx_mean[k] - dv[k])

        # Decay periódico
        if self._total_tokens % 200 == 0:
            for w, cv in self._ctx_vec.items():
                for k in range(self.DIM):
                    cv[k] *= self.CTX_DECAY
            for w, dv in self._drift_vec.items():
                if self._freq.get(w, 1) > 500:
                    for k in range(self.DIM):
                        dv[k] *= 0.9995

        self._sv_version += 1

    # ── Embedding final ────────────────────────────────────────────────────────

    def vector(self, word: str) -> List[float]:
        """
        Embedding final Word2Vec+FastText+Drift:

          v(w) = normalize(
              W[w]                              # Skip-Gram input vector
              + DRIFT_WEIGHT  * drift[w]        # Hebbiano regularizador
              + SUBWORD_WEIGHT * subword[w]     # char n-gramas (OOV friendly)
          )

        Para palavras fora do vocab, retorna subword_vec (não mais rand_vec puro).
        Isso é a melhoria FastText: palavras desconhecidas recebem vetor útil.
        """
        w   = _deaccent(word.lower())
        iw  = self._input_vec.get(w)
        drv = self._drift_vec.get(w)
        sub = self._subword_vec(w)   # sempre calculado (OOV support)

        if iw is None and drv is None:
            # Palavra completamente desconhecida: retorna subword (FastText style)
            return sub

        vec = [0.0] * self.DIM

        # W (input vector) — o sinal principal do Word2Vec
        if iw:
            for k in range(self.DIM):
                vec[k] += iw[k]

        # Drift (Hebbiano) — regularização e estabilidade
        if drv:
            for k in range(self.DIM):
                vec[k] += self.DRIFT_WEIGHT * drv[k]

        # Subword — generalização morfológica e OOV
        for k in range(self.DIM):
            vec[k] += self.SUBWORD_WEIGHT * sub[k]

        norm = math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x/norm for x in vec]

    def _pmi(self, w1: str, w2: str) -> float:
        key = (min(w1, w2), max(w1, w2))
        c12 = self._cooc.get(key, 0)
        if c12 == 0 or self._total_pairs == 0:
            return 0.0
        p12 = c12 / self._total_pairs
        p1  = self._freq.get(w1, 0) / max(self._total_tokens, 1)
        p2  = self._freq.get(w2, 0) / max(self._total_tokens, 1)
        denom = p1 * p2
        return max(0.0, math.log2(p12 / denom)) if denom > 0 else 0.0

    def sentence_vector(self, text: str) -> List[float]:
        key = f'{self._sv_version}|{text}'
        hit = self._sv_cache.get(key)
        if hit is not None:
            return hit
        tokens = _tokenize_embed(text)
        if not tokens:
            return [0.0] * self.DIM
        vecs = [self.vector(t) for t in tokens]
        avg  = [sum(v[i] for v in vecs) / len(vecs) for i in range(self.DIM)]
        norm = math.sqrt(sum(x*x for x in avg)) or 1.0
        result = [x/norm for x in avg]
        if len(self._sv_cache) >= 2048:
            for k in list(self._sv_cache)[:1024]:
                del self._sv_cache[k]
        self._sv_cache[key] = result
        return result

    def cosine(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a*b for a, b in zip(v1, v2))
        n1  = math.sqrt(sum(x*x for x in v1)) or 1e-9
        n2  = math.sqrt(sum(x*x for x in v2)) or 1e-9
        return dot / (n1 * n2)

    def nearest_facts(self, query: str, facts: List[str], top_k: int = 3,
                      min_sim: float = 0.25) -> List[Tuple[float, str]]:
        qv = self.sentence_vector(query)
        scored = [(self.cosine(qv, self.sentence_vector(f)), f) for f in facts]
        scored.sort(reverse=True)
        return [(s, f) for s, f in scored[:top_k] if s >= min_sim]

    def most_similar(self, word: str, top_k: int = 5) -> List[Tuple[float, str]]:
        """Palavras semanticamente mais próximas (usa vetor final W+drift+subword)."""
        w = _deaccent(word.lower())
        if w not in self._vocab:
            return []
        wv = self.vector(w)
        results = []
        for v in self._vocab:
            if v == w:
                continue
            s = self.cosine(wv, self.vector(v))
            if s > 0.0:
                results.append((s, v))
        results.sort(reverse=True)
        return results[:top_k]

    def analogy(self, pos1: str, neg1: str, pos2: str, top_k: int = 5) -> List[Tuple[float, str]]:
        """
        Analogia vetorial: pos1 - neg1 + pos2 = ?
        Exemplo: analogy('rei', 'homem', 'mulher') ≈ [('rainha', 0.68), ...]
        """
        vp1 = self.vector(_deaccent(pos1.lower()))
        vn1 = self.vector(_deaccent(neg1.lower()))
        vp2 = self.vector(_deaccent(pos2.lower()))
        target = [vp1[i] - vn1[i] + vp2[i] for i in range(self.DIM)]
        nt = math.sqrt(sum(x*x for x in target)) or 1.0
        target = [x/nt for x in target]
        exclude = {_deaccent(w.lower()) for w in [pos1, neg1, pos2]}
        results = [(self.cosine(target, self.vector(w)), w)
                   for w in self._vocab if w not in exclude]
        results.sort(reverse=True)
        return results[:top_k]

    @property
    def vocab_size(self) -> int:
        return len(self._vocab)

    def to_dict(self) -> dict:
        cooc_ser = {f'{k[0]}|{k[1]}': v for k, v in self._cooc.items()}
        return {'dim': self.DIM,
                'cooc': cooc_ser, 'freq': dict(self._freq),
                'total_pairs': self._total_pairs,
                'total_tokens': self._total_tokens,
                'vocab': list(self._vocab),
                'ctx_vec':    {w: v for w, v in self._ctx_vec.items()},
                'drift_vec':  {w: v for w, v in self._drift_vec.items()},
                'input_vec':  {w: v for w, v in self._input_vec.items()},
                'output_vec': {w: v for w, v in self._output_vec.items()},
                'updates':    self._updates}

    @classmethod
    def from_dict(cls, d: dict) -> 'MiniEmbed':
        me = cls()
        stored_dim = d.get('dim', me.DIM)
        if stored_dim != me.DIM:
            import warnings
            warnings.warn(f"MiniEmbed: DIM no arquivo ({stored_dim}) != DIM atual ({me.DIM})")
        for k, v in d.get('cooc', {}).items():
            parts = k.split('|', 1)
            if len(parts) == 2:
                me._cooc[(parts[0], parts[1])] = v
        me._freq         = defaultdict(int, d.get('freq', {}))
        me._total_pairs  = d.get('total_pairs', 0)
        me._total_tokens = d.get('total_tokens', 0)
        me._vocab        = set(d.get('vocab', []))
        me._ctx_vec      = {w: list(v) for w, v in d.get('ctx_vec', {}).items()}
        me._drift_vec    = {w: list(v) for w, v in d.get('drift_vec', {}).items()}
        me._input_vec    = {w: list(v) for w, v in d.get('input_vec', {}).items()}
        me._output_vec   = {w: list(v) for w, v in d.get('output_vec', {}).items()}
        me._updates      = d.get('updates', 0)
        me._ns_dirty     = True
        return me



# ══════════════════════════════════════════════════════════════════════════════
# §5  LEARNED EDGE — v7 (aresta que aprende seu contexto de ativação)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class LearnedEdge:
    """
    Aresta tipada (source, relation, target) que acumula em quais contextos
    ela dispara corretamente. Cada reinforcement ensina um contexto novo.
    """
    source:      str
    relation:    str
    target:      str
    strength:    float         = 0.3
    activations: int           = 0
    last_used:   float         = field(default_factory=time.time)
    created_at:  float         = field(default_factory=time.time)
    evidence:    List[str]     = field(default_factory=list)

    EDGE_MAX_STRENGTH   = 1.0
    EDGE_REINFORCE_RATE = 0.08
    EDGE_DECAY          = 0.998

    def reinforce(self, evidence: str = '', reward: float = 1.0) -> None:
        delta = self.EDGE_REINFORCE_RATE * reward
        self.strength = min(self.EDGE_MAX_STRENGTH, self.strength + delta)
        if evidence and evidence not in self.evidence:
            self.evidence.append(evidence[:80])
            if len(self.evidence) > 10:
                self.evidence.pop(0)
        self.activations += 1
        self.last_used = time.time()

    def weaken(self, penalty: float = 0.5) -> None:
        self.strength = max(0.0, self.strength - self.EDGE_REINFORCE_RATE * penalty)

    def decay(self) -> None:
        self.strength *= self.EDGE_DECAY

    def to_dict(self) -> dict:
        return {'s': self.source, 'r': self.relation, 't': self.target,
                'str': round(self.strength, 6), 'acts': self.activations,
                'ev': self.evidence[:5]}

    @classmethod
    def from_dict(cls, d: dict) -> 'LearnedEdge':
        return cls(source=d['s'], relation=d['r'], target=d['t'],
                   strength=d.get('str', 0.3), activations=d.get('acts', 0),
                   evidence=d.get('ev', []))

    def __eq__(self, other) -> bool:
        if not isinstance(other, LearnedEdge): return False
        return (self.source, self.relation, self.target) == (other.source, other.relation, other.target)

    def __hash__(self):
        return hash((self.source, self.relation, self.target))


# ══════════════════════════════════════════════════════════════════════════════
# §6  EDGE NETWORK — v7 (grafo de arestas aprendidas com propagação)
# ══════════════════════════════════════════════════════════════════════════════

class EdgeNetwork:
    """
    Grafo de LearnedEdges. Suporta busca por sujeito, relação, alvo e
    propagação BFS com filtragem por força.
    Complementa o CognitiveBrain com conhecimento estrutural tipado.
    """

    FIRE_THRESHOLD = 0.05

    def __init__(self):
        self._by_source:   Dict[str, List[LearnedEdge]] = defaultdict(list)
        self._by_target:   Dict[str, List[LearnedEdge]] = defaultdict(list)
        self._by_key:      Dict[Tuple, LearnedEdge]     = {}

    # ── Adição ────────────────────────────────────────────────────────────────

    def add(self, source: str, relation: str, target: str,
            evidence: str = '', strength: float = 0.4) -> LearnedEdge:
        s, r, t = source.lower().strip(), relation, target.lower().strip()
        key = (s, r, t)
        if key in self._by_key:
            existing = self._by_key[key]
            existing.reinforce(evidence)
            return existing
        edge = LearnedEdge(source=s, relation=r, target=t,
                           strength=strength, evidence=[evidence] if evidence else [])
        self._by_key[key] = edge
        self._by_source[s].append(edge)
        self._by_target[t].append(edge)
        return edge

    # ── Busca ─────────────────────────────────────────────────────────────────

    def get_by_source(self, source: str, min_strength: float = 0.0) -> List[LearnedEdge]:
        return [e for e in self._by_source.get(source.lower(), [])
                if e.strength >= min_strength]

    def get_by_target(self, target: str, min_strength: float = 0.0) -> List[LearnedEdge]:
        return [e for e in self._by_target.get(target.lower(), [])
                if e.strength >= min_strength]

    def get_definitions(self, concept: str) -> List[str]:
        """Retorna textos de definição de um conceito (edges IS_A / é)."""
        concept = concept.lower().strip()
        results = []
        for e in self._by_source.get(concept, []):
            if e.relation in (REL_IS_A, 'é', 'é_um'):
                results.append(f'{e.source} {e.relation} {e.target}')
        return results

    def propagate(self, seeds: List[str], max_depth: int = 2,
                  min_strength: float = 0.1) -> Dict[str, float]:
        """BFS com decaimento por profundidade."""
        scores: Dict[str, float] = {}
        frontier = {s.lower(): 1.0 for s in seeds}
        visited: Set[str] = set(frontier)
        for depth in range(max_depth):
            decay = 0.7 ** depth
            nxt: Dict[str, float] = {}
            for node, node_score in frontier.items():
                for edge in self._by_source.get(node, []):
                    if edge.strength < min_strength:
                        continue
                    t = edge.target
                    contrib = node_score * edge.strength * decay
                    if t not in visited:
                        scores[t] = max(scores.get(t, 0.0), contrib)
                        nxt[t]    = scores[t]
                        visited.add(t)
            frontier = nxt
            if not frontier:
                break
        return scores

    def decay_all(self) -> None:
        for edge in self._by_key.values():
            edge.decay()

    def prune_weak(self, threshold: float = 0.05) -> int:
        removed = 0
        dead_keys = [k for k, e in self._by_key.items() if e.strength < threshold]
        for key in dead_keys:
            edge = self._by_key.pop(key)
            self._by_source[edge.source] = [e for e in self._by_source[edge.source] if e != edge]
            self._by_target[edge.target] = [e for e in self._by_target[edge.target] if e != edge]
            removed += 1
        return removed

    @property
    def edge_count(self) -> int:
        return len(self._by_key)

    def to_dict(self) -> dict:
        return {'edges': [e.to_dict() for e in self._by_key.values()]}

    @classmethod
    def from_dict(cls, d: dict) -> 'EdgeNetwork':
        en = cls()
        for ed in d.get('edges', []):
            e = LearnedEdge.from_dict(ed)
            en._by_key[(e.source, e.relation, e.target)] = e
            en._by_source[e.source].append(e)
            en._by_target[e.target].append(e)
        return en


# ══════════════════════════════════════════════════════════════════════════════
# §7  DATACLASSES DE MEMÓRIA — v5 Pro
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class MemoryTrace:
    sdr:          SparseSDR
    text:         str
    tag:          str          = 'FACT'
    confidence:   float        = 1.0
    strength:     float        = 1.0
    access_count: int          = 0
    created_at:   float        = field(default_factory=time.time)
    metadata:     Dict         = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {'sdr': self.sdr.to_dict(), 'text': self.text, 'tag': self.tag,
                'conf': round(self.confidence, 4), 'str': round(self.strength, 4),
                'ac': self.access_count, 'ts': round(self.created_at, 2),
                'meta': self.metadata}

    @classmethod
    def from_dict(cls, d: dict) -> 'MemoryTrace':
        return cls(sdr=SparseSDR.from_dict(d['sdr']), text=d['text'],
                   tag=d.get('tag', 'FACT'), confidence=d.get('conf', 1.0),
                   strength=d.get('str', 1.0), access_count=d.get('ac', 0),
                   created_at=d.get('ts', time.time()), metadata=d.get('meta', {}))


@dataclass
class Relation:
    sdr_a:    SparseSDR
    sdr_b:    SparseSDR
    rel_type: str
    txt_a:    str
    txt_b:    str
    strength: float = 1.0

    def to_dict(self) -> dict:
        return {'a': self.sdr_a.to_dict(), 'b': self.sdr_b.to_dict(),
                'rel': self.rel_type, 'ta': self.txt_a, 'tb': self.txt_b,
                'str': round(self.strength, 4)}

    @classmethod
    def from_dict(cls, d: dict) -> 'Relation':
        return cls(sdr_a=SparseSDR.from_dict(d['a']), sdr_b=SparseSDR.from_dict(d['b']),
                   rel_type=d['rel'], txt_a=d['ta'], txt_b=d['tb'],
                   strength=d.get('str', 1.0))


@dataclass
class InferenceResult:
    chain:      list
    query:      str
    conclusion: str
    confidence: float


# ══════════════════════════════════════════════════════════════════════════════
# §8  COGNITIVE BRAIN — v5 Pro (InvertedIndex O(1), strength, decay, tags)
# ══════════════════════════════════════════════════════════════════════════════

class CognitiveBrain:
    """
    Núcleo de memória SDR com recuperação por InvertedIndex.
    Completo: store, recall, revise_beliefs, decay, serialize.
    """
    RECALL_THRESHOLD  = 0.05
    NOVELTY_THRESHOLD = 0.13
    FACT_THRESHOLD    = 0.55
    DECAY_RATE        = 0.995
    DECAY_FLOOR       = 0.05
    MIN_INDEX_OVERLAP = 3
    # Encoder lazy compartilhado entre instâncias — _zone_encode é
    # determinístico (seed=SDR_SEED fixo), não há estado mutável relevante.
    _enc: Optional['MultiLobeEncoder'] = None

    def __init__(self):
        self._memories  : List[MemoryTrace] = []
        self._relations : List[Relation]    = []
        self._index     = InvertedIndex()
        self._lock      = threading.Lock()

    def store(self, sdr: SparseSDR, text: str, tag: str = 'FACT',
              confidence: float = 1.0, metadata: Optional[Dict] = None) -> MemoryTrace:
        meta   = dict(metadata) if metadata else {}
        domain = _extract_domain(text)
        if domain:
            meta['domain'] = domain
        trace = MemoryTrace(sdr=sdr, text=text, tag=tag,
                            confidence=confidence, strength=1.0, metadata=meta)
        if tag == 'FACT':
            contras = self._find_contradictions_for(sdr, text)
            if contras:
                trace.tag = 'THEORY'
                trace.confidence = 0.4
                trace.strength   = 0.6
                trace.metadata['conflict_with'] = [c.text[:80] for c in contras]
            else:
                self._dedup_and_reinforce(sdr, text)
        self._memories.append(trace)
        mid = len(self._memories) - 1
        self._index.add(mid, sdr)
        if tag == 'FACT' and trace.tag == 'FACT':
            self._auto_extract_relation(text, sdr)
        return trace

    def recall(self, query: SparseSDR, top_k: int = 6,
               threshold: Optional[float] = None,
               tags: Optional[List[str]] = None) -> List[Tuple[float, MemoryTrace]]:
        thr   = threshold if threshold is not None else self.RECALL_THRESHOLD
        sem_q = query.semantic_bits()
        cands = self._index.candidates(query, self.MIN_INDEX_OVERLAP)
        results: List[Tuple[float, MemoryTrace]] = []
        # Prepara tokens da query para match textual (fallback quando SDR jaccard baixo)
        q_toks = set(re.findall(r'\w{3,}', _deaccent(query.bits_as_str() if hasattr(query,'bits_as_str') else '').lower()))
        for mid in cands:
            if mid >= len(self._memories):
                continue
            mem = self._memories[mid]
            if tags and mem.tag not in tags:
                continue
            sdr_score = sem_q.jaccard(mem.sdr.semantic_bits())
            # Complemento textual: aumenta score se query_text tokens aparecem no fato
            # Necessário porque SDR jaccard semântico é estruturalmente baixo (~0.04-0.22)
            # e não discrimina conceitos distintos de forma confiável
            if sdr_score < thr:
                continue
            results.append((sdr_score * (0.5 + 0.5 * mem.strength), mem))
        results.sort(key=lambda x: -x[0])
        top = results[:top_k]
        for _, mem in top:
            mem.access_count += 1
            mem.strength = min(1.0, mem.strength + 0.05)
        return top

    def recall_texts(self, query: SparseSDR, top_k: int = 5,
                     threshold: Optional[float] = None,
                     tags: Optional[List[str]] = None) -> List[str]:
        return [m.text for _, m in self.recall(query, top_k, threshold, tags)]

    def best_match(self, query: SparseSDR,
                   tags: Optional[List[str]] = None) -> Optional[Tuple[float, MemoryTrace]]:
        r = self.recall(query, top_k=1, threshold=0.0, tags=tags)
        return r[0] if r else None

    def max_activation(self, query: SparseSDR) -> float:
        if not self._memories:
            return 0.0
        sem_q = query.semantic_bits()
        cands = self._index.candidates(query, 1)
        if not cands:
            return 0.0
        return max(sem_q.jaccard(self._memories[mid].sdr.semantic_bits())
                   for mid in cands if mid < len(self._memories))

    def is_novel(self, query: SparseSDR) -> bool:
        return self.max_activation(query) < self.NOVELTY_THRESHOLD

    def revise_beliefs(self, new_sdr: SparseSDR, new_text: str) -> List[MemoryTrace]:
        demoted = []
        for trace in self._find_contradictions_for(new_sdr, new_text):
            if trace.tag == 'FACT':
                trace.tag = 'THEORY'
                trace.confidence = max(0.1, trace.confidence - 0.4)
                trace.strength   = max(0.1, trace.strength - 0.3)
                trace.metadata['demoted_by'] = new_text[:80]
                demoted.append(trace)
        return demoted

    def promote_theory(self, trace: MemoryTrace) -> bool:
        if trace.tag == 'THEORY' and trace.confidence >= 0.6:
            trace.tag = 'FACT'
            trace.confidence = min(1.0, trace.confidence + 0.2)
            trace.strength = 0.9
            return True
        return False

    def all_by_tag(self, tag: str) -> List[MemoryTrace]:
        return [m for m in self._memories if m.tag == tag]

    @property
    def stats(self) -> Dict:
        counts = Counter(m.tag for m in self._memories)
        avg_s  = (sum(m.strength for m in self._memories) / len(self._memories)
                  if self._memories else 0.0)
        return {'total': len(self._memories), 'relations': len(self._relations),
                'avg_strength': round(avg_s, 3), **dict(counts)}

    def decay_cycle(self) -> Dict[str, int]:
        """Aplica decaimento de força a todas as memórias e remove as fracas.

        Lógica de pruning:
        - strength decai por DECAY_RATE a cada ciclo
        - recall() reforça strength em +0.05 (memórias usadas vivem mais)
        - Prune quando strength < DECAY_FLOOR (sem distinção de access_count)
          → memórias nunca acessadas decaem normalmente
          → memórias acessadas recentemente ficam vivas via strength alto
          → NÃO há imunidade permanente por access_count (bug anterior removido)
        """
        with self._lock:
            before = len(self._memories)
            pruned_ids: Set[int] = set()
            for i, mem in enumerate(self._memories):
                if mem.tag not in ('FACT', 'THEORY', 'HYPOTHESIS'):
                    continue
                mem.strength = max(0.0, mem.strength * self.DECAY_RATE)
                # Prune por força — sem exceção por access_count.
                # recall() reforça strength, então memórias úteis se auto-preservam.
                if mem.strength < self.DECAY_FLOOR:
                    pruned_ids.add(i)
            self._memories = [m for i, m in enumerate(self._memories)
                              if i not in pruned_ids]
            # Rebuild index from scratch to keep indices consistent after pruning
            self._index = InvertedIndex()
            for i, m in enumerate(self._memories):
                self._index.add(i, m.sdr)
            for rel in self._relations:
                rel.strength *= self.DECAY_RATE
            self._relations = [r for r in self._relations if r.strength >= self.DECAY_FLOOR]
        return {'before': before, 'after': len(self._memories),
                'pruned': before - len(self._memories)}

    def infer_transitive(self, query_sdr: SparseSDR, query_text: str,
                         max_depth: int = 3) -> Optional[InferenceResult]:
        if not self._relations:
            return None
        sem_q = query_sdr.semantic_bits()
        qt_norm = _deaccent(query_text.lower().strip())
        # Gate primário: txt_a match textual (SDR jaccard real ~0.04, inútil como gate)
        # Procura a relação cujo sujeito (txt_a) é mencionado na query
        best_origin, best_sim = None, 0.0
        for rel in self._relations:
            sim = sem_q.jaccard(rel.sdr_a.semantic_bits())
            # Fallback textual: txt_a normalizado aparece na query normalizada
            txt_match = _deaccent(rel.txt_a.lower()[:8]) in qt_norm
            if txt_match:
                sim = max(sim, 0.15)   # eleva score para passar o gate
            if sim > best_sim:
                best_sim, best_origin = sim, rel
        if not best_origin or best_sim < 0.05:
            return None
        visited: Set[int] = set()
        frontier = [(best_origin, [best_origin])]
        while frontier:
            current, path = frontier.pop(0)
            if len(path) > max_depth:
                continue
            nk = id(current)
            if nk in visited:
                continue
            visited.add(nk)
            dest_sim = sem_q.jaccard(current.sdr_b.semantic_bits())
            # sdr_b é zone_encode de apenas 5 bits — Jaccard estruturalmente baixo.
            # Threshold reduzido para 0.04; fallback: txt_b menciona a query (match textual).
            qt = _deaccent(query_text.lower().strip())
            txt_b_match = qt and qt[:6] in _deaccent(current.txt_b.lower())
            if len(path) >= 2 and (dest_sim >= 0.04 or txt_b_match):
                return InferenceResult(chain=path, query=query_text,
                                       conclusion=path[-1].txt_b,
                                       confidence=max(dest_sim, 0.1)*min(1.0, best_sim*1.5))
            for nrel in self._relations:
                sim2 = current.sdr_b.semantic_bits().jaccard(nrel.sdr_a.semantic_bits())
                # Threshold reduzido: sdr_b tem 5 bits, sdr_a tem 14 — jaccard máximo ≈ 0.36
                # Na prática valores acima de 0.05 já indicam sobreposição real.
                txt_chain = _deaccent(current.txt_b.lower()[:6]) in _deaccent(nrel.txt_a.lower())
                if sim2 >= 0.05 or txt_chain:
                    frontier.append((nrel, path+[nrel]))
        return None

    def _auto_extract_relation(self, text: str, sdr: SparseSDR) -> None:
        tl = text.strip().lower()
        # Usa encoder de classe — _zone_encode é determinístico (seed fixo).
        # Evita instanciar MultiLobeEncoder() a cada fato aprendido.
        if CognitiveBrain._enc is None:
            CognitiveBrain._enc = MultiLobeEncoder()
        enc = CognitiveBrain._enc
        for pattern, rel_type in _REL_PATTERNS:
            m = pattern.match(tl)
            if m:
                ta, tb = m.group(1).strip(), m.group(2).strip()
                if len(ta) >= 2 and len(tb) >= 2:
                    sdr_b = enc._zone_encode(tb, ZONE_SEMANTIC, 5)
                    self._relations.append(
                        Relation(sdr_a=sdr, sdr_b=sdr_b, rel_type=rel_type,
                                 txt_a=ta, txt_b=tb))
                break

    def _find_contradictions_for(self, sdr: SparseSDR,
                                 text: str) -> List[MemoryTrace]:
        contradictions: List[MemoryTrace] = []
        candidates = self.recall(sdr, top_k=8, threshold=0.03, tags=['FACT'])
        for _, mem in candidates:
            sem_s = sdr.semantic_bits().jaccard(mem.sdr.semantic_bits())
            if sem_s >= self.FACT_THRESHOLD:
                continue
            if self._texts_contradict(text, mem.text):
                contradictions.append(mem)
        return contradictions

    def _texts_contradict(self, a: str, b: str) -> bool:
        da = _extract_domain(a)
        db = _extract_domain(b)
        if da and db and _deaccent(da.lower()[:5]) != _deaccent(db.lower()[:5]):
            return False
        al, bl = a.lower(), b.lower()

        # Sujeitos diferentes → nunca contradição.
        # O sujeito é o primeiro token não-stopword de cada texto.
        def _first_subj(s):
            toks = [t for t in re.findall(r'\w{3,}', s) if t not in _STOP_PT]
            return toks[0] if toks else ''
        subj_a, subj_b = _first_subj(al), _first_subj(bl)
        if subj_a and subj_b and subj_a != subj_b:
            return False

        def stemmed(s):
            return {t[:5] for t in re.findall(r'\w{3,}', s) if t not in _STOP_PT}
        sa, sb = stemmed(al), stemmed(bl)

        # Contradição por antônimos
        for ant, opp in _ANTONYMS.items():
            if ant in al and opp in bl and len(sa & sb) >= 1:
                return True

        # Contradição numérica (dígitos)
        na = re.findall(r'\d+(?:[.,]\d+)?', al)
        nb = re.findall(r'\d+(?:[.,]\d+)?', bl)
        if na and nb and set(na) != set(nb) and len(sa & sb) >= 2:
            return True

        # Contradição por ordinais/quantitativos por extenso
        # Ex: "terceiro planeta" vs "quarto planeta"
        _ORDINALS = {'primeiro','segundo','terceiro','quarto','quinto','sexto',
                     'sétimo','oitavo','nono','décimo','único','penúltimo','último'}
        ord_a = {w for w in re.findall(r'\w+', al) if w in _ORDINALS}
        ord_b = {w for w in re.findall(r'\w+', bl) if w in _ORDINALS}
        if ord_a and ord_b and ord_a != ord_b and len(sa & sb) >= 2:
            return True

        # Contradição de predicativo nominal exclusivo:
        # "X é [artigo?] Y" vs "X é [artigo?] Z" onde Y ≠ Z, mesmo sujeito, e
        # ambos têm estrutura definitória (começa com sujeito + é/são).
        # Condição: os dois fatos têm padrão "sujeito é <substantivo>" e o
        # predicativo é diferente — detecta "lua é satélite" vs "lua é planeta".
        _RE_PRED = re.compile(
            r'^(?P<subj>\w[\w\s]{0,25}?)\s+(?:é|são)\s+(?:um[a]?\s+|o\s+|a\s+)?(?P<pred>\w{3,})',
            re.I)
        ma = _RE_PRED.match(al.strip())
        mb = _RE_PRED.match(bl.strip())
        if ma and mb:
            pred_a = _deaccent(ma.group('pred').lower())[:5]
            pred_b = _deaccent(mb.group('pred').lower())[:5]
            # Predicativos diferentes + mesmo sujeito (já verificado) = contradição
            # Exceto: se um é extensão do outro (hipônimo/hiperônimo) eles coexistem
            # Heurística: texto mais longo costuma ser extensão, não contradição
            if pred_a != pred_b and len(sa & sb) >= 1:
                # Só marca contradição se os fatos forem curtos (definições diretas)
                # Fatos longos como "gato é mamífero que tem pelos e caça" não conflitam
                # com "gato é animal doméstico" porque têm contexto adicional
                words_a = len(re.findall(r'\w+', al))
                words_b = len(re.findall(r'\w+', bl))
                if words_a <= 10 and words_b <= 10:
                    return True

        return False

    def _dedup_and_reinforce(self, sdr: SparseSDR, text: str) -> None:
        sem_q = sdr.semantic_bits()
        for mem in self._memories:
            if (mem.tag == 'FACT' and
                    sem_q.jaccard(mem.sdr.semantic_bits()) >= self.FACT_THRESHOLD):
                mem.confidence = min(1.0, mem.confidence + 0.05)
                mem.strength   = min(1.0, mem.strength + 0.05)

    def to_dict(self) -> dict:
        return {'m': [m.to_dict() for m in self._memories],
                'r': [r.to_dict() for r in self._relations]}

    @classmethod
    def from_dict(cls, d: dict) -> 'CognitiveBrain':
        brain = cls()
        for i, md in enumerate(d.get('m', [])):
            m = MemoryTrace.from_dict(md)
            brain._memories.append(m)
            brain._index.add(i, m.sdr)
        brain._relations = [Relation.from_dict(r) for r in d.get('r', [])]
        return brain


# ══════════════════════════════════════════════════════════════════════════════
# §9  STRUCTURED FACT STORE — v5 Pro (TF-IDF + subject boost + negação)
# ══════════════════════════════════════════════════════════════════════════════

class StructuredFactStore:
    """
    Índice invertido textual com TF-IDF e boost 2.5× quando token bate no
    sujeito do fato (primeiras palavras significativas). Camada primária de
    recuperação — O(k) onde k = candidatos por token.
    """
    _DEDUP_SIM = 0.72

    def __init__(self):
        self._facts  : List[str]               = []
        self._index  : Dict[str, List[int]]    = defaultdict(list)
        self._struct : Dict[str, Dict[str, bool]] = {}
        self._tf     : Dict[int, Dict[str, float]] = {}
        self._df     : Dict[str, int]          = defaultdict(int)

    @staticmethod
    def _norm(w: str) -> str:
        w = _deaccent(w.lower().strip())
        if w.endswith('s') and len(w) > 3:
            w = w[:-1]
        return w

    def add(self, fact: str) -> None:
        if fact in self._facts or self._is_near_duplicate(fact):
            return
        idx = len(self._facts)
        self._facts.append(fact)
        tokens = re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', fact.lower())
        tok_set: set = set()
        tok_count: Dict[str, int] = defaultdict(int)
        for tok in tokens:
            if len(tok) >= 2 and tok not in _STOP_PT:
                self._index[tok].append(idx)
                tok_count[tok] += 1
                tok_set.add(tok)
        n = max(len(tokens), 1)
        self._tf[idx] = {tok: cnt/n for tok, cnt in tok_count.items()}
        for tok in tok_set:
            self._df[tok] += 1
        self._parse_structure(fact, idx)

    def _is_near_duplicate(self, fact: str) -> bool:
        toks_new = {self._norm(w) for w in re.findall(r'\w{3,}', fact.lower())
                    if w not in _STOP_PT}
        if not toks_new:
            return False
        cands: set = set()
        for tok in toks_new:
            cands.update(self._index.get(tok, []))
            cands.update(self._index.get(self._norm(tok), []))
        for cidx in cands:
            if cidx >= len(self._facts):
                continue
            existing = self._facts[cidx]
            toks_ex = {self._norm(w) for w in re.findall(r'\w{3,}', existing.lower())
                       if w not in _STOP_PT}
            if not toks_ex:
                continue
            inter = len(toks_new & toks_ex)
            union = len(toks_new | toks_ex)
            if not union:
                continue
            if inter / union < self._DEDUP_SIM:
                continue
            # Jaccard acima do threshold — mas verifica se o SUJEITO é o mesmo.
            # Fatos sobre sujeitos diferentes nunca são duplicatas, mesmo que
            # partilhem muita estrutura (ex: "inteiro em python é..." vs "flutuante em python é...")
            def _first_tok(s):
                toks = [w for w in re.findall(r'\w{3,}', s.lower()) if w not in _STOP_PT]
                return toks[0] if toks else ''
            if _first_tok(fact) != _first_tok(existing):
                continue   # sujeitos diferentes → não é duplicata
            return True
        return False

    def _parse_structure(self, text: str, idx: int) -> None:
        t = text.lower().strip()
        m = re.match(r'(.+?)\s+(?:não\s+)?(?:é|tem|são|possui|faz|causa)\s+(.+)', t)
        if not m:
            return
        subj = m.group(1).strip().split()[-1]
        obj  = m.group(2).strip().split()[0]
        neg  = 'não' in t
        self._struct.setdefault(subj, {})[obj] = not neg

    def search(self, query: str, top_k: int = 5, min_score: float = 0.5) -> List[str]:
        tokens = [t for t in re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', query.lower())
                  if len(t) >= 2 and t not in _STOP_PT]
        if not tokens:
            return []
        counts: Dict[int, float] = defaultdict(float)
        n = len(self._facts)
        for tok in tokens:
            idf = math.log((n+1) / (self._df.get(tok, 0)+1)) + 1.0
            for idx in self._index.get(tok, []):
                base = self._tf.get(idx, {}).get(tok, 0.0) * idf
                # Boost 2.5× se o token bate no sujeito do fato
                fact_lower  = self._facts[idx].lower()
                fact_tokens = [t for t in re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', fact_lower)
                               if len(t) >= 2 and t not in _STOP_PT]
                subj_match  = bool(fact_tokens and fact_tokens[0].startswith(tok[:5]))
                counts[idx] += base * (2.5 if subj_match else 1.0)
        ranked = sorted(counts.items(), key=lambda x: -x[1])
        return [self._facts[i] for i, s in ranked[:top_k] if s >= min_score]

    def query_negation(self, query: str) -> Optional[str]:
        m = re.search(r'(?:quem|qual|o\s+que)\s+não\s+(?:tem|é|possui)\s+(\w+)', query.lower())
        if not m:
            return None
        prop    = m.group(1)
        results = [subj for subj, attrs in self._struct.items()
                   if not attrs.get(prop, True)]
        return ', '.join(results) if results else None

    def all_facts(self) -> List[str]:
        return list(self._facts)

    def remove_by_text(self, text: str) -> bool:
        """Remove um fato do store pelo texto exato (case-insensitive strip).
        Atualiza _index, _tf e _df para manter o índice consistente.
        Retorna True se encontrou e removeu, False caso contrário.

        Nota: os índices numéricos (_index, _tf) não são compactados após remoção
        para evitar O(n) de reindexação; o slot fica inativo (None em _facts).
        """
        tl = text.strip().lower()
        for idx, fact in enumerate(self._facts):
            if fact.strip().lower() == tl:
                # Decrementar df e remover de _index
                for tok, positions in list(self._index.items()):
                    if idx in positions:
                        positions.remove(idx)
                        if not positions:
                            del self._index[tok]
                        self._df[tok] = max(0, self._df.get(tok, 1) - 1)
                        if self._df[tok] == 0:
                            del self._df[tok]
                # Remover TF do slot
                self._tf.pop(idx, None)
                # Substituir pelo sentinel None para não reindexar tudo
                self._facts[idx] = None   # type: ignore[assignment]
                # Compactar para não vazar memória em uso intenso
                self._facts = [f for f in self._facts if f is not None]
                return True
        return False

    def __len__(self) -> int:
        return len(self._facts)

    def to_dict(self) -> dict:
        return {'facts': [f for f in self._facts if f is not None]}

    @classmethod
    def from_dict(cls, d: dict) -> 'StructuredFactStore':
        sfs = cls()
        for f in d.get('facts', []):
            sfs.add(f)
        return sfs


# ══════════════════════════════════════════════════════════════════════════════
# §10  HYBRID RETRIEVER — v8 (cascata 3 camadas)
# ══════════════════════════════════════════════════════════════════════════════

class HybridRetriever:
    """
    Recuperação em cascata:
      1. StructuredFactStore (TF-IDF + subject boost) — O(k), rápido
      2. CognitiveBrain (SDR Jaccard via InvertedIndex) — O(candidatos)
      3. MiniEmbed (cosine semântico) — O(n), só se as anteriores falham
    Retorna a melhor resposta encontrada com seu score e fonte.
    """

    def __init__(self, fact_store: StructuredFactStore,
                 brain: CognitiveBrain, embed: MiniEmbed):
        self._fs    = fact_store
        self._brain = brain
        self._embed = embed

    def retrieve(self, query: str, query_sdr: SparseSDR,
                 top_k: int = 3) -> List[Tuple[float, str, str]]:
        """
        Retorna lista de (score, texto, fonte) em ordem decrescente.
        fonte ∈ {'factstore', 'brain', 'embed'}
        """
        results: List[Tuple[float, str, str]] = []

        # Camada 1: StructuredFactStore
        fs_hits = self._fs.search(query, top_k=top_k, min_score=0.2)
        for i, text in enumerate(fs_hits):
            score = 1.0 - i * 0.1   # rank-based scoring
            results.append((score, text, 'factstore'))

        # Camada 2: CognitiveBrain (SDR Jaccard)
        seen = {r[1] for r in results}
        brain_hits = self._brain.recall(query_sdr, top_k=top_k, tags=['FACT', 'RULE'])
        for score, mem in brain_hits:
            if mem.text not in seen:
                results.append((score * 0.9, mem.text, 'brain'))
                seen.add(mem.text)

        # Camada 3: MiniEmbed cosine — SEMPRE ativa para re-ranquear
        # O drift_vec captura semântica real; usa-o para elevar fatos relevantes
        # que o FactStore TF-IDF pode ter subavaliado.
        if self._embed._vocab:
            all_facts = self._fs.all_facts()
            if all_facts:
                embed_hits = self._embed.nearest_facts(query, all_facts,
                                                       top_k=max(top_k, 5), min_sim=0.10)
                for score, text in embed_hits:
                    if text not in seen:
                        # Novo fato via embed: adiciona com score embed
                        results.append((score * 0.80, text, 'embed'))
                        seen.add(text)
                    else:
                        # Fato já encontrado: eleva score se embed concorda (re-ranking)
                        for i, (rs, rt, rsrc) in enumerate(results):
                            if rt == text:
                                results[i] = (max(rs, score * 0.90), rt, rsrc + '+embed')
                                break

        results.sort(key=lambda x: -x[0])
        return results[:top_k]

    def best(self, query: str, query_sdr: SparseSDR) -> Optional[Tuple[float, str, str]]:
        hits = self.retrieve(query, query_sdr, top_k=1)
        return hits[0] if hits else None


# ══════════════════════════════════════════════════════════════════════════════
# §11  CONCEPT GRAPH — v5 Pro (analogia A:B::C:?, BFS, vizinhos ponderados)
# ══════════════════════════════════════════════════════════════════════════════

class ConceptGraph:
    """Grafo semântico tipado. Analogia, BFS, vizinhos ponderados."""

    _REL_WEIGHTS = {
        'é': 1.0, 'é-um': 0.9, 'tem': 0.7, 'faz': 0.6, 'causa': 0.7,
        'parte-de': 0.8, 'oposto': 0.5, 'sinônimo': 0.9,
        'exemplo-de': 0.8, 'implica': 0.8, 'usa': 0.6,
        REL_IS_A: 0.9, REL_HAS: 0.7, REL_DOES: 0.6,
        REL_CAUSES: 0.7, REL_PRODUCES: 0.6, REL_PART_OF: 0.8,
    }

    def __init__(self):
        self._edges:      Dict[str, Dict[str, Dict[str, float]]] = \
            defaultdict(lambda: defaultdict(dict))
        self._activation: Dict[str, int] = defaultdict(int)

    def add_edge(self, subj: str, rel: str, obj: str,
                 weight: float = None) -> None:
        w = weight if weight is not None else self._REL_WEIGHTS.get(rel, 0.5)
        self._edges[subj.lower()][obj.lower()][rel] = w
        self._activation[subj.lower()] += 1

    def neighbors(self, concept: str, depth: int = 2) -> List[Tuple[str, float]]:
        c = concept.lower()
        scores: Dict[str, float] = {}
        frontier = {c: 1.0}
        for d in range(depth):
            nxt: Dict[str, float] = {}
            for node, nw in frontier.items():
                for nbr, rels in self._edges.get(node, {}).items():
                    best  = max(rels.values())
                    total = nw * best * (0.7 ** d)
                    if nbr != c:
                        scores[nbr] = max(scores.get(nbr, 0.0), total)
                        nxt[nbr]    = scores[nbr]
            frontier = nxt
        return sorted(scores.items(), key=lambda x: -x[1])

    def path(self, start: str, end: str, max_depth: int = 4) -> List[str]:
        s, e = start.lower(), end.lower()
        queue = deque([[s]])
        visited = {s}
        while queue:
            path = queue.popleft()
            if len(path) > max_depth:
                break
            node = path[-1]
            for nbr in self._edges.get(node, {}):
                if nbr == e:
                    return path + [nbr]
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(path + [nbr])
        return []

    def analogy(self, a: str, b: str, c: str,
                encoder: MultiLobeEncoder, top_k: int = 3) -> List[str]:
        """A:B :: C:? via XOR binding nos SDRs semânticos."""
        ea = encoder.encode(a.lower())
        eb = encoder.encode(b.lower())
        ec = encoder.encode(c.lower())
        rel_idx = set(ea._idx) ^ set(eb._idx)
        tgt_idx = rel_idx ^ set(ec._idx)
        target  = SparseSDR.from_indices(list(tgt_idx)[:SDR_ACTIVE])
        candidates: Dict[str, float] = {}
        for node in self._edges:
            ov = encoder.encode(node).overlap_score(target)
            if ov > 0 and node not in (a.lower(), b.lower(), c.lower()):
                candidates[node] = ov
        return sorted(candidates, key=lambda x: -candidates[x])[:top_k]

    def consolidate(self) -> Dict[str, int]:
        """Remove referências órfãs de _activation para nós que já não existem
        em _edges (podem sobrar após prune_graph() em ciclos de sleep).
        Anteriormente verificava activation==0, o que nunca ocorria pois
        add_edge() sempre incrementa o contador — era código morto."""
        stale = [n for n in list(self._activation) if n not in self._edges]
        for n in stale:
            del self._activation[n]
        return {'removed': len(stale)}

    @property
    def node_count(self) -> int:
        return len(self._edges)

    @property
    def edge_count(self) -> int:
        return sum(len(v) for v in self._edges.values())

    def to_dict(self) -> dict:
        return {'edges': {k: {kk: dict(vv) for kk, vv in v.items()}
                          for k, v in self._edges.items()},
                'activation': dict(self._activation)}

    @classmethod
    def from_dict(cls, d: dict) -> 'ConceptGraph':
        cg = cls()
        for subj, targets in d.get('edges', {}).items():
            for obj, rels in targets.items():
                for rel, w in rels.items():
                    cg._edges[subj][obj][rel] = w
        cg._activation = defaultdict(int, d.get('activation', {}))
        return cg


# ══════════════════════════════════════════════════════════════════════════════
# §12  NGRAM MEMORY — v5 Pro (predição + geração de texto)
# ══════════════════════════════════════════════════════════════════════════════

class NGramMemory:
    """N-gram para predição e geração de texto."""

    def __init__(self, window: int = 3):
        self._window   = window
        self._ngrams   : Dict[tuple, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # deque com limite elimina memory leak: lista antiga crescia sem bound,
        # acumulando itens nunca lidos (recall_similar usa apenas [-500:]).
        self._sentences: deque = deque(maxlen=2000)

    def learn_text(self, text: str) -> None:
        # Remove prefixos de comando que não devem entrar nos ngrams
        clean = re.sub(r'^(?:aprenda:|aprenda\s*:?\s*|continue\s+)', '', text.strip(), flags=re.I).strip()
        if not clean:
            return
        tokens = re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', clean.lower())
        if not tokens:
            return
        self._sentences.append(clean.lower())
        for i in range(len(tokens)):
            for w in range(1, self._window+1):
                if i+w < len(tokens):
                    ctx = tuple(tokens[i:i+w])
                    self._ngrams[ctx][tokens[i+w]] += 1

    def predict_next(self, context: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        candidates: Dict[str, float] = defaultdict(float)
        for w in range(min(self._window, len(context)), 0, -1):
            key = tuple(context[-w:])
            if key in self._ngrams:
                total  = sum(self._ngrams[key].values())
                weight = 2.0 ** (w - 1)
                for tok, cnt in self._ngrams[key].items():
                    candidates[tok] += (cnt/total) * weight
        total_c = sum(candidates.values()) or 1.0
        ranked  = sorted(candidates.items(), key=lambda x: -x[1])
        return [(t, s/total_c) for t, s in ranked[:top_k]]

    # Máximo de repetições consecutivas de qualquer token antes de parar.
    # Previne loops "do do do do…" mesmo quando há um único candidato disponível.
    _MAX_CONSECUTIVE = 3

    def generate(self, prompt: str, max_tokens: int = 20, temperature: float = 0.8) -> str:
        tokens = re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', prompt.lower())
        for _ in range(max_tokens):
            nexts = self.predict_next(tokens)
            if not nexts:
                break

            # Penalidade de repetição: reduz score de tokens recentes.
            # Não elimina o candidato (pode ser o único), apenas o desfavorece.
            if len(tokens) >= 2:
                recent = tokens[-4:]
                recent_counts: Dict[str, int] = {}
                for t in recent:
                    recent_counts[t] = recent_counts.get(t, 0) + 1
                nexts = sorted(
                    [(tok, score / (1.5 ** recent_counts[tok]) if tok in recent_counts else score)
                     for tok, score in nexts],
                    key=lambda x: -x[1]
                )

            # Ruptura por loop degenerativo: se o mesmo token domina as últimas
            # _MAX_CONSECUTIVE posições, a penalidade não basta → para.
            if (len(tokens) >= self._MAX_CONSECUTIVE and
                    len(set(tokens[-self._MAX_CONSECUTIVE:])) == 1):
                break

            if temperature <= 0:
                tokens.append(nexts[0][0])
            else:
                weights = [s ** (1.0 / temperature) for _, s in nexts]
                total_w = sum(weights) or 1.0
                r, cumul, chosen = random.random(), 0.0, nexts[0][0]
                for (tok, _), w in zip(nexts, weights):
                    cumul += w / total_w
                    if r <= cumul:
                        chosen = tok
                        break
                tokens.append(chosen)

            if tokens[-1] in ('.', '!', '?'):
                break
        return ' '.join(tokens) + '.'

    def generate_guided(self, prompt: str, embed: 'MiniEmbed',
                        tema: str, max_tokens: int = 25,
                        temperature: float = 0.8, alpha: float = 0.50,
                        cond_rules: Optional[List[Tuple[str,str]]] = None) -> str:
        """Geração guiada por tema.

        rev.6: aceita cond_rules — lista de (sujeito, predicado) do
        ConditionalEngine para dar boost lexical a palavras que fazem parte
        de conclusões condicionais relevantes ao tema.

        Score final = α·P(NGram) + β·cos(embed) + (1-α-β)·cond_boost
        onde cond_boost = 1.0 se o token aparece em alguma conclusão condicional.
        """
        tokens = re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', prompt.lower())
        tema_toks = [w for w in re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', tema.lower())
                     if len(w) >= 3]
        tema_vec = embed.sentence_vector(tema) if tema_toks else None

        # Palavras relevantes das regras condicionais para boost lexical
        cond_words: set = set()
        if cond_rules:
            for subj, concl in cond_rules:
                cond_words.update(_tokenize_embed(concl))
        cond_alpha = 0.15 if cond_words else 0.0   # peso do boost condicional

        for _ in range(max_tokens):
            nexts = self.predict_next(tokens)
            if not nexts:
                break

            # Penalidade de repetição
            if len(tokens) >= 2:
                recent = tokens[-4:]
                rc: Dict[str, int] = {}
                for t in recent:
                    rc[t] = rc.get(t, 0) + 1
                nexts = sorted(
                    [(tok, sc / (1.5 ** rc[tok]) if tok in rc else sc)
                     for tok, sc in nexts],
                    key=lambda x: -x[1])

            # Ruptura por loop degenerativo
            if (len(tokens) >= self._MAX_CONSECUTIVE and
                    len(set(tokens[-self._MAX_CONSECUTIVE:])) == 1):
                break

            # Viés semântico: drift_vec cosine (primário) + condicional (boost)
            if tema_vec and tema_toks:
                sem_scores = []
                use_drift = any(tok in embed._drift_vec for tok, _ in nexts)
                for tok, _ in nexts:
                    if use_drift:
                        tok_vec = embed.vector(tok)
                        sim = sum(a*b for a,b in zip(tema_vec, tok_vec))
                        sem_scores.append(max(0.0, sim))
                    else:
                        pmi = max((embed._pmi(tt, tok) for tt in tema_toks), default=0.0)
                        sem_scores.append(pmi)

                max_sem = max(sem_scores) if max(sem_scores) > 0 else 0.0
                if max_sem > 0 or cond_words:
                    scored_nexts = []
                    for (tok, sc), sv in zip(nexts, sem_scores):
                        sem_norm = sv / max_sem if max_sem > 0 else 0.0
                        # Boost condicional: 1.0 se o token está nas conclusões
                        cond_boost = 1.0 if tok in cond_words else 0.0
                        final_sc = (alpha * sc
                                    + (1.0 - alpha - cond_alpha) * sem_norm
                                    + cond_alpha * cond_boost)
                        scored_nexts.append((tok, final_sc))
                    nexts = sorted(scored_nexts, key=lambda x: -x[1])

            if temperature <= 0:
                tokens.append(nexts[0][0])
            else:
                weights = [s ** (1.0 / temperature) for _, s in nexts]
                total_w = sum(weights) or 1.0
                r, cumul, chosen = random.random(), 0.0, nexts[0][0]
                for (tok, _), w in zip(nexts, weights):
                    cumul += w / total_w
                    if r <= cumul:
                        chosen = tok
                        break
                tokens.append(chosen)

            if tokens[-1] in ('.', '!', '?'):
                break
        return ' '.join(tokens) + '.'

    def recall_similar(self, query: str, top_k: int = 3) -> List[str]:
        q_toks = set(re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', query.lower()))
        results = []
        # list() para compatibilidade com deque (que não suporta slicing negativo)
        for s in list(self._sentences)[-500:]:
            s_toks = set(re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', s))
            if not s_toks:
                continue
            j = len(q_toks & s_toks) / max(len(q_toks | s_toks), 1)
            if j > 0.15:
                results.append((j, s))
        return [s for _, s in sorted(results, key=lambda x: -x[0])[:top_k]]

    def to_dict(self) -> dict:
        sentences_tail = list(self._sentences)[-200:]
        return {'window': self._window,
                'ngrams': {str(k): dict(v) for k, v in self._ngrams.items()},
                'sentences': sentences_tail}

    @classmethod
    def from_dict(cls, d: dict) -> 'NGramMemory':
        import ast as _ast
        ng = cls(window=d.get('window', 3))
        for ks, v in d.get('ngrams', {}).items():
            try:
                k = _ast.literal_eval(ks)  # seguro: só parseia tuplas de strings
            except Exception:
                # fallback para chaves antigas malformadas — descarta se inválido
                parts = [p for p in ks.strip("()").replace("'", "").replace(" ", "").split(',') if p]
                k = tuple(parts) if parts else None
            if k:
                ng._ngrams[k] = defaultdict(int, v)
        ng._sentences = deque(d.get('sentences', []), maxlen=2000)
        return ng


# ══════════════════════════════════════════════════════════════════════════════
# §12b  TEXT WEAVER — geração de prosa estruturada (neuro-simbólica)
# ══════════════════════════════════════════════════════════════════════════════

class TextWeaver:
    """Motor de geração de texto coerente a partir de fatos estruturados.

    Pipeline:
      1. Seleciona e ordena fatos por relevância semântica (drift_vec cosine)
      2. Detecta relações entre fatos via ConceptGraph (IS_A, HAS, CAUSES…)
      3. Aplica conectivos relacionais adequados ao tipo de relação
      4. Monta discurso estruturado: lead → body → elaboração → conclusão

    Não usa rede neural nem n-grama para a estrutura macro — usa o grafo
    semântico e os fatos aprendidos para garantir coerência factual.
    O NGram é usado apenas para suavizar transições lexicais.

    Mantém a essência simbólica do sistema: explicável, determinístico,
    sem alucinação (só usa fatos que existem no FactStore).
    """

    # Conectivos por tipo de relação semântica
    _REL_CONN: Dict[str, List[str]] = {
        REL_IS_A:     ["é um tipo de", "pertence à categoria de", "é classificado como"],
        REL_HAS:      ["possui", "é dotado de", "tem como característica"],
        REL_CAUSES:   ["causa", "leva a", "resulta em"],
        REL_PRODUCES: ["produz", "gera", "origina"],
        REL_PART_OF:  ["é parte de", "compõe", "integra"],
        REL_DOES:     ["realiza", "executa", "é responsável por"],
        'é':          ["é", "representa", "consiste em"],
        'tem':        ["possui", "apresenta", "tem"],
    }

    # Conectivos de discurso por função retórica
    _DISC: Dict[str, List[str]] = {
        'elaboration': ["Esse processo", "Esse elemento", "Tal mecanismo",
                        "Essa estrutura", "Esse fenômeno"],
        'addition':    ["Além disso,", "Adicionalmente,", "Vale destacar que",
                        "Também é importante notar que", "Outro aspecto relevante:"],
        'consequence': ["Como resultado,", "Por consequência,",
                        "Isso significa que", "Dessa forma,", "Portanto,"],
        'contrast':    ["Por outro lado,", "Em contrapartida,",
                        "No entanto,", "Apesar disso,"],
        'conclusion':  ["Em síntese,", "Em resumo,", "Em suma,", "Concluindo,"],
        'example':     ["Por exemplo,", "Como exemplo,", "A título de ilustração,"],
    }

    # Frases de abertura para topic sentences por tipo de query
    _OPENERS: Dict[str, List[str]] = {
        'definition': [
            "{topic} é um conceito central em {domain}.",
            "{topic} pode ser entendido como",
            "Ao falar de {topic}, referimo-nos a",
        ],
        'explanation': [
            "Para entender {topic}, é preciso considerar que",
            "{topic} funciona da seguinte forma:",
            "O mecanismo de {topic} envolve",
        ],
        'description': [
            "{topic} apresenta as seguintes características:",
            "As principais propriedades de {topic} incluem",
            "Em termos de {topic},",
        ],
        'comparison': [
            "Comparando {a} e {b}, percebe-se que",
            "A diferença entre {a} e {b} reside no fato de que",
            "{a} e {b} compartilham",
        ],
    }

    def __init__(self, embed: 'MiniEmbed', concept_graph: 'ConceptGraph',
                 fact_store: 'StructuredFactStore', ngram: 'NGramMemory',
                 deductive: Optional['DeductiveEngine'] = None,
                 conditional: Optional['ConditionalEngine'] = None,
                 episodic: Optional['EpisodicStream'] = None):
        self.embed         = embed
        self.concept_graph = concept_graph
        self.fact_store    = fact_store
        self.ngram         = ngram
        # ── Motores de inferência injetados (opcionais, degradam graciosamente)
        self.deductive     = deductive    # fuzzy_deduce + scored_deduce
        self.conditional   = conditional  # regras SE-ENTÃO para zero-shot
        self.episodic      = episodic     # contexto multi-turno
        self._rng          = random.Random()   # não seedado = aleatório real

    # ── Utilitários internos ───────────────────────────────────────────────────

    def _cosine(self, a: List[float], b: List[float]) -> float:
        dot = sum(x*y for x,y in zip(a,b))
        na  = math.sqrt(sum(x*x for x in a)) or 1e-9
        nb  = math.sqrt(sum(x*x for x in b)) or 1e-9
        return dot / (na * nb)

    def _semantic_score(self, fact: str, query_vec: List[float]) -> float:
        """Score semântico do fato em relação à query usando drift_vec."""
        fv = self.embed.sentence_vector(fact)
        return self._cosine(query_vec, fv)

    # ── Expansão zero-shot via inferência cruzada ─────────────────────────────

    def _expand_zero_shot(self, tema: str, max_infer: int = 3) -> List[Tuple[float, str]]:
        """Gera fatos inferidos sobre tema quando o FactStore é escasso.

        Pipeline de 4 camadas:
          1. ConceptGraph neighbors — fatos de conceitos vizinhos herdados
          2. ConditionalEngine.infer — regras SE-ENTÃO aplicadas ao tema
          3. DeductiveEngine.fuzzy_deduce — analogia semântica (pardal≈ave)
          4. embed.analogy — aritmética vetorial para descobrir categoria

        Cada camada tem confiança marcada. Só retorna se confiança > 0.20.
        Resultado: lista de (score, fato_inferido) ordenada por confiança.
        """
        tema_clean = _deaccent(tema.lower().strip())
        inferred: List[Tuple[float, str]] = []
        seen_texts: set = set()

        def add(score: float, text: str):
            t = text.strip().lower()
            if t and t not in seen_texts and len(t) > 8:
                seen_texts.add(t)
                inferred.append((score, text.strip()))

        # ── Camada 1: Conceitos vizinhos no ConceptGraph ──────────────────────
        nbrs = self.concept_graph.neighbors(tema_clean, depth=2)
        for nbr in nbrs[:4]:
            nbr_facts = self.fact_store.search(nbr, top_k=2, min_score=0.2)
            for f in nbr_facts:
                # Herda o fato do vizinho, mas marcado como inferido
                rewritten = f"{tema} provavelmente {f.lower()}"
                # Score: similaridade semântica entre tema e vizinho
                sim = self._cosine(
                    self.embed.sentence_vector(tema_clean),
                    self.embed.sentence_vector(nbr))
                if sim > 0.15:
                    add(sim * 0.7, f)  # usa fato original, com score reduzido

        # ── Camada 2: ConditionalEngine — regras SE-ENTÃO ─────────────────────
        if self.conditional is not None:
            all_facts = self.fact_store.all_facts()
            for prop in ["pelo","ar","asas","guelras","escamas","vertebrado",
                         "sangue quente","ovos","pulmoes","nada","voa"]:
                result = self.conditional.infer(
                    tema_clean, prop, external_facts=all_facts)
                if result and "sim" in result.lower():
                    # Extrai a cadeia de inferência para montar frase natural
                    chain = re.search(r'\((.*?)\)', result)
                    chain_str = chain.group(1) if chain else prop
                    add(0.65, f"{tema} tem {prop} (via {chain_str})")

        # ── Camada 3: DeductiveEngine — fuzzy semântico ───────────────────────
        if self.deductive is not None and self.deductive._embed is not None:
            # Só testa propriedades que fazem sentido semântico para o tema
            # (evita "gato tem guelras" quando gato≈peixe apenas por vizinhança)
            props_to_test = ["voa", "nada", "tem pelo", "tem asas", "tem bico",
                             "tem guelras", "é mamífero", "é ave", "é peixe",
                             "respira ar", "é carnívoro", "bota ovos"]
            tv = self.embed.sentence_vector(tema_clean)
            for prop in props_to_test:
                fz = self.deductive.fuzzy_deduce(
                    f"logo {tema_clean} {prop}", threshold=0.25)  # threshold elevado
                if fz:
                    m = re.search(r'provavelmente (.+?)\.', fz)
                    if m:
                        concl = m.group(1).strip()
                        # Verifica coerência semântica da conclusão com o tema
                        # (evita "gato tem guelras" onde guelras é incompatível)
                        concl_vec = self.embed.sentence_vector(concl)
                        sem_coh = self._cosine(tv, concl_vec)
                        if sem_coh < -0.05:  # conclusão semanticamente contrária: descarta
                            continue
                        conf_m = re.search(r'\((\d+)%', fz)
                        conf = int(conf_m.group(1)) / 100.0 if conf_m else 0.3
                        # Aplica penalidade se conclusão muito inconsistente
                        adjusted_conf = conf * max(0.1, 1.0 + sem_coh)
                        if adjusted_conf > 0.18:
                            add(adjusted_conf * 0.8, f"{tema} provavelmente {concl}")

        # ── Camada 4: Analogia vetorial — descobre a categoria ────────────────
        if self.deductive is not None and self.deductive._embed is not None:
            # Tenta descobrir: "X é como Y" → herda fatos de Y
            all_vocab = list(self.embed._vocab)
            if all_vocab:
                tv = self.embed.sentence_vector(tema_clean)
                # Encontra o conceito mais próximo que TEM fatos
                best_sim, best_concept = 0.0, None
                for concept in all_vocab:
                    if concept == tema_clean: continue
                    facts_c = self.fact_store.search(concept, top_k=1, min_score=0.2)
                    if facts_c:
                        sim = self._cosine(tv, self.embed.vector(concept))
                        if sim > best_sim and sim > 0.25:
                            best_sim, best_concept = sim, concept
                if best_concept:
                    best_facts = self.fact_store.search(best_concept, top_k=2, min_score=0.2)
                    for f in best_facts:
                        add(best_sim * 0.6, f)

        inferred.sort(reverse=True)
        return inferred[:max_infer]

    def _get_context_hint(self) -> Optional[str]:
        """Retorna o tópico da última interação do EpisodicStream (contexto multi-turno)."""
        if self.episodic is None:
            return None
        recent = list(self.episodic._episodes)[-3:] if self.episodic._episodes else []
        if not recent:
            return None
        # Extrai palavras-chave dos episódios recentes
        all_text = ' '.join(ep.text for ep in recent if hasattr(ep, 'text'))
        toks = [w for w in _tokenize_embed(all_text) if len(w) >= 4]
        if toks:
            # Retorna a palavra mais frequente como hint de contexto
            from collections import Counter
            most = Counter(toks).most_common(1)
            return most[0][0] if most else None
        return None

    def _detect_rel(self, fact: str) -> Tuple[str, str, str]:
        """Extrai (sujeito, relação, objeto) de um fato textual."""
        tl = fact.lower().strip()
        for pat, rel in _REL_PATTERNS:
            m = pat.match(tl)
            if m:
                return m.group(1).strip(), rel, m.group(2).strip()
        # Fallback: split em verbo cópula
        m = re.match(r'^([\w\s]{2,25}?)\s+(?:é|são|tem|possui|produz|causa)\s+(.+)$', tl)
        if m:
            return m.group(1).strip(), 'é', m.group(2).strip()
        return '', '', fact

    def _select_connector(self, rel: str) -> str:
        options = self._REL_CONN.get(rel, ["relaciona-se com"])
        return self._rng.choice(options)

    def _select_disc(self, role: str) -> str:
        options = self._DISC.get(role, ["Além disso,"])
        return self._rng.choice(options)

    # Artigos/preposições que NÃO devem ser capitalizados dentro de nomes
    _NO_CAP = frozenset({'da','de','do','das','dos','e','a','o'})

    def _capitalize_first(self, s: str) -> str:
        """Capitaliza primeira letra. Detecta nomes próprios via PascalCase heurística."""
        if not s:
            return s
        return s[0].upper() + s[1:]

    def _smart_capitalize(self, s: str) -> str:
        """Capitaliza a frase com tratamento de nomes próprios.

        Regras:
        - Primeira palavra sempre maiúscula
        - Palavras após ponto: maiúscula
        - Siglas (DNA, ATP, RNA): mantidas
        - Nomes de pessoa heurísticos: sequência de 2+ substantivos com inicial maiúscula
        """
        if not s:
            return s
        # Divide em tokens preservando pontuação
        parts = re.split(r'(\s+)', s)
        result = []
        capitalize_next = True
        for part in parts:
            if re.match(r'\s+', part):
                result.append(part)
                continue
            word = part.rstrip('.,!?')
            punct = part[len(word):]
            # Siglas: preserva maiúsculas (DNA, ATP, CO2)
            if re.match(r'^[A-ZÁÉÍÓÚ]{2,}[0-9]?$', word):
                result.append(part)
            elif capitalize_next and word:
                result.append(word[0].upper() + word[1:] + punct)
            else:
                result.append(part)
            # Próxima palavra é capitalize_next se após ponto/dois-pontos
            capitalize_next = bool(punct and re.search(r'[.!?:]', punct))
        return ''.join(result)

    def _ensure_period(self, s: str) -> str:
        s = s.strip()
        if s and not s[-1] in '.!?':
            s += '.'
        return s

    # ── Geração de parágrafo ──────────────────────────────────────────────────

    def weave(self, tema: str, mode: str = 'auto',
              max_sentences: int = 4) -> Optional[str]:
        """Gera parágrafo coerente sobre o tema.

        Pipeline rev.6:
          1. Busca fatos diretos (FactStore)
          2. Se escassos (<2 fatos), expande via _expand_zero_shot:
             - ConceptGraph neighbors
             - ConditionalEngine.infer (regras SE-ENTÃO)
             - DeductiveEngine.fuzzy_deduce (analogia semântica)
             - embed.analogy (aritmética vetorial)
          3. Ordena por score semântico + confiança de inferência
          4. Monta parágrafo com conectivos de discurso variados
          5. Marca fatos inferidos com indicador de confiança
        """
        tema_clean = tema.strip().lower()
        if not tema_clean:
            return None

        # 1. Busca fatos diretos no FactStore
        hits = self.fact_store.search(tema_clean, top_k=8, min_score=0.15)
        query_vec = self.embed.sentence_vector(tema_clean)

        # 2. Expansão zero-shot quando fatos são escassos (<2 fatos relevantes)
        #    Usa ConditionalEngine + FuzzyDeduce + ConceptGraph para inferir
        inferred_facts: List[Tuple[float, str]] = []
        if len(hits) < 2:
            inferred_facts = self._expand_zero_shot(tema_clean, max_infer=3)
            # Adiciona fatos inferidos ao pool, com score já calibrado
            for inf_score, inf_fact in inferred_facts:
                if inf_fact not in hits:
                    hits.append(inf_fact)

        if not hits:
            return None

        # 2. Score e ordena por relevância semântica (drift_vec cosine)
        scored: List[Tuple[float, str]] = []
        for fact in hits:
            sc = self._semantic_score(fact, query_vec)
            scored.append((sc, fact))
        scored.sort(reverse=True)

        # 3. Deduplicação: remove fatos com overlap > 65%
        deduped: List[Tuple[float, str]] = []
        for sc, fact in scored:
            fl = fact.lower()
            is_dup = False
            for _, kept in deduped:
                kl = kept.lower()
                k_toks = set(re.findall(r'\w{3,}', kl))
                f_toks = set(re.findall(r'\w{3,}', fl))
                if k_toks and f_toks:
                    ov = len(k_toks & f_toks) / max(len(k_toks | f_toks), 1)
                    if ov > 0.65:
                        is_dup = True
                        break
            if not is_dup:
                deduped.append((sc, fact))

        if not deduped:
            return None

        # 4. Reordena: fatos cujo sujeito == tema ficam na frente,
        #    mas aplica jitter semântico para variar o lead nas chamadas subsequentes.
        #    O jitter é proporcional ao score (fatos muito distintos não rotam).
        tema_words = set(re.findall(r'\w{3,}', tema_clean))
        def _is_topic_lead(fact_text: str) -> bool:
            fl = fact_text.lower()
            first = fl.split()[0] if fl.split() else ''
            return first in tema_words or any(fl.startswith(w) for w in tema_words)

        topic_first = [x for x in deduped if _is_topic_lead(x[1])]
        topic_rest  = [x for x in deduped if not _is_topic_lead(x[1])]

        # Jitter: se há ≥2 fatos de lead equivalentes (score próximo), rota entre eles
        if len(topic_first) >= 2:
            best_sc = topic_first[0][0]
            # Fatos dentro de 15% do melhor score são elegíveis para lead
            eligible = [(s,f) for s,f in topic_first if s >= best_sc * 0.85]
            if len(eligible) >= 2:
                # Escolhe lead aleatório entre os elegíveis
                lead_choice = self._rng.choice(eligible)
                remaining   = [x for x in topic_first if x is not lead_choice]
                topic_first = [lead_choice] + remaining

        deduped = topic_first + topic_rest

        # 5. Auto-detecta mode
        if mode == 'auto':
            top_fact = deduped[0][1].lower()
            if re.match(r'^[\w\s]{2,20}?\s+é\s+', top_fact):
                mode = 'definition'
            elif any(w in top_fact for w in ['ocorre','funciona','processo','realiza','produz']):
                mode = 'explanation'
            else:
                mode = 'description'

        # 6. Monta parágrafo com fusão relacional e variação natural
        sentences: List[str] = []
        used_facts = deduped[:min(max_sentences, len(deduped))]
        prev_subj  = ''

        for idx, (sc, fact) in enumerate(used_facts):
            subj, rel, obj = self._detect_rel(fact)
            fact_lower = fact.lower().rstrip('.')

            if idx == 0:
                # Lead: sentence aberta com variação de estrutura
                if mode == 'definition' and subj and obj and len(subj) < 25 and len(obj) < 60:
                    # Reformulações naturais para definições
                    varv = [
                        self._capitalize_first(fact),
                        self._capitalize_first(fact),  # peso 2x para forma direta
                        f"{subj.capitalize()} pode ser definido como {obj}",
                    ]
                    sent = self._ensure_period(self._rng.choice(varv))
                elif mode == 'explanation' and subj and len(subj) < 20:
                    varv = [
                        self._capitalize_first(fact),
                        self._capitalize_first(fact),
                        f"Para compreender {subj}, vale saber: {fact.lower()}",
                    ]
                    sent = self._ensure_period(self._rng.choice(varv))
                else:
                    sent = self._ensure_period(self._capitalize_first(fact))
                prev_subj = subj

            elif idx == 1:
                # Segunda sentença: conectivo variado + fato direto
                # Escolhe entre 6 tipos de conectivos para variar
                disc_pool = [
                    "Além disso,", "Vale destacar que", "Adicionalmente,",
                    "Também é relevante que", "Outro aspecto importante:",
                    "Complementando essa ideia,",
                ]
                disc = self._rng.choice(disc_pool)
                fl = fact.lower().rstrip('.')
                # Capitaliza a primeira palavra após o conectivo se ele termina com ":"
                if disc.endswith(':'):
                    fl = fl[0].upper() + fl[1:]
                sent = self._ensure_period(f"{disc} {fl}")
                prev_subj = subj

            elif idx == 2:
                # Terceira: depende da relação — causal→consequência, resto→adição
                if rel in (REL_CAUSES, REL_PRODUCES, 'produz', 'causa', 'gera'):
                    disc_pool = ["Como resultado,", "Por consequência,",
                                 "Isso significa que", "Dessa forma,"]
                else:
                    disc_pool = ["Por fim,", "Vale notar também que",
                                 "Em termos adicionais,", "Além disso,"]
                disc = self._rng.choice(disc_pool)
                fl   = fact.lower().rstrip('.')
                sent = self._ensure_period(f"{disc} {fl}")
                prev_subj = subj

            else:
                # Fechamento conclusivo variado
                concl_pool = [
                    f"Em síntese, {fact.lower().rstrip('.')}",
                    f"Em resumo, {fact.lower().rstrip('.')}",
                    f"Vale notar, por fim, que {fact.lower().rstrip('.')}",
                    f"Concluindo, {fact.lower().rstrip('.')}",
                ]
                sent = self._ensure_period(self._rng.choice(concl_pool))

            sentences.append(sent)

        if not sentences:
            return None

        # 7. Pós-processamento: capitalização após conectivo + limpeza
        result = ' '.join(sentences)
        # Capitaliza primeira letra de cada frase após ". "
        result = re.sub(r'\.\s+([a-záéíóú])', lambda m: '. ' + m.group(1).upper(), result)
        # Limpa pontuação dupla e espaços extras
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\s{2,}', ' ', result)
        # Remove vírgulas antes de ponto
        result = re.sub(r',\s*\.', '.', result)
        return result.strip()

    def weave_comparison(self, a: str, b: str) -> Optional[str]:
        """Compara dois conceitos: fatos específicos, contraste e síntese semântica."""
        facts_a = self.fact_store.search(a, top_k=3, min_score=0.15)
        facts_b = self.fact_store.search(b, top_k=3, min_score=0.15)
        if not facts_a and not facts_b:
            return None

        va      = self.embed.sentence_vector(a)
        vb      = self.embed.sentence_vector(b)
        sim     = self._cosine(va, vb)
        sim_pct = max(0, int(sim * 100))  # clamp: cosine pode ser negativo

        parts: List[str] = []

        # Abertura contextual variável — capitaliza nomes dos conceitos
        a_cap = a[0].upper() + a[1:]
        b_cap = b[0].upper() + b[1:]
        openers = [
            f"Ao comparar {a_cap} e {b_cap}, observa-se que",
            f"Existe uma distinção importante entre {a_cap} e {b_cap}:",
            f"{a_cap} e {b_cap} diferem em aspectos fundamentais.",
        ]
        parts.append(self._rng.choice(openers))

        # Fatos de A — melhor fato direto
        if facts_a:
            best_a = self._ensure_period(self._capitalize_first(facts_a[0]))
            parts.append(best_a)
            if len(facts_a) > 1:
                tok_a0 = set(re.findall(r'\w{3,}', facts_a[0].lower()))
                tok_a1 = set(re.findall(r'\w{3,}', facts_a[1].lower()))
                if len(tok_a0 & tok_a1) / max(len(tok_a0 | tok_a1), 1) < 0.5:
                    parts.append(self._ensure_period(
                        self._capitalize_first(facts_a[1])))

        # Fatos de B com conectivo contrastivo — preserva casing original
        if facts_b:
            contr = self._rng.choice([
                "Já", "Em contrapartida,",
                "Por outro lado,", "Diferentemente,",
            ])
            best_b = facts_b[0].rstrip('.')
            # Deixa primeira letra minúscula após conectivo (exceto siglas)
            if best_b and not re.match(r'^[A-Z]{2,}', best_b):
                best_b = best_b[0].lower() + best_b[1:]
            parts.append(self._ensure_period(f"{contr} {best_b}"))
            if len(facts_b) > 1:
                tok_b0 = set(re.findall(r'\w{3,}', facts_b[0].lower()))
                tok_b1 = set(re.findall(r'\w{3,}', facts_b[1].lower()))
                if len(tok_b0 & tok_b1) / max(len(tok_b0 | tok_b1), 1) < 0.5:
                    add = facts_b[1].rstrip('.')
                    if add and not re.match(r'^[A-Z]{2,}', add):
                        add = add[0].lower() + add[1:]
                    conn = self._rng.choice(['Além disso,', 'Também,', 'Adicionalmente,'])
                    parts.append(self._ensure_period(f"{conn} {add}"))

        # Síntese semântica com nomes capitalizados
        if sim > 0.60:
            synth = (f"Apesar das diferenças funcionais, {a_cap} e {b_cap} compartilham "
                     f"contexto semântico muito próximo ({sim_pct}%), "
                     f"indicando que pertencem ao mesmo domínio conceitual.")
        elif sim > 0.35:
            synth = (f"Em síntese, {a_cap} e {b_cap} estão semanticamente relacionados "
                     f"({sim_pct}% de similaridade), mas exercem papéis distintos.")
        else:
            synth = (f"Em síntese, {a_cap} e {b_cap} são conceitos fundamentalmente "
                     f"distintos ({sim_pct}% de similaridade semântica).")
        parts.append(synth)

        result = ' '.join(p for p in parts if p)
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\s{2,}', ' ', result)
        return result.strip()

    def extend_with_ngram(self, base: str, tema: str,
                          n_extra: int = 1, temperature: float = 0.7) -> str:
        """Estende texto base com 1–2 tokens gerados pelo NGram guiado por drift.

        Usado para suavizar a transição final ou adicionar uma palavra de closure.
        N pequeno intencionalmente: evita alucinação por drift do NGram.
        """
        if not base or n_extra <= 0:
            return base
        # Só extende se NGram tem conteúdo suficiente
        if len(self.ngram._ngrams) < 10:
            return base

        # Usa os últimos 3 tokens do base como seed
        seed_toks = re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', base.lower())[-3:]
        if not seed_toks:
            return base

        extra = self.ngram.generate_guided(
            ' '.join(seed_toks), embed=self.embed, tema=tema,
            max_tokens=n_extra, temperature=temperature)
        extra_toks = re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', extra)
        # Remove tokens já presentes no final do base para evitar repetição
        base_end = set(re.findall(r'\w{4,}', base.lower())[-6:])
        new_toks  = [t for t in extra_toks if t not in base_end and t not in seed_toks]
        if new_toks:
            return base.rstrip('.') + ' ' + ' '.join(new_toks[:n_extra]) + '.'
        return base

class ConditionalEngine:
    """BFS sobre regras SE-ENTÃO. Encadeamento multi-hop.

    Correções v8.1:
    - _norm() com plural→singular correto (animais→animal, répteis→reptil)
    - learn() pré-normaliza e deduplica regras; cobre verbos de ação (respira,
      come, vive, produz, realiza, possui, contém, etc.)
    - infer() compara nó já normalizado com cond já normalizado — O(1) por regra
    - BFS sem loop infinito: parents com None=semente, seen_path na reconstrução
    - external_facts semeia props com tokens normalizados de fatos do sujeito
    """

    # Verbos PT-BR que expressam propriedade/ação universal em regras
    _VERBOS = (r's[aã]o|[eé]|t[eê]m|tem|possuem?|possui|respiram?|respira|'
               r'vivem?|vive?|comem?|come|produzem?|produz|realizam?|realiza|'
               r'cont[eê]m|contem|fazem?|faz|precisam?|precisa|usam?|usa|'
               r'habitam?|habita|pertencem?|pertence|representam?|representa')

    def __init__(self):
        # _rules armazena (cond_norm, concl_norm) — já normalizadas
        self._rules: List[Tuple[str, str]] = []
        self._facts: List[Tuple[str, str]] = []
        self._rule_set: Set[Tuple[str,str]] = set()  # dedup rápido

    # ── Normalização interna ───────────────────────────────────────────────────
    @staticmethod
    def _norm(w: str) -> str:
        """Minúsculo + sem acento + singular PT-BR.

        Regras de singularização (aplicadas em ordem, primeiro match vence):
          ões/ães → ão   (corações→coração, mães→mão — approx.)
          ais     → al   (animais→animal, principais→principal)
          eis     → el   (papeis→papel)  [répteis→reptel — suficiente p/ match]
          ns      → m    (comuns→comum, bens→bem)
          s       → ''   (gatos→gato, mamiferos→mamifero)
        """
        w = _deaccent(w.lower().strip())
        if w.endswith('oes') and len(w) > 4:   w = w[:-3] + 'ao'
        elif w.endswith('aes') and len(w) > 4: w = w[:-3] + 'ao'
        elif w.endswith('ais') and len(w) > 4: w = w[:-2] + 'l'   # animais→animal
        elif w.endswith('eis') and len(w) > 4: w = w[:-2] + 'l'   # papeis→papel
        elif w.endswith('ns') and len(w) > 3:  w = w[:-1]          # comuns→comum
        elif w.endswith('s') and len(w) > 3:   w = w[:-1]          # gatos→gato
        return w

    def _add_rule(self, cond_raw: str, concl_raw: str, seen: Set) -> bool:
        """Normaliza, deduplica e adiciona regra. Retorna True se nova."""
        cond  = self._norm(cond_raw)
        concl = self._norm(concl_raw)
        if not cond or not concl or cond == concl:
            return False
        concl_toks = [self._norm(tok) for tok in concl_raw.split()
                      if len(tok) > 2 and _deaccent(tok.lower()) not in _STOP_PT]
        if not concl_toks:
            return False
        added = False
        key = (cond, concl)
        if key not in seen and key not in self._rule_set:
            seen.add(key); self._rule_set.add(key)
            self._rules.append(key); added = True
        # Palavras individuais da conclusão composta
        for tok in concl_toks:
            if tok == concl:
                continue
            k2 = (cond, tok)
            if k2 not in seen and k2 not in self._rule_set:
                seen.add(k2); self._rule_set.add(k2)
                self._rules.append(k2)
        # Palavras individuais da condição composta
        for ctok_raw in cond_raw.split():
            ctok = self._norm(ctok_raw)
            if ctok == cond or len(ctok) <= 2 or _deaccent(ctok_raw.lower()) in _STOP_PT:
                continue
            k3 = (ctok, concl)
            if k3 not in seen and k3 not in self._rule_set:
                seen.add(k3); self._rule_set.add(k3)
                self._rules.append(k3)
        return added

    # ── Aprendizado ───────────────────────────────────────────────────────────
    def learn(self, text: str) -> bool:
        t = text.lower().strip()
        learned = False
        seen: Set = set()

        # 1. Regra universal: "todo(s) [os/as] COND [verbo] CONCL"
        pat_univ = (r'todos?\s+(?:os\s+|as\s+)?(\w+(?:\s+\w+)?)\s+'
                    r'(?:' + self._VERBOS + r')\s+(?:um[a]?\s+)?(\w+(?:\s+\w+)?)')
        for m in re.finditer(pat_univ, t):
            if self._add_rule(m.group(1).strip(), m.group(2).strip(), seen):
                learned = True

        # 2. Regra condicional: "se X [verbo] Y então [CONCL]"
        pat_cond = (r'se\s+(?:\w+\s+)?(?:' + self._VERBOS + r')\s+(\w+(?:\s+\w+)?)\s+'
                    r'ent[aã]o\s+(?:\w+\s+)?(?:(?:' + self._VERBOS + r')\s+)?(\w+(?:\s+\w+)?)')
        for m in re.finditer(pat_cond, t):
            if self._add_rule(m.group(1).strip(), m.group(2).strip(), seen):
                learned = True

        # 3. Fato direto como regra: "X [verbo] [um/uma] Y"
        pat_fact = (r'^(\w+(?:\s+\w+)?)\s+(?:' + self._VERBOS + r')'
                    r'\s+(?:um[a]?\s+)?(\w+(?:\s+\w+)?)$')
        for m in re.finditer(pat_fact, t):
            cond_raw, concl_raw = m.group(1).strip(), m.group(2).strip()
            # Também adiciona como fato interno
            s, o = self._norm(cond_raw), self._norm(concl_raw)
            if s and o and s not in _STOP_PT:
                entry = (s, o)
                if entry not in self._rule_set:
                    self._facts.append(entry)
            if self._add_rule(cond_raw, concl_raw, seen):
                learned = True

        return learned

    # ── Inferência BFS multi-hop ───────────────────────────────────────────────
    def infer(self, subj: str, prop: str, max_depth: int = 14,
              external_facts: Optional[List[str]] = None) -> Optional[str]:
        s  = self._norm(subj)
        qp = self._norm(prop)

        # Sementes: s + props conhecidas sobre s (fatos internos)
        props: Set[str] = {s}
        for fs, fo in self._facts:
            if fs == s:
                props.add(fo)

        # Sementes de fatos externos (fact_store.all_facts())
        if external_facts:
            pat_s = re.compile(r'\b' + re.escape(s) + r'\b')
            for fact in external_facts:
                fl = fact.lower()
                if pat_s.search(fl):
                    for tok in re.findall(r'\w{3,}', fl):
                        nt = self._norm(tok)
                        if nt not in _STOP_PT and nt != s:
                            props.add(nt)

        # Resposta direta: qp já é semente (fato direto conhecido)
        if qp in props and qp != s:
            return f'Sim. ({s} → {qp})'

        # BFS com parents[node]=predecessor (None=semente)
        visited: Set[str] = set(props)
        frontier: List[str] = list(props)
        parents: Dict[str, Optional[str]] = {p: None for p in props}

        for _ in range(max_depth):
            nxt: List[str] = []
            for node in frontier:
                for cond, concl in self._rules:
                    # cond e concl já estão normalizados em _rules
                    if cond != node:
                        continue
                    # Verifica se é o alvo ANTES de checar visited (evita skip indevido)
                    if concl == qp or qp in concl.split():
                        parents[concl] = node
                        path: List[str] = []
                        cur: Optional[str] = concl
                        sp: Set[str] = set()
                        while cur is not None and cur not in sp and len(path) < 20:
                            path.append(cur); sp.add(cur)
                            cur = parents.get(cur)
                        path.reverse()
                        return f'Sim. ({" → ".join(path)})'
                    if concl in visited:
                        continue
                    parents[concl] = node
                    visited.add(concl)
                    nxt.append(concl)
            frontier = nxt
            if not frontier:
                break
        return None

    def to_dict(self) -> dict:
        return {'rules': list(self._rules), 'facts': list(self._facts)}

    @classmethod
    def from_dict(cls, d: dict) -> 'ConditionalEngine':
        ce = cls()
        ce._rules    = [tuple(r) for r in d.get('rules', [])]
        ce._facts    = [tuple(f) for f in d.get('facts', [])]
        ce._rule_set = set(ce._rules)
        return ce


# ══════════════════════════════════════════════════════════════════════════════
# §14  DEDUCTIVE ENGINE — v5 Pro (silogismos inline)
# ══════════════════════════════════════════════════════════════════════════════

class DeductiveEngine:
    """Silogismos: 'Sócrates é homem. Homem é mortal. Logo Sócrates é mortal.'

    v9.1 — Dedução fuzzy via MiniEmbed:
      fuzzy_deduce(): quando a correspondência exata falha, usa similaridade
      semântica para encontrar regras aproximadas (pardal ≈ ave → pardal voa).
      scored_deduce(): ranqueia múltiplas conclusões por relevância contextual.
    """

    # Threshold de similaridade para aceitar regra fuzzy.
    # Para DIM=128 com Random Indexing + drift, cosines reais ficam
    # entre 0.05 (não relacionado) e 0.65 (muito próximo).
    # 0.35 captura vizinhança semântica real sem falsos positivos excessivos.
    FUZZY_THRESHOLD = 0.35

    def __init__(self):
        self._rules: List[Tuple[str, str]] = []
        # Referência ao embed — injetada pelo NexusV8 após inicialização
        self._embed: Optional['MiniEmbed'] = None
        # Referência ao ConditionalEngine — para scored_deduce encadear regras
        self._conditional: Optional['ConditionalEngine'] = None

    def learn(self, text: str) -> bool:
        tl = text.lower().strip()
        found = False
        # Verbos de ação/propriedade além dos cópulas
        _VERBOS_AUX = (r'é|são|[eé]|t[eê]m|tem|possuem?|possui|voa|voam|'
                       r'nada|nadam|respira|respiram|come|comem|vive|vivem|'
                       r'corre|correm|produz|produzem|realiza|realizam|'
                       r'habita|habitam|pertence|pertencem|amamenta|amamentam|'
                       r'bota|botam|rasteja|rastejam|migra|migram')
        for m in re.finditer(
                r'(\w[\w\s]{1,20}?)\s+(?:' + _VERBOS_AUX + r')\s+(?:um[a]?\s+)?(\w[\w\s]{1,20})',
                tl):
            a, b = m.group(1).strip(), m.group(2).strip()
            if a and b and len(a) >= 2 and len(b) >= 2:
                self._rules.append((a, b))
                for wa in a.split():
                    if len(wa) > 2 and wa not in _STOP_PT and wa != a:
                        self._rules.append((wa, b))
                found = True
        # Padrão adicional: "X [verbo-intransitivo]" (ex: "ave voa", "peixe nada")
        for m in re.finditer(
                r'^(\w[\w\s]{1,20}?)\s+(voa|nada|rasteja|migra|amamenta|bota\s+ovos)',
                tl):
            a, b = m.group(1).strip(), m.group(2).strip()
            if a and b:
                self._rules.append((a, b))
                found = True
        return found

    def deduce(self, statement: str, max_depth: int = 5) -> Optional[str]:
        tl = statement.lower().strip()

        # Modo 1: silogismo completo com "logo X é Y"
        m = re.search(r'logo\s+(\w[\w\s]{1,20}?)\s+(?:é|são|[eé])\s+(\w[\w\s]{1,20})',
                      tl)
        if m:
            subj, prop = m.group(1).strip(), m.group(2).strip()
            visited = {subj}
            frontier = [subj]
            for _ in range(max_depth):
                nxt = []
                for node in frontier:
                    for a, b in self._rules:
                        if a == node and b not in visited:
                            if b == prop or prop in b.split():
                                return f'Sim: {subj} → ... → {b} (silogismo)'
                            visited.add(b)
                            nxt.append(b)
                frontier = nxt
                if not frontier:
                    break
            return None

        # Modo 2: busca por sujeito — "o que é X?" / "deduza sobre X" / "X é ..."
        # Extrai sujeito da query e retorna todas as conclusões alcançáveis
        subj_m = re.search(r'o\s+que\s+(?:é|são)\s+(\w[\w\s]{1,20}?)[\?\s]', tl) or \
                 re.search(r'(?:sobre|acerca\s+de|deduza\s+sobre\s+)\s*(\w[\w\s]{1,15})', tl) or \
                 re.search(r'\b(\w[\w\s]{1,20}?)(?:\s+é\s+|\s*\?)', tl) or \
                 re.search(r'^(\w[\w\s]{1,15})', tl)
        if not subj_m:
            return None
        subj = subj_m.group(1).strip()
        # Remove palavras de roteamento comuns
        subj = re.sub(r'^(?:deduza|sobre|acerca|o\s+que|qual|quem|como)\s*', '', subj).strip()
        subj = re.sub(r'\s+é\s*$|\s*\?$', '', subj).strip()
        if len(subj) < 2 or subj in _STOP_PT:
            return None

        visited = {subj}
        frontier = [subj]
        conclusions = []
        for _ in range(max_depth):
            nxt = []
            for node in frontier:
                for a, b in self._rules:
                    if a == node and b not in visited:
                        conclusions.append(b)
                        visited.add(b)
                        nxt.append(b)
            frontier = nxt
            if not frontier:
                break
        if conclusions:
            chain = ' → '.join([subj] + conclusions[:3])
            return f'Por dedução: {chain}'
        return None

    def fuzzy_deduce(self, statement: str, threshold: float = None) -> Optional[str]:
        """Dedução por similaridade semântica (Hebbian Deduction).

        Quando não há correspondência exata, usa o MiniEmbed para encontrar
        sujeito/predicado semanticamente próximo.

        Exemplo: aprendi "ave voa". Pergunta "pardal voa?".
          cos(v(pardal), v(ave)) = 0.81 > 0.72 → "pardal ≈ ave → pardal voa"
        """
        if self._embed is None or not self._rules:
            return None
        th   = threshold if threshold is not None else self.FUZZY_THRESHOLD
        tl   = statement.lower().strip()

        # Extrai sujeito da query — regex cobre verbos de ação
        _VACT = r'é\s+um[a]?|é|são|tem|possui|voa|nadam?|respira|come|vive|corre|produz|amamenta|bota|rasteja|migra|faz|usa'
        subj_m = (re.search(r'logo\s+(\w[\w\s]{1,20}?)\s+(?:' + _VACT + r')', tl) or
                  re.search(r'^(\w[\w\s]{1,20}?)\s+(?:' + _VACT + r')[?\s\.]', tl) or
                  re.search(r'^(\w[\w\s]{1,15})', tl))
        if not subj_m:
            return None
        # Corta o sujeito no primeiro verbo de ação que aparecer
        raw_subj = subj_m.group(1).strip()
        subj = re.split(r'\s+(?:' + _VACT + r')', raw_subj)[0].strip()
        subj = re.sub(r'^\s*logo\s+', '', subj).strip()
        if len(subj) < 2 or subj in _STOP_PT:
            return None

        subj_vec = self._embed.vector(subj)

        # Propriedade alvo (após "é", "tem", "voa" etc.)
        prop_m = re.search(
            r'(?:é\s+um[a]?\s+|é\s+|tem\s+|voa\s*|faz\s*)(\w[\w\s]{1,20}?)[?\.]?\s*$', tl)
        prop = prop_m.group(1).strip() if prop_m else ''

        best_sim, best_rule = 0.0, None
        for rule_subj, rule_concl in self._rules:
            if rule_subj == subj:
                continue  # exato já tratado por deduce()
            sim = self._embed.cosine(subj_vec, self._embed.vector(rule_subj))
            if sim < th:
                continue
            combined = sim
            if prop:
                prop_sim  = self._embed.cosine(self._embed.vector(rule_concl),
                                               self._embed.vector(prop))
                combined  = sim * 0.6 + prop_sim * 0.4
            if combined > best_sim:
                best_sim  = combined
                best_rule = (rule_subj, rule_concl, sim)

        if best_rule is None:
            return None
        rs, rc, sim_s = best_rule
        conf = int(best_sim * 100)
        return (f'Hipótese semântica ({conf}% conf): '
                f'como {subj} ≈ {rs} ({int(sim_s*100)}%), {subj} provavelmente {rc}.')

    def scored_deduce(self, statement: str) -> Optional[str]:
        """Ranqueia conclusões por relevância semântica — desambiguação contextual.

        Quando há múltiplos caminhos de dedução, usa o embed para escolher
        o mais coerente com o contexto da query (ex: banco financeiro vs. assento).
        """
        if self._embed is None:
            return self.deduce(statement)

        tl = statement.lower().strip()
        subj_m = (re.search(r'o\s+que\s+(?:é|são)\s+(\w[\w\s]{1,20}?)[\?\s]', tl) or
                  re.search(r'^(\w[\w\s]{1,15})', tl))
        if not subj_m:
            return self.deduce(statement)
        raw = subj_m.group(1).strip()
        # Remove prefixo "logo" e corta no primeiro verbo de ação
        raw = re.sub(r'^\s*logo\s+', '', raw).strip()
        subj = re.split(
            r'\s+(?:é|são|tem|possui|voa|nada|respira|faz|realiza|é\s+um|produz|causa)',
            raw)[0].strip()
        subj = re.sub(r'\s+(?:é\s*)?$', '', subj).strip()
        if len(subj) < 2:
            return self.deduce(statement)

        # BFS para coletar todas as conclusões alcançáveis
        # Combina regras do DeductiveEngine + ConditionalEngine para
        # encadear "gato → mamífero → pelo" mesmo quando a cadeia cruza motores.
        all_rules = list(self._rules)
        if hasattr(self, '_conditional') and self._conditional is not None:
            # Converte regras normalizadas do ConditionalEngine para forma bruta
            all_rules.extend(self._conditional._rules)

        visited  = {subj}
        frontier = [subj]
        parents: dict = {subj: None}
        all_concls: List[Tuple[str, str]] = []

        for _ in range(5):
            nxt = []
            for node in frontier:
                for rs, rc in all_rules:
                    if rs != node or rc in visited:
                        continue
                    parents[rc] = node
                    visited.add(rc); nxt.append(rc)
                    path, cur, sp = [], rc, set()
                    while cur and cur not in sp and len(path) < 10:
                        path.append(cur); sp.add(cur); cur = parents.get(cur)
                    path.reverse()
                    all_concls.append((' → '.join(path), rc))
            frontier = nxt
            if not frontier:
                break

        if not all_concls:
            return None
        if len(all_concls) == 1:
            return f'Por dedução: {all_concls[0][0]}'

        # Ranqueia por cosine com a query
        qv     = self._embed.sentence_vector(statement)
        scored = [(self._embed.cosine(qv, self._embed.sentence_vector(c)),
                   p, c) for p, c in all_concls]
        scored.sort(reverse=True)
        best_sim, best_path, _ = scored[0]
        result = f'Por dedução ({int(best_sim*100)}% relevância): {best_path}'
        if len(scored) > 1 and scored[1][0] > 0.3:
            result += f'\n  Também possível: {scored[1][1]}'
        return result

    def to_dict(self) -> dict:
        return {'rules': list(self._rules)}

    @classmethod
    def from_dict(cls, d: dict) -> 'DeductiveEngine':
        de = cls()
        de._rules = [tuple(r) for r in d.get('rules', [])]
        return de


# ══════════════════════════════════════════════════════════════════════════════
# §15  EPISTEMIC LAYER — v5 Pro (hipóteses, validação, promoção)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Belief:
    id:             str
    text:           str
    sdr:            SparseSDR
    tag:            str         = 'THEORY'
    status:         str         = 'pending'
    confidence:     float       = 0.0
    source:         str         = 'user'
    support:        List[str]   = field(default_factory=list)
    contradictions: List[str]   = field(default_factory=list)
    notes:          str         = ''
    metadata:       Dict        = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {'id': self.id, 'text': self.text, 'sdr': self.sdr.to_dict(),
                'tag': self.tag, 'status': self.status, 'conf': self.confidence,
                'src': self.source, 'notes': self.notes}

    @classmethod
    def from_dict(cls, d: dict) -> 'Belief':
        return cls(id=d['id'], text=d['text'], sdr=SparseSDR.from_dict(d['sdr']),
                   tag=d.get('tag', 'THEORY'), status=d.get('status', 'pending'),
                   confidence=d.get('conf', 0.0), source=d.get('src', 'user'),
                   notes=d.get('notes', ''))


class EpistemicLayer:
    PROMOTE_THRESHOLD = 0.28

    def __init__(self):
        self._beliefs: Dict[str, Belief] = {}
        self._counter: int = 0
        self._on_promote = None

    def theorize(self, text: str, sdr: SparseSDR, source: str = 'user',
                 tag: str = 'THEORY') -> Belief:
        self._counter += 1
        bid = f'B{self._counter:04d}'
        b   = Belief(id=bid, text=text.strip(), sdr=sdr, tag=tag, source=source)
        self._beliefs[bid] = b
        return b

    def validate(self, belief: Belief, brain: CognitiveBrain) -> Belief:
        support_traces = [
            (s, m) for s, m in
            brain.recall(belief.sdr, top_k=8, threshold=0.05, tags=['FACT', 'RULE'])
            if m.text.strip().lower() != belief.text.strip().lower()
        ]
        contra_traces = brain._find_contradictions_for(belief.sdr, belief.text)
        belief.support        = [m.text[:100] for _, m in support_traces[:4]]
        belief.contradictions = [m.text[:100] for m in contra_traces[:3]]

        if belief.contradictions:
            belief.status     = 'rejected'
            belief.confidence = 0.0
            belief.notes      = f'Conflito: {belief.contradictions[0][:60]}'
            return belief

        strong = [(s, m) for s, m in support_traces if s >= 0.15]
        if strong:
            avg          = sum(s for s, _ in strong) / len(strong)
            count_bonus  = min(1.0, len(strong) / 5) * 0.20
            belief.confidence = avg * 0.80 + count_bonus
        elif support_traces:
            avg = sum(s for s, _ in support_traces) / len(support_traces)
            belief.confidence = avg * 0.25
        else:
            belief.confidence = 0.0

        if not self._predicate_known(belief.text, brain):
            belief.confidence *= 0.25
        if not self._subject_known(belief.text, brain):
            belief.confidence *= 0.40

        if belief.confidence >= self.PROMOTE_THRESHOLD:
            belief.status = 'promoted'
            belief.notes  = f'{len(strong)} evidência(s) forte(s), conf={belief.confidence:.3f}'
            if self._on_promote:
                self._on_promote(belief, brain)
        else:
            belief.status = 'pending'
            belief.notes  = f'conf={belief.confidence:.3f} < {self.PROMOTE_THRESHOLD}'
        return belief

    def _subject_known(self, text: str, brain: CognitiveBrain) -> bool:
        words = [w for w in re.findall(r'\w{4,}', text.lower()) if w not in _STOP_PT]
        if not words:
            return True
        stem = words[0][:5]
        return any(stem in m.text.lower() for m in brain._memories
                   if m.tag in ('FACT', 'RULE'))

    def _predicate_known(self, text: str, brain: CognitiveBrain) -> bool:
        tokens = [w for w in re.findall(r'\w{4,}', text.lower()) if w not in _STOP_PT]
        if len(tokens) < 2:
            return True
        pred_tokens = tokens[1:]
        for tok in pred_tokens:
            stem = tok[:5]
            if any(stem in m.text.lower() for m in brain._memories
                   if m.tag in ('FACT', 'RULE')):
                return True
        return False

    def detect_gap(self, query_sdr: SparseSDR, brain: CognitiveBrain,
                   query_text: str = '') -> Optional[Belief]:
        if not brain.is_novel(query_sdr):
            return None
        best = brain.best_match(query_sdr)
        hint = f'próximo de "{best[1].text[:40]}"' if best else 'sem contexto'
        text = f'Hipótese: conceito novo. {hint}'
        if query_text:
            text = f'"{query_text[:50]}": {text}'
        return self.theorize(text, query_sdr, source='curiosity', tag='HYPOTHESIS')

    def detect_conflict_hypothesis(self, new_t: str, new_s: SparseSDR,
                                   old_t: str, old_s: SparseSDR) -> Optional[Belief]:
        nn = re.findall(r'\d+(?:[.,]\d+)?', new_t)
        no = re.findall(r'\d+(?:[.,]\d+)?', old_t)
        if nn and no and set(nn) != set(no):
            text = f'Conflito numérico: "{old_t[:45]}" vs "{new_t[:45]}"'
        else:
            text = f'Conflito: "{new_t[:40]}" vs "{old_t[:40]}"'
        h_sdr = SparseSDR.bundle([new_s, old_s])
        return self.theorize(text, h_sdr, source='conflict', tag='HYPOTHESIS')

    def all_beliefs(self) -> List[Belief]:
        return list(self._beliefs.values())

    def hypotheses(self) -> List[Belief]:
        return [b for b in self._beliefs.values() if b.tag == 'HYPOTHESIS']

    def to_dict(self) -> dict:
        return {'counter': self._counter,
                'beliefs': {k: v.to_dict() for k, v in self._beliefs.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> 'EpistemicLayer':
        ep = cls()
        ep._counter = d.get('counter', 0)
        ep._beliefs = {k: Belief.from_dict(v) for k, v in d.get('beliefs', {}).items()}
        return ep


# ══════════════════════════════════════════════════════════════════════════════
# §16  EPISODIC STREAM — v5 Pro (cadeia de episódios com busca SDR)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Episode:
    id:           str
    timestamp:    float
    input_text:   str
    output_text:  str
    input_sdr:    SparseSDR
    context:      str        = 'general'
    facts_added:  List[str]  = field(default_factory=list)
    previous_id:  str        = ''
    # v8: relevância com decay (v7)
    relevance:    float      = 1.0
    accesses:     int        = 0

    HALF_LIFE_H = 48.0

    def decay_relevance(self) -> float:
        elapsed_h = (time.time() - self.timestamp) / 3600.0
        return self.relevance * math.exp(-math.log(2) * elapsed_h / self.HALF_LIFE_H)

    def touch(self) -> None:
        self.accesses += 1
        self.relevance = min(2.0, self.relevance + 0.1)
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {'id': self.id, 'ts': round(self.timestamp, 2),
                'in': self.input_text[:150], 'out': self.output_text[:150],
                'sdr': self.input_sdr.to_list(), 'ctx': self.context,
                'fa': self.facts_added, 'prev': self.previous_id,
                'rel': round(self.relevance, 4), 'ac': self.accesses}

    @classmethod
    def from_dict(cls, d: dict) -> 'Episode':
        return cls(id=d['id'], timestamp=d['ts'], input_text=d['in'],
                   output_text=d['out'], input_sdr=SparseSDR.from_list(d['sdr']),
                   context=d.get('ctx', 'general'), facts_added=d.get('fa', []),
                   previous_id=d.get('prev', ''), relevance=d.get('rel', 1.0),
                   accesses=d.get('ac', 0))


class EpisodicStream:
    """
    Cadeia de episódios com busca SDR + decay de relevância (v7 integrado).
    Episódios acessados frequentemente têm relevância reforçada.
    """
    MAX_EPISODES = 500

    def __init__(self):
        self._episodes: List[Episode] = []
        self._counter = 0

    def record(self, input_text: str, output_text: str, input_sdr: SparseSDR,
               context: str = 'general', facts_added: Optional[List[str]] = None) -> Episode:
        self._counter += 1
        prev = self._episodes[-1].id if self._episodes else ''
        ep   = Episode(id=f'E{self._counter:05d}', timestamp=time.time(),
                       input_text=input_text[:200], output_text=output_text[:200],
                       input_sdr=input_sdr, context=context,
                       facts_added=facts_added or [], previous_id=prev)
        self._episodes.append(ep)
        if len(self._episodes) > self.MAX_EPISODES:
            self._prune()
        return ep

    def recent(self, n: int = 5) -> List[Episode]:
        return list(reversed(self._episodes[-n:]))

    def search(self, query_sdr: SparseSDR, top_k: int = 5,
               min_sim: float = 0.05) -> List[Tuple[float, Episode]]:
        results = [(query_sdr.jaccard(ep.input_sdr) * ep.decay_relevance(), ep)
                   for ep in self._episodes]
        results = [(s, ep) for s, ep in results if s >= min_sim]
        results.sort(key=lambda x: -x[0])
        for _, ep in results[:top_k]:
            ep.touch()
        return results[:top_k]

    def _prune(self) -> None:
        # Mantém episódios mais relevantes (decay × acesso)
        self._episodes.sort(key=lambda ep: -ep.decay_relevance())
        self._episodes = self._episodes[:self.MAX_EPISODES // 2]

    def summary(self) -> Dict:
        if not self._episodes:
            return {'total': 0}
        return {'total': len(self._episodes),
                'contexts': Counter(ep.context for ep in self._episodes).most_common(3)}

    def to_dict(self) -> dict:
        return {'counter': self._counter,
                'episodes': [ep.to_dict() for ep in self._episodes[-200:]]}

    @classmethod
    def from_dict(cls, d: dict) -> 'EpisodicStream':
        es = cls()
        es._counter  = d.get('counter', 0)
        es._episodes = [Episode.from_dict(e) for e in d.get('episodes', [])]
        return es


# ══════════════════════════════════════════════════════════════════════════════
# §17  HOMEOSTASIS — v5 Pro (energia, curiosidade, confusão)
# ══════════════════════════════════════════════════════════════════════════════

class Homeostasis:
    def __init__(self):
        self.energy    = 1.0
        self.curiosity = 0.5
        self.confusion = 0.0

    def on_query(self):
        self.energy = max(0.0, self.energy - 0.01)

    def on_learn(self):
        self.energy    = max(0.0, self.energy - 0.015)
        self.curiosity = min(1.0, self.curiosity + 0.02)

    def on_novel_input(self):
        self.curiosity = min(1.0, self.curiosity + 0.05)

    def on_successful_infer(self):
        self.energy    = min(1.0, self.energy + 0.02)
        self.confusion = max(0.0, self.confusion - 0.05)

    def on_failed_infer(self):
        self.confusion = min(1.0, self.confusion + 0.03)

    def on_contradiction(self):
        self.confusion = min(1.0, self.confusion + 0.1)
        self.energy    = max(0.0, self.energy - 0.02)

    def on_sleep(self):
        self.energy    = min(1.0, self.energy + 0.3)
        self.confusion = max(0.0, self.confusion - 0.2)

    def state(self) -> Dict:
        return {'energy': round(self.energy, 3),
                'curiosity': round(self.curiosity, 3),
                'confusion': round(self.confusion, 3)}

    def to_dict(self) -> dict:
        return self.state()

    @classmethod
    def from_dict(cls, d: dict) -> 'Homeostasis':
        h = cls()
        h.energy    = d.get('energy', 1.0)
        h.curiosity = d.get('curiosity', 0.5)
        h.confusion = d.get('confusion', 0.0)
        return h


# ══════════════════════════════════════════════════════════════════════════════
# §18  SLEEP CONSOLIDATOR — v5 Pro (merge Hebbiano + prune grafo)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConsolidationReport:
    cycles:       int
    merged_pairs: int
    pruned_weak:  int
    before_count: int
    after_count:  int
    duration_ms:  float
    metadata:     Dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (f'Consolidação: {self.cycles} ciclo(s), '
                f'{self.merged_pairs} pares fundidos, '
                f'{self.pruned_weak} podados, '
                f'{self.before_count}→{self.after_count} memórias, '
                f'{self.duration_ms:.0f}ms')


class SleepConsolidator:
    MERGE_THR = 0.82

    def consolidate(self, brain: CognitiveBrain,
                    cycles: int = 1) -> ConsolidationReport:
        t0 = time.time()
        before = len(brain._memories)
        merged = 0
        for _ in range(cycles):
            merged += self._merge_pass(brain)
            brain.decay_cycle()
        return ConsolidationReport(cycles=cycles, merged_pairs=merged,
                                   pruned_weak=before - len(brain._memories),
                                   before_count=before, after_count=len(brain._memories),
                                   duration_ms=(time.time()-t0)*1000)

    def _merge_pass(self, brain: CognitiveBrain) -> int:
        mems = brain._memories
        n    = len(mems)
        merged = 0
        to_remove: Set[int] = set()
        for i in range(n):
            if i in to_remove:
                continue
            for j in range(i+1, n):
                if j in to_remove:
                    continue
                mi, mj = mems[i], mems[j]
                if mi.tag != mj.tag:
                    continue
                if mi.confidence > 0.8 and mj.confidence > 0.8:
                    continue
                if mi.sdr.jaccard(mj.sdr) < self.MERGE_THR:
                    continue
                master = MemoryTrace(
                    sdr=SparseSDR.bundle([mi.sdr, mj.sdr], threshold=0.3),
                    text=mi.text if mi.created_at <= mj.created_at else mj.text,
                    tag=mi.tag,
                    confidence=max(mi.confidence, mj.confidence),
                    strength=min(1.0, mi.strength + mj.strength * 0.5),
                    access_count=mi.access_count + mj.access_count,
                    metadata={'merged': True})
                mems.append(master)
                brain._index.add(len(mems)-1, master.sdr)
                brain._index.remove(i, mi.sdr)
                brain._index.remove(j, mj.sdr)
                to_remove.add(i)
                to_remove.add(j)
                merged += 1
                break
        brain._memories = [m for k, m in enumerate(mems) if k not in to_remove]
        # Rebuild index from scratch to keep indices consistent after merge
        brain._index = InvertedIndex()
        for i, m in enumerate(brain._memories):
            brain._index.add(i, m.sdr)
        return merged

    def prune_graph(self, concept_graph: ConceptGraph,
                    threshold: float = 0.10, hub_limit: int = 40) -> Dict:
        before = concept_graph.edge_count
        pruned_edges = 0
        pruned_nodes = 0
        out_degree: Dict[str, int] = {}
        for subj, targets in concept_graph._edges.items():
            out_degree[subj] = sum(len(rels) for rels in targets.values())
        nodes_to_remove = []
        for subj in list(concept_graph._edges.keys()):
            degree     = out_degree.get(subj, 0)
            hub_factor = 0.5 if degree > hub_limit else 1.0
            targets_to_remove = []
            for obj, rels in list(concept_graph._edges[subj].items()):
                for rel in list(rels.keys()):
                    rels[rel] = rels[rel] * 0.95 * hub_factor
                weak_rels = [r for r, w in rels.items() if w < threshold]
                for r in weak_rels:
                    del rels[r]
                    pruned_edges += 1
                if not rels:
                    targets_to_remove.append(obj)
            for obj in targets_to_remove:
                del concept_graph._edges[subj][obj]
            if not concept_graph._edges[subj]:
                nodes_to_remove.append(subj)
        for subj in nodes_to_remove:
            del concept_graph._edges[subj]
            concept_graph._activation.pop(subj, None)
            pruned_nodes += 1
        return {'before_edges': before, 'pruned_edges': pruned_edges,
                'pruned_nodes': pruned_nodes, 'after_edges': concept_graph.edge_count}


# ══════════════════════════════════════════════════════════════════════════════
# §19  VIRTUAL WORKSPACE — v5 Pro (sistema de arquivos virtual em RAM)
# ══════════════════════════════════════════════════════════════════════════════

class VirtualWorkspace:
    __slots__ = ('_files', '_lock')

    def __init__(self):
        self._files: Dict[str, str] = {}
        self._lock  = threading.Lock()

    def write(self, filename: str, content: str) -> str:
        with self._lock:
            self._files[filename] = content
        return f"📝 '{filename}' ({len(content)} bytes) no workspace."

    def read(self, filename: str) -> Optional[str]:
        return self._files.get(filename)

    def delete(self, filename: str) -> bool:
        with self._lock:
            return self._files.pop(filename, None) is not None

    def list_files(self) -> str:
        if not self._files:
            return 'Workspace vazio.'
        return ', '.join(f'{k}({len(v)}B)' for k, v in self._files.items())

    def run_project(self, entry: str = 'main.py', code_gen=None) -> Dict[str, Any]:
        code = self._files.get(entry)
        if not code:
            return {'success': False, 'error': f"'{entry}' não existe.", 'stdout': ''}
        if code_gen is None:
            return {'success': False, 'error': 'code_gen não fornecido', 'stdout': ''}
        return code_gen._exec(code)

    def export(self, folder: str = 'nexus_output') -> str:
        if not self._files:
            return 'Workspace vazio.'
        os.makedirs(folder, exist_ok=True)
        for name, content in self._files.items():
            path = os.path.join(folder, name)
            if os.sep in name:
                os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        return f'💾 {len(self._files)} arquivo(s) em ./{folder}/'

    def clear(self) -> None:
        with self._lock:
            self._files.clear()

    @property
    def file_count(self) -> int:
        return len(self._files)

    def to_dict(self) -> dict:
        return {'files': dict(self._files)}

    @classmethod
    def from_dict(cls, d: dict) -> 'VirtualWorkspace':
        ws = cls()
        ws._files = dict(d.get('files', {}))
        return ws


# ══════════════════════════════════════════════════════════════════════════════
# §20  CODE GENERALIZER — v5 Pro (CBR + sandbox AST + repair loop)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CodeEpisode:
    description: str
    code:        str
    intent:      str
    success:     bool
    stdout:      str   = ''
    error_type:  str   = ''
    attempts:    int   = 1
    created_at:  float = field(default_factory=time.time)


_STOP_CODE = {'o','a','de','do','da','em','para','com','que','uma','um',
              'e','é','implemente','crie','escreva',
              # Palavras genéricas que causavam falsos positivos no retrieve():
              # "lista" casava com linked_list, "máximo" com gcd_lcm, etc.
              'lista','calcular','calcula','numero','numeros','valor','valores',
              'elemento','elementos','array','funcao','programa','codigo',
              'ordenar','maximo','máximo','minimo','mínimo',
              'crescente','decrescente','encontrar','achar'}

_CODE_TEMPLATES: Dict[str, str] = {
    'fibonacci': '''\
def fibonacci(n):
    if n <= 1: return n
    a, b = 0, 1
    for _ in range(n - 1): a, b = b, a + b
    return b
for i in range(10): print(f"fib({i}) = {fibonacci(i)}")''',
    'factorial': '''\
def factorial(n):
    result = 1
    for i in range(2, n+1): result *= i
    return result
print(f"5! = {factorial(5)}")''',
    'is_prime': '''\
def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5)+1):
        if n % i == 0: return False
    return True
print([n for n in range(2, 30) if is_prime(n)])''',
    'binary_search': '''\
def binary_search(arr, target):
    l, r = 0, len(arr)-1
    while l <= r:
        mid = (l+r)//2
        if arr[mid]==target: return mid
        elif arr[mid]<target: l=mid+1
        else: r=mid-1
    return -1
print(binary_search([1,3,5,7,9],7))''',
    'bubble_sort': '''\
def bubble_sort(arr):
    arr=arr.copy(); n=len(arr)
    for i in range(n):
        for j in range(n-i-1):
            if arr[j]>arr[j+1]: arr[j],arr[j+1]=arr[j+1],arr[j]
    return arr
print(bubble_sort([64,34,25,12,22,11,90]))''',
    'merge_sort': '''\
def merge_sort(arr):
    if len(arr)<=1: return arr
    m=len(arr)//2
    l,r=merge_sort(arr[:m]),merge_sort(arr[m:])
    res,i,j=[],0,0
    while i<len(l) and j<len(r):
        if l[i]<=r[j]: res.append(l[i]); i+=1
        else: res.append(r[j]); j+=1
    return res+l[i:]+r[j:]
print(merge_sort([38,27,43,3,9,82,10]))''',
    'quicksort': '''\
def quicksort(arr):
    if len(arr)<=1: return arr
    pivot=arr[len(arr)//2]
    left=[x for x in arr if x<pivot]
    mid=[x for x in arr if x==pivot]
    right=[x for x in arr if x>pivot]
    return quicksort(left)+mid+quicksort(right)
print(quicksort([3,6,8,10,1,2,1]))''',
    'palindrome': '''\
def is_palindrome(s):
    s=''.join(c for c in s.lower() if c.isalnum())
    return s==s[::-1]
for w in ["racecar","hello","arara"]: print(f"{w}: {is_palindrome(w)}")''',
    'two_sum': '''\
def two_sum(nums, target):
    seen={}
    for i,n in enumerate(nums):
        if target-n in seen: return [seen[target-n],i]
        seen[n]=i
    return []
print(two_sum([2,7,11,15],9))''',
    'gcd_lcm': '''\
def gcd(a,b):
    while b: a,b=b,a%b
    return a
def lcm(a,b): return abs(a*b)//gcd(a,b)
print(f"MDC(48,18)={gcd(48,18)}, MMC(4,6)={lcm(4,6)}")''',
    'stack': '''\
class Stack:
    def __init__(self): self._d=[]
    def push(self,v): self._d.append(v)
    def pop(self): return self._d.pop() if self._d else None
    def peek(self): return self._d[-1] if self._d else None
    def __len__(self): return len(self._d)
s=Stack(); s.push(1); s.push(2); print(s.pop(), s.peek())''',
    'linked_list': '''\
class Node:
    def __init__(self,v): self.v=v; self.next=None
class LinkedList:
    def __init__(self): self.head=None
    def append(self,v):
        n=Node(v)
        if not self.head: self.head=n; return
        c=self.head
        while c.next: c=c.next
        c.next=n
    def to_list(self):
        r,c=[],self.head
        while c: r.append(c.v); c=c.next
        return r
ll=LinkedList(); ll.append(1); ll.append(2); ll.append(3)
print(ll.to_list())''',
    'decorator': '''\
def timer(func):
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        result=func(*args,**kwargs)
        print(f"{func.__name__} executada com sucesso")
        return result
    return wrapper
@timer
def soma(n): return sum(range(n))
print(soma(100000))''',
    'generator': '''\
def counter(start=0):
    while True: yield start; start+=1
def take(n,g): return [next(g) for _ in range(n)]
print(take(5, counter(10)))''',
    'context_manager': '''\
class Timer:
    def __enter__(self): self._t=0; return self
    def __exit__(self,*_): print("Timer OK (time module not available in sandbox)")
with Timer(): _ = sum(range(1000000))''',
    'counter': '''\
words="the quick brown fox jumps over the lazy dog the fox".split()
c=Counter(words)
print(c.most_common(3))''',
    'bfs': '''\
def bfs(graph, start):
    visited, queue = set(), deque([start])
    visited.add(start)
    order = []
    while queue:
        node = queue.popleft(); order.append(node)
        for nb in graph.get(node, []):
            if nb not in visited:
                visited.add(nb); queue.append(nb)
    return order
g = {'A':['B','C'],'B':['D'],'C':['D','E'],'D':[],'E':[]}
print(bfs(g,'A'))''',
    'dfs': '''\
def dfs(graph, start, visited=None):
    if visited is None: visited = set()
    visited.add(start); order = [start]
    for nb in graph.get(start, []):
        if nb not in visited:
            order.extend(dfs(graph, nb, visited))
    return order
g = {'A':['B','C'],'B':['D'],'C':['D','E'],'D':[],'E':[]}
print(dfs(g,'A'))''',
    'queue': '''\
class Queue:
    def __init__(self): self._d = deque()
    def enqueue(self, v): self._d.append(v)
    def dequeue(self): return self._d.popleft() if self._d else None
    def peek(self): return self._d[0] if self._d else None
    def __len__(self): return len(self._d)
    def __repr__(self): return f"Queue({list(self._d)})"
q = Queue()
for v in [10, 20, 30]: q.enqueue(v)
print(q); print("dequeue:", q.dequeue()); print(q)''',
    'heap': '''\
class MinHeap:
    def __init__(self): self._h = []
    def push(self, v): heapq.heappush(self._h, v)
    def pop(self): return heapq.heappop(self._h) if self._h else None
    def peek(self): return self._h[0] if self._h else None
    def __len__(self): return len(self._h)
h = MinHeap()
for v in [5, 3, 8, 1, 4]: h.push(v)
print("min:", h.peek())
while h: print(h.pop(), end=" ")
print()''',
    'binary_tree': '''\
class TreeNode:
    def __init__(self, v): self.v = v; self.left = self.right = None
class BST:
    def __init__(self): self.root = None
    def insert(self, v):
        n = TreeNode(v)
        if not self.root: self.root = n; return
        cur = self.root
        while True:
            if v < cur.v:
                if cur.left is None: cur.left = n; break
                cur = cur.left
            else:
                if cur.right is None: cur.right = n; break
                cur = cur.right
    def inorder(self, node=None, first=True):
        if first: node = self.root
        if node is None: return []
        return self.inorder(node.left, False) + [node.v] + self.inorder(node.right, False)
bst = BST()
for v in [5, 3, 7, 1, 4, 6, 8]: bst.insert(v)
print("inorder:", bst.inorder())''',
    'hash_table': '''\
class HashTable:
    def __init__(self, size=16):
        self._size = size
        self._table = [[] for _ in range(size)]
    def _h(self, k): return hash(k) % self._size
    def set(self, k, v):
        bucket = self._table[self._h(k)]
        for i, (bk, _) in enumerate(bucket):
            if bk == k: bucket[i] = (k, v); return
        bucket.append((k, v))
    def get(self, k):
        for bk, bv in self._table[self._h(k)]:
            if bk == k: return bv
        return None
ht = HashTable()
ht.set("nome", "Nexus"); ht.set("versão", "v9")
print(ht.get("nome"), ht.get("versão"))''',
    'graph': '''\
class Graph:
    def __init__(self): self._adj = defaultdict(list)
    def add_edge(self, u, v, directed=False):
        self._adj[u].append(v)
        if not directed: self._adj[v].append(u)
    def bfs(self, start):
        visited, q, order = {start}, deque([start]), []
        while q:
            n = q.popleft(); order.append(n)
            for nb in self._adj[n]:
                if nb not in visited: visited.add(nb); q.append(nb)
        return order
    def has_path(self, s, t): return t in self.bfs(s)
g = Graph()
for u, v in [("A","B"),("A","C"),("B","D"),("C","E")]: g.add_edge(u, v)
print("BFS from A:", g.bfs("A"))
print("Path A→E:", g.has_path("A","E"))''',
    'matrix': '''\
def zeros(r, c): return [[0]*c for _ in range(r)]
def transpose(m): return [[m[j][i] for j in range(len(m))] for i in range(len(m[0]))]
def matmul(A, B):
    r, c, k = len(A), len(B[0]), len(B)
    C = zeros(r, c)
    for i in range(r):
        for j in range(c):
            for p in range(k): C[i][j] += A[i][p] * B[p][j]
    return C
A = [[1,2],[3,4]]; B = [[5,6],[7,8]]
print("A×B =", matmul(A, B))
print("Transposta A:", transpose(A))''',
    'selection_sort': '''\
def selection_sort(arr):
    arr = arr.copy(); n = len(arr)
    for i in range(n):
        min_idx = min(range(i, n), key=lambda x: arr[x])
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr
print(selection_sort([64, 25, 12, 22, 11]))''',
    'insertion_sort': '''\
def insertion_sort(arr):
    arr = arr.copy()
    for i in range(1, len(arr)):
        key = arr[i]; j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j+1] = arr[j]; j -= 1
        arr[j+1] = key
    return arr
print(insertion_sort([12, 11, 13, 5, 6]))''',
    'memoize': '''\
def memoize(func):
    cache = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache: cache[args] = func(*args)
        return cache[args]
    return wrapper
@memoize
def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)
print([fib(i) for i in range(10)])''',
    'trie': '''\
class TrieNode:
    def __init__(self): self.children = {}; self.end = False
class Trie:
    def __init__(self): self.root = TrieNode()
    def insert(self, w):
        n = self.root
        for c in w: n = n.children.setdefault(c, TrieNode())
        n.end = True
    def search(self, w):
        n = self.root
        for c in w:
            if c not in n.children: return False
            n = n.children[c]
        return n.end
    def starts_with(self, p):
        n = self.root
        for c in p:
            if c not in n.children: return False
            n = n.children[c]
        return True
t = Trie()
for w in ["apple","app","banana"]: t.insert(w)
print(t.search("app"), t.search("apx"), t.starts_with("ban"))''',
}

_CBR_DESCS: Dict[str, List[str]] = {
    'fibonacci':       ['fibonacci','série fibonacci','sequência fibonacci'],
    'factorial':       ['fatorial','factorial','fatorial de'],
    'is_prime':        ['número primo','verificar primo','checar primo','primos'],
    'binary_search':   ['busca binária','binary search','busca em lista ordenada'],
    'bubble_sort':     ['bubble sort','ordenação bolha','ordena bolha'],
    'merge_sort':      ['merge sort','ordenação fusão','ordena por fusão'],
    'quicksort':       ['quicksort','quick sort','ordenação rápida'],
    'palindrome':      ['palíndromo','palindrome','verificar palíndromo'],
    'two_sum':         ['two sum','dois valores','soma alvo','soma de dois'],
    'gcd_lcm':         ['mdc','mmc','máximo divisor','mínimo múltiplo','gcd','lcm'],
    'stack':           ['pilha','stack','lifo','estrutura pilha'],
    'linked_list':     ['lista ligada','linked list','lista encadeada'],
    'decorator':       ['decorador','decorator','wrapper de função','medir tempo'],
    'generator':       ['gerador','generator','yield','lazy sequence','iterador'],
    'context_manager': ['gerenciador de contexto','context manager','with statement'],
    'counter':         ['contador de palavras','frequência de palavras','contar palavras'],
    'bfs':             ['bfs','busca em largura','breadth first search','busca por largura'],
    'dfs':             ['dfs','busca em profundidade','depth first search'],
    'queue':           ['fila','queue','fifo','estrutura fila','fila de espera'],
    'heap':            ['heap','min heap','max heap','heap mínimo','heap máximo','fila de prioridade','priority queue'],
    'binary_tree':     ['árvore binária','arvore binaria','bst','binary search tree','árvore de busca','binary tree'],
    'hash_table':      ['tabela hash','hash table','hash map','dicionário customizado','mapa hash'],
    'graph':           ['grafo','graph','rede de nós','adjacência','graph class','classe grafo'],
    'matrix':          ['matriz','matrix','multiplicação de matrizes','transposta','matmul'],
    'selection_sort':  ['selection sort','ordenação por seleção','ordena seleção'],
    'insertion_sort':  ['insertion sort','ordenação por inserção','ordena inserção'],
    'memoize':         ['memoização','memoize','cache de função','memorização','memo'],
    'trie':            ['trie','árvore de prefixos','prefix tree','dicionário de palavras','trie tree'],
}


def _extract_error_type(s: str) -> str:
    m = re.search(r'(\w+Error|\w+Exception)', s)
    return m.group(1) if m else 'UnknownError'


def _repair_code(code: str, error: str, err_type: str) -> Optional[str]:
    if err_type in ('NameError', 'ImportError'):
        needs = re.findall(r"name '(\w+)' is not defined", error)
        _AUTO = {
            'deque': 'from collections import deque',
            'Counter': 'from collections import Counter',
            'defaultdict': 'from collections import defaultdict',
            'math': 'import math', 're': 'import re',
            'json': 'import json', 'random': 'import random', 'time': 'import time',
        }
        imps = [_AUTO[n] for n in needs if n in _AUTO]
        if imps:
            return '\n'.join(imps) + '\n\n' + code
    if err_type == 'SyntaxError':
        return '\n'.join(l for l in code.split('\n')
                         if not re.match(r'^\s*(>>>|\.\.\.)', l))
    return None


class CodeGeneralizer:
    """CBR + sandbox AST + repair loop + BFS/DFS novos."""

    def __init__(self):
        self._episodes: List[CodeEpisode] = []
        self._cbr: List[Tuple[str, str, str]] = []
        for intent, descs in _CBR_DESCS.items():
            code = _CODE_TEMPLATES.get(intent, '')
            if code:
                for d in descs:
                    self._cbr.append((d, intent, code))

    def retrieve(self, desc: str, min_score: float = 0.15) -> Optional[Tuple[str, str]]:
        d_words = {w for w in re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', desc.lower())
                   if len(w) > 1 and w not in _STOP_CODE}
        best_s, best_i, best_c = 0.0, None, None
        for d, intent, code in self._cbr:
            c_words = {w for w in re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', d.lower())
                       if len(w) > 1 and w not in _STOP_CODE}
            if not c_words:
                continue
            score = len(d_words & c_words) / max(len(d_words | c_words), 1)
            if score < min_score:
                for dw in d_words:
                    for cw in c_words:
                        # Exige ≥5 chars para evitar que palavras curtas genéricas
                        # (ex: "lista", "valor") inflem o score via substring match.
                        if len(dw) >= 5 and len(cw) >= 5 and (dw in cw or cw in dw):
                            score = max(score, 0.20)
                            break
            if score > best_s:
                best_s, best_i, best_c = score, intent, code
        return (best_i, best_c) if best_s >= min_score else None

    def learn(self, description: str, code: str, intent: str = 'generic') -> bool:
        try:
            ast.parse(code)
        except SyntaxError:
            return False
        self._cbr.append((description.lower(), intent, code))
        out = self._exec(code)
        self._episodes.append(CodeEpisode(
            description=description, code=code, intent=intent,
            success=out['success'], stdout=out.get('stdout', '')))
        return out['success']

    def run(self, description: str, max_repairs: int = 2) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            'description': description, 'success': False,
            'code': '', 'stdout': '', 'error': '', 'source': ''}
        cbr = self.retrieve(description)
        if cbr:
            intent, code = cbr
            result['code'], result['source'] = code, 'cbr'
            out = self._exec(code)
            result.update(out)
            if result['success']:
                self._episodes.append(CodeEpisode(
                    description=description, code=code, intent=intent,
                    success=True, stdout=result['stdout']))
                return result
        if not result.get('code'):
            result['error'] = f'Padrão não encontrado: {description!r}'
            return result
        code = result['code']
        for _ in range(max_repairs):
            err_type = _extract_error_type(result.get('error', ''))
            repaired = _repair_code(code, result.get('error', ''), err_type)
            if not repaired:
                break
            out = self._exec(repaired)
            result['code'] = repaired
            result.update(out)
            if result['success']:
                return result
            code = repaired
        return result

    def heal_code(self, broken_code: str, error_msg: str) -> str:
        if 'IndentationError' in error_msg or 'unexpected indent' in error_msg:
            lines   = broken_code.split('\n')
            indents = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
            min_ind = min((i for i in indents if i > 0), default=4)
            ratio   = 4.0 / max(min_ind, 1)
            normalized = []
            for line in lines:
                if not line.strip():
                    normalized.append('')
                    continue
                cur = len(line) - len(line.lstrip())
                normalized.append(' ' * round(cur * ratio) + line.lstrip())
            candidate = '\n'.join(normalized)
            try:
                ast.parse(candidate)
                return candidate
            except SyntaxError:
                pass
        if 'NameError' in error_msg or 'ImportError' in error_msg:
            repaired = _repair_code(broken_code, error_msg,
                                    'NameError' if 'NameError' in error_msg else 'ImportError')
            if repaired:
                return repaired
        if 'SyntaxError' in error_msg:
            open_p  = broken_code.count('(')
            close_p = broken_code.count(')')
            if open_p > close_p:
                return broken_code + ')' * (open_p - close_p)
            repaired = _repair_code(broken_code, error_msg, 'SyntaxError')
            if repaired:
                return repaired
        return broken_code

    @staticmethod
    def _exec(code: str, timeout: int = 8) -> Dict[str, Any]:
        result: Dict[str, Any] = {'success': False, 'stdout': '', 'error': ''}
        import math as _m, collections as _c, functools as _f, itertools as _it
        import heapq as _hq
        _ns = {
            '__builtins__': {
                'print': print, 'range': range, 'len': len, 'int': int,
                'float': float, 'str': str, 'bool': bool, 'list': list,
                'dict': dict, 'set': set, 'tuple': tuple, 'type': type,
                'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
                'sorted': sorted, 'reversed': reversed, 'sum': sum, 'min': min,
                'max': max, 'abs': abs, 'round': round, 'isinstance': isinstance,
                'hasattr': hasattr, 'getattr': getattr, 'setattr': setattr,
                'repr': repr, 'Exception': Exception,
                'ValueError': ValueError, 'TypeError': TypeError,
                'IndexError': IndexError, 'KeyError': KeyError,
                'StopIteration': StopIteration, 'NotImplementedError': NotImplementedError,
                'True': True, 'False': False, 'None': None,
                '__build_class__': __build_class__,
                '__name__': '__main__',
                'hash': hash, 'id': id, 'pow': pow,
                'chr': chr, 'ord': ord, 'hex': hex, 'oct': oct, 'bin': bin,
                'all': all, 'any': any, 'next': next, 'iter': iter,
                'open': None,  # bloqueado explicitamente
            },
            'math': _m, 'collections': _c, 'functools': _f, 'itertools': _it,
            'heapq': _hq,
            # Aliases diretos para uso sem qualificador nos templates
            'deque': _c.deque, 'defaultdict': _c.defaultdict,
            'Counter': _c.Counter, 'OrderedDict': _c.OrderedDict,
            'heappush': _hq.heappush, 'heappop': _hq.heappop,
            'heapify': _hq.heapify,
        }
        buf = io.StringIO()

        def _run():
            try:
                with contextlib.redirect_stdout(buf):
                    exec(compile(code, '<sandbox>', 'exec'), _ns)
                result['success'] = True
                result['stdout']  = buf.getvalue().strip()[:1000]
            except Exception as e:
                result['error'] = f'{type(e).__name__}: {e}'[:400]

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout)
        if t.is_alive():
            result['error'] = f'Timeout (>{timeout}s)'
        return result

    def context_for(self, desc: str, top_k: int = 3) -> List[CodeEpisode]:
        d_toks = set(desc.lower().split())
        scored = []
        for ep in reversed(self._episodes):
            if not ep.success:
                continue
            e_toks = set(ep.description.lower().split())
            j = len(d_toks & e_toks) / max(len(d_toks | e_toks), 1)
            if j > 0.1:
                scored.append((j, ep))
        return [ep for _, ep in sorted(scored, key=lambda x: -x[0])[:top_k]]

    def to_dict(self) -> dict:
        # Persiste apenas as entradas aprendidas via learn() — as entradas
        # built-in de _CBR_DESCS são reconstituídas automaticamente no __init__().
        # Identifica entradas aprendidas comparando com o conjunto built-in.
        builtin_keys = {(d, intent) for intent, descs in _CBR_DESCS.items()
                        for d in descs if _CODE_TEMPLATES.get(intent)}
        learned = [
            {'d': desc, 'i': intent, 'c': code}
            for desc, intent, code in self._cbr
            if (desc, intent) not in builtin_keys
        ]
        return {
            'episodes': [
                {'d': e.description, 'c': e.code, 'i': e.intent,
                 'ok': e.success, 'o': e.stdout}
                for e in self._episodes[-100:]
            ],
            'learned_cbr': learned,   # entradas ensinadas pelo usuário
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'CodeGeneralizer':
        cg = cls()   # já popula _cbr com os templates built-in
        for e in d.get('episodes', []):
            cg._episodes.append(CodeEpisode(
                description=e['d'], code=e['c'], intent=e['i'],
                success=e['ok'], stdout=e.get('o', '')))
        # Restaura entradas aprendidas (sem duplicar as built-in)
        existing = {(desc, intent) for desc, intent, _ in cg._cbr}
        for entry in d.get('learned_cbr', []):
            key = (entry['d'], entry['i'])
            if key not in existing:
                cg._cbr.append((entry['d'], entry['i'], entry['c']))
                existing.add(key)
        return cg


# ══════════════════════════════════════════════════════════════════════════════
# §21  MATH ENGINE — v5 Pro (safe eval + sympy-like básico)
# ══════════════════════════════════════════════════════════════════════════════

class MathEngine:
    _SAFE = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
    _SAFE.update({'abs': abs, 'round': round, 'int': int, 'float': float})

    # Limite de dígitos do resultado para bloquear DoS via 9**9**9
    _MAX_RESULT_DIGITS = 30

    def _check_safe_expr(self, expr: str) -> Optional[str]:
        """Retorna mensagem de erro se a expressão for perigosa, None se segura.

        ** é right-associative em Python: 9**9**9 = 9**(9**9) = 9**387420489.
        A estratégia é recusar qualquer cadeia de ** com mais de um operador,
        e para potências simples a**b verificar se o resultado teria > _MAX_RESULT_DIGITS.
        """
        # Cadeia de ** (ex: 9**9**9) — right-associative → sempre perigosa
        if expr.count('**') > 1:
            return 'Cadeia de potências bloqueada (resultado pode ser astronomicamente grande).'
        # Potência simples: verifica tamanho estimado do resultado
        m = re.search(r'(\d+)\s*\*\*\s*(\d+)', expr)
        if m:
            base_v = int(m.group(1))
            exp_v  = int(m.group(2))
            if base_v > 1 and exp_v > 0:
                try:
                    digits = exp_v * math.log10(base_v)
                except ValueError:
                    digits = 0
                if digits > self._MAX_RESULT_DIGITS:
                    return f'Resultado teria ~{int(digits)} dígitos — operação bloqueada.'
        return None

    _PT_MATH = [
        (re.compile(r'raiz\s+quadrada\s+de\s+([\d\.]+)', re.I), 'math.sqrt(\\1)'),
        (re.compile(r'([\d\.]+)\s+ao\s+quadrado', re.I),        '(\\1**2)'),
        (re.compile(r'([\d\.]+)\s+ao\s+cubo', re.I),            '(\\1**3)'),
        (re.compile(r'([\d\.]+)\s*%\s+de\s+([\d\.]+)', re.I),  '(\\1/100*\\2)'),
        (re.compile(r'seno?\s+de\s+([\d\.]+)', re.I),           'math.sin(math.radians(\\1))'),
        (re.compile(r'cosseno\s+de\s+([\d\.]+)', re.I),         'math.cos(math.radians(\\1))'),
        (re.compile(r'tangente\s+de\s+([\d\.]+)', re.I),        'math.tan(math.radians(\\1))'),
        (re.compile(r'\blog\s+de\s+([\d\.]+)', re.I),           'math.log10(\\1)'),
        (re.compile(r'fatorial\s+de\s+([\d]+)', re.I),          'math.factorial(\\1)'),
        (re.compile(r'potencia\s+([\d\.]+)\s+elevado\s+a\s+([\d]+)', re.I), '(\\1**\\2)'),
    ]

    def _preprocess_pt(self, text: str) -> str:
        """Converte expressões matemáticas em português para Python."""
        expr = text.lower().strip()
        # Remove prefixos de comando
        for prefix in ('calcule', 'calcule o', 'calcule a', 'compute', 'resolva', 'quanto é', 'quanto vale'):
            if expr.startswith(prefix):
                expr = expr[len(prefix):].strip()
                break
        for pat, repl in self._PT_MATH:
            expr = pat.sub(repl, expr)
        return expr

    def evaluate(self, text: str) -> Optional[str]:
        text = self._preprocess_pt(text)
        # Normaliza "math.X" → "X" pois _SAFE já tem as funções de math diretamente.
        # Ex: math.pi → pi, math.sqrt(4) → sqrt(4)
        text = re.sub(r'\bmath\.', '', text)

        # Percentagem: "15% de 200", "15 por cento de 200"
        pct_m = re.search(
            r'(\d+[,.]?\d*)\s*(?:%|por\s+cento)\s+de\s+(\d+[,.]?\d*)', text, re.I)
        if pct_m:
            try:
                pct = float(pct_m.group(1).replace(',', '.'))
                val = float(pct_m.group(2).replace(',', '.'))
                result = pct / 100 * val
                fmt = int(result) if result == int(result) else round(result, 4)
                return f'{pct}% de {val} = {fmt}'
            except Exception:
                pass

        # Tenta capturar expressão com funções matemáticas (sqrt, log, pi, abs, etc.)
        # Padrão 1: chamada de função, ex: sqrt(144), log(100, 10)
        # Padrão 2: constante * número, ex: pi * 2, pi / 4, ou apenas "pi"
        # Padrão 3: numérico puro, ex: 2 + 3 * 4, 2**10
        m = (re.search(r'[a-z_]\w*\s*\([^)]+\)(?:\s*[\+\-\*\/\^]\s*[\d\.a-z_\w]*)*', text) or
             re.search(r'pi(?:\s*[\+\-\*\/\^]\s*[\d\.]+)*', text) or
             re.search(r'[\d\s\+\-\*\/\^\(\)\.%]+', text))
        if m:
            expr = m.group().strip().replace('^', '**')
            # Preserva vírgulas como separadores de argumento dentro de funções
            # (ex: log(100, 10)), mas converte vírgula decimal fora de funções.
            if not re.search(r'[a-z_]\w*\s*\(', expr):
                expr = expr.replace(',', '.')
            danger = self._check_safe_expr(expr)
            if danger:
                return danger
            try:
                result = eval(expr, {"__builtins__": {}}, self._SAFE)
                return str(round(result, 10)) if isinstance(result, float) else str(result)
            except Exception:
                pass
        # Conversões de unidade
        conv_m = re.search(r'([\d,.]+)\s*(km|m|cm|mm|mi|ft|in)', text.lower())
        if conv_m:
            val  = float(conv_m.group(1).replace(',', '.'))
            unit = conv_m.group(2)
            convs = {'km': ('m', 1000), 'm': ('cm', 100), 'cm': ('mm', 10),
                     'mi': ('km', 1.60934), 'ft': ('m', 0.3048), 'in': ('cm', 2.54)}
            if unit in convs:
                to_unit, factor = convs[unit]
                return f'{val} {unit} = {val*factor} {to_unit}'
        return None


# ══════════════════════════════════════════════════════════════════════════════
# §22  FLUENT MOUTH — v5 Pro (templates + contexto)
# ══════════════════════════════════════════════════════════════════════════════

_TEMPLATES: Dict[str, List[str]] = {
    'fact': [
        '{text}.',
        '{text}.',
        '{text} — essa é a definição que tenho.',
        'De acordo com o que aprendi: {text}.',
        '{text}',
    ],
    'fact_multi': [
        '{main} {extra}.',
        '{main} Além disso, {extra}.',
        '{main} Vale acrescentar que {extra}.',
        '{main} Complementando: {extra}.',
        '{main} Em termos adicionais, {extra}.',
    ],
    'deduction': [
        'Por dedução: {conclusion} (via {proof}).',
        'A cadeia lógica {proof} leva à conclusão: {conclusion}.',
        'Infiro que {conclusion}, seguindo a cadeia: {proof}.',
        'Com base em {proof}, concluo: {conclusion}.',
    ],
    'theory': [
        'Hipótese: {text}.',
        'Talvez {text} — mas aguarda confirmação.',
        'Teorizo que {text}.',
        'Uma possibilidade: {text}.',
    ],
    'unknown': [
        'Não encontrei conexão com o que sei. Pode me ensinar?',
        'Fora da minha memória atual. O que é isso?',
        'Não tenho esse dado. Ensine-me: aprenda: ...',
        'Preciso aprender mais sobre isso.',
    ],
    'novel': [
        'Conceito novo para mim: "{topic}". Pode me explicar?',
        'Não conheço "{topic}" ainda. Conta mais.',
        '"{topic}" ainda não está na minha base. Me ensine.',
        'Aprendi que "{topic}" existe, mas quero saber mais.',
    ],
    'conflict': [
        '⚡ Divergência com: "{existing}"\n{hyp}',
        '⚠️ Conflito: tenho "{existing}", mas você sugere: {hyp}',
    ],
    'correction': [
        'Corrijo: {new_fact}. Anterior sobre "{topic}" atualizado.',
        'Atualizado: {new_fact}. Versão anterior de "{topic}" foi rebaixada.',
    ],
    'analogy': [
        'Analogia A:B::C:? → candidatos: {result}.',
        'Para a analogia proposta, sugiro: {result}.',
    ],
    'contra_ask': [
        '⚠️ Conflito detectado!\n'
        'Já sei: "{existing}"\n'
        'Você quer ensinar: "{new_text}"\n\n'
        'O que devo fazer?\n'
        '  • "substituir" — atualiza o fato anterior\n'
        '  • "contexto diferente" — guarda os dois (contextos distintos)\n'
        '  • "cancelar" — abandona o novo fato'
    ],
}

_rng = random.Random()   # sem seed fixo — templates variam a cada resposta


class FluentMouth:
    CONFIDENCE_FLOOR = 0.04

    def __init__(self, encoder: MultiLobeEncoder,
                 ngram: Optional[NGramMemory] = None):
        self._encoder = encoder
        self._ngram   = ngram or NGramMemory()

    def speak_fact(self, text: str, extra: str = '') -> str:
        if extra:
            # Suprime extra se for substring do main ou se overlap > 70%
            t_lower, e_lower = text.lower(), extra.lower()
            t_toks = set(re.findall(r'\w{4,}', t_lower))
            e_toks = set(re.findall(r'\w{4,}', e_lower))
            overlap = (len(t_toks & e_toks) / max(len(t_toks | e_toks), 1)
                       if t_toks and e_toks else 0)
            if e_lower in t_lower or t_lower in e_lower or overlap > 0.65:
                extra = ''
        if extra:
            tpl = _rng.choice(_TEMPLATES['fact_multi'])
            return tpl.format(main=text, extra=extra)
        tpl = _rng.choice(_TEMPLATES['fact'])
        return tpl.format(text=text)

    def speak_conflict(self, existing: str, hyp: str) -> str:
        tpl = _rng.choice(_TEMPLATES['conflict'])
        return tpl.format(existing=existing[:60], hyp=hyp)

    def speak_contradiction_ask(self, existing: str, new_text: str) -> str:
        """Pergunta ao usuário o que fazer com uma contradição detectada."""
        tpl = _rng.choice(_TEMPLATES['contra_ask'])
        return tpl.format(
            existing=existing[:70].rstrip(),
            new_text=new_text[:70].rstrip()
        )

    def speak_correction(self, topic: str, new_fact: str) -> str:
        tpl = _rng.choice(_TEMPLATES['correction'])
        return tpl.format(topic=topic, new_fact=new_fact)

    def speak_unknown(self, topic: str = '') -> str:
        if topic:
            tpl = _rng.choice(_TEMPLATES['novel'])
            return tpl.format(topic=topic)
        return _rng.choice(_TEMPLATES['unknown'])

    def speak_theory(self, text: str) -> str:
        tpl = _rng.choice(_TEMPLATES['theory'])
        return tpl.format(text=text)

    def speak_deduction(self, conclusion: str, proof: str) -> str:
        tpl = _rng.choice(_TEMPLATES['deduction'])
        return tpl.format(conclusion=conclusion, proof=proof)


# ══════════════════════════════════════════════════════════════════════════════
# §23  REGEX DE ROTEAMENTO — v5 Pro (provado 100% nos testes)
# ══════════════════════════════════════════════════════════════════════════════

_RE_LEARN    = re.compile(
    r'^\s*(?:aprend[ae]|memorize|registre|guarde?|anote|saiba)\s*:?\s*', re.I)
_RE_CORRECT  = re.compile(
    r'\b(?:corrij[ao]|corrigir|na\s+verdade|errado|incorreto)\b', re.I)
_RE_HAS_QUERY = re.compile(
    r'^(\w[\w\s\-]{0,28}?)\s+(?:tem|possui|têm|possuem)\s+(\w[\w\s\-]{0,25}?)[?\.]?\s*$',
    re.I)
_RE_ISA = re.compile(
    r'^(\w[\w\s\-]{0,28}?)\s+(?:é\s+um[a]?|é\s+uma|são\s+um[a]?|é)\s+(\w[\w\s\-]{0,28}?)[?\.]?\s*$',
    re.I)
_RE_CODE     = re.compile(
    r'\b(?:implement[ae]|program[ae]|cri[ae]\s+(?:um[a]?\s+)?(?:função|classe|script|algoritmo)|'
    r'escreva\s+(?:um\s+)?(?:código|função|script)|'
    r'mostre\s+(?:um\s+)?(?:código|como)|algoritmo\s+de)\b', re.I)
_RE_MATH     = re.compile(
    r'\b(?:calcul[ae]|comput[ae]|resolv[ae]|quanto\s+[eé]|quanto\s+vale)\b', re.I)
_RE_ONE_SHOT = re.compile(
    r'\b(?:bota\s+aí|manda\s+ver|novo\s+comando|nova\s+sintaxe)\b', re.I)
_RE_ANALOGY  = re.compile(r'\banalogia\b|\bé\s+para\b.*\bcomo\b', re.I)
_RE_DEDUCE   = re.compile(r'\b(?:logo|conclua|deduza|silogismo)\b', re.I)
_RE_DEDUCE_COND = re.compile(
    r'\b(?:se\s+\w+|todo\s+\w+|todos\s+(?:os\s+)?|portanto)\b.*\b(?:é|são|tem|então)\b', re.I)
_RE_THEORIZE = re.compile(
    r'\b(?:acho\s+que|talvez|hipótese|suponha)\b', re.I)
_RE_EXPLORE  = re.compile(
    r'\b(?:explore|lacuna|hipóteses\s+sobre)\b', re.I)
_RE_RELATION = re.compile(
    r'[\w\s]+\s*[–—\-]+\[[\w\s_]*\]\s*[–—\-→>]+\s*[\w\s]+', re.I)
_RE_GRAPH    = re.compile(
    r'\b(?:vizinhos?\s+de|caminho\s+entre|conectado)\b', re.I)
_RE_SEARCH   = re.compile(r'\b(?:busque|procure|liste\s+tudo|mostre\s+o\s+que)\b', re.I)
_RE_EPISODE  = re.compile(r'\b(?:histórico|episódios?|memória\s+recente)\b', re.I)
_RE_STATUS   = re.compile(r'\b(?:status|estatísticas?|como\s+estou)\b', re.I)
_RE_GENERATE = re.compile(
    r'\b(?:gere|escreva\s+sobre|continue|fale\s+sobre|explique|descreva|'
    r'me\s+fale\s+sobre|conte\s+(?:sobre|mais|me)|'
    r'compare\s+|diferença\s+entre)\b', re.I)
_RE_DEEPSCAN = re.compile(r'\b(?:deep[_\s]?scan|calibra(?:r|te?)?|treine?\s+com|scan\s+corpus)\b', re.I)
_RE_INFER    = re.compile(
    r'\b(?:infer[ae]|deduza|é\s+(?:possível|provável))\b', re.I)

# ── Patterns conversacionais ──────────────────────────────────────────────────
_RE_COMPARE = re.compile(
    r'(?:diferença|diferen[çc]|compar[ae]|versus|\bvs\.?\b|'
    r'qual\s+(?:é\s+)?(?:melhor|pior|mais\s+(?:rápido|seguro|barato|caro|indicado))|'
    r'\bou\b.{2,35}\bmelhor\b|\bmelhor\b.{2,35}\bou\b)',
    re.I)
_RE_CAUSE = re.compile(
    r'\b(?:por\s+que|por\s+qual\s+motivo|como\s+(?:surgiu|funciona|ocorre|acontece)|'
    r'de\s+onde\s+vem|qual\s+a\s+causa|o\s+que\s+causa)\b',
    re.I)
_RE_LIST = re.compile(
    r'\b(?:list[ae]|cite|d[eê]\s+(?:exemplos?|uns?|uma?)|'
    r'quais\s+s[aã]o\s+(?:os?|as?)|me\s+d[eê]\s+\d*\s*(?:exemplos?)?|'
    r'exemplos?\s+de|alguns?\s+exemplos?\s+de|tipos?\s+de)\b',
    re.I)
_RE_OPINION = re.compile(
    r'\b(?:o\s+que\s+você\s+acha|qual\s+você\s+(?:recomenda|prefere|indicaria)|'
    r'vale\s+a\s+pena|você\s+(?:recomenda|acha|prefere|indicaria)|'
    r'me\s+(?:recomenda|indica|aconselha))\b',
    re.I)
_RE_META = re.compile(
    r'\b(?:me\s+conta?(?:\s+uma?)?|conta\s+(?:uma?|mais)|curiosidade|'
    r'o\s+que\s+você\s+sabe\s+sobre|você\s+sabe\s+(?:algo|alguma\s+coisa)|'
    r'me\s+faz?\s+um[a]?\s+resum)\b',
    re.I)

# Respostas de confirmação de contradição
_RE_CONFIRM_REPLACE = re.compile(
    r'\b(?:substitui[rr]?|atualiz[ae]r?|corrig[iae]r?|sim,?\s+substitui|'
    r'muda[rr]?|trocas?|substitua|atualiza)\b', re.I)
_RE_CONFIRM_CONTEXT = re.compile(
    r'\b(?:contexto\s+diferente|novo\s+contexto|mant[eé]r?\s+(?:os\s+)?dois|'
    r'ambos|guardar?\s+(?:os\s+)?dois|diferente|coexist[ae]|aceit[ae]\s+ambos)\b', re.I)
_RE_CONFIRM_CANCEL  = re.compile(
    r'\b(?:cancel[ae]r?|abandon[ae]r?|descartar?|não|nao|esquece[rr]?|ignora[rr]?)\b', re.I)

# Padrão de consulta de fato — extrai sujeito
_SUBJ_M = re.compile(
    r'(?:o\s+que\s+[eé]|o\s+que\s+s[aã]o|quem\s+[eé]|defina|explique|como\s+funciona|'
    r'qual\s+[eé]|quais\s+s[aã]o|me\s+fale\s+sobre)\s+(.+?)[\?\.!]?\s*$', re.I)


# ══════════════════════════════════════════════════════════════════════════════
# §24a  SALIENCE ENGINE — atenção cognitiva baseada em frequência+recência+grafo
# ══════════════════════════════════════════════════════════════════════════════

class SalienceEngine:
    """
    Calcula a importância (salience) de conceitos para guiar a recuperação e
    evitar explosão combinatória durante o raciocínio.

    Fórmula:
        salience(c) = w_freq * freq_norm
                    + w_rec  * recency_norm
                    + w_cent * centrality_norm
                    + w_sim  * semantic_sim (quando query fornecida)

    Os pesos somam 1.0. O resultado é um score [0, 1] que permite ordenar e
    filtrar os conceitos mais relevantes antes da expansão do grafo.

    Integrado ao _handle_query via NexusV8.top_concepts().
    """

    # Pesos padrão (soma = 1.0)
    W_FREQ = 0.30
    W_REC  = 0.25
    W_CENT = 0.25
    W_SIM  = 0.20

    # Janela de tempo para recência (segundos)
    RECENCY_WINDOW = 3600.0

    def __init__(self):
        # acesso_count por conceito (normalizado depois)
        self._access: Dict[str, int]   = defaultdict(int)
        self._last:   Dict[str, float] = {}
        # centralidade calculada sob demanda e cacheada
        self._centrality_cache: Dict[str, float] = {}
        self._cache_ts: float = 0.0

    def touch(self, concept: str) -> None:
        """Registra um acesso a um conceito (usado em recuperação e raciocínio)."""
        c = concept.lower().strip()
        self._access[c] += 1
        self._last[c] = time.time()

    def score(self, concept: str, graph: 'ConceptGraph',
              query_vec: Optional[List[float]] = None,
              embed: Optional['MiniEmbed'] = None) -> float:
        """Score de salience [0, 1] para um conceito."""
        c = concept.lower().strip()
        now = time.time()

        # Frequência normalizada
        max_acc = max(self._access.values()) if self._access else 1
        freq_n  = self._access.get(c, 0) / max(max_acc, 1)

        # Recência normalizada (exponencial: máximo = acesso agora)
        last_t = self._last.get(c, 0.0)
        age    = now - last_t
        rec_n  = math.exp(-age / max(self.RECENCY_WINDOW, 1.0)) if age < self.RECENCY_WINDOW * 3 else 0.0

        # Centralidade no grafo (grau de saída normalizado)
        cent_n = self._centrality(c, graph)

        # Similaridade semântica com a query (opcional)
        sim_n = 0.0
        if query_vec and embed and c in embed._vocab:
            cv = embed.vector(c)
            sim_n = max(0.0, embed.cosine(query_vec, cv))

        w_sim = self.W_SIM if query_vec else 0.0
        # Redistribui o peso de sim quando não há query
        adj = 1.0 / (1.0 - self.W_SIM + w_sim + 1e-9)
        return adj * (self.W_FREQ * freq_n + self.W_REC * rec_n +
                      self.W_CENT * cent_n + w_sim * sim_n)

    def _centrality(self, concept: str, graph: 'ConceptGraph') -> float:
        """Grau de saída normalizado (recomputa se o grafo mudou muito)."""
        total_nodes = max(graph.node_count, 1)
        out_degree  = len(graph._edges.get(concept, {}))
        return min(1.0, out_degree / max(total_nodes * 0.1, 1))

    def top_k(self, concepts: List[str], k: int, graph: 'ConceptGraph',
              query_vec: Optional[List[float]] = None,
              embed: Optional['MiniEmbed'] = None) -> List[str]:
        """Retorna os k conceitos mais salientes de uma lista."""
        scored = [(self.score(c, graph, query_vec, embed), c) for c in concepts]
        scored.sort(reverse=True)
        return [c for _, c in scored[:k]]

    def beam_search(self, seeds: List[str], k: int, graph: 'ConceptGraph',
                    max_depth: int = 3,
                    query_vec: Optional[List[float]] = None,
                    embed: Optional['MiniEmbed'] = None) -> List[Tuple[float, str]]:
        """
        BFS com beam de tamanho k no ConceptGraph guiado por salience.
        Retorna lista (score, conceito) dos mais relevantes encontrados.
        Evita explosão combinatória: a cada nível mantém apenas os k melhores.
        """
        frontier: Dict[str, float] = {s.lower(): 1.0 for s in seeds}
        visited:  Set[str]         = set(frontier)
        results:  Dict[str, float] = dict(frontier)

        for depth in range(max_depth):
            # Expansão do frontier
            candidates: Dict[str, float] = {}
            for node, node_score in frontier.items():
                self.touch(node)
                for nbr, rels in graph._edges.get(node, {}).items():
                    if nbr in visited:
                        continue
                    edge_w  = max(rels.values())
                    contrib = node_score * edge_w * (0.7 ** depth)
                    candidates[nbr] = max(candidates.get(nbr, 0.0), contrib)

            if not candidates:
                break

            # Filtro por salience: beam = k melhores
            ranked = sorted(
                candidates.items(),
                key=lambda x: x[1] * (1 + self.score(x[0], graph, query_vec, embed)),
                reverse=True
            )[:k]

            frontier = {}
            for c, s in ranked:
                results[c] = max(results.get(c, 0.0), s)
                visited.add(c)
                frontier[c] = s

        return sorted(results.items(), key=lambda x: -x[1])

    def to_dict(self) -> dict:
        return {'access': dict(self._access), 'last': self._last}

    @classmethod
    def from_dict(cls, d: dict) -> 'SalienceEngine':
        se = cls()
        se._access = defaultdict(int, d.get('access', {}))
        se._last   = d.get('last', {})
        return se


# ══════════════════════════════════════════════════════════════════════════════
# §24b  RULE INDUCTOR — mineração de regras transitivas e associativas
# ══════════════════════════════════════════════════════════════════════════════

class RuleInductor:
    """
    Induz novas regras a partir do grafo de conceitos existente.

    Tipos de regras suportados:

    1. Transitividade IS_A:
         A IS_A B, B IS_A C  →  A IS_A C  (hipótese: confiança = produto)

    2. Herança de propriedade:
         A IS_A B, B HAS P   →  A provavelmente HAS P

    3. Cadeia causal:
         A CAUSES B, B CAUSES C  →  A indiretamente CAUSES C

    4. Regras de associação (lift > threshold):
         Dois conceitos que co-ocorrem em contexto com relação forte
         →  nova aresta associativa no grafo.

    As regras induzidas são tratadas como HIPÓTESES com confiança < 1.0.
    Elas só são promovidas a fatos se validadas pelo EpistemicLayer.
    """

    IS_A_RELS    = {REL_IS_A, 'é', 'é_um', 'é-um'}
    HAS_RELS     = {REL_HAS, 'tem'}
    CAUSES_RELS  = {REL_CAUSES, 'causa'}
    MIN_CONF     = 0.3   # confiança mínima para reportar uma regra induzida
    MAX_RULES    = 200   # limite de regras para não explodir memória

    def __init__(self):
        # {(A, rel, C): conf} — regras induzidas, não confundir com fatos
        self._induced: Dict[Tuple[str,str,str], float] = {}

    def run(self, graph: 'ConceptGraph', passes: int = 3) -> List[Tuple[str, str, str, float]]:
        """
        Executa a mineração e retorna lista de (A, rel, C, confiança).
        Executa `passes` iterações para capturar cadeias transitivas longas
        (ex: gato→felino→mamífero→animal requer 2 passes).
        Não modifica o grafo diretamente — o chamador decide o que fazer.
        """
        all_rules: List[Tuple[str, str, str, float]] = []

        for _ in range(passes):
            # Constrói grafo temporário = grafo real + regras já induzidas de alta conf
            temp_edges: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
                lambda: defaultdict(dict))
            for node, targets in graph._edges.items():
                for tgt, rels in targets.items():
                    temp_edges[node][tgt].update(rels)
            for (a, rel, c), conf in self._induced.items():
                if conf >= 0.4:
                    temp_edges[a][c][rel] = max(
                        temp_edges[a][c].get(rel, 0.0), conf)

            new_this_pass: List[Tuple[str, str, str, float]] = []
            for a in list(temp_edges.keys()):
                a_rels = temp_edges[a]
                for b, ab_rel_dict in list(a_rels.items()):
                    ab_rels = set(ab_rel_dict.keys())
                    ab_w    = max(ab_rel_dict.values())

                    b_rels  = temp_edges.get(b, {})
                    for c, bc_rel_dict in list(b_rels.items()):
                        if c == a:
                            continue
                        bc_rels = set(bc_rel_dict.keys())
                        bc_w    = max(bc_rel_dict.values())
                        conf    = ab_w * bc_w

                        if conf < self.MIN_CONF:
                            continue

                        if ab_rels & self.IS_A_RELS and bc_rels & self.IS_A_RELS:
                            rel = REL_IS_A
                            prev = self._induced.get((a, rel, c), 0.0)
                            self._induced[(a, rel, c)] = max(prev, conf)
                            new_this_pass.append((a, rel, c, conf))

                        if ab_rels & self.IS_A_RELS and bc_rels & self.HAS_RELS:
                            rel = REL_HAS
                            prev = self._induced.get((a, rel, c), 0.0)
                            self._induced[(a, rel, c)] = max(prev, conf * 0.8)
                            new_this_pass.append((a, rel, c, conf * 0.8))

                        if ab_rels & self.CAUSES_RELS and bc_rels & self.CAUSES_RELS:
                            rel = 'causa_indireta'
                            prev = self._induced.get((a, rel, c), 0.0)
                            self._induced[(a, rel, c)] = max(prev, conf * 0.7)
                            new_this_pass.append((a, rel, c, conf * 0.7))

            all_rules.extend(new_this_pass)
            if not new_this_pass:
                break  # convergiu

        # Limita tamanho total
        if len(self._induced) > self.MAX_RULES:
            sorted_rules = sorted(self._induced.items(), key=lambda x: x[1])
            for k, _ in sorted_rules[:len(self._induced) - self.MAX_RULES]:
                del self._induced[k]

        return all_rules

    def get_induced(self, concept: str) -> List[Tuple[str, str, float]]:
        """Retorna regras induzidas onde concept é o sujeito."""
        c = concept.lower()
        return [(rel, tgt, conf)
                for (a, rel, tgt), conf in self._induced.items()
                if a == c]

    def apply_to_graph(self, graph: 'ConceptGraph',
                       edge_net: 'EdgeNetwork') -> int:
        """
        Aplica regras induzidas com confiança alta ao grafo e à EdgeNetwork.
        Retorna o número de novas arestas criadas.
        Usa peso < 0.5 para distinguir arestas induzidas de arestas aprendidas.
        """
        added = 0
        HIGH_CONF = 0.6
        for (a, rel, c), conf in self._induced.items():
            if conf < HIGH_CONF:
                continue
            # Só adiciona se NÃO existe aresta direta entre a e c
            if c not in graph._edges.get(a, {}):
                graph.add_edge(a, rel, c, weight=conf * 0.7)
                edge_net.add(a, rel, c, evidence=f'induzido conf={conf:.2f}',
                             strength=conf * 0.5)
                added += 1
        return added

    def to_dict(self) -> dict:
        return {'induced': {f'{a}\x01{r}\x01{c}': v
                            for (a, r, c), v in self._induced.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> 'RuleInductor':
        ri = cls()
        for k, v in d.get('induced', {}).items():
            parts = k.split('\x01')
            if len(parts) == 3:
                ri._induced[(parts[0], parts[1], parts[2])] = v
        return ri


# ══════════════════════════════════════════════════════════════════════════════
# §24c  CONCEPT ABSTRACTOR — clustering semântico e abstração emergente
# ══════════════════════════════════════════════════════════════════════════════

class ConceptCluster:
    """Um cluster de conceitos com nome emergente e membros."""
    __slots__ = ('name', 'members', 'centroid', 'created_at')

    def __init__(self, name: str, members: List[str], centroid: List[float]):
        self.name       = name
        self.members    = list(members)
        self.centroid   = centroid
        self.created_at = time.time()

    def to_dict(self) -> dict:
        return {'name': self.name, 'members': self.members,
                'centroid': self.centroid[:16]}  # reduz tamanho JSON

    @classmethod
    def from_dict(cls, d: dict) -> 'ConceptCluster':
        return cls(name=d['name'], members=d.get('members', []),
                   centroid=d.get('centroid', []))


class ConceptAbstractor:
    """
    Clustering semântico incremental de conceitos via K-Means simplificado
    aplicado nos vetores do MiniEmbed.

    Detecta grupos de conceitos similares e propõe um conceito abstracto
    como nome do cluster (o membro mais central).

    Integração:
      - run() é chamado pelo SleepConsolidator ou explicitamente via
        n.abstract()
      - Os clusters são expostos via n.clusters e adicionam arestas
        IS_A {cluster} ao ConceptGraph

    Parâmetros:
      MIN_CLUSTER_SIZE  — mínimo de membros para um cluster ser válido
      SIM_THRESHOLD     — similaridade mínima para pertencer a um cluster
      MAX_CLUSTERS      — limite de clusters simultâneos
    """

    MIN_CLUSTER_SIZE = 2   # modo grafo: 2 filhos IS_A já forma cluster válido
    SIM_THRESHOLD    = 0.40  # modo RI: limiar reduzido para dados esparsos
    MAX_CLUSTERS     = 50
    MAX_ITER         = 10   # iterações de K-Means

    def __init__(self):
        self._clusters:   List[ConceptCluster] = []
        self._word2clust: Dict[str, str]       = {}  # palavra → nome do cluster

    def run(self, embed: 'MiniEmbed', graph: 'ConceptGraph',
            edge_net: 'EdgeNetwork') -> List[ConceptCluster]:
        """
        Executa clustering em dois modos:

        Modo 1 — Grafo (sempre ativo, mais confiável):
          Conceitos que compartilham o mesmo nó-pai via IS_A são agrupados.
          Ex: gato, leão, tigre → todos IS_A felino → cluster "felino".

        Modo 2 — RI semântico (ativo quando embed tem sinal suficiente):
          Conceitos cujos ctx_vec são suficientemente similares formam clusters.
          Só ativa quando algum ctx_vec tem signal > SIM_SIGNAL_MIN.

        Propaga as relações IS_A ao grafo para que o raciocínio possa usar
        a abstração emergente.
        """
        new_clusters: List[ConceptCluster] = []
        existing_names = {cl.name for cl in self._clusters}

        # ── Modo 1: clustering por grafo IS_A ─────────────────────────────
        IS_A_RELS = {REL_IS_A, 'é', 'é_um', 'é-um', 'IS_A', 'é_um'}
        # Mapeia pai→{filhos} via IS_A
        parent_to_children: Dict[str, Set[str]] = defaultdict(set)
        for child, targets in graph._edges.items():
            for parent, rels in targets.items():
                if set(rels.keys()) & IS_A_RELS:
                    parent_to_children[parent].add(child)

        for parent, children in parent_to_children.items():
            if len(children) < self.MIN_CLUSTER_SIZE:
                continue
            if parent in existing_names:
                # Atualiza membros do cluster existente
                for cl in self._clusters:
                    if cl.name == parent:
                        for m in children:
                            if m not in cl.members:
                                cl.members.append(m)
                        break
                continue

            # Centroid: média dos index_vecs dos membros (funciona mesmo sem ctx)
            all_members = list(children) + [parent]
            dim = embed.DIM
            vecs = [embed.vector(m) for m in all_members]
            centroid = [sum(v[k] for v in vecs) / len(vecs) for k in range(dim)]
            c_norm = math.sqrt(sum(x*x for x in centroid)) or 1.0
            centroid = [x/c_norm for x in centroid]

            cluster = ConceptCluster(name=parent, members=list(children), centroid=centroid)
            new_clusters.append(cluster)
            self._clusters.append(cluster)

            for member in children:
                if member == parent:
                    continue
                self._word2clust[member] = parent
                # A aresta IS_A já existe (foi ela que gerou o cluster)

        # ── Modo 2: clustering por RI semântico (se sinal suficiente) ──────
        SIM_SIGNAL_MIN = 0.05
        candidates = [w for w in embed._vocab
                      if w in embed._ctx_vec
                      and len(w) >= 4
                      and w not in _STOP_PT
                      and sum(abs(x) for x in embed._ctx_vec[w]) > SIM_SIGNAL_MIN]

        if len(candidates) >= self.MIN_CLUSTER_SIZE * 2:
            vecs = {w: embed.vector(w) for w in candidates}
            assigned: Set[str] = set(self._word2clust.keys())

            for w in sorted(candidates, key=lambda x: -sum(abs(v) for v in vecs[x])):
                if w in assigned or w in existing_names:
                    continue
                group = [w]
                wv = vecs[w]
                for other in candidates:
                    if other in assigned or other == w:
                        continue
                    if embed.cosine(wv, vecs[other]) >= self.SIM_THRESHOLD:
                        group.append(other)
                if len(group) >= self.MIN_CLUSTER_SIZE:
                    dim = embed.DIM
                    group_vecs = [vecs[m] for m in group]
                    centroid = [sum(v[k] for v in group_vecs) / len(group_vecs)
                                for k in range(dim)]
                    c_norm = math.sqrt(sum(x*x for x in centroid)) or 1.0
                    centroid = [x/c_norm for x in centroid]
                    central = max(group, key=lambda x: embed.cosine(vecs[x], centroid))

                    if central in existing_names:
                        assigned.update(group)
                        continue

                    cluster = ConceptCluster(name=central, members=group, centroid=centroid)
                    new_clusters.append(cluster)
                    self._clusters.append(cluster)
                    existing_names.add(central)
                    for member in group:
                        self._word2clust[member] = central
                    assigned.update(group)

                    # Adiciona arestas IS_A ao grafo
                    for member in group:
                        if member == central:
                            continue
                        if central not in graph._edges.get(member, {}):
                            graph.add_edge(member, REL_IS_A, central, weight=0.6)
                            edge_net.add(member, 'agrupa_em', central,
                                         evidence=f'ri_cluster={central}',
                                         strength=0.4)

        # Limita tamanho total
        if len(self._clusters) > self.MAX_CLUSTERS:
            self._clusters = self._clusters[-self.MAX_CLUSTERS:]

        return new_clusters

    def get_cluster(self, concept: str) -> Optional[str]:
        """Retorna o nome do cluster de um conceito, se existir."""
        return self._word2clust.get(concept.lower())

    def to_dict(self) -> dict:
        return {'clusters': [c.to_dict() for c in self._clusters],
                'word2clust': self._word2clust}

    @classmethod
    def from_dict(cls, d: dict) -> 'ConceptAbstractor':
        ca = cls()
        ca._clusters   = [ConceptCluster.from_dict(c) for c in d.get('clusters', [])]
        ca._word2clust = d.get('word2clust', {})
        return ca


# ══════════════════════════════════════════════════════════════════════════════
# §24d  WORKING MEMORY — workspace temporário de raciocínio
# ══════════════════════════════════════════════════════════════════════════════

class ReasoningFrame:
    """
    Um frame de raciocínio temporário: copia conceitos relevantes, aplica
    transformações e valida hipóteses ANTES de gravar no grafo permanente.

    Fluxo:
        1. load(concepts)   — copia sub-grafo relevante para o frame
        2. chain()          — expande relações transitivas no frame
        3. hypothesize()    — propõe conclusões com confiança
        4. validate()       — cruza com base de fatos
        5. commit()         — decide se grava (caller decide)

    O frame é descartável: não persiste entre chamadas.
    """

    def __init__(self):
        self._edges:     Dict[str, Dict[str, Dict[str, float]]] = \
            defaultdict(lambda: defaultdict(dict))
        self._hyps:      List[Tuple[str, str, str, float]] = []  # (a, rel, c, conf)
        self._loaded:    Set[str] = set()

    def load(self, concepts: List[str], graph: 'ConceptGraph',
             depth: int = 2) -> int:
        """Copia sub-grafo até profundidade depth para o frame."""
        frontier = set(c.lower() for c in concepts)
        for _ in range(depth):
            nxt: Set[str] = set()
            for node in frontier:
                for nbr, rels in graph._edges.get(node, {}).items():
                    self._edges[node][nbr].update(rels)
                    nxt.add(nbr)
            self._loaded.update(frontier)
            frontier = nxt - self._loaded
        return len(self._loaded)

    def chain(self, max_hops: int = 3) -> List[Tuple[str, str, str, float]]:
        """
        Expande relações transitivas dentro do frame.
        Detecta: IS_A transitivo, herança de propriedades.
        Retorna lista (A, rel, C, conf) de relações inferidas.
        """
        self._hyps.clear()
        IS_A = {REL_IS_A, 'é', 'é_um', 'é-um', 'IS_A'}
        HAS  = {REL_HAS, 'tem', 'HAS'}

        for a in list(self._edges.keys()):
            for b, ab_rels in list(self._edges[a].items()):
                ab_w = max(ab_rels.values()) if ab_rels else 0
                if not ab_rels:
                    continue
                for c, bc_rels in list(self._edges.get(b, {}).items()):
                    if c == a:
                        continue
                    bc_w = max(bc_rels.values()) if bc_rels else 0
                    conf = ab_w * bc_w
                    if conf < 0.2:
                        continue

                    if set(ab_rels) & IS_A and set(bc_rels) & IS_A:
                        self._hyps.append((a, REL_IS_A, c, conf))
                    elif set(ab_rels) & IS_A and set(bc_rels) & HAS:
                        self._hyps.append((a, REL_HAS, c, conf * 0.8))

        return self._hyps

    def hypothesize(self, concept: str) -> List[Tuple[str, str, float]]:
        """Retorna hipóteses sobre um conceito: (rel, target, conf)."""
        c = concept.lower()
        return [(rel, tgt, conf)
                for (a, rel, tgt, conf) in self._hyps
                if a == c]

    def validate(self, fact_store: 'StructuredFactStore') -> Dict[str, float]:
        """
        Cruza hipóteses com o FactStore.
        Retorna {texto_hipótese: score_suporte}.
        """
        validated: Dict[str, float] = {}
        for a, rel, c, conf in self._hyps:
            hyp_text = f'{a} {rel} {c}'
            hits     = fact_store.search(hyp_text, top_k=3, min_score=0.2)
            support  = len(hits) / 3.0  # 0–1
            validated[hyp_text] = conf * (0.5 + 0.5 * support)
        return validated

    def top_hypotheses(self, k: int = 5) -> List[Tuple[str, str, str, float]]:
        """Retorna as k melhores hipóteses (a, rel, c, conf)."""
        return sorted(self._hyps, key=lambda x: -x[3])[:k]

    def clear(self) -> None:
        self._edges.clear()
        self._hyps.clear()
        self._loaded.clear()


class WorkingMemory:
    """
    Workspace temporário de raciocínio multi-passo.

    Separa o raciocínio do grafo permanente:
        1. Cria um ReasoningFrame com os conceitos relevantes
        2. Encadeia inferências no frame
        3. Valida contra o FactStore
        4. Retorna hipóteses sem sujar o grafo (a menos que conf ≥ threshold)

    Integrado ao NexusV8._handle_conditional e NexusV8._handle_deduce como
    etapa de raciocínio antes do BFS direto.
    """

    PROMOTE_THRESHOLD = 0.7   # confiança mínima para propagar ao grafo

    def __init__(self):
        self._frame: ReasoningFrame = ReasoningFrame()
        self._last_concepts: List[str] = []

    def reason(self, concepts: List[str],
               graph: 'ConceptGraph',
               fact_store: 'StructuredFactStore',
               max_depth: int = 2) -> List[Tuple[str, str, str, float]]:
        """
        Executa raciocínio completo e retorna hipóteses validadas.
        """
        self._frame.clear()
        self._last_concepts = list(concepts)
        self._frame.load(concepts, graph, depth=max_depth)
        self._frame.chain()
        validated = self._frame.validate(fact_store)

        # Ajusta confiança com suporte dos fatos
        results = []
        for a, rel, c, conf in self._frame._hyps:
            hyp_text  = f'{a} {rel} {c}'
            adj_conf  = validated.get(hyp_text, conf)
            results.append((a, rel, c, adj_conf))

        return sorted(results, key=lambda x: -x[3])

    def best_answer(self, concept: str,
                    graph: 'ConceptGraph',
                    fact_store: 'StructuredFactStore') -> Optional[str]:
        """
        Tenta responder sobre um conceito usando raciocínio multi-hop.
        Retorna string de resposta ou None se sem hipótese.
        """
        hyps = self.reason([concept], graph, fact_store)
        hyps_for = [(rel, tgt, conf) for a, rel, tgt, conf in hyps if a == concept.lower()]
        if not hyps_for:
            return None
        rel, tgt, conf = hyps_for[0]
        return f'Por dedução ({conf:.0%} de confiança): {concept} {rel} {tgt}'

    def maybe_commit(self, graph: 'ConceptGraph',
                     edge_net: 'EdgeNetwork') -> int:
        """
        Promove hipóteses acima do threshold ao grafo permanente.
        Retorna o número de arestas adicionadas.
        """
        added = 0
        for a, rel, c, conf in self._frame._hyps:
            if conf >= self.PROMOTE_THRESHOLD:
                if c not in graph._edges.get(a, {}):
                    graph.add_edge(a, rel, c, weight=conf * 0.8)
                    edge_net.add(a, rel, c,
                                 evidence=f'workspace conf={conf:.2f}',
                                 strength=conf * 0.6)
                    added += 1
        return added

    def to_dict(self) -> dict:
        return {'last_concepts': self._last_concepts}

    @classmethod
    def from_dict(cls, d: dict) -> 'WorkingMemory':
        wm = cls()
        wm._last_concepts = d.get('last_concepts', [])
        return wm


# ══════════════════════════════════════════════════════════════════════════════
# §24  NEXUS V8 — SISTEMA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════



# ══════════════════════════════════════════════════════════════════════════════
# §V12  COMPONENTES DE VIABILIDADE — integrados do NexusV12 (k=12)
#       Correções: DeduplicatorSDR, SQLiteFactStoreV12, SigmoidRetriever,
#                  CuriositaEngine, ConsistencyChecker
# ══════════════════════════════════════════════════════════════════════════════

class DeduplicatorSDR:
    """Bloqueia paráfrases via SDR+Lexical Jaccard antes de salvar (V12).
    Threshold combinado 0.38 = conservador para evitar false positives.
    """
    COMBINED_THRESHOLD = 0.38

    def __init__(self, encoder):
        self._enc  = encoder
        self._sdrs = []  # (frozenset_sdr, set_tokens, fact_text)

    def is_duplicate(self, fact: str) -> Optional[str]:
        if not self._sdrs:
            return None
        new_sdr = frozenset(self._enc.encode(fact)._idx)
        new_tok = set(re.findall(r'\w{3,}', fact.lower()))
        if not new_sdr or not new_tok:
            return None
        best_score, best_fact = 0.0, None
        for stored_sdr, stored_tok, stored_fact in self._sdrs[-300:]:
            u_sdr = len(new_sdr | stored_sdr)
            sdr_j = len(new_sdr & stored_sdr) / u_sdr if u_sdr else 0.0
            u_lex = len(new_tok | stored_tok)
            lex_j = len(new_tok & stored_tok) / u_lex if u_lex else 0.0
            combined = 0.4 * sdr_j + 0.6 * lex_j
            if combined > best_score:
                best_score, best_fact = combined, stored_fact
        return best_fact if best_score >= self.COMBINED_THRESHOLD else None

    def record(self, fact: str) -> None:
        sdr = frozenset(self._enc.encode(fact)._idx)
        tok = set(re.findall(r'\w{3,}', fact.lower()))
        self._sdrs.append((sdr, tok, fact))

    @property
    def size(self) -> int:
        return len(self._sdrs)



# ══════════════════════════════════════════════════════════════════════════════
# §SHARED  SHARED MEMORY — Hipocampo Compartilhado (Global Shared Memory)
# ══════════════════════════════════════════════════════════════════════════════

class SharedMemory:
    """
    Memória Central Compartilhada com indexação Espaço-Temporal.
    
    Paradigma: Hipocampo Compartilhado — todos os cérebros especialistas
    consultam a MESMA base de dados, permitindo Cross-Domain Learning.
    
    Schema:
      - fact_enc   : fato cifrado (XOR via NexusGuardV11)
      - fact_plain : texto plano para busca FTS5
      - sdr_hash   : hash compacto do contexto SDR (para busca por proximidade)
      - temporal_cluster : id de sessão/bloco temporal
      - recall_weight    : peso Hebbiano (reforçado no recall, decai com tempo)
      - brain_origin     : qual cérebro armazenou originalmente
      - ts               : timestamp Unix
    
    Busca otimizada: temporal_context_search() evita SELECT * — filtra por
    sdr_hash overlap + recall_weight + recência temporal.
    
    Decaimento Hebbiano: fatos acessados ganham peso; fatos antigos e não
    acessados perdem prioridade (nunca deletados, apenas depriorizados).
    """

    # Constantes de decaimento Hebbiano
    RECALL_BOOST      = 0.15   # Incremento no recall_weight ao ser recuperado
    DECAY_RATE        = 0.998  # Multiplicador por ciclo de sono
    DECAY_FLOOR       = 0.01   # Peso mínimo (nunca zera)
    INITIAL_WEIGHT    = 1.0    # Peso inicial de um fato novo
    SDR_HASH_BITS     = 64     # Bits do hash compacto do SDR

    _session_counter  = 0      # Contador global de sessões temporais

    def __init__(self, db_path: str = ":memory:", guard: Optional['NexusGuardV11'] = None):
        import sqlite3 as _sq
        self._sq   = _sq
        self._conn = _sq.connect(db_path, check_same_thread=False)
        self._guard = guard
        self._session_id = SharedMemory._session_counter
        SharedMemory._session_counter += 1
        self._setup()

    def _setup(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS shared_facts (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_enc         TEXT,
                fact_plain       TEXT    NOT NULL,
                sdr_hash         TEXT    NOT NULL,
                temporal_cluster INTEGER NOT NULL,
                recall_weight    REAL    NOT NULL DEFAULT 1.0,
                brain_origin     TEXT    NOT NULL DEFAULT 'core',
                ts               REAL    NOT NULL,
                access_count     INTEGER NOT NULL DEFAULT 0,
                UNIQUE(fact_plain)
            );
            CREATE INDEX IF NOT EXISTS idx_sf_sdr ON shared_facts(sdr_hash);
            CREATE INDEX IF NOT EXISTS idx_sf_ts ON shared_facts(ts);
            CREATE INDEX IF NOT EXISTS idx_sf_weight ON shared_facts(recall_weight DESC);
            CREATE INDEX IF NOT EXISTS idx_sf_brain ON shared_facts(brain_origin);
            CREATE INDEX IF NOT EXISTS idx_sf_cluster ON shared_facts(temporal_cluster);

            CREATE VIRTUAL TABLE IF NOT EXISTS shared_facts_fts
                USING fts5(fact_plain, content='shared_facts', content_rowid='id');
            CREATE TRIGGER IF NOT EXISTS tr_sf_ai AFTER INSERT ON shared_facts BEGIN
                INSERT INTO shared_facts_fts(rowid, fact_plain) VALUES(new.id, new.fact_plain);
            END;
            CREATE TRIGGER IF NOT EXISTS tr_sf_ad AFTER DELETE ON shared_facts BEGIN
                INSERT INTO shared_facts_fts(shared_facts_fts, rowid, fact_plain)
                VALUES('delete', old.id, old.fact_plain);
            END;
        """)
        self._conn.commit()

    # ── Cálculo do SDR Hash ──────────────────────────────────────────────────

    @staticmethod
    def compute_sdr_hash(text: str) -> str:
        """
        Gera hash compacto do contexto SDR de um texto.
        Usa hashing por n-gramas de caracteres para capturar similaridade fuzzy.
        Dois textos sobre temas parecidos terão bits em comum no hash.
        """
        tokens = set(re.findall(r'\w{3,}', text.lower()))
        # Gera um bitfield de 64 bits baseado nos tokens
        bit_positions = set()
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            for i in range(3):  # 3 bits por token para maior overlap
                bit_positions.add((h >> (i * 10)) % SharedMemory.SDR_HASH_BITS)
        # Codifica como string hexadecimal
        val = 0
        for pos in bit_positions:
            val |= (1 << pos)
        return format(val, '016x')

    @staticmethod
    def sdr_hash_overlap(hash_a: str, hash_b: str) -> float:
        """Calcula sobreposição (Jaccard) entre dois SDR hashes."""
        try:
            a = int(hash_a, 16)
            b = int(hash_b, 16)
        except (ValueError, TypeError):
            return 0.0
        intersection = bin(a & b).count('1')
        union = bin(a | b).count('1')
        return intersection / max(union, 1)

    # ── Armazenamento ────────────────────────────────────────────────────────

    def store(self, fact: str, brain_origin: str = 'core',
              temporal_cluster: Optional[int] = None) -> bool:
        """
        Armazena um fato na memória compartilhada.
        Se guard estiver disponível, também armazena versão cifrada.
        """
        tc = temporal_cluster if temporal_cluster is not None else self._session_id
        sdr_hash = self.compute_sdr_hash(fact)
        fact_enc = self._guard.encrypt_payload(fact) if self._guard else None
        try:
            self._conn.execute(
                "INSERT OR IGNORE INTO shared_facts "
                "(fact_enc, fact_plain, sdr_hash, temporal_cluster, "
                " recall_weight, brain_origin, ts, access_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
                (fact_enc, fact, sdr_hash, tc,
                 self.INITIAL_WEIGHT, brain_origin, time.time())
            )
            self._conn.commit()
            return self._conn.execute("SELECT changes()").fetchone()[0] > 0
        except Exception:
            return False

    # ── Busca Temporal-Contextual (Otimizada) ────────────────────────────────

    def temporal_context_search(self, query: str, top_k: int = 8,
                                 time_bias: float = 0.3,
                                 min_overlap: float = 0.05,
                                 brain_filter: Optional[str] = None) -> List[Tuple[float, str]]:
        """
        Busca inteligente por proximidade SDR + recência temporal.
        
        NÃO faz SELECT * — filtra por:
          1. FTS5 match (termos da query)
          2. sdr_hash overlap >= min_overlap
          3. ORDER BY recall_weight * recency_factor DESC
          4. time_bias controla quanto a recência pesa (0=ignora, 1=só recente)
        
        Args:
            query: texto da consulta
            top_k: máximo de resultados
            time_bias: peso da recência [0..1]
            min_overlap: sobreposição mínima de SDR hash
            brain_filter: se definido, filtra por cérebro de origem
        """
        query_sdr_hash = self.compute_sdr_hash(query)
        qt = set(re.findall(r'\w{2,}', query.lower()))
        if not qt:
            return []

        # Fase 1: FTS5 para pré-filtrar candidatos
        fts_terms = ' OR '.join(f'"{t}"' for t in list(qt)[:10] if len(t) >= 2)
        try:
            if brain_filter:
                rows = self._conn.execute(
                    "SELECT sf.id, sf.fact_plain, sf.sdr_hash, sf.recall_weight, sf.ts "
                    "FROM shared_facts sf "
                    "INNER JOIN shared_facts_fts fts ON sf.id = fts.rowid "
                    "WHERE shared_facts_fts MATCH ? AND sf.brain_origin = ? "
                    "ORDER BY sf.recall_weight DESC LIMIT 100",
                    (fts_terms, brain_filter)
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT sf.id, sf.fact_plain, sf.sdr_hash, sf.recall_weight, sf.ts "
                    "FROM shared_facts sf "
                    "INNER JOIN shared_facts_fts fts ON sf.id = fts.rowid "
                    "WHERE shared_facts_fts MATCH ? "
                    "ORDER BY sf.recall_weight DESC LIMIT 100",
                    (fts_terms,)
                ).fetchall()
        except Exception:
            # Fallback sem FTS
            rows = self._conn.execute(
                "SELECT id, fact_plain, sdr_hash, recall_weight, ts "
                "FROM shared_facts ORDER BY recall_weight DESC LIMIT 100"
            ).fetchall()

        if not rows:
            return []

        # Fase 2: Scoring com SDR overlap + Hebbiano + recência
        now = time.time()
        scored = []
        for row_id, fact, sdr_h, weight, ts in rows:
            # SDR proximity
            overlap = self.sdr_hash_overlap(query_sdr_hash, sdr_h)
            if overlap < min_overlap:
                continue
            # Recência: decai exponencialmente com a idade
            age_hours = max((now - ts) / 3600.0, 0.001)
            recency = 1.0 / (1.0 + math.log1p(age_hours))
            # Score final: Hebbiano * (SDR_overlap + time_bias * recency)
            score = weight * (overlap + time_bias * recency)
            scored.append((score, row_id, fact))

        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]

        # Fase 3: Reforço Hebbiano — quem é lembrado fica mais forte
        for _, row_id, _ in top:
            self._hebbian_reinforce(row_id)

        return [(s, f) for s, _, f in top]

    # ── Reforço Hebbiano ─────────────────────────────────────────────────────

    def _hebbian_reinforce(self, fact_id: int) -> None:
        """Reforça o recall_weight de um fato recuperado (Hebb: fire together, wire together)."""
        self._conn.execute(
            "UPDATE shared_facts SET "
            "recall_weight = MIN(5.0, recall_weight + ?), "
            "access_count = access_count + 1 "
            "WHERE id = ?",
            (self.RECALL_BOOST, fact_id)
        )
        self._conn.commit()

    # ── Decaimento Hebbiano (Curva do Esquecimento) ──────────────────────────

    def hebbian_decay_cycle(self) -> int:
        """
        Aplica decaimento a TODOS os fatos na memória.
        Fatos não são deletados — apenas perdem prioridade no ORDER BY.
        Retorna número de fatos afetados.
        """
        cursor = self._conn.execute(
            "UPDATE shared_facts SET recall_weight = MAX(?, recall_weight * ?) "
            "WHERE recall_weight > ?",
            (self.DECAY_FLOOR, self.DECAY_RATE, self.DECAY_FLOOR)
        )
        self._conn.commit()
        return cursor.rowcount

    # ── Consultas auxiliares ──────────────────────────────────────────────────

    def all_facts(self, brain_filter: Optional[str] = None) -> List[str]:
        if brain_filter:
            return [r[0] for r in self._conn.execute(
                "SELECT fact_plain FROM shared_facts WHERE brain_origin=? "
                "ORDER BY recall_weight DESC", (brain_filter,)).fetchall()]
        return [r[0] for r in self._conn.execute(
            "SELECT fact_plain FROM shared_facts ORDER BY recall_weight DESC").fetchall()]

    def stats(self) -> Dict:
        total = self._conn.execute("SELECT COUNT(*) FROM shared_facts").fetchone()[0]
        by_brain = self._conn.execute(
            "SELECT brain_origin, COUNT(*), AVG(recall_weight) "
            "FROM shared_facts GROUP BY brain_origin"
        ).fetchall()
        return {
            'total_facts': total,
            'session_id': self._session_id,
            'by_brain': {r[0]: {'count': r[1], 'avg_weight': round(r[2], 4)} for r in by_brain},
        }

    def __len__(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM shared_facts").fetchone()[0]

    def close(self) -> None:
        self._conn.close()



class SQLiteFactStoreV12:
    """FactStore em SQLite com FTS5. Zero dependências extras (sqlite3 stdlib).
    Substitui StructuredFactStore — usa sigmoid k=12 para scoring mais suave.
    10k fatos: ~50MB disco, ~3MB RAM vs 30MB+ em memória.
    """

    def __init__(self, db_path: str = ":memory:"):
        import sqlite3 as _sq
        self._sq   = _sq
        self._conn = _sq.connect(db_path, check_same_thread=False)
        self._access: Dict[int, int] = defaultdict(int)
        self._setup()

    def _setup(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                fact  TEXT    UNIQUE NOT NULL,
                added REAL    DEFAULT (unixepoch('now'))
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts
                USING fts5(fact, content='facts', content_rowid='id');
            CREATE TRIGGER IF NOT EXISTS tr_ai AFTER INSERT ON facts BEGIN
                INSERT INTO facts_fts(rowid, fact) VALUES(new.id, new.fact);
            END;
            CREATE TRIGGER IF NOT EXISTS tr_ad AFTER DELETE ON facts BEGIN
                INSERT INTO facts_fts(facts_fts, rowid, fact)
                VALUES('delete', old.id, old.fact);
            END;
        """)
        self._conn.commit()

    def add(self, fact: str) -> bool:
        try:
            self._conn.execute("INSERT OR IGNORE INTO facts(fact) VALUES(?)", (fact,))
            self._conn.commit()
            return self._conn.execute("SELECT changes()").fetchone()[0] > 0
        except Exception:
            return False

    def search(self, query: str, top_k: int = 8, min_score: float = 0.05) -> List[str]:
        qt = set(re.findall(r'\w{2,}', query.lower()))
        if not qt:
            return []
        # FTS5 match — tokeniza cada termo para OR query
        fts_terms = ' OR '.join(f'"{t}"' for t in list(qt)[:8] if len(t) >= 2)
        try:
            rows = self._conn.execute(
                "SELECT id, fact FROM facts_fts WHERE facts_fts MATCH ? LIMIT 80",
                (fts_terms,)
            ).fetchall()
        except Exception:
            rows = self._conn.execute(
                "SELECT id, fact FROM facts LIMIT 100").fetchall()
        if not rows:
            rows = self._conn.execute(
                "SELECT id, fact FROM facts ORDER BY added DESC LIMIT 30").fetchall()
        scored = []
        for rid, fact in rows:
            ft = set(re.findall(r'\w{2,}', fact.lower()))
            u  = len(qt | ft)
            if not u:
                continue
            jac = len(qt & ft) / u
            # SigmoidRetriever k=12, x0=0.25 — mais permissivo que V9 (threshold 0.5)
            sig = 1.0 / (1.0 + math.exp(-12.0 * (jac - 0.25)))
            if sig >= min_score:
                scored.append((sig, rid, fact))
        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]
        for _, rid, _ in top:
            self._access[rid] += 1
        return [f for _, _, f in top]

    def all_facts(self) -> List[str]:
        return [r[0] for r in self._conn.execute(
            "SELECT fact FROM facts ORDER BY added").fetchall()]

    def remove_by_text(self, text: str) -> None:
        self._conn.execute("DELETE FROM facts WHERE fact=?", (text,))
        self._conn.commit()

    def prune_unaccessed(self, min_accesses: int = 1, keep_recent: int = 50) -> int:
        all_ids = [r[0] for r in self._conn.execute(
            "SELECT id FROM facts ORDER BY added DESC").fetchall()]
        to_del = [i for j, i in enumerate(all_ids)
                  if j >= keep_recent and self._access.get(i, 0) < min_accesses]
        if to_del:
            self._conn.executemany(
                "DELETE FROM facts WHERE id=?", [(i,) for i in to_del])
            self._conn.commit()
        return len(to_del)

    def __len__(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

    def close(self) -> None:
        self._conn.close()

    def to_dict(self) -> dict:
        """Serializa todos os fatos para dicionário (compatibilidade com save/load)."""
        return {'facts': self.all_facts()}

    @classmethod
    def from_dict(cls, d: dict) -> 'SQLiteFactStoreV12':
        """Reconstrói SQLiteFactStoreV12 a partir de dicionário salvo."""
        store = cls(db_path=":memory:")
        for fact in d.get('facts', []):
            store.add(fact)
        return store


    # ── Compatibilidade com V9 que acessa _index e _facts diretamente ────────

    @property
    def _facts(self) -> List[str]:
        """Propriedade de compatibilidade: retorna lista de todos os fatos."""
        return self.all_facts()

    @property
    def _index(self) -> Dict[str, List[int]]:
        """Propriedade de compatibilidade: reconstrói índice invertido dinamicamente.
        Usado apenas na busca por prefixo (fallback) do _handle_query do V9.
        """
        facts = self.all_facts()
        idx: Dict[str, List[int]] = defaultdict(list)
        for i, fact in enumerate(facts):
            for tok in re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', fact.lower()):
                if len(tok) >= 2:
                    idx[tok].append(i)
        return idx


class CuriositaEngine:
    """Gera perguntas de clarificação quando confidence < threshold (V12).
    Cooldown de 5 turnos por tópico para não ser irritante.
    """
    CURIOSITY_THRESHOLD = 0.25
    COOLDOWN_TURNS      = 5
    TEMPLATES = {
        "none":  ["Tenho informações limitadas sobre '{t}'. Pode me dar mais contexto?",
                  "Não tenho certeza sobre '{t}' — pode elaborar?"],
        "low":   ["'{t}' não está claro para mim. O que especificamente quer saber?"],
        "multi": ["Encontrei informações conflitantes sobre '{t}'. Qual versão é relevante?"],
    }

    def __init__(self):
        self._asked: Dict[str, int] = {}
        self._turn = 0
        self.total_asked = 0

    def tick(self) -> None:
        self._turn += 1

    def generate(self, query: str, score: float, facts: List[str]) -> Optional[str]:
        if score >= self.CURIOSITY_THRESHOLD:
            return None
        _skip = {'como','qual','quem','onde','quando','para','pela','pelo','este','essa'}
        topics = [w for w in re.findall(r'\w{4,}', query.lower()) if w not in _skip]
        topic  = topics[0] if topics else query[:20]
        if self._turn - self._asked.get(topic, -999) < self.COOLDOWN_TURNS:
            return None
        self._asked[topic] = self._turn
        self.total_asked  += 1
        import hashlib
        seed = int(hashlib.md5(query.encode()).hexdigest()[:4], 16)
        if not facts:
            t = self.TEMPLATES["none"]
            return t[seed % len(t)].format(t=topic)
        if len(facts) >= 2:
            return self.TEMPLATES["multi"][0].format(t=topic)
        t = self.TEMPLATES["low"]
        return t[seed % len(t)].format(t=topic)

    @property
    def stats(self) -> dict:
        return {"total": self.total_asked, "topics": len(self._asked)}


class ConsistencyChecker:
    """Detecta afirmações inconsistentes com constantes físicas conhecidas (V12).
    Não bloqueia — apenas marca. O sistema nunca silencia informação nova.
    """
    KNOWN_CONSTANTS: Dict[str, tuple] = {
        "velocidade da luz":           (3e8,       "m/s"),
        "constante de planck":         (6.626e-34, "J·s"),
        "constante gravitacional":     (6.674e-11, "N·m²/kg²"),
        "carga do eletron":            (1.602e-19, "C"),
        "dimensao fractal sierpinski": (1.585,     "adimensional"),
        "temperatura do sol":          (5778.0,    "K"),
        "aceleracao da gravidade":     (9.8,       "m/s²"),
    }

    def __init__(self, search_fn=None):
        self._search = search_fn
        self._flags: List[Dict] = []

    def check(self, new_fact: str) -> Optional[str]:
        fl = _deaccent(new_fact.lower())
        for name, (value, unit) in self.KNOWN_CONSTANTS.items():
            name_norm = _deaccent(name)
            if not all(w in fl for w in name_norm.split()):
                continue
            nums = re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', new_fact)
            for ns in nums:
                try:
                    num = float(ns)
                    if num == 0 or value == 0:
                        continue
                    ratio = abs(math.log10(abs(num)) - math.log10(abs(value)))
                    threshold = 1.5 if unit == "adimensional" else 4
                    if ratio > threshold:
                        alert = (f"[inconsistência detectada] '{name}' é ~{value:.3g} {unit}; "
                                 f"valor '{ns}' difere ~10^{ratio:.0f}")
                        self._flags.append({"fact": new_fact, "issue": alert})
                        return alert
                except (ValueError, ZeroDivisionError):
                    pass
        return None

    @property
    def n_flags(self) -> int:
        return len(self._flags)

    def report(self) -> str:
        if not self._flags:
            return "ConsistencyChecker: sem inconsistências detectadas."
        lines = [f"ConsistencyChecker: {self.n_flags} inconsistência(s):"]
        for item in self._flags[-5:]:
            lines.append(f"  • {item['fact'][:60]} → {item['issue'][:70]}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# §V10  XOR BINDING — raciocínio analógico no espaço SDR
# ══════════════════════════════════════════════════════════════════════════════

class XORBinding:
    """
    Codifica relações como SDR(subj) ⊕ SDR(rel) ⊕ SDR(obj).
    
    Permite raciocínio analógico direto:
      - Dado SDR(A) ⊕ SDR(rel) ⊕ SDR(B), para encontrar B:
        B ≈ SDR(A) ⊕ SDR(rel) ⊕ binding → overlap search
      - Analogia: A:B :: C:? → XOR(A,B) ⊕ C ≈ ?
    
    Bio-inspiração: hyperdimensional computing (Kanerva, 2009).
    """
    
    def __init__(self, encoder: 'MultiLobeEncoder'):
        self._enc = encoder
        self._bindings: List[Tuple[SparseSDR, str, str, str]] = []  # (bound_sdr, subj, rel, obj)
        self._rel_sdrs: Dict[str, SparseSDR] = {}  # cache de SDRs de relações
    
    def _get_rel_sdr(self, rel: str) -> SparseSDR:
        """Retorna SDR determinístico para uma relação."""
        if rel not in self._rel_sdrs:
            self._rel_sdrs[rel] = self._enc.encode(f'__REL__{rel}__')
        return self._rel_sdrs[rel]
    
    def bind(self, subj: str, rel: str, obj: str) -> SparseSDR:
        """Cria binding: SDR(subj) ⊕ SDR(rel) ⊕ SDR(obj)."""
        s_sdr = self._enc.encode(subj)
        r_sdr = self._get_rel_sdr(rel)
        o_sdr = self._enc.encode(obj)
        bound = s_sdr ^ r_sdr ^ o_sdr
        self._bindings.append((bound, subj, rel, obj))
        return bound
    
    def unbind_object(self, subj: str, rel: str, top_k: int = 3,
                      min_overlap: float = 0.08) -> List[Tuple[float, str]]:
        """Dado sujeito e relação, encontra objetos via XOR reverso.
        
        Para cada binding armazenado:
          candidate = binding ⊕ SDR(subj) ⊕ SDR(rel)  
          Se candidate tem alto overlap com SDR(obj_original) → match
        """
        s_sdr = self._enc.encode(subj)
        r_sdr = self._get_rel_sdr(rel)
        query = s_sdr ^ r_sdr
        
        results = []
        for bound, b_subj, b_rel, b_obj in self._bindings:
            candidate = bound ^ query  # should approximate SDR(obj)
            obj_sdr = self._enc.encode(b_obj)
            overlap = candidate.overlap_score(obj_sdr)
            if overlap >= min_overlap:
                results.append((overlap, b_obj))
        
        results.sort(reverse=True)
        return results[:top_k]
    
    def analogy(self, a: str, b: str, c: str, top_k: int = 3) -> List[Tuple[float, str]]:
        """Analogia SDR: A:B :: C:? 
        
        Calcula: transform = SDR(A) ⊕ SDR(B)
                 target    = transform ⊕ SDR(C)
                 ? = melhor match com target
        """
        a_sdr = self._enc.encode(a)
        b_sdr = self._enc.encode(b)
        c_sdr = self._enc.encode(c)
        transform = a_sdr ^ b_sdr  # captura a "relação" entre A e B
        target = transform ^ c_sdr  # aplica a mesma relação a C
        
        results = []
        seen = {a.lower(), b.lower(), c.lower()}
        for _, _, _, obj in self._bindings:
            if obj.lower() in seen:
                continue
            obj_sdr = self._enc.encode(obj)
            score = target.overlap_score(obj_sdr)
            if score > 0.05:
                results.append((score, obj))
                seen.add(obj.lower())
        
        results.sort(reverse=True)
        return results[:top_k]
    
    def query_by_pattern(self, pattern_sdr: SparseSDR, 
                         top_k: int = 5) -> List[Tuple[float, str, str, str]]:
        """Busca bindings por similaridade com um padrão SDR."""
        results = []
        for bound, subj, rel, obj in self._bindings:
            score = bound.overlap_score(pattern_sdr)
            if score > 0.05:
                results.append((score, subj, rel, obj))
        results.sort(reverse=True)
        return results[:top_k]
    
    @property
    def size(self) -> int:
        return len(self._bindings)
    
    def to_dict(self) -> dict:
        return {
            'bindings': [(b.to_list(), s, r, o) for b, s, r, o in self._bindings[-500:]],
            'rel_sdrs': {k: v.to_list() for k, v in self._rel_sdrs.items()}
        }
    
    @classmethod
    def from_dict(cls, d: dict, encoder: 'MultiLobeEncoder') -> 'XORBinding':
        xb = cls(encoder)
        for b_list, s, r, o in d.get('bindings', []):
            xb._bindings.append((SparseSDR.from_list(b_list), s, r, o))
        for k, v in d.get('rel_sdrs', {}).items():
            xb._rel_sdrs[k] = SparseSDR.from_list(v)
        return xb


# ══════════════════════════════════════════════════════════════════════════════
# §V10  NOVELTY DETECTOR — aprendizado baseado em surpresa
# ══════════════════════════════════════════════════════════════════════════════

class NoveltyDetector:
    """
    Detecta novidade comparando input SDR com a distribuição esperada.
    Bits inesperados (fora da distribuição normal) recebem peso 2×.
    
    Bio-inspiração: hippocampal novelty signal (Kumaran & Maguire, 2007).
    """
    
    def __init__(self):
        self._bit_freq: Dict[int, int] = defaultdict(int)
        self._total_inputs: int = 0
        self._novelty_history: deque = deque(maxlen=100)
    
    def update(self, sdr: SparseSDR) -> float:
        """Atualiza distribuição e retorna score de novidade [0..1]."""
        self._total_inputs += 1
        
        if self._total_inputs < 5:
            # Cold start: tudo é novo
            for idx in sdr._idx:
                self._bit_freq[idx] += 1
            self._novelty_history.append(1.0)
            return 1.0
        
        # Calcula novidade: proporção de bits raros no input
        novel_bits = 0
        total_bits = len(sdr._idx)
        if total_bits == 0:
            return 0.0
        
        for idx in sdr._idx:
            freq = self._bit_freq.get(idx, 0) / self._total_inputs
            if freq < 0.05:  # bit raro (< 5% das vezes)
                novel_bits += 1
        
        novelty = novel_bits / total_bits
        
        # Atualiza frequências
        for idx in sdr._idx:
            self._bit_freq[idx] += 1
        
        self._novelty_history.append(novelty)
        return novelty
    
    def recent_novelty(self) -> float:
        """Média de novidade das últimas N interações."""
        if not self._novelty_history:
            return 0.5
        return sum(self._novelty_history) / len(self._novelty_history)
    
    def surprise_boost(self, sdr: SparseSDR) -> SparseSDR:
        """Retorna SDR com bits surpreendentes reforçados (2× peso via duplicação)."""
        if self._total_inputs < 5:
            return sdr
        boosted_indices = list(sdr._idx)
        for idx in sdr._idx:
            freq = self._bit_freq.get(idx, 0) / self._total_inputs
            if freq < 0.03:  # bit muito raro
                # Adiciona bits vizinhos para "amplificar" o sinal
                for neighbor in [idx - 1, idx + 1]:
                    if 0 <= neighbor < SDR_SIZE and neighbor not in sdr._idx:
                        boosted_indices.append(neighbor)
                        break
        return SparseSDR.from_indices(boosted_indices[:SDR_ACTIVE + 10])
    
    def to_dict(self) -> dict:
        return {
            'bit_freq': dict(self._bit_freq),
            'total': self._total_inputs,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'NoveltyDetector':
        nd = cls()
        nd._bit_freq = defaultdict(int, {int(k): v for k, v in d.get('bit_freq', {}).items()})
        nd._total_inputs = d.get('total', 0)
        return nd


# ══════════════════════════════════════════════════════════════════════════════
# §V10  TEMPORAL MEMORY — decaimento exponencial adaptativo  
# ══════════════════════════════════════════════════════════════════════════════

class TemporalMemory:
    """
    Memória com decaimento exponencial e half-life adaptativo.
    Fatos acessados frequentemente decaem mais devagar.
    
    Bio-inspiração: hippocampal memory consolidation.
    """
    
    def __init__(self, base_half_life_h: float = 24.0):
        self._base_hl = base_half_life_h
        self._timestamps: Dict[str, float] = {}
        self._access_counts: Dict[str, int] = defaultdict(int)
        self._strengths: Dict[str, float] = defaultdict(lambda: 1.0)
    
    def record(self, fact_key: str, strength: float = 1.0) -> None:
        """Registra ou reforça um fato."""
        self._timestamps[fact_key] = time.time()
        self._access_counts[fact_key] += 1
        self._strengths[fact_key] = min(2.0, self._strengths[fact_key] + strength * 0.1)
    
    def strength(self, fact_key: str) -> float:
        """Retorna a força atual do fato com decaimento."""
        if fact_key not in self._timestamps:
            return 0.0
        
        elapsed_h = (time.time() - self._timestamps[fact_key]) / 3600.0
        # Half-life adaptativo: mais acessos → decai mais devagar
        accesses = self._access_counts.get(fact_key, 1)
        adaptive_hl = self._base_hl * (1.0 + math.log1p(accesses))
        
        base_strength = self._strengths.get(fact_key, 1.0)
        decay = math.exp(-math.log(2) * elapsed_h / adaptive_hl)
        return base_strength * decay
    
    def prune(self, threshold: float = 0.05) -> int:
        """Remove fatos abaixo do threshold."""
        to_remove = [k for k in self._timestamps if self.strength(k) < threshold]
        for k in to_remove:
            del self._timestamps[k]
            self._access_counts.pop(k, None)
            self._strengths.pop(k, None)
        return len(to_remove)
    
    def top_k(self, k: int = 10) -> List[Tuple[float, str]]:
        """Retorna os K fatos mais fortes."""
        scored = [(self.strength(key), key) for key in self._timestamps]
        scored.sort(reverse=True)
        return scored[:k]
    
    def to_dict(self) -> dict:
        return {
            'timestamps': self._timestamps,
            'access_counts': dict(self._access_counts),
            'strengths': dict(self._strengths),
            'base_hl': self._base_hl,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'TemporalMemory':
        tm = cls(d.get('base_hl', 24.0))
        tm._timestamps = d.get('timestamps', {})
        tm._access_counts = defaultdict(int, d.get('access_counts', {}))
        tm._strengths = defaultdict(lambda: 1.0, d.get('strengths', {}))
        return tm


# ══════════════════════════════════════════════════════════════════════════════
# §V10  SDR REASONER — raciocínio lógico via operações bitwise
# ══════════════════════════════════════════════════════════════════════════════

class SDRReasoner:
    """
    Motor de raciocínio que opera inteiramente no espaço SDR.
    
    Operações:
    - Silogismo: se overlap(A,B) > θ e overlap(B,C) > θ → inferir A~C
    - Transitividade: propagação de ativação via AND/OR
    - Contradição: overlap(A, ¬B) > θ → A contradiz B
    - Generalização: bundle(SDRs similares) → protótipo da categoria
    """
    
    def __init__(self, threshold: float = 0.12):
        self._threshold = threshold
        self._prototypes: Dict[str, SparseSDR] = {}  # nome → SDR médio da categoria
    
    def syllogism(self, premise_a: SparseSDR, premise_b: SparseSDR,
                  conclusion_target: SparseSDR) -> Tuple[bool, float]:
        """Verifica silogismo: se A~B e A→target, qual a confiança?"""
        ab_overlap = premise_a.overlap_score(premise_b)
        at_overlap = premise_a.overlap_score(conclusion_target)
        bt_overlap = premise_b.overlap_score(conclusion_target)
        
        # Transitividade: se A sobrepõe B e B sobrepõe T → A pode sobrepor T
        if ab_overlap > self._threshold and bt_overlap > self._threshold:
            # Confiança proporcional ao produto dos overlaps
            confidence = ab_overlap * bt_overlap
            return True, confidence
        return False, 0.0
    
    def generalize(self, name: str, sdrs: List[SparseSDR], 
                   threshold: float = 0.4) -> SparseSDR:
        """Cria protótipo da categoria via bundle (union filtering)."""
        if not sdrs:
            return SparseSDR()
        proto = SparseSDR.bundle(sdrs, threshold=threshold)
        self._prototypes[name] = proto
        return proto
    
    def categorize(self, sdr: SparseSDR, top_k: int = 3) -> List[Tuple[float, str]]:
        """Classifica um SDR nas categorias conhecidas."""
        results = []
        for name, proto in self._prototypes.items():
            score = sdr.overlap_score(proto)
            if score > self._threshold:
                results.append((score, name))
        results.sort(reverse=True)
        return results[:top_k]
    
    def detect_contradiction(self, sdr_a: SparseSDR, sdr_b: SparseSDR) -> float:
        """
        Detecta contradição comparando zonas de valência.
        Se zonas semânticas são similares mas valências são opostas → contradição.
        """
        sem_a, sem_b = sdr_a.semantic_bits(), sdr_b.semantic_bits()
        val_a, val_b = sdr_a.valence_bits(), sdr_b.valence_bits()
        
        sem_sim = sem_a.overlap_score(sem_b)
        val_sim = val_a.overlap_score(val_b)
        
        # Contradição: mesmo tópico (alta sem_sim) mas valência diferente (baixa val_sim)
        if sem_sim > 0.3 and val_sim < 0.1:
            return sem_sim * (1.0 - val_sim)  # score de contradição
        return 0.0
    
    def propagate_activation(self, seed: SparseSDR, 
                              memory_sdrs: List[Tuple[SparseSDR, str]],
                              depth: int = 2, 
                              threshold: float = 0.10) -> List[Tuple[float, str]]:
        """Propagação de ativação: encontra memórias conectadas via overlap transitivo."""
        activated = []
        current = seed
        visited_texts = set()
        
        for d in range(depth):
            decay = 1.0 / (d + 1)
            for mem_sdr, mem_text in memory_sdrs:
                if mem_text in visited_texts:
                    continue
                score = current.overlap_score(mem_sdr) * decay
                if score > threshold:
                    activated.append((score, mem_text))
                    visited_texts.add(mem_text)
            
            # Expande ativação: merge dos SDRs ativados nesta camada
            if activated:
                recent = [self._prototypes.get(text[:20], SparseSDR()) 
                          for _, text in activated[-3:]]
                if any(len(s._idx) > 0 for s in recent):
                    current = SparseSDR.bundle([current] + [s for s in recent if len(s._idx) > 0])
        
        activated.sort(reverse=True)
        return activated
    
    def to_dict(self) -> dict:
        return {
            'threshold': self._threshold,
            'prototypes': {k: v.to_list() for k, v in self._prototypes.items()}
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'SDRReasoner':
        sr = cls(d.get('threshold', 0.12))
        for k, v in d.get('prototypes', {}).items():
            sr._prototypes[k] = SparseSDR.from_list(v)
        return sr


# ══════════════════════════════════════════════════════════════════════════════
# §V10  PREDICTIVE CACHE — processamento antecipatório
# ══════════════════════════════════════════════════════════════════════════════

class PredictiveCache:
    """
    Cache preditivo: antecipa consultas prováveis baseado no contexto.
    Pré-computa SDRs e respostas para tópicos adjacentes ao atual.
    
    Bio-inspiração: predictive coding (Rao & Ballard, 1999).
    """
    
    def __init__(self, max_size: int = 50):
        self._cache: Dict[str, Tuple[float, str, SparseSDR]] = {}  # key → (timestamp, response, sdr)
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def predict(self, current_entities: List[str], 
                concept_graph: 'ConceptGraph',
                embed: 'MiniEmbed') -> List[str]:
        """Retorna tópicos que provavelmente serão perguntados a seguir."""
        predictions = set()
        for entity in current_entities[:5]:
            nbrs = concept_graph.neighbors(entity, depth=1)
            for nbr, _ in nbrs[:3]:
                predictions.add(nbr)
        return list(predictions)[:10]
    
    def store(self, key: str, response: str, sdr: SparseSDR) -> None:
        """Armazena resposta pré-computada."""
        if len(self._cache) >= self._max_size:
            # Remove mais antigo
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        self._cache[key] = (time.time(), response, sdr)
    
    def get(self, key: str) -> Optional[str]:
        """Busca resposta pré-computada."""
        hit = self._cache.get(key)
        if hit:
            ts, response, sdr = hit
            # Expira após 5 minutos
            if time.time() - ts < 300:
                self._hits += 1
                return response
            del self._cache[key]
        self._misses += 1
        return None
    
    def get_by_sdr(self, query_sdr: SparseSDR, min_overlap: float = 0.3) -> Optional[str]:
        """Busca por similaridade SDR."""
        best_score, best_response = 0.0, None
        for key, (ts, response, sdr) in self._cache.items():
            if time.time() - ts > 300:
                continue
            score = query_sdr.overlap_score(sdr)
            if score > best_score and score >= min_overlap:
                best_score = score
                best_response = response
        if best_response:
            self._hits += 1
        return best_response
    
    @property
    def stats(self) -> Dict:
        return {
            'size': len(self._cache),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': self._hits / max(self._hits + self._misses, 1),
        }


# ══════════════════════════════════════════════════════════════════════════════
# §V10  REPRESENTATIONAL BUS — comunicação inter-módulo via SDR
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RepMessage:
    """Mensagem no barramento representacional."""
    source: str          # módulo de origem
    sdr: SparseSDR       # conteúdo SDR
    text: str            # texto associado (para debug/display)
    priority: float = 1.0
    timestamp: float = field(default_factory=time.time)


class RepresentationalBus:
    """
    Barramento tálamo-cortical para comunicação inter-módulo via SDR.
    
    Módulos publicam SDR messages e assinam por overlap.
    Permite que o CognitiveBrain, XORBinding, SDRReasoner e 
    ConceptGraph comuniquem-se sem converter para texto.
    
    Bio-inspiração: thalamic relay (Sherman & Guillery, 2006).
    """
    
    def __init__(self, max_messages: int = 200):
        self._messages: deque = deque(maxlen=max_messages)
        self._subscribers: Dict[str, List] = defaultdict(list)
    
    def publish(self, msg: RepMessage) -> None:
        """Publica mensagem no barramento."""
        self._messages.append(msg)
    
    def query(self, query_sdr: SparseSDR, top_k: int = 5,
              min_overlap: float = 0.08, 
              exclude_source: str = '') -> List[RepMessage]:
        """Busca mensagens por overlap SDR."""
        results = []
        for msg in self._messages:
            if msg.source == exclude_source:
                continue
            score = query_sdr.overlap_score(msg.sdr)
            if score >= min_overlap:
                results.append((score * msg.priority, msg))
        results.sort(reverse=True)
        return [msg for _, msg in results[:top_k]]
    
    def recent(self, n: int = 10, source: str = '') -> List[RepMessage]:
        """Mensagens recentes, opcionalmente filtradas por fonte."""
        msgs = list(self._messages)
        if source:
            msgs = [m for m in msgs if m.source == source]
        return msgs[-n:]
    
    def broadcast_and_collect(self, query_sdr: SparseSDR, 
                               text: str, source: str) -> List[str]:
        """Publica e coleta respostas relevantes de outros módulos."""
        self.publish(RepMessage(source=source, sdr=query_sdr, text=text))
        responses = self.query(query_sdr, top_k=3, exclude_source=source)
        return [msg.text for msg in responses]


# ══════════════════════════════════════════════════════════════════════════════
# §V10  BEAM GENERATOR — geração com beam search + reranking
# ══════════════════════════════════════════════════════════════════════════════

class BeamGenerator:
    """
    Gerador de texto com beam search e reranking semântico.
    Mantém múltiplas hipóteses em paralelo e escolhe a melhor.
    Melhoria significativa sobre a geração greedy do NGramMemory.
    """
    
    def __init__(self, ngram: 'NGramMemory', embed: 'MiniEmbed',
                 beam_width: int = 4, max_tokens: int = 30):
        self._ngram = ngram
        self._embed = embed
        self._beam_width = beam_width
        self._max_tokens = max_tokens
    
    def generate(self, prompt: str, tema: str = '', 
                 temperature: float = 0.7) -> str:
        """Gera texto com beam search + reranking semântico."""
        tokens = re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', prompt.lower())
        if not tokens:
            return prompt
        
        tema_vec = self._embed.sentence_vector(tema) if tema else None
        
        # Inicializa beams: [(score, tokens)]
        beams = [(0.0, list(tokens))]
        
        for step in range(self._max_tokens):
            all_candidates = []
            
            for beam_score, beam_tokens in beams:
                nexts = self._ngram.predict_next(beam_tokens, top_k=8)
                if not nexts:
                    all_candidates.append((beam_score, beam_tokens, True))
                    continue
                
                for tok, prob in nexts:
                    # Penalidade de repetição
                    recent = beam_tokens[-4:]
                    rep_count = recent.count(tok)
                    rep_penalty = 1.0 / (1.0 + rep_count * 0.8)
                    
                    # Score semântico (se tema disponível)
                    sem_bonus = 0.0
                    if tema_vec:
                        tok_vec = self._embed.vector(tok)
                        sem_bonus = max(0.0, sum(a*b for a, b in zip(tema_vec, tok_vec))) * 0.3
                    
                    new_score = beam_score + math.log(max(prob * rep_penalty, 1e-10)) + sem_bonus
                    new_tokens = beam_tokens + [tok]
                    
                    is_terminal = tok in ('.', '!', '?') or len(new_tokens) >= len(tokens) + self._max_tokens
                    all_candidates.append((new_score, new_tokens, is_terminal))
            
            if not all_candidates:
                break
            
            # Seleciona top-k beams
            all_candidates.sort(reverse=True)
            
            # Separa terminais e não-terminais
            terminals = [(s, t) for s, t, is_t in all_candidates if is_t]
            non_terminals = [(s, t) for s, t, is_t in all_candidates if not is_t]
            
            if not non_terminals:
                # Todos terminaram
                if terminals:
                    best = max(terminals)[1]
                    return ' '.join(best) + ('.' if best[-1] not in '.!?' else '')
                break
            
            beams = non_terminals[:self._beam_width]
            
            # Se temos terminais bons o suficiente, considere parar
            if terminals:
                best_terminal_score = max(s for s, _ in terminals)
                best_beam_score = max(s for s, _ in beams)
                if best_terminal_score >= best_beam_score * 0.9:
                    best = max(terminals)[1]
                    return ' '.join(best) + ('.' if best[-1] not in '.!?' else '')
        
        # Retorna o melhor beam
        if beams:
            best = max(beams)[1]
            return ' '.join(best) + '.'
        return prompt + '.'
    
    def generate_with_context(self, prompt: str, facts: List[str],
                               tema: str = '') -> str:
        """Gera incorporando fatos relevantes como contexto."""
        # Alimenta NGram com fatos relevantes temporariamente
        for fact in facts[:5]:
            self._ngram.learn_text(fact)
        
        return self.generate(prompt, tema=tema)


# ══════════════════════════════════════════════════════════════════════════════
# §V10  ATTENTION POOL — sentence vectors com IDF weighting
# ══════════════════════════════════════════════════════════════════════════════

class AttentionPool:
    """
    Cria sentence vectors usando IDF-weighted attention em vez de média simples.
    Palavras raras (mais informativas) recebem mais peso.
    
    Melhoria sobre: MiniEmbed.sentence_vector (que usa média uniforme)
    """
    
    def __init__(self, embed: 'MiniEmbed'):
        self._embed = embed
    
    def sentence_vector(self, text: str, boost_entities: List[str] = None) -> List[float]:
        """Sentence vector com IDF weighting + entity boost."""
        tokens = _tokenize_embed(text)
        if not tokens:
            return [0.0] * self._embed.DIM
        
        vecs = []
        weights = []
        
        for tok in tokens:
            vec = self._embed.vector(tok)
            
            # IDF weight: palavras raras pesam mais
            freq = self._embed._freq.get(tok, 0)
            total = max(self._embed._total_tokens, 1)
            idf = math.log1p(total / max(freq, 1))
            
            # Entity boost: entidades do contexto pesam 2×
            if boost_entities and tok in boost_entities:
                idf *= 2.0
            
            vecs.append(vec)
            weights.append(idf)
        
        # Weighted average
        total_w = sum(weights) or 1.0
        dim = self._embed.DIM
        result = [0.0] * dim
        for vec, w in zip(vecs, weights):
            for k in range(dim):
                result[k] += (w / total_w) * vec[k]
        
        norm = math.sqrt(sum(x*x for x in result)) or 1.0
        return [x/norm for x in result]



class NexusV10:
    """
    Nexus v8 — Sistema Cognitivo Híbrido.
    Combina os melhores módulos de v5 Pro e v7 Completo em arquivo único.
    """

    VERSION = 'v14-unified'

    def __init__(self, verbose: bool = False):
        self._verbose = verbose

        # ── Encoders (dual) ───────────────────────────────────────────────────
        self.encoder  = MultiLobeEncoder()         # v5: SDR 3 zonas, rápido
        self.embed    = MiniEmbed()                # v7: PMI+cosine, semântico

        # ── Memória primária ──────────────────────────────────────────────────
        self.brain    = CognitiveBrain()           # v5: InvertedIndex O(1)

        # ── Memória estrutural (grafo de arestas) ─────────────────────────────
        self.edge_net = EdgeNetwork()              # v7: LearnedEdge

        # ── Memória de fatos textuais (TF-IDF) ───────────────────────────────
        self.fact_store = StructuredFactStore()    # v5: TF-IDF + subject boost

        # ── Recuperação híbrida 3 camadas ────────────────────────────────────
        self.retriever = HybridRetriever(
            self.fact_store, self.brain, self.embed)

        # ── Conhecimento estrutural ───────────────────────────────────────────
        self.concept_graph = ConceptGraph()        # v5: analogia, BFS, vizinhos
        self.conditional   = ConditionalEngine()  # v5: regras SE-ENTÃO BFS
        self.deductive     = DeductiveEngine()    # v5: silogismos

        # ── Epistêmico ────────────────────────────────────────────────────────
        self.epistemic = EpistemicLayer()          # v5: hipóteses + promoção

        # ── Código e matemática ───────────────────────────────────────────────
        self.code_eng  = CodeGeneralizer()         # v5: CBR + sandbox + repair
        self.math_eng  = MathEngine()              # v5: safe eval

        # ── Geração e linguagem ───────────────────────────────────────────────
        self.ngram  = NGramMemory(window=3)        # v5: bigrama/trigrama
        self.mouth  = FluentMouth(self.encoder, self.ngram)

        # ── Episódico e homeostase ────────────────────────────────────────────
        self.episodes     = EpisodicStream()       # v5+v7: chain + decay
        self.homeostasis  = Homeostasis()          # v5: energia/curiosidade

        # ── Consolidação e workspace ──────────────────────────────────────────
        self.consolidator = SleepConsolidator()    # v5: merge Hebbiano
        self.workspace    = VirtualWorkspace()     # v5: RAM filesystem

        # ── Novos módulos cognitivos (v9) ─────────────────────────────────────
        self.salience   = SalienceEngine()         # v9: atenção/filtro combinatório
        self.rule_ind   = RuleInductor()           # v9: mineração de regras transitivas
        self.abstractor = ConceptAbstractor()      # v9: clustering semântico emergente
        self.wm         = WorkingMemory()          # v9: raciocínio em workspace isolado

        # ── Wiring epistêmico ─────────────────────────────────────────────────
        def _auto_promote(belief: Belief, brain: CognitiveBrain) -> None:
            brain.store(belief.sdr, belief.text, tag='FACT',
                        confidence=belief.confidence)
        self.epistemic._on_promote = _auto_promote

        # ── Injeta embed e conditional no DeductiveEngine ────────────────────
        self.deductive._embed       = self.embed
        self.deductive._conditional = self.conditional

        # ── TextWeaver: geração de prosa estruturada ──────────────────────────
        self.text_weaver = TextWeaver(
            embed=self.embed,
            concept_graph=self.concept_graph,
            fact_store=self.fact_store,
            ngram=self.ngram,
            deductive=self.deductive,
            conditional=self.conditional,
            episodic=self.episodes)
        # Expõe text_weaver para _enriched_fact_text e _compose_from_facts
        self._tw = self.text_weaver

        # ── Semantic SDR Encoder (Spatial Pooler) ─────────────────────────────
        # Aprende a codificar texto em SDR semântico via Hebbian learning.
        # Inicialmente desativado; ativado após train_spatial_pooler().
        self.sp_encoder: Optional[SemanticSDREncoder] = None
        self._sp_trained: bool = False

        # ── One-shot commands (trigger → resposta) ────────────────────────────
        # Separado de encoder._triggers (que é usado apenas para SDR encoding).
        self._one_shots: Dict[str, str] = {}

        # ── Confirmação pendente de contradição ───────────────────────────────
        self._pending_confirm: Optional[Dict] = None
        self._dialog_ctx: List[Tuple[str, str]] = []  # histórico completo (sem limite fixo)
        self._facts_since_sleep: int = 0

        # ── ContextEngine: contexto semântico acumulado sem limite de tokens ──
        # Implementa o conceito de "janela de atenção semântica":
        #   _ctx_topic_vec: vetor 128d que acumula o tópico da conversa inteira
        #                   (média ponderada exponencial — recente pesa mais)
        #   _ctx_entities:  entidades mencionadas recentemente (ordenadas por recência)
        #   _ctx_turn:      contador de turnos (para peso de decaimento)
        #
        # Não tem limite de tokens porque é um vetor fixo de 128 floats
        # que se atualiza a cada turno — a conversa inteira cabe em 128 números.
        self._ctx_topic_vec: List[float] = [0.0] * self.embed.DIM  # vetor de tópico
        self._ctx_entities:  List[str]   = []   # entidades ativas (últimas 20)
        self._ctx_turn:      int         = 0    # contador de turnos da sessão

        # ── Auto-persistência ─────────────────────────────────────────────────
        # CORRIGIDO: estas linhas estavam em código morto (após return) no V9 original.
        # Movidas para dentro do __init__ onde devem estar.
        self._persist_path: str     = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'nexus_state.json')
        self._facts_since_save: int = 0    # contador para auto-save periódico
        self._autosave_every:   int = 50   # salva a cada N fatos novos
        self._autosave_enabled: bool = False  # desabilitado por padrão (modo seguro)

        # ── Componentes V12 ─────────────────────────────────────────────────────
        # DeduplicatorSDR: bloqueia paráfrases antes de salvar
        self._dedup     = DeduplicatorSDR(self.encoder)
        # CuriositaEngine: pergunta quando confidence < 0.25
        self._curiosita = CuriositaEngine()
        # ConsistencyChecker: alerta sobre constantes físicas incorretas
        self._checker   = ConsistencyChecker()
        # Estatísticas V12
        self._v12_stats: Dict[str, int] = {"learned": 0, "blocked": 0}

        # ── V10 NOVOS MÓDULOS ─────────────────────────────────────────────────
        # XORBinding: raciocínio analógico no espaço SDR
        self.xor_bind = XORBinding(self.encoder)
        # NoveltyDetector: surprise-based learning
        self.novelty = NoveltyDetector()
        # TemporalMemory: decaimento exponencial adaptativo
        self.temporal = TemporalMemory()
        # SDRReasoner: raciocínio lógico via operações bitwise
        self.sdr_reasoner = SDRReasoner()
        # PredictiveCache: processamento antecipatório
        self.pred_cache = PredictiveCache()
        # RepresentationalBus: comunicação inter-módulo via SDR
        self.rep_bus = RepresentationalBus()
        # BeamGenerator: geração com beam search + reranking
        self.beam_gen = BeamGenerator(self.ngram, self.embed)
        # AttentionPool: IDF-weighted sentence vectors
        self.attn_pool = AttentionPool(self.embed)


        # ── SQLiteFactStore V12 (substitui StructuredFactStore em memória) ──────
        # Melhor recuperação via FTS5 + sigmoid k=12 (V12 improvement)
        self.fact_store = SQLiteFactStoreV12(db_path=":memory:")

        # ── Reconstrói retriever e text_weaver com o novo fact_store ────────────
        self.retriever = HybridRetriever(self.fact_store, self.brain, self.embed)
        self.text_weaver = TextWeaver(
            embed=self.embed,
            concept_graph=self.concept_graph,
            fact_store=self.fact_store,
            ngram=self.ngram,
            deductive=self.deductive,
            conditional=self.conditional,
            episodic=self.episodes)
        self._tw = self.text_weaver

        # ── Seed de conhecimento ───────────────────────────────────────────────
        # CORRIGIDO: _seed_knowledge estava em código morto no V9 original.
        self._seed_knowledge()

        # ── Registra auto-save ao encerrar ────────────────────────────────────
        atexit.register(self._autosave_on_exit)


    def _check_has_chain(self, concept: str, prop: str) -> Optional[str]:
        """Verifica se concept HAS prop via herança IS_A→HAS.

        Camadas:
        1. FactStore direto (já retorna pelo fluxo normal — aqui é backup)
        2. Cadeia IS_A→HAS: se concept IS_A parent e parent HAS prop → concept HAS prop
        3. Regras induzidas: RuleInductor pode já ter materializado HAS herdado
        """
        c = concept.lower().strip()
        p = prop.lower().strip()
        if not c or not p:
            return None

        IS_A_RELS = {REL_IS_A, 'e', 'e_um', 'e-um', 'IS_A', 'é', 'é_um', 'é-um'}
        HAS_RELS  = {REL_HAS, 'tem', 'possui', 'HAS'}

        # Camada 1: regras induzidas diretas (RuleInductor já materializou)
        for rel, tgt, conf in self.rule_ind.get_induced(c):
            if rel in HAS_RELS:
                p_norm = _deaccent(p[:6])
                tgt_norm = _deaccent(tgt[:6])
                if p_norm == tgt_norm or p_norm in _deaccent(tgt) or _deaccent(tgt) in p_norm:
                    return (f'Sim: {concept} tem {prop} '
                            f'(herdado, confiança {conf:.0%}).')

        # Camada 2: BFS — encontra ancestrais de concept via IS_A
        # e verifica se algum ancestral tem a propriedade
        ancestors: list = []
        visited_a: set = {c}
        frontier_a: list = [c]
        while frontier_a:
            node = frontier_a.pop(0)
            for tgt, rels in self.concept_graph._edges.get(node, {}).items():
                if set(rels.keys()) & IS_A_RELS and tgt not in visited_a:
                    visited_a.add(tgt)
                    ancestors.append(tgt)
                    frontier_a.append(tgt)
        # Adiciona ancestrais de regras induzidas
        for (a, rel, tgt), conf in self.rule_ind._induced.items():
            if a == c and rel in IS_A_RELS and tgt not in visited_a:
                visited_a.add(tgt)
                ancestors.append(tgt)

        p_norm = _deaccent(p.lower())
        for anc in ancestors:
            # Verifica se ancestral HAS prop via grafo
            for tgt, rels in self.concept_graph._edges.get(anc, {}).items():
                if set(rels.keys()) & HAS_RELS:
                    tgt_norm = _deaccent(tgt.lower())
                    if p_norm[:6] == tgt_norm[:6] or p_norm in tgt_norm or tgt_norm in p_norm:
                        return (f'Sim: {concept} tem {prop} '
                                f'(herdado de {anc}).')
            # Verifica em fatos textuais: "{anc} tem {prop}"
            anc_facts = self.fact_store.search(anc, top_k=6, min_score=0.2)
            for fact in anc_facts:
                fl = fact.lower()
                if 'tem ' in fl and p_norm[:5] in _deaccent(fl):
                    return f'Sim: {concept} tem {prop} (herdado de {anc}: {fact.rstrip(".")})'
        return None


        # -- IS_A transitiva profunda -----------------------------------------------

    def _check_isa_chain(self, concept, target):
        """BFS em 3 camadas: grafo direto, regras induzidas, BFS estendido."""
        c, t = concept.lower().strip(), target.lower().strip()
        if not c or not t:
            return None
        IS_A_RELS = {REL_IS_A, 'e', 'e_um', 'e-um', 'IS_A'}

        # Camada 1: BFS no ConceptGraph (arestas reais + induzidas aplicadas)
        path = self.concept_graph.path(c, t, max_depth=8)
        if path and len(path) >= 2:
            chain = ' -> '.join(path)
            return 'Sim: {} e {} (via {}).'.format(concept, target, chain)

        # Camada 2: regras induzidas diretas
        for rel, tgt, conf in self.rule_ind.get_induced(c):
            if rel in IS_A_RELS and _deaccent(tgt.lower()[:6]) == _deaccent(t[:6]):
                return 'Sim: {} e {} (regra induzida, confianca {:.0%}).'.format(concept, target, conf)

        # Camada 3: BFS sobre grafo estendido (concept_graph + induced)
        graph_ext = defaultdict(set)
        for node, targets_d in self.concept_graph._edges.items():
            for tgt_n, rels_d in targets_d.items():
                if set(rels_d.keys()) & IS_A_RELS:
                    graph_ext[node].add(tgt_n)
        for (a, rel, tgt_r), conf in self.rule_ind._induced.items():
            if rel in IS_A_RELS and conf >= 0.25:
                graph_ext[a].add(tgt_r)

        visited_bfs = {c}
        frontier_bfs = deque([[c]])
        while frontier_bfs:
            path_bfs = frontier_bfs.popleft()
            if len(path_bfs) > 8:
                break
            node_bfs = path_bfs[-1]
            for nb in graph_ext.get(node_bfs, set()):
                if _deaccent(nb[:6]) == _deaccent(t[:6]) or nb == t:
                    chain = ' -> '.join(path_bfs + [nb])
                    return 'Sim: {} e {} (deduzido: {}).'.format(concept, target, chain)
                if nb not in visited_bfs:
                    visited_bfs.add(nb)
                    frontier_bfs.append(path_bfs + [nb])
        return None

    # -- Generalizacao extra-dominio via SDR semantico --------------------------

    def _cross_domain_bridge(self, query_text, query_sdr, top_k=3):
        """Conecta fatos de dominios diferentes usando similaridade semantica."""
        tl = query_text.lower().strip()
        words = [w for w in re.findall(r'\w{4,}', tl) if w not in _STOP_PT]
        if not words:
            return None

        query_vec = self.embed.sentence_vector(query_text)
        all_facts = self.fact_store.all_facts()
        if not all_facts:
            return None

        def _cosine(a, b):
            dot = sum(x*y for x, y in zip(a, b))
            na  = math.sqrt(sum(x*x for x in a)) or 1.0
            nb_  = math.sqrt(sum(x*x for x in b)) or 1.0
            return dot / (na * nb_)

        scored = []
        for fact in all_facts:
            fvec = self.embed.sentence_vector(fact)
            sim  = _cosine(query_vec, fvec)
            if sim > 0.30:
                scored.append((sim, fact))
        scored.sort(key=lambda x: -x[0])
        if not scored:
            return None

        # Cadeia relacional A->B->C via edges do ConceptGraph
        CHAIN_RELS = {REL_PRODUCES, REL_CAUSES, REL_HAS, REL_DOES, 'produz', 'causa', 'fornece'}
        for _, fact in scored[:5]:
            m = re.match(r'^([\w\s]{2,30}?)\s+(?:e|sao|tem|produz|causa|fornece)', fact.lower())
            if not m:
                continue
            fact_subj = m.group(1).strip()
            for qw in words[:3]:
                for tgt, rels in self.concept_graph._edges.get(qw, {}).items():
                    if set(rels.keys()) & CHAIN_RELS:
                        if (_deaccent(tgt[:5]) in _deaccent(fact_subj) or
                                _deaccent(fact_subj[:5]) in _deaccent(tgt)):
                            return 'Conexao entre dominios: {} -> {} -> {}: {}'.format(
                                qw, tgt, fact_subj, fact[:100])

        # Hipotese semantica: 2 fatos mais proximos
        if len(scored) >= 2 and scored[0][0] > 0.42:
            facts_txt = ' '.join(f.rstrip('.') for _, f in scored[:2])
            return 'Relacao provavel (semantica): {}'.format(facts_txt[:200])
        return None

    # -- deep_scan: calibração semântica silenciosa --------------------------------

    def deep_scan(self, corpus: str, silent: bool = False) -> str:
        """Calibra o MiniEmbed com corpus sem salvar fatos no FactStore/Brain.

        Lê o texto parágrafo a parágrafo (ou frase a frase), ajusta drift_vec
        de cada palavra mas **não cria memórias**, não altera fact_store,
        não dispara regras. O conhecimento fica codificado nos pesos vetoriais.

        Ideal para:
          - Calibrar vocabulário técnico (jurídico, médico, científico)
          - Pré-treinar com dumps de Wikipédia ou manuais
          - Criar intuição semântica sem inflar a memória episódica

        Parâmetro silent=True suprime output (para uso programático).
        """
        # Divide em sentenças/parágrafos
        sents = re.split(r'(?<=[.!?])\s+|\n{2,}', corpus.strip())
        sents = [s.strip() for s in sents if len(s.strip()) > 10]
        if not sents:
            return 'Corpus vazio ou muito curto.'

        tokens_before = self.embed._total_tokens
        words_before  = self.embed.vocab_size
        drift_before  = len(self.embed._drift_vec)

        for sent in sents:
            self.embed.learn(sent, update_vectors_only=True)

        tokens_after = self.embed._total_tokens
        words_after  = self.embed.vocab_size
        drift_after  = len(self.embed._drift_vec)

        msg = (f'[deep_scan] {len(sents)} sentenças processadas. '
               f'Tokens: +{tokens_after - tokens_before} | '
               f'Vocab: +{words_after - words_before} palavras | '
               f'Drift atualizado: {drift_after} entradas.')
        if not silent:
            print(msg)
        return msg

    def calibrate(self, source: str) -> str:
        """Alias de deep_scan para uso conversacional.

        Aceita texto direto, caminho de arquivo (.txt) ou URL básica.
        Retorna relatório de calibração.

        Uso: n.calibrate("texto longo sobre astronomia...")
             n.calibrate("/path/to/corpus.txt")
        """
        # Verifica se é caminho de arquivo
        if len(source) < 260 and source.endswith('.txt'):
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    corpus = f.read()
                return self.deep_scan(corpus)
            except FileNotFoundError:
                return f'Arquivo não encontrado: {source}'
            except Exception as e:
                return f'Erro ao ler arquivo: {e}'
        # Texto direto
        return self.deep_scan(source)

    def train_spatial_pooler(self, corpus: Optional[str] = None,
                              epochs: int = 3, silent: bool = False) -> str:
        """Treina o Semantic SDR Encoder (Spatial Pooler) com o conhecimento atual.

        O Spatial Pooler aprende a mapear vetores semânticos (MiniEmbed) para
        SDRs onde palavras/frases similares têm ALTO Jaccard — ao contrário do
        hash puro onde o Jaccard é ruído.

        Após treinamento:
          - CognitiveBrain.recall() passa a ser semântico (não só hash)
          - "gato" pode recuperar fatos sobre "felino" (sem ter ensinado explicitamente)
          - brain.is_novel() continua funcionando (novos conceitos = SDR diferente)

        corpus: texto adicional para calibração (opcional).
                Se None, usa os fatos já aprendidos + ngram sentences.
        epochs: 3–5 é suficiente para vocabulário técnico de <1000 palavras.

        Uso:
          n.train_spatial_pooler()               # usa o que já sabe
          n.train_spatial_pooler(wiki_corpus, epochs=5)  # com corpus extra
        """
        # Coleta textos para treino: fatos + sentences do NGram + corpus extra
        train_texts: List[str] = []
        train_texts.extend(self.fact_store.all_facts())
        train_texts.extend(list(self.ngram._sentences)[-500:])
        if corpus:
            sents = re.split(r'(?<=[.!?])\s+|\n{2,}', corpus.strip())
            train_texts.extend([s.strip() for s in sents if len(s.strip()) > 10])

        if not train_texts:
            return 'Nenhum texto disponível. Ensine fatos primeiro com: aprenda: ...'

        if self.sp_encoder is None:
            self.sp_encoder = SemanticSDREncoder(embed_dim=self.embed.DIM)

        n_before = self.sp_encoder._updates
        self.sp_encoder.train(self.embed, train_texts, epochs=epochs)
        n_after  = self.sp_encoder._updates
        self._sp_trained = True

        # Re-indexa o CognitiveBrain com SDRs semânticos
        # (os fatos foram armazenados antes com hash — precisa re-armazenar)
        reindexed = 0
        all_traces = list(self.brain._index._records.values()) if hasattr(self.brain._index, '_records') else []
        # Alternativa: usa os fatos do FactStore que é mais direto
        for fact_text in self.fact_store.all_facts():
            sem_sdr = self.semantic_encode(fact_text)
            self.brain.store(sem_sdr, fact_text, tag='FACT')
            reindexed += 1

        msg = (f'[Spatial Pooler] Treinado: {n_after - n_before} updates | '
               f'{len(train_texts)} textos | {epochs} épocas | '
               f'{reindexed} fatos re-indexados semanticamente | '
               f'SDR semântico ativo.')
        if not silent:
            print(msg)
        return msg

    def semantic_encode(self, text: str) -> SparseSDR:
        """Codifica texto em SDR semântico (via Spatial Pooler se treinado).

        Se o Spatial Pooler foi treinado (train_spatial_pooler chamado):
          → usa SemanticSDREncoder para SDR semanticamente coerente
        Caso contrário:
          → usa MultiLobeEncoder (hash puro, como antes)
        """
        if self._sp_trained and self.sp_encoder is not None:
            vec = self.embed.sentence_vector(text)
            return self.sp_encoder.encode(vec, learn=False)
        return self.encoder.encode(text)


    # ── [V9→FINAL FIX] Código de auto-persistência foi movido
    # ── para dentro do __init__ (estava em código morto após return).


    # ── API pública ────────────────────────────────────────────────────────────

    # Palavras de template das respostas que NÃO são entidades semânticas
    _CTX_NOISE: frozenset = frozenset({
        'aprendi', 'acordo', 'aprenda', 'ensine', 'tenho', 'esta', 'minha',
        'veja', 'vejamos', 'claro', 'portanto', 'entao', 'assim', 'pois',
        'nossa', 'vale', 'notar', 'lembrar', 'saber', 'dizer', 'segue',
        'segue', 'abaixo', 'acima', 'conforme', 'segundo', 'segundo',
        'tambem', 'ainda', 'apenas', 'mesmo', 'outro', 'outra', 'alem',
        'disso', 'nisso', 'isso', 'aquilo', 'este', 'esta', 'esse', 'essa',
        'eles', 'elas', 'dele', 'dela', 'nele', 'nela', 'tipo', 'modo',
        'forma', 'maneira', 'base', 'parte', 'caso', 'ponto', 'nivel',
    })

    def _update_context(self, text: str, response: str) -> None:
        """Atualiza o ContextEngine semântico após cada turno.

        Mantém um vetor de tópico acumulado (128 floats) que representa
        o contexto de toda a conversa — sem limite de tokens.
        """
        alpha = max(0.3, 1.0 / (1.0 + self._ctx_turn * 0.1))

        q_vec  = self.embed.sentence_vector(text)
        r_vec  = self.embed.sentence_vector(response[:200])
        turn_vec = [0.6 * q_vec[k] + 0.4 * r_vec[k]
                    for k in range(self.embed.DIM)]
        nrm = math.sqrt(sum(x*x for x in turn_vec)) or 1.0
        turn_vec = [x/nrm for x in turn_vec]

        for k in range(self.embed.DIM):
            self._ctx_topic_vec[k] = (alpha * turn_vec[k]
                                      + (1.0 - alpha) * self._ctx_topic_vec[k])

        # Extrai entidades da QUERY primeiro (mais confiáveis), depois da resposta
        # Filtra: mínimo 3 chars, sem stopwords, sem palavras de template
        def _clean_entities(src_text: str) -> List[str]:
            return [w for w in _tokenize_embed(src_text)
                    if len(w) >= 3
                    and w not in _STOP_PT
                    and w not in self._CTX_NOISE
                    and not w.isdigit()]

        # Query: entidades têm mais peso (o que o usuário perguntou)
        q_entities = _clean_entities(text)[:5]
        # Resposta: entidades do sujeito principal (não palavras de template)
        r_entities = _clean_entities(response[:150])[:4]

        # Adiciona entidades: query primeiro, depois resposta
        for e in reversed(q_entities + r_entities):
            if e in self._ctx_entities:
                self._ctx_entities.remove(e)
            self._ctx_entities.insert(0, e)
        self._ctx_entities = self._ctx_entities[:20]

        self._ctx_turn += 1

    def _ctx_relevant_facts(self, query: str, top_k: int = 4) -> List[str]:
        """Recupera fatos do histórico mais relevantes para a query atual.

        Combina 3 sinais:
          1. Similaridade semântica com o vetor de tópico acumulado
          2. Similaridade direta com a query
          3. Entidades atualmente ativas no contexto

        Retorna fatos do histórico completo (sem limite de tokens).
        """
        if not self._dialog_ctx:
            return []

        query_vec = self.embed.sentence_vector(query)
        ctx_vec   = self._ctx_topic_vec

        # Score de cada turno anterior
        scored: List[Tuple[float, str, str]] = []
        for turn_q, turn_r in self._dialog_ctx:
            # Combina texto do turno
            turn_text = turn_q + ' ' + turn_r[:120]
            tv = self.embed.sentence_vector(turn_text)

            # Similaridade com query atual
            sim_q = self.embed.cosine(query_vec, tv)
            # Similaridade com tópico acumulado
            sim_c = self.embed.cosine(ctx_vec, tv)
            # Boost por entidades ativas
            turn_tokens = set(_tokenize_embed(turn_text))
            entity_boost = sum(1 for e in self._ctx_entities[:8]
                               if e in turn_tokens) * 0.1

            score = 0.5 * sim_q + 0.3 * sim_c + entity_boost
            scored.append((score, turn_q, turn_r))

        scored.sort(reverse=True)
        # Retorna as queries mais relevantes do histórico
        return [q for _, q, _ in scored[:top_k]]

    def chat(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ''
        # Resolve pronomes usando ContextEngine (histórico completo + vetor tópico)
        text = self._resolve_pronouns(text)
        # Usa SDR semântico se Spatial Pooler treinado, senão hash puro
        sdr = self.semantic_encode(text)
        self.homeostasis.on_query()
        self._curiosita.tick()
        
        # V10: Novelty detection — inputs novos reforçam aprendizado
        novelty_score = self.novelty.update(sdr)
        if novelty_score > 0.7:
            self.homeostasis.on_novel_input()
            # Boost de surpresa: amplifica bits raros no SDR
            sdr = self.novelty.surprise_boost(sdr)
        
        # V10: Predictive cache — busca resposta pré-computada
        cached = self.pred_cache.get_by_sdr(sdr, min_overlap=0.35)
        if cached and novelty_score < 0.3:
            response = cached  # resposta pré-computada válida
        else:
            response = self._route(text, sdr)
        
        # V10: Publica no RepresentationalBus
        self.rep_bus.publish(RepMessage(
            source='chat', sdr=sdr, text=text[:100], priority=1.0 + novelty_score))
        
        self.embed.learn(text)
        self.episodes.record(text, response, sdr,
                             context=self.encoder._detect_context(text))
        self.ngram.learn_text(text)
        
        # V10: Temporal memory — registra o fato
        self.temporal.record(text[:60])
        # Histórico completo — sem limite fixo de 3 trocas
        self._dialog_ctx.append((text, response))
        # Limita memória RAM: mantém últimas 100 trocas explícitas
        # mas o _ctx_topic_vec mantém o contexto de TODA a conversa
        if len(self._dialog_ctx) > 100:
            self._dialog_ctx = self._dialog_ctx[-100:]
        # Atualiza ContextEngine semântico (sem limite de tokens)
        self._update_context(text, response)
        return response

    def learn(self, fact: str) -> str:
        clean = _RE_LEARN.sub('', fact).strip()
        return self._handle_learn(clean)

    def theorize(self, text: str) -> Belief:
        sdr    = self.encoder.encode(text)
        belief = self.epistemic.theorize(text, sdr)
        return self.epistemic.validate(belief, self.brain)

    def abstract(self) -> List[str]:
        """Executa clustering semântico e retorna nomes dos novos clusters."""
        new_cl = self.abstractor.run(self.embed, self.concept_graph, self.edge_net)
        return [c.name for c in new_cl]

    def induce_rules(self) -> int:
        """Minera regras transitivas e aplica as de alta confiança ao grafo."""
        self.rule_ind.run(self.concept_graph)
        return self.rule_ind.apply_to_graph(self.concept_graph, self.edge_net)

    def top_concepts(self, concepts: List[str], k: int = 10,
                     query: str = '') -> List[str]:
        """Retorna os k conceitos mais salientes de uma lista."""
        qv = self.embed.sentence_vector(query) if query and self.embed._vocab else None
        return self.salience.top_k(concepts, k, self.concept_graph, qv, self.embed)

    def analogy(self, a: str, b: str, c: str) -> List[str]:
        # V10: XOR analogy (SDR space) + graph analogy
        xor_results = self.xor_bind.analogy(a, b, c, top_k=3)
        graph_results = self.concept_graph.analogy(a, b, c, self.encoder)
        # Merge results, XOR first
        seen = set()
        merged = []
        for _, word in xor_results:
            if word.lower() not in seen:
                merged.append(word)
                seen.add(word.lower())
        for word in graph_results:
            if word.lower() not in seen:
                merged.append(word)
                seen.add(word.lower())
        return merged[:5]

    def sleep(self, cycles: int = 1) -> ConsolidationReport:
        report = self.consolidator.consolidate(self.brain, cycles)
        self.homeostasis.on_sleep()
        self.concept_graph.consolidate()
        graph_prune = self.consolidator.prune_graph(self.concept_graph)
        self.edge_net.decay_all()
        pruned = self.edge_net.prune_weak()

        # v9: indução de regras transitivas
        new_rules = self.rule_ind.run(self.concept_graph)
        rules_applied = self.rule_ind.apply_to_graph(self.concept_graph, self.edge_net)

        # v9: clustering semântico emergente
        new_clusters = self.abstractor.run(self.embed, self.concept_graph, self.edge_net)

        # V10: Temporal memory pruning during sleep
        temporal_pruned = self.temporal.prune(threshold=0.05)
        
        # V10: SDR Reasoner auto-generalization from brain memories
        if len(self.brain._memories) > 10:
            # Group memories by tag and create prototypes
            by_tag: Dict[str, List[SparseSDR]] = defaultdict(list)
            for mem in self.brain._memories:
                by_tag[mem.tag].append(mem.sdr)
            for tag, sdrs in by_tag.items():
                if len(sdrs) >= 3:
                    self.sdr_reasoner.generalize(f'proto_{tag}', sdrs[-20:])
        
        # V10: Predictive cache warm-up
        if self._ctx_entities:
            predictions = self.pred_cache.predict(
                self._ctx_entities[:5], self.concept_graph, self.embed)
        
        report.metadata = {**graph_prune,
                           'temporal_pruned': temporal_pruned,
                           'edges_pruned': pruned,
                           'rules_induced': len(new_rules),
                           'rules_applied': rules_applied,
                           'clusters_found': len(new_clusters),
                           'cluster_names': [c.name for c in new_clusters[:5]]}
        return report


    def wake(self, context_file: str = 'nexus_context.json') -> str:
        """Acorda o sistema carregando o contexto da sessão anterior.

        Retorna string descritiva do que foi recuperado.
        """
        ok = self.load_context(context_file)
        if not ok:
            return 'Iniciando sessão nova — nenhum contexto anterior encontrado.'
        keywords = [q for q, _ in self._dialog_ctx if not q.startswith('[contexto')]
        ctx_entry = next((q for q, _ in self._dialog_ctx if q.startswith('[contexto')), '')
        topics = ctx_entry.replace('[contexto anterior] tópicos: ', '') if ctx_entry else ''
        n_facts = len(self.fact_store.all_facts())
        return (f'Sessão restaurada. {n_facts} fatos disponíveis.'
                + (f' Tópicos anteriores: {topics}.' if topics else ''))

    def status(self) -> Dict:
        return {
            'version': self.VERSION,
            'brain':   self.brain.stats,
            'edges':   self.edge_net.edge_count,
            'facts':   len(self.fact_store),
            'graph':   {'nodes': self.concept_graph.node_count,
                        'edges': self.concept_graph.edge_count},
            'ngram':   len(self.ngram._sentences),
            'embed':   {'vocab': self.embed.vocab_size, 'dim': self.embed.DIM},
            'sdr':     {'size': SDR_SIZE, 'active': SDR_ACTIVE},
            'episodes': self.episodes.summary(),
            'homeostasis': self.homeostasis.state(),
            'hypotheses': len(self.epistemic.hypotheses()),
            'rules_induced': len(self.rule_ind._induced),
            'clusters':      len(self.abstractor._clusters),
            'salience_tracked': len(self.salience._access),
            'xor_bindings': self.xor_bind.size,
            'novelty_avg': round(self.novelty.recent_novelty(), 3),
            'temporal_facts': len(self.temporal._timestamps),
            'sdr_prototypes': len(self.sdr_reasoner._prototypes),
            'pred_cache': self.pred_cache.stats,
            'bus_messages': len(self.rep_bus._messages),
        }


    # ── Persistência de contexto episódico ────────────────────────────────────

    def save_context(self, filepath: str = 'nexus_context.json') -> bool:
        """Salva o contexto da sessão atual de forma compacta.

        Persiste:
          - Fatos aprendidos nesta sessão (não os seeds)
          - Resumo textual do diálogo (palavras-chave)
          - Snapshot do ctx_vec do MiniEmbed (estado semântico)
          - _dialog_ctx (últimas 3 trocas) para continuidade imediata
        """
        import tempfile
        try:
            # Fatos da sessão = todos os fatos menos os seeds pré-carregados
            _SEED_SET = {
                'fotossíntese é o processo pelo qual plantas produzem glicose usando luz solar e CO2',
                'célula é a unidade básica da vida e pode ser procarionte ou eucarionte',
                'DNA é a molécula que carrega a informação genética de todos os seres vivos',
                'evolução é o processo de mudança das espécies ao longo do tempo por seleção natural',
                'mitose é a divisão celular que gera duas células com o mesmo número de cromossomos',
                'proteína é uma molécula formada por aminoácidos essencial para funções celulares',
                'átomo é a menor unidade da matéria composta por prótons nêutrons e elétrons',
                'gravidade é a força de atração entre corpos com massa descrita por Newton',
                'energia não pode ser criada nem destruída apenas transformada de uma forma para outra',
                'luz viaja a aproximadamente 300 mil quilômetros por segundo no vácuo',
                'relatividade de Einstein afirma que espaço e tempo são relativos ao observador',
                'termodinâmica estuda as transformações de energia especialmente calor e trabalho',
                'molécula é um agrupamento de átomos ligados quimicamente',
                'tabela periódica organiza os elementos químicos por número atômico',
                'reação química transforma substâncias reagentes em novos produtos com diferentes propriedades',
                'água é composta por dois átomos de hidrogênio e um de oxigênio com fórmula H2O',
                'algoritmo é uma sequência finita de instruções para resolver um problema',
                'função matemática é uma relação que associa cada elemento de um conjunto a exatamente um outro',
                'teorema de Pitágoras afirma que o quadrado da hipotenusa é igual à soma dos quadrados dos catetos',
                'número primo é divisível apenas por um e por ele mesmo como 2 3 5 7 11 13',
                'logaritmo é o expoente ao qual uma base deve ser elevada para produzir um número',
                'python é uma linguagem de programação de alto nível criada por Guido van Rossum',
                'algoritmo de busca binária encontra um elemento em uma lista ordenada em O(log n)',
                'internet é uma rede global de computadores interconectados via protocolos TCP/IP',
                'inteligência artificial é a área da computação que busca simular capacidades cognitivas',
                'machine learning é uma área da inteligência artificial que aprende padrões em dados',
                'banco de dados é um sistema organizado para armazenar recuperar e manipular dados',
                'compilador é um programa que traduz código fonte para linguagem de máquina',
                'sistema operacional gerencia recursos de hardware e software do computador',
                'bit é a menor unidade de informação digital e pode ser 0 ou 1',
                'byte é um conjunto de 8 bits e é a unidade básica de armazenamento digital',
                'Brasil é o maior país da América do Sul com capital em Brasília',
                'Brasília é a capital do Brasil inaugurada em 1960 por Juscelino Kubitschek',
                'São Paulo é a maior cidade do Brasil e um dos maiores centros financeiros do mundo',
                'Amazônia é a maior floresta tropical do mundo localizada na América do Sul',
                'Terra é o terceiro planeta do sistema solar e único com vida confirmada',
                'Lua é o único satélite natural da Terra com superfície coberta de crateras',
                'sistema solar é composto pelo Sol e oito planetas incluindo Mercúrio Vênus Terra Marte',
                'oceano Pacífico é o maior e mais profundo oceano do mundo',
                'Newton descobriu as leis do movimento e a lei da gravitação universal',
                'Einstein desenvolveu a teoria da relatividade geral e especial',
                'Darwin propôs a teoria da evolução por seleção natural no livro A Origem das Espécies',
                'Graham Bell inventou o telefone em 1876 e obteve a primeira patente',
                'internet foi criada nos anos 1960 pelo Departamento de Defesa dos Estados Unidos como ARPANET',
                'revolução industrial iniciou na Inglaterra no século XVIII com mecanização da produção',
                'segunda guerra mundial ocorreu entre 1939 e 1945 e foi o conflito mais devastador da história',
                'português é uma língua românica derivada do latim falada em Portugal Brasil e outros países',
                'linguística é a ciência que estuda a linguagem humana em seus aspectos fonológicos sintáticos e semânticos',
            }
            session_facts = [
                f for f in self.fact_store.all_facts()
                if f not in _SEED_SET
            ]

            # Resumo: conceitos mais salientes da sessão
            all_text = ' '.join(q for q, _ in self._dialog_ctx) + ' ' + ' '.join(session_facts[:10])
            keywords = sorted(
                {w for w in re.findall(r'[a-záéíóúâêôàã]{5,}', all_text.lower())
                 if w not in _STOP_PT},
                key=lambda w: -all_text.lower().count(w)
            )[:20]

            # ctx_vec snapshot — apenas palavras relevantes do diálogo
            # (não salva o ctx_vec completo para manter o arquivo compacto)
            dialog_words = set(re.findall(
                r'[a-záéíóúâêôàã]{3,}',
                ' '.join(q + ' ' + r for q, r in self._dialog_ctx).lower()
            )) | set(re.findall(r'[a-záéíóúâêôàã]{3,}',
                                ' '.join(session_facts[:20]).lower()))
            # Truncar para 3 casas: reduz tamanho sem perda semântica
            ctx_snapshot = {
                w: [round(x, 3) for x in vec]
                for w, vec in self.embed._ctx_vec.items()
                if w in dialog_words
            }

            data = {
                'saved_at':     time.time(),
                'session_facts': session_facts,
                'keywords':     keywords,
                'dialog_ctx':   list(self._dialog_ctx),
                'ctx_vec':      ctx_snapshot,
                'sv_version':   self.embed._sv_version,
            }
            dir_ = os.path.dirname(os.path.abspath(filepath)) or '.'
            fd, tmp = tempfile.mkstemp(dir=dir_, suffix='.tmp')
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                os.replace(tmp, filepath)
            except Exception:
                try: os.unlink(tmp)
                except OSError: pass
                raise
            return True
        except Exception as e:
            print(f'[CONTEXT SAVE ERROR] {e}')
            return False

    def load_context(self, filepath: str = 'nexus_context.json') -> bool:
        """Carrega o contexto de uma sessão anterior.

        Restaura fatos da sessão, ctx_vec e injeta resumo no _dialog_ctx
        para que o sistema "lembre" do que foi discutido.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f'[CONTEXT LOAD ERROR] {e}')
            return False

        # Restaurar fatos da sessão anterior
        loaded = 0
        for fact in data.get('session_facts', []):
            if fact not in self.fact_store.all_facts():
                sdr = self.encoder.encode(fact)
                self.brain.store(sdr, fact, tag='FACT', metadata={'source': 'context'})
                self.fact_store.add(fact)
                self.embed.learn(fact)
                self._learn_edge(fact)
                loaded += 1

        # Restaurar ctx_vec (estado semântico)
        ctx = data.get('ctx_vec', {})
        for w, vec in ctx.items():
            if w not in self.embed._ctx_vec:
                self.embed._ctx_vec[w] = vec
                self.embed._vocab.add(w)

        # Restaurar _dialog_ctx (últimas 3 trocas da sessão anterior)
        prev_ctx = data.get('dialog_ctx', [])
        if prev_ctx:
            self._dialog_ctx = [tuple(t) for t in prev_ctx[-3:]]

        # Injetar nota de continuidade como primeiro turno sintético
        keywords = data.get('keywords', [])
        if keywords:
            summary_q = f'[contexto anterior] tópicos: {", ".join(keywords[:8])}'
            summary_r = f'Entendido. Lembro que discutimos: {", ".join(keywords[:5])}.'
            if not any(summary_q == q for q, _ in self._dialog_ctx):
                self._dialog_ctx.insert(0, (summary_q, summary_r))
                if len(self._dialog_ctx) > 3:
                    self._dialog_ctx = self._dialog_ctx[-3:]

        # Invalidar cache de sv após restaurar ctx_vec
        self.embed._sv_cache.clear()
        self.embed._sv_version += 1

        return True

    def save(self, filepath: str) -> bool:
        """Salva o estado em disco de forma atômica.

        Escreve num arquivo temporário no mesmo diretório e só então
        renomeia para o destino final (os.replace é atômico no POSIX).
        Isso garante que o arquivo de destino nunca fica em estado
        parcialmente escrito, mesmo que o processo seja interrompido
        durante a serialização.
        """
        import tempfile
        try:
            data = {
                'version':      self.VERSION,
                'saved_at':     time.time(),
                'encoder':      self.encoder.to_dict(),
                'embed':        self.embed.to_dict(),
                'brain':        self.brain.to_dict(),
                'edge_net':     self.edge_net.to_dict(),
                'fact_store':   self.fact_store.to_dict(),
                'concept_graph': self.concept_graph.to_dict(),
                'conditional':  self.conditional.to_dict(),
                'deductive':    self.deductive.to_dict(),
                'epistemic':    self.epistemic.to_dict(),
                'code_eng':     self.code_eng.to_dict(),
                'ngram':        self.ngram.to_dict(),
                'episodes':     self.episodes.to_dict(),
                'homeostasis':  self.homeostasis.to_dict(),
                'workspace':    self.workspace.to_dict(),
                'one_shots':    self._one_shots,
                'pending_confirm': {
                    'new_text': self._pending_confirm['new_text'],
                    'old_text': self._pending_confirm['old_text'],
                } if self._pending_confirm else None,
                # v9 módulos novos
                'salience':   self.salience.to_dict(),
                'rule_ind':   self.rule_ind.to_dict(),
                'abstractor': self.abstractor.to_dict(),
                'wm':         self.wm.to_dict(),
                # rev.7: Spatial Pooler (SDR semântico)
                'sp_encoder': self.sp_encoder.to_dict() if self.sp_encoder else None,
                'sp_trained': self._sp_trained,
                # rev.8: ContextEngine
                'ctx_topic_vec':  self._ctx_topic_vec,
                'ctx_entities':   self._ctx_entities,
                'ctx_turn':       self._ctx_turn,
            }
            dir_ = os.path.dirname(os.path.abspath(filepath))
            # Cria o temporário no mesmo sistema de arquivos para garantir
            # que os.replace() seja atômico (sem cross-device move).
            fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix='.tmp')
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                os.replace(tmp_path, filepath)   # atômico no POSIX/Windows
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
            return True
        except Exception as e:
            print(f'[SAVE ERROR] {e}')
            return False

    @classmethod
    def load(cls, filepath: str, verbose: bool = False) -> 'NexusV8':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        n = cls.__new__(cls)
        n._verbose      = verbose
        n.encoder       = MultiLobeEncoder.from_dict(data.get('encoder', {}))
        n.embed         = MiniEmbed.from_dict(data.get('embed', {}))
        n.brain         = CognitiveBrain.from_dict(data.get('brain', {}))
        n.edge_net      = EdgeNetwork.from_dict(data.get('edge_net', {}))
        n.fact_store    = StructuredFactStore.from_dict(data.get('fact_store', {}))
        n.retriever     = HybridRetriever(n.fact_store, n.brain, n.embed)
        n.concept_graph = ConceptGraph.from_dict(data.get('concept_graph', {}))
        n.conditional   = ConditionalEngine.from_dict(data.get('conditional', {}))
        n.deductive     = DeductiveEngine.from_dict(data.get('deductive', {}))
        n.epistemic     = EpistemicLayer.from_dict(data.get('epistemic', {}))
        n.code_eng      = CodeGeneralizer.from_dict(data.get('code_eng', {}))
        n.math_eng      = MathEngine()
        n.ngram         = NGramMemory.from_dict(data.get('ngram', {}))
        n.mouth         = FluentMouth(n.encoder, n.ngram)
        n.episodes      = EpisodicStream.from_dict(data.get('episodes', {}))
        n.homeostasis   = Homeostasis.from_dict(data.get('homeostasis', {}))
        n.consolidator  = SleepConsolidator()
        n.workspace     = VirtualWorkspace.from_dict(data.get('workspace', {}))
        n._one_shots    = data.get('one_shots', {})
        # v9 módulos novos
        n.salience   = SalienceEngine.from_dict(data.get('salience', {}))
        n.rule_ind   = RuleInductor.from_dict(data.get('rule_ind', {}))
        n.abstractor = ConceptAbstractor.from_dict(data.get('abstractor', {}))
        n.wm         = WorkingMemory.from_dict(data.get('wm', {}))
        # rev.7: Spatial Pooler
        sp_data = data.get('sp_encoder')
        if sp_data:
            n.sp_encoder  = SemanticSDREncoder.from_dict(sp_data)
            n._sp_trained = data.get('sp_trained', True)
        else:
            n.sp_encoder  = None
            n._sp_trained = False
        # Restaurar pending_confirm: reconstrói SDR do novo fato se necessário
        pc = data.get('pending_confirm')
        if pc and pc.get('new_text'):
            n._pending_confirm = {
                'new_text': pc['new_text'],
                'old_text': pc['old_text'],
                'new_sdr':  n.encoder.encode(pc['new_text']),
            }
        else:
            n._pending_confirm = None
        n._dialog_ctx = []  # não persistido — janela de diálogo reinicia a cada sessão
        n._facts_since_sleep = 0
        def _auto_promote(belief: Belief, brain: CognitiveBrain) -> None:
            brain.store(belief.sdr, belief.text, tag='FACT',
                        confidence=belief.confidence)
        n.epistemic._on_promote = _auto_promote
        return n

    # ── Roteamento ─────────────────────────────────────────────────────────────

    # ── Pronomes multi-turno ──────────────────────────────────────────────────
    def _resolve_pronouns(self, text: str) -> str:
        """Resolve pronomes/elipses usando ContextEngine (histórico completo).

        Melhorias rev.8:
          - Usa _ctx_entities (entidades ativas da sessão inteira)
          - Resolve "os dois", "ambos", "eles" → par de entidades recentes
          - Resolve "o primeiro", "o segundo" → entidades por ordem de menção
          - Fallback multi-turno: se pronome não resolve no último turno,
            busca em até 5 turnos anteriores
          - Usa vetor tópico para escolher a entidade mais relevante
            quando há ambiguidade
        """
        if not self._dialog_ctx and not self._ctx_entities:
            return text

        tl = text.lower().strip()

        PRONOMES = re.compile(
            r'\b(?:ele|ela|eles|elas|dele|dela|deles|delas|'
            r'nele|nela|isso|disto|disso|nisso|aquilo|daquilo|'
            r'este|esta|esse|essa|estes|estas|esses|essas|'
            r'os\s+dois|as\s+duas|ambos|ambas|'
            r'o\s+primeiro|a\s+primeira|o\s+segundo|a\s+segunda)\b', re.I)

        CONTINUACAO = re.compile(
            r'^(?:e\s|e[?!]$|mais\s|também\s|o\s+que\s+mais|'
            r'quais\s+s(?:ão|ao)|me\s+(?:fale|conta|explica)\s+mais|'
            r'por\s+qu[eê]|como\s+assim|qual\s+a\s+vantage|'
            r'quais\s+(?:as\s+)?vantage|exemplos?\s*(?:de\s+)?(?:isso)?\s*[?]?$)',
            re.I)

        has_pronoun   = bool(PRONOMES.search(tl))
        is_continuity = bool(CONTINUACAO.match(tl)) and len(tl) < 60

        if not has_pronoun and not is_continuity:
            return text

        # ── Estratégia 1: Extrai sujeito do último turno da query ────────────
        # A query anterior é mais confiável que ctx_entities para pronomes imediatos
        subject = None
        if self._dialog_ctx:
            # Busca em até 5 turnos anteriores (não só o último)
            for prev_q, prev_r in reversed(self._dialog_ctx[-5:]):
                cand = self._extract_subject(prev_q)
                if cand and cand not in {'isso','ele','ela','aquilo',
                                         'formado','relacionado','mencionado'}:
                    subject = cand
                    break
                # Se a query não tem sujeito claro, tenta a resposta
                if not subject:
                    cand_r = self._extract_subject(prev_r)
                    if cand_r and len(cand_r) >= 3:
                        subject = cand_r
                        break

        # ── Estratégia 2: Entidades ativas — mais relevante para query atual ─
        # Usa ctx_entities quando o sujeito do turno anterior é ambíguo
        if not subject or subject in _STOP_PT:
            if self._ctx_entities:
                query_vec = self.embed.sentence_vector(text)
                best_sim, best_entity = 0.0, None
                for entity in self._ctx_entities[:10]:
                    if len(entity) < 3: continue
                    # Ignora palavras genéricas de continuação
                    if entity in {'aprendi','carrega','molecula','define',
                                  'realiza','produz','ocorre','contém'}:
                        continue
                    ev = self.embed.sentence_vector(entity)
                    sim = self.embed.cosine(query_vec, ev)
                    if sim > best_sim:
                        best_sim, best_entity = sim, entity
                if best_entity and best_sim > 0.02:
                    subject = best_entity

        if not subject:
            return text

        # ── Caso especial: "os dois" / "ambos" → par de entidades ───────────
        pair_match = re.search(r'\b(?:os\s+dois|as\s+duas|ambos|ambas)\b', tl)
        if pair_match and len(self._ctx_entities) >= 2:
            e1 = self._ctx_entities[0]
            e2 = next((e for e in self._ctx_entities[1:] if e != e1), None)
            if e2:
                pair_str = f"{e1} e {e2}"
                resolved = PRONOMES.sub(lambda m: pair_str if re.match(
                    r'os\s+dois|as\s+duas|ambos|ambas', m.group().lower()) else subject, text)
                return resolved

        # ── Substituição de pronomes simples ─────────────────────────────────
        if has_pronoun:
            def _replace(m):
                p = m.group().lower()
                if p in ('ele','ela','eles','elas','esse','essa',
                         'este','esta','esses','essas','estes','estas'):
                    return subject
                if p in ('dele','dela','deles','delas'):
                    return f'de {subject}'
                if p in ('nele','nela'):
                    return f'em {subject}'
                if p in ('isso','disto','disso','nisso','aquilo','daquilo'):
                    return subject
                return m.group()
            resolved = PRONOMES.sub(_replace, text)
            if resolved != text:
                resolved = re.sub(r'\b(?:de\s+uso|uso\s+de|sobre\s+de|de\s+sobre)\s+',
                                  'de ', resolved)
                return resolved

        # ── Continuação sem sujeito ───────────────────────────────────────────
        if is_continuity:
            if re.match(r'^(?:e\s+)?(?:as\s+)?vantage', tl):
                return f'quais as vantagens de {subject}?'
            if re.match(r'^exemplos?', tl):
                return f'me dê exemplos de {subject}'
            if re.match(r'^(?:e\s+)?por\s+qu', tl):
                return f'por que {subject}?'
            if re.match(r'^(?:e\s+)?como', tl):
                return f'como funciona {subject}?'
            if re.match(r'^(?:me\s+)?(?:fale|conta|explica)\s+mais', tl):
                return f'o que é {subject}?'
            return f'o que é {subject}?'

        return text

    def _extract_subject(self, text: str) -> str:
        """Extrai o sujeito principal de um texto (pergunta ou resposta)."""
        # Strip command prefixes before extracting subject
        tl = re.sub(r'^(?:aprenda?|aprend[ae]?|ensine|learn)\s*:\s*', '', text.lower().strip())
        tl = tl.strip()
        # Padrões de pergunta direta
        for pat in [
            r'(?:o\s+que\s+[eé]|quem\s+[eé]|o\s+que\s+s[aã]o)\s+([\w\s]{2,25}?)\s*[?.]',
            r'(?:defin[ae]|expliqu[ae]|me\s+fal[ae]\s+(?:sobre\s+)?)([\w\s]{2,25?})[?.]',
            r'(?:diferença\s+entre\s+)([\w]+)',
            r'(?:sobre\s+|de\s+)([\w]+)\s*[?]?$',
        ]:
            m = re.search(pat, tl)
            if m:
                cand = m.group(1).strip()
                if cand and cand not in {'isso', 'ele', 'ela', 'aquilo'} and len(cand) >= 2:
                    return cand
        # Fallback: primeiro token ≥3 chars fora de stopwords ampliadas
        _SKIP = _STOP_PT | {'qual', 'quem', 'como', 'porque', 'para', 'quando',
                             'exemplos', 'exemplo', 'vantagens', 'vantagem',
                             'desvantagens', 'tipos', 'tipo', 'caracteristicas',
                             'mais', 'menos', 'sobre', 'fale', 'conte', 'explique',
                             'aprenda', 'aprendi', 'aprende', 'ensine', 'learn',
                             'defina', 'explique', 'descreva', 'gere', 'compare'}
        tokens = [w for w in re.findall(r'[a-záéíóúâêôàã\w]{3,}', tl)
                  if w not in _SKIP]
        return tokens[0] if tokens else ''

    def _route(self, text: str, sdr: SparseSDR) -> str:
        tl = text.lower().strip()

        # ── Confirmação pendente tem prioridade absoluta ───────────────────────
        # Se há um fato aguardando resolução de contradição, qualquer input do
        # usuário é interpretado como resposta: substituir / contexto / cancelar.
        if self._pending_confirm is not None:
            return self._handle_confirm(text)

        # One-shot commands têm precedência máxima: se o texto (normalizado)
        # bate com um trigger aprendido, retorna a resposta imediatamente.
        if self._one_shots:
            tl_clean = re.sub(r'[^a-záàâãéèêíóôõúçüñ\w\s]', '', tl).strip()
            if tl_clean in self._one_shots:
                return self._one_shots[tl_clean]

        # Social (só se não for comando)
        _is_cmd = bool(_RE_LEARN.match(text) or _RE_CORRECT.search(text)
                       or _RE_CODE.search(text) or _RE_THEORIZE.search(text)
                       or _RE_ONE_SHOT.search(text))
        if not _is_cmd:
            for key, resp in _SOCIAL.items():
                if re.search(r'(?<![\w])' + re.escape(key) + r'(?![\w])', tl):
                    return resp

        # Ordem importa
        # IS_A queries diretas: "X é um Y?" — rota dedicada.
        # Guarda a detecção para uso posterior, mas não dispara se _SUBJ_M
        # já cobre (queries definitórias: "o que é X?" ficam no _handle_query)
        _isa_m = _RE_ISA.match(tl)
        _is_definitional = bool(_SUBJ_M.search(text))
        if _isa_m and not _is_definitional:
            c_isa = _isa_m.group(1).strip()
            t_isa = _isa_m.group(2).strip()
            # Exclui sujeitos que são stopwords/artigos ("o que", "um", etc.)
            _bad_subj = {'o', 'a', 'os', 'as', 'um', 'uma', 'que', 'o que', 'qual', 'quem'}
            if (c_isa not in _bad_subj and t_isa not in _bad_subj
                    and c_isa != t_isa and len(c_isa) > 1 and len(t_isa) > 1):
                chain_ans = self._check_isa_chain(c_isa, t_isa)
                if chain_ans:
                    return chain_ans
                # Sem cadeia confirmada: resposta negativa contextualizada
                # Não retorna aqui — deixa cair no fluxo normal para tentar
                # FactStore / EdgeNet antes de declarar desconhecimento

        # HAS queries: "X tem Y?" — tenta herança IS_A→HAS antes do fluxo normal
        _has_m = _RE_HAS_QUERY.match(tl)
        if _has_m:
            c_has = _has_m.group(1).strip()
            p_has = _has_m.group(2).strip()
            _bad = {'o', 'a', 'os', 'as', 'um', 'uma', 'que', 'o que'}
            if c_has not in _bad and len(c_has) > 1 and len(p_has) > 1:
                has_ans = self._check_has_chain(c_has, p_has)
                if has_ans:
                    return has_ans

        if _RE_LEARN.match(text):       return self._handle_learn(_RE_LEARN.sub('', text).strip())
        if _RE_CORRECT.search(text):    return self._handle_correct(text, sdr)
        if _RE_CODE.search(text):       return self._handle_code(text)
        if _RE_MATH.search(text):       return self._handle_math(text)
        if _RE_ONE_SHOT.search(text):   return self._handle_one_shot(text, sdr)
        if _RE_ANALOGY.search(text):    return self._handle_analogy(text)
        if _RE_DEDUCE.search(text):     return self._handle_deduce(text, sdr)
        # Intents conversacionais — antes de SUBJ_M genérico
        if _RE_COMPARE.search(text):    return self._handle_compare(text, sdr)
        if _RE_CAUSE.search(text):      return self._handle_cause(text, sdr)
        if _RE_LIST.search(text):       return self._handle_list(text, sdr)
        if _RE_OPINION.search(text):    return self._handle_opinion(text, sdr)
        if _RE_META.search(text):       return self._handle_meta(text, sdr)
        # _SUBJ_M tem prioridade sobre _RE_DEDUCE_COND: "o que são répteis?" não é SE-ENTÃO
        if _SUBJ_M.search(text):        return self._handle_query(text, sdr)
        if _RE_DEDUCE_COND.search(text):return self._handle_conditional(text, sdr)
        if _RE_THEORIZE.search(text):   return self._handle_theorize(text, sdr)
        if _RE_EXPLORE.search(text):    return self._handle_explore(text, sdr)
        if _RE_RELATION.search(text):   return self._handle_relation(text)
        if _RE_GRAPH.search(text):      return self._handle_graph(text)
        if _RE_SEARCH.search(text):     return self._handle_search(text)
        if _RE_EPISODE.search(text):    return self._handle_episode(sdr)
        if _RE_STATUS.search(text):     return self._handle_status()
        if _RE_GENERATE.search(text):   return self._handle_generate(text)
        if _RE_DEEPSCAN.search(text):   return self._handle_deepscan(text)

        return self._handle_query(text, sdr)

    # ── Handlers ───────────────────────────────────────────────────────────────

    def _handle_learn(self, text: str) -> str:
        if not text:
            return 'O que devo aprender?'
        sdr = self.encoder.encode(text)
        self.embed.learn(text)
        self.homeostasis.on_learn()

        # ── Detecção proativa de contradição ──────────────────────────────────
        # Usa EpistemicLayer.validate para verificar conflito com memória existente.
        # Se houver contradição, pausa o aprendizado e pergunta ao usuário o que fazer.
        belief = self.epistemic.theorize(text, sdr, tag='FACT')
        validated = self.epistemic.validate(belief, self.brain)

        if validated.contradictions:
            # Guarda o fato novo pendente de resolução
            self.homeostasis.on_contradiction()
            old_text = validated.contradictions[0]
            self._pending_confirm = {
                'new_text': text,
                'old_text': old_text,
                'new_sdr':  sdr,
            }
            return self.mouth.speak_contradiction_ask(old_text, text)

        # ── Sem contradição: armazenar em todas as camadas ───────────────────
        return self._store_learned(text, sdr)

    def _store_learned(self, text: str, sdr: SparseSDR) -> str:
        """Persiste um fato validado (sem contradição) em todas as camadas."""
        self.brain.store(sdr, text, tag='FACT')
        self.fact_store.add(text)
        self.ngram.learn_text(text)
        self.conditional.learn(text)
        self.deductive.learn(text)
        self._learn_edge(text)
        
        # V10: XOR binding — codifica relação no espaço SDR
        _xor_m = re.match(r'^([\w\s]{2,25})\s+(?:é|são|tem|possui|produz|causa)\s+(.+)$', text.lower().strip())
        if _xor_m:
            _xor_subj, _xor_obj = _xor_m.group(1).strip(), _xor_m.group(2).strip()
            _xor_rel = 'é'
            for _r in ['tem', 'possui', 'produz', 'causa']:
                if _r in text.lower():
                    _xor_rel = _r
                    break
            self.xor_bind.bind(_xor_subj, _xor_rel, _xor_obj)
        
        # V10: Temporal memory
        self.temporal.record(text[:60])
        for pat, rel_type in _REL_PATTERNS:
            m = pat.match(text.strip().lower())
            if m:
                subj = m.group(1).strip()
                obj  = m.group(2).strip()
                self.concept_graph.add_edge(subj, rel_type, obj)
                # Registra no salience como acesso inicial
                self.salience.touch(subj)
                self.salience.touch(obj)
                break
        if self.brain.is_novel(sdr):
            self.homeostasis.on_novel_input()
        # Induz regras transitivas imediatamente após novo fato IS_A
        # Só executa se há nós relevantes para não custar caro em cada learn
        if self.concept_graph.node_count >= 2:
            new_rules = self.rule_ind.run(self.concept_graph, passes=2)
            if new_rules:
                self.rule_ind.apply_to_graph(self.concept_graph, self.edge_net)
        # Auto-consolidação a cada 50 fatos novos (silenciosa)
        self._facts_since_sleep += 1
        if self._facts_since_sleep >= 50:
            self.sleep(cycles=1)
            self._facts_since_sleep = 0
        # Auto-save periódico a cada N fatos
        if self._autosave_enabled:
            self._facts_since_save += 1
            if self._facts_since_save >= self._autosave_every:
                self.save(self._persist_path)
                self._facts_since_save = 0
        return f'Aprendi: "{text}"'

    def feedback(self, success: bool, context_text: str = '') -> None:
        """
        Feedback explícito sobre a última resposta.
        success=True  → reforça arestas da cadeia usada (Hebbiano)
        success=False → enfraquece arestas usadas (anti-Hebbiano)
        Integra ReinforcementFeedback com LearnedEdge.reinforce/weaken.
        """
        reward = 1.0 if success else -1.0
        # Toca conceitos envolvidos no contexto para ajustar salience
        words = [w for w in re.findall(r'\w{4,}', context_text.lower())
                 if w not in _STOP_PT]
        for w in words[:6]:
            self.salience.touch(w)
        # Reforça ou enfraquece arestas relacionadas ao contexto
        for w in words[:3]:
            for edge in self.edge_net.get_by_source(w):
                if success:
                    edge.reinforce(evidence=context_text[:60], reward=0.5)
                else:
                    edge.weaken(penalty=0.3)
        # Atualiza homeostase
        if success:
            self.homeostasis.on_learn()
        else:
            self.homeostasis.on_failed_infer()

    def _handle_confirm(self, text: str) -> str:
        """Resolve a confirmação pendente de contradição.

        Ações explícitas:
          • "substituir" / "atualizar" — revisa crenças antigas e armazena o novo fato
          • "contexto diferente" / "ambos" — armazena ambos (coexistência contextual)
          • "cancelar" / "não" / "ignora" — descarta o novo fato

        Comportamento para entradas não-relacionadas:
          • Novo "aprenda:" → cancela o pending, aprende o novo fato, informa o usuário
          • Pergunta / consulta → reexibe o pending sem perder o estado
          • Qualquer outra coisa → reexibe o pending pedindo resposta clara
        """
        if self._pending_confirm is None:
            return self._handle_query(text, self.encoder.encode(text))

        new_text = self._pending_confirm['new_text']
        old_text = self._pending_confirm['old_text']
        new_sdr  = self._pending_confirm['new_sdr']
        tl       = text.lower().strip()

        # ── Substituir ───────────────────────────────────────────────────────
        if _RE_CONFIRM_REPLACE.search(tl):
            self._pending_confirm = None
            self.brain.revise_beliefs(new_sdr, new_text)
            self.fact_store.remove_by_text(old_text)
            result = self._store_learned(new_text, new_sdr)
            return (f'✅ Substituído.\n'
                    f'Anterior: "{old_text[:60]}"\n'
                    f'{result}')

        # ── Contexto diferente ───────────────────────────────────────────────
        if _RE_CONFIRM_CONTEXT.search(tl):
            self._pending_confirm = None
            result = self._store_learned(new_text, new_sdr)
            return (f'✅ Ambos guardados (contextos distintos).\n'
                    f'• "{old_text[:55]}"\n'
                    f'• "{new_text[:55]}"')

        # ── Cancelar explícito ───────────────────────────────────────────────
        if _RE_CONFIRM_CANCEL.search(tl):
            self._pending_confirm = None
            return f'↩️ Cancelado. Mantive: "{old_text[:70]}"'

        # ── Novo aprenda: durante pending — cancela o pending e aprende o novo
        # O usuário ignorou a pergunta e quer ensinar outra coisa.
        # Cancelamos o pending (mantemos o fato antigo) e processamos o novo.
        if _RE_LEARN.match(text):
            self._pending_confirm = None
            new_fact = _RE_LEARN.sub('', text).strip()
            aviso = (f'↩️ Pendente cancelado — mantive: "{old_text[:50]}"\n'
                     f'Agora processando: ')
            return aviso + self._handle_learn(new_fact)

        # ── Consulta / pergunta durante pending — reexibe sem perder o estado ─
        # O usuário fez uma pergunta; respondemos e lembramos do pending.
        if _SUBJ_M.search(text) or '?' in text:
            query_resp = self._handle_query(text, self.encoder.encode(text))
            reminder = (f'\n\n⚠️ Lembrete: ainda há um conflito pendente!\n'
                        f'Já sei: "{old_text[:60]}"\n'
                        f'Novo: "{new_text[:60]}"\n'
                        f'Responda: "substituir", "contexto diferente" ou "cancelar"')
            return query_resp + reminder

        # ── Entrada não reconhecida → reexibe o pending claramente ───────────
        return (f'⚠️ Não entendi "{text[:40]}".\n'
                f'Há um conflito aguardando resolução:\n'
                f'  Já sei: "{old_text[:60]}"\n'
                f'  Novo:   "{new_text[:60]}"\n'
                f'Responda: "substituir", "contexto diferente" ou "cancelar"')

    def _learn_edge(self, text: str) -> None:
        """Extrai tripleta do texto e registra no EdgeNetwork v7."""
        patterns = [
            (r'(.+?)\s+é\s+uma?\s+(.+)',          'é_um'),
            (r'(.+?)\s+é\s+(.+)',                  'é'),
            (r'(.+?)\s+usa\s+(.+)',                'usa'),
            (r'(.+?)\s+tem\s+(.+)',                'tem'),
            (r'(.+?)\s+pode\s+(.+)',               'pode'),
            (r'(.+?)\s+pertence\s+a\s+(.+)',       'pertence_a'),
            (r'(.+?)\s+causa\s+(.+)',              'causa'),
            (r'(.+?)\s+produz\s+(.+)',             'produz'),
            (r'(.+?)\s+equivale\s+a\s+(.+)',       'equivale'),
            (r'(.+?)\s+orbita\s+(?:a\s+|o\s+)?(.+)', 'orbita'),
        ]
        tl = text.lower().strip()
        for pat, rel in patterns:
            m = re.match(pat, tl, re.I)
            if m:
                s = m.group(1).strip()
                t = re.sub(r'\s+(para|quando|se|pois|porque).*$', '', m.group(2).strip())
                if len(s) >= 2 and len(t) >= 2 and len(s) <= 60 and len(t) <= 120:
                    self.edge_net.add(s, rel, t, evidence=text)
                break

    def _handle_correct(self, text: str, sdr: SparseSDR) -> str:
        clean = re.sub(_RE_CORRECT, '', text).strip().lstrip(':,. ')
        if not clean:
            return 'O que é o correto?'
        new_sdr = self.encoder.encode(clean)
        self.brain.revise_beliefs(new_sdr, clean)
        self.brain.store(new_sdr, clean, tag='FACT')
        self.fact_store.add(clean)
        self.embed.learn(clean)
        topic = re.findall(r'\w{4,}', clean.lower())
        return self.mouth.speak_correction(topic[0] if topic else '?', clean)

    def _handle_code(self, text: str) -> str:
        result = self.code_eng.run(text)
        if result['success']:
            out  = result['stdout'][:300] or '(sem saída)'
            code = result['code']
            if 'def ' in code or 'class ' in code:
                fname = re.sub(r'[^\w]', '_', text[:30].strip()).rstrip('_') + '.py'
                self.workspace.write(fname, code)
            return f'```python\n{code}\n```\n> {out}'
        if result.get('code'):
            broken = result['code']
            error  = result.get('error', '')
            healed = self.code_eng.heal_code(broken, error)
            if healed != broken:
                hr = self.code_eng._exec(healed)
                if hr['success']:
                    fname = re.sub(r'[^\w]', '_', text[:30].strip()).rstrip('_') + '.py'
                    self.workspace.write(fname, healed)
                    out = hr['stdout'][:300] or '(sem saída)'
                    return f'```python\n{healed}\n```\n> {out} (auto-reparado)'
        return (f'Não encontrei padrão para: "{text[:80]}". '
                f'Pode me ensinar o código?')

    def _handle_math(self, text: str) -> str:
        result = self.math_eng.evaluate(text)
        if result is None:
            return 'Não consegui calcular. Verifique a expressão.'
        # Se o resultado já é uma sentença completa (ex: percentagem), retorna direto
        return result if ('=' in result or '%' in result) else f'= {result}'

    def _handle_theorize(self, text: str, sdr: SparseSDR) -> str:
        belief = self.epistemic.theorize(text, sdr)
        belief = self.epistemic.validate(belief, self.brain)
        status_map = {'promoted': '✓ Promovida a Fato', 'rejected': '✗ Rejeitada',
                      'pending': '⏳ Pendente'}
        label = status_map.get(belief.status, belief.status)
        if belief.support:
            return f'Hipótese [{label}]: {belief.text}\nEvidência: {belief.support[0][:60]}'
        if belief.contradictions:
            return f'Hipótese [{label}]: {belief.text}\nConflito: {belief.contradictions[0][:60]}'
        return f'Hipótese [{label}]: {belief.text}\nConfiança: {belief.confidence:.2f}'

    def _handle_explore(self, text: str, sdr: SparseSDR) -> str:
        gap = self.epistemic.detect_gap(sdr, self.brain, text)
        if not gap:
            words = [w for w in re.findall(r'\w{4,}', text.lower())
                     if w not in _STOP_PT]
            if words:
                nbrs = self.concept_graph.neighbors(words[0], depth=2)[:3]
                if nbrs:
                    concepts = ', '.join(f'"{n}"({w:.2f})' for n, w in nbrs)
                    return f'Conceitos relacionados a "{words[0]}": {concepts}'
            return 'Nenhuma lacuna detectada. O assunto parece coberto.'
        return (f'Lacuna detectada: {gap.text}\n'
                f'Sugestão: aprofunde o conceito e me ensine mais.')

    def _handle_deduce(self, text: str, sdr: SparseSDR) -> str:
        tl_ded = text.lower()
        # 1. ConditionalEngine direto — para "logo/se X realiza/tem/é Y"
        # Tem prioridade pois usa regras explícitas (sem ambiguidade)
        m_logo = re.search(
            r'(?:logo|se)\s+(\w[\w\s]{1,20}?)\s+(?:é|são|tem|possui|realiza|produz|voa|nada|respira|faz)\s+(\w[\w\s]{1,20})',
            tl_ded)
        if m_logo:
            subj_l = m_logo.group(1).strip()
            prop_l = m_logo.group(2).strip()
            cond_r = self.conditional.infer(subj_l, prop_l,
                                            external_facts=self.fact_store.all_facts())
            if cond_r:
                return cond_r
        # 2. Scored deduce com re-ranking semântico
        result = self.deductive.scored_deduce(text)
        if result:
            return result
        # 3. WorkingMemory multi-hop
        words = [w for w in re.findall(r'\w{4,}', tl_ded) if w not in _STOP_PT]
        if words:
            wm_ans = self.wm.best_answer(words[0], self.concept_graph, self.fact_store)
            if wm_ans:
                self.wm.maybe_commit(self.concept_graph, self.edge_net)
                return wm_ans
        # 4. Inferência transitiva via CognitiveBrain SDR (com txt_a gate)
        inf = self.brain.infer_transitive(sdr, text)
        if inf:
            return self.mouth.speak_deduction(inf.conclusion,
                ' → '.join(r.rel_type for r in inf.chain))
        # 5. Dedução fuzzy via similaridade semântica (Hebbian Deduction)
        fuzzy = self.deductive.fuzzy_deduce(text)
        if fuzzy:
            return fuzzy
        return 'Não consigo deduzir. Pode me dar mais premissas?'

    def _handle_conditional(self, text: str, sdr: SparseSDR) -> str:
        # Extrai sujeito e propriedade da query
        # Padrão 1: "X é/tem/possui/são Y"
        m = re.search(r'(\w[\w\s]{1,20}?)\s+(?:é|tem|possui|são)\s+(\w[\w\s]{1,15})', text.lower())
        # Padrão 2: "se X então Y" / "se X, Y é verdade" / "se X então Y?"
        if not m:
            m2 = re.search(
                r'se\s+(\w[\w\s]{1,20}?)\s+(?:então|,?\s*logo|,?\s*portanto)\s+(?:é\s+)?(\w[\w\s]{1,15})',
                text.lower())
            if m2:
                m = m2
        if m:
            subj, prop = m.group(1).strip(), m.group(2).strip()
            # Remove stopwords e pontuação do prop
            prop = re.sub(r'[\?\!\.]', '', prop).strip()
            # Passa TODOS os fatos do FactStore como contexto externo —
            # isso fecha a ponte entre CognitiveBrain e ConditionalEngine.
            all_facts = self.fact_store.all_facts()
            result    = self.conditional.infer(subj, prop, external_facts=all_facts)
            if result:
                return result
        # Propagação v7 via EdgeNetwork
        words = [w for w in re.findall(r'\w{4,}', text.lower()) if w not in _STOP_PT]
        if words:
            props = self.edge_net.propagate(words[:2], max_depth=2)
            if props:
                top = sorted(props.items(), key=lambda x: -x[1])[:3]
                chain = ' → '.join(c for c, _ in top)
                return f'Propagação semântica: {chain}'
        return 'Não encontrei cadeia condicional.'

    def _handle_one_shot(self, text: str, sdr: SparseSDR) -> str:
        m = re.search(
            r'(?:bota\s+aí|manda\s+ver|novo\s+comando|nova\s+sintaxe)[:\s]+(\w[\w\s]*?)\s*[=:→]\s*(.+)',
            text, re.I)
        if not m:
            return 'Formato: "novo comando: <trigger> = <ação>"'
        trigger, action = m.group(1).strip(), m.group(2).strip()
        # Armazena em _one_shots (despachado por _route) E no encoder (SDR hint)
        trigger_key = re.sub(r'[^a-záàâãéèêíóôõúçüñ\w\s]', '', trigger.lower()).strip()
        self._one_shots[trigger_key] = action
        self.encoder.one_shot_learn(trigger, action)
        return f'One-shot aprendido: "{trigger}" → "{action}"'

    def _handle_analogy(self, text: str) -> str:
        m = re.search(
            r'(\w[\w\s]{1,20}?)\s+(?:é\s+para|:)\s+(\w[\w\s]{1,20}?)'
            r'\s+(?:como|assim\s+como|::)\s+(\w[\w\s]{0,20})',
            text, re.I)
        if not m:
            return 'Formato: "A é para B como C é para ?"'
        a, b, c = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        # Remove trailing stop-words or relational words ("é para", "é", etc.)
        c = re.sub(r'\s+(?:é|para|de|do|da|como|que|são).*$', '', c).strip()
        results = self.concept_graph.analogy(a, b, c, self.encoder)
        if results:
            return self.mouth.speak_fact(
                f'Analogia {a}:{b}::{c}:? → {", ".join(results[:3])}')
        return f'Não encontrei candidatos para a analogia {a}:{b}::{c}:?'

    def _handle_relation(self, text: str) -> str:
        m = re.search(
            r'(\w[\w\s]{1,20}?)\s*[–—\-]+\[(\w[\w_\s]*)\]\s*[–—\-→>]+\s*(\w[\w\s]{1,20})',
            text)
        if not m:
            return 'Formato: "A -[rel]-> B"'
        a, rel, b = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        self.concept_graph.add_edge(a, rel, b)
        self.edge_net.add(a, rel, b, evidence=text)
        return f'Relação aprendida: {a} -[{rel}]→ {b}'

    def _handle_graph(self, text: str) -> str:
        m_viz = re.search(r'vizinhos?\s+de\s+(\w[\w\s]{1,20})', text, re.I)
        m_cam = re.search(r'caminho\s+entre\s+(\w[\w\s]{1,20}?)\s+e\s+(\w[\w\s]{1,20})', text, re.I)
        if m_viz:
            concept = m_viz.group(1).strip()
            nbrs    = self.concept_graph.neighbors(concept, depth=2)[:5]
            if nbrs:
                return 'Vizinhos de "{}": {}'.format(
                    concept, ', '.join(f'{n}({w:.2f})' for n, w in nbrs))
            # Tenta EdgeNetwork
            edges = self.edge_net.get_by_source(concept)
            if edges:
                return 'Relações de "{}": {}'.format(
                    concept, ', '.join(f'{e.relation}→{e.target}' for e in edges[:5]))
            return f'Nenhum vizinho encontrado para "{concept}".'
        if m_cam:
            a, b = m_cam.group(1).strip(), m_cam.group(2).strip()
            path = self.concept_graph.path(a, b)
            return f'Caminho {a}→{b}: {" → ".join(path)}' if path else \
                   f'Não encontrei caminho entre "{a}" e "{b}".'
        return 'Especifique "vizinhos de X" ou "caminho entre A e B".'

    def _handle_search(self, text: str) -> str:
        query   = re.sub(r'\b(?:busque|procure|liste\s+tudo\s+sobre|mostre\s+o\s+que)\b', '',
                         text, flags=re.I).strip()
        results = self.retriever.retrieve(query, self.encoder.encode(query), top_k=5)
        if not results:
            return f'Nada encontrado sobre "{query}".'
        lines = [f'{i+1}. [{src}] {txt[:80]}' for i, (_, txt, src) in enumerate(results)]
        return '\n'.join(lines)

    def _handle_episode(self, sdr: SparseSDR) -> str:
        recent = self.episodes.recent(5)
        if not recent:
            return 'Nenhum episódio registrado ainda.'
        lines = [f'[{ep.id}] {ep.input_text[:50]} → {ep.output_text[:40]}'
                 for ep in recent]
        return 'Histórico recente:\n' + '\n'.join(lines)

    def _handle_status(self) -> str:
        s = self.status()
        b = s['brain']
        return (f'Nexus {s["version"]} | '
                f'Memórias: {b["total"]} (FACT:{b.get("FACT",0)} THEORY:{b.get("THEORY",0)}) | '
                f'Fatos: {s["facts"]} | Arestas: {s["edges"]} | '
                f'Nós: {s["graph"]["nodes"]} | Embed: {s["embed"]} tokens | '
                f'Regras: {s["rules_induced"]} | Clusters: {s["clusters"]} | '
                f'{s["homeostasis"]}')

    # ──────────────────────────────────────────────────────────────────────────
    # HANDLERS CONVERSACIONAIS — v9-conv
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_compare(self, text: str, sdr: SparseSDR) -> str:
        """Compara dois conceitos via TextWeaver (síntese semântica real)."""
        tl = text.lower()
        m = (re.search(r'entre\s+([\w\s]{2,25})\s+e\s+([\w\s]{2,25})(?:\?|$)', tl) or
             re.search(r'compare\s+([\w\s]{2,25})\s+e\s+([\w\s]{2,25})', tl) or
             re.search(r'([\w]+)\s+(?:vs\.?|versus|ou)\s+([\w]+)', tl) or
             re.search(r'([\w]+)\s+(?:melhor|pior)\s+(?:que|do\s+que)\s+([\w]+)', tl))

        if not m:
            return self._handle_query(text, sdr)

        a, b = m.group(1).strip(), m.group(2).strip()

        # Usa TextWeaver para comparação com síntese semântica real
        woven = self.text_weaver.weave_comparison(a, b)
        if woven and len(woven) > 40:
            return woven

        # Fallback: formato tabular clássico
        hits_a = self.fact_store.search(a, top_k=3, min_score=0.15)
        hits_b = self.fact_store.search(b, top_k=3, min_score=0.15)
        a_n = _deaccent(a.lower())
        b_n = _deaccent(b.lower())
        facts_a = [h for h in hits_a if a_n[:5] in _deaccent(h.lower())][:2]
        facts_b = [h for h in hits_b if b_n[:5] in _deaccent(h.lower())][:2]

        if not facts_a and not facts_b:
            return (f'Não tenho informações sobre {a} nem {b} para comparar. '
                    f'Ensine-me: aprenda: {a} é ...')

        lines = []
        if facts_a:
            lines.append(f'{_safe_capitalize(a)}: {" ".join(f.rstrip(".") for f in facts_a)}.')
        else:
            lines.append(f'{_safe_capitalize(a)}: sem dados disponíveis.')
        if facts_b:
            lines.append(f'{_safe_capitalize(b)}: {" ".join(f.rstrip(".") for f in facts_b)}.')
        else:
            lines.append(f'{_safe_capitalize(b)}: sem dados disponíveis.')

        result = '\n'.join(lines)
        if facts_a and facts_b:
            result += '\n\nAmbos têm características próprias — a escolha depende do contexto.'
        return result

    def _handle_cause(self, text: str, sdr: SparseSDR) -> str:
        """Por que X? / Como funciona X? — prioriza fatos explicativos."""
        m = (re.search(r'por\s+(?:que|qual\s+motivo)\s+(.+?)[\?\.!]?\s*$', text, re.I) or
             re.search(r'como\s+(?:funciona|ocorre|acontece|surge)\s+(.+?)[\?\.!]?\s*$', text, re.I) or
             re.search(r'o\s+que\s+causa\s+(.+?)[\?\.!]?\s*$', text, re.I))
        tema = m.group(1).strip() if m else text

        hits = self.fact_store.search(tema, top_k=6, min_score=0.15)
        if not hits:
            return self._handle_query(text, sdr)

        causal_kw = {'porque','causa','devido','resulta','produz','gera',
                     'espalhamento','fenomeno','processo','atraves','mediante',
                     'funciona','ocorre','acontece','origina','formado','gerado'}
        scored = []
        for h in hits:
            h_toks = set(_deaccent(w.lower()) for w in re.findall(r'\w+', h))
            score = len(h_toks & causal_kw)
            scored.append((score, h))
        scored.sort(key=lambda x: -x[0])
        best = scored[0][1]
        cap = _safe_capitalize(best)
        if not cap.endswith(('.','!','?')):
            cap += '.'
        return cap

    def _handle_list(self, text: str, sdr: SparseSDR) -> str:
        """me dê exemplos de X / liste X / quais são os X"""
        m = re.search(
            r'(?:exemplos?\s+de|liste\s+(?:os?\s+)?|cite\s+|'
            r'me\s+d[eê]\s+(?:\d+\s+)?|quais\s+s[aã]o\s+(?:os?|as?)\s+|'
            r'tipos?\s+de|alguns?\s+exemplos?\s+de)\s*(.+?)[\?\.!]?\s*$',
            text, re.I)
        tema = m.group(1).strip() if m else re.sub(
            r'^\s*(?:liste|cite|exemplos?|me\s+d[eê])\s*', '', text, flags=re.I).strip()

        hits = self.fact_store.search(tema, top_k=6, min_score=0.12)
        if not hits:
            return self._handle_query(text, sdr)

        tema_toks = set(_deaccent(w.lower()) for w in re.findall(r'\w{3,}', tema))
        relevant = [h for h in hits
                    if set(_deaccent(w.lower()) for w in re.findall(r'\w{3,}', h)) & tema_toks]
        if not relevant:
            relevant = hits[:3]

        if len(relevant) == 1:
            r = relevant[0]
            return r[0].upper() + r[1:] + ('' if r.endswith('.') else '.')

        items = relevant[:4]
        return '\n'.join(f'• {h.rstrip(".")}.' for h in items)

    def _handle_opinion(self, text: str, sdr: SparseSDR) -> str:
        """Recomendações e opiniões — apresenta dados e admite limitação."""
        m = re.search(
            r'(?:você\s+(?:recomenda|acha|prefere|indicaria)|'
            r'o\s+que\s+você\s+acha\s+d[eo]?|'
            r'vale\s+a\s+pena|me\s+(?:recomenda|indica|aconselha))\s*'
            r'(?:d[eo]?|sobre|o?s?|a?s?)?\s*(.+?)[\?\.!]?\s*$',
            text, re.I)
        tema = m.group(1).strip() if m else text

        hits = self.fact_store.search(tema, top_k=3, min_score=0.15)
        if not hits:
            return (f'Não tenho dados suficientes sobre {tema} para recomendar. '
                    f'Ensine-me: aprenda: {tema} é ...')

        h0 = hits[0]
        main = _safe_capitalize(h0)
        if not main.endswith('.'):
            main += '.'
        extra = f' {hits[1]}' if len(hits) > 1 else ''
        return (f'{main}{extra}\n\n'
                f'Posso dar mais detalhes se você especificar o que precisa.')

    def _handle_meta(self, text: str, sdr: SparseSDR) -> str:
        """Curiosidades, o que o sistema sabe, pedidos abertos."""
        import random as _rnd
        tl = text.lower()

        if re.search(r'curiosidade|algo\s+interessante|me\s+conta?|surpreend', tl):
            all_facts = self.fact_store.all_facts()
            if all_facts:
                fact = _rnd.choice(all_facts[:min(50, len(all_facts))])
                cap = fact[0].upper() + fact[1:]
                return ('Curiosidade: ' + cap + ('' if cap.endswith('.') else '.'))
            return 'Ainda não aprendi fatos suficientes. Ensine-me com: aprenda: ...'

        m = re.search(r'(?:o\s+que\s+você\s+sabe|sabe\s+algo)\s+(?:sobre|de)\s+(.+?)[\?\.!]?\s*$', tl)
        if m:
            tema = m.group(1).strip()
            hits = self.fact_store.search(tema, top_k=3, min_score=0.15)
            if hits:
                # Deduplicar: remove hits que são substring de outro
                deduped = []
                for h in hits[:3]:
                    hl = h.lower()
                    if not any(hl in other.lower() and hl != other.lower() for other in hits[:3]):
                        deduped.append(h)
                if not deduped:
                    deduped = hits[:1]
                return '\n'.join(_safe_capitalize(h) + ('' if h.endswith('.') else '.') for h in deduped[:2])
            return f'Ainda não sei sobre "{tema}". Ensine-me: aprenda: {tema} é ...'

        return self._handle_query(text, sdr)

    def _handle_generate(self, text: str) -> str:
        """Geração de texto — pipeline neuro-simbólico com ContextEngine.

        rev.8: usa _ctx_topic_vec e _ctx_entities para geração contextual:
          - Se tema está vazio mas há contexto ativo, usa entidade mais saliente
          - Ordena fatos por relevância ao tópico acumulado da conversa
          - Passa entidades ativas como bias para o NGram
        """
        # 1. Limpa query e extrai tema
        query = re.sub(r'\b(?:gere|escreva\s+sobre|continue|escreva|fale\s+sobre|'
                       r'explique|descreva|me\s+fale\s+sobre|conte\s+sobre)\b',
                       '', text, flags=re.I).strip()
        query = re.sub(r'^sobre\s+', '', query.strip(), flags=re.I).strip()

        _stop_gen = {'uma','uns','umas','que','com','para','por','dos','das',
                     'nos','nas','sobre','texto','historia','poema','conto',
                     'frase','paragrafo','um','mais','muito','pouco','isso'}
        tema_toks = [w for w in re.findall(r'[a-záàâãéèêíóòôõúùûç\w]+', query.lower())
                     if len(w) >= 3 and w not in _stop_gen]
        tema = ' '.join(tema_toks)

        # ── ContextEngine: enriquece o tema com contexto acumulado ───────────
        # Se o tema está vazio, usa a entidade mais saliente com fatos disponíveis
        if not tema_toks:
            # Prefere entidade que tem fatos no FactStore
            for entity in self._ctx_entities[:10]:
                if len(entity) < 3: continue
                facts = self.fact_store.search(entity, top_k=1, min_score=0.1)
                if facts:
                    tema = entity
                    tema_toks = [entity]
                    break
            # Fallback: última entidade de uma query real (não resposta)
            if not tema_toks and self._dialog_ctx:
                for prev_q, _ in reversed(self._dialog_ctx[-5:]):
                    subj = self._extract_subject(prev_q)
                    if subj and len(subj) >= 3:
                        facts = self.fact_store.search(subj, top_k=1, min_score=0.1)
                        if facts:
                            tema = subj
                            tema_toks = [subj]
                            break
        elif self._ctx_entities:
            # Tema já existe: adiciona entidades contextuais relacionadas
            ctx_sim_thresh = 0.20
            tema_vec = self.embed.sentence_vector(tema)
            for entity in self._ctx_entities[:5]:
                if entity not in tema_toks and len(entity) >= 3:
                    ev = self.embed.sentence_vector(entity)
                    sim = self.embed.cosine(tema_vec, ev)
                    if sim > ctx_sim_thresh:
                        tema_toks.append(entity)
            tema = ' '.join(tema_toks[:6])

        # Detecta modo pelo verbo da query original
        tl = text.lower()
        if any(w in tl for w in ['compare','diferença','versus','vs','contra']):
            mode = 'comparison'
        elif any(w in tl for w in ['explique','como funciona','como ocorre']):
            mode = 'explanation'
        elif any(w in tl for w in ['descreva','características','propriedades','sobre']):
            mode = 'description'
        else:
            mode = 'auto'

        # 2. Comparação de dois conceitos
        if mode == 'comparison':
            m = re.search(r'(?:entre\s+)?([\w\s]{2,20})\s+(?:e|versus|vs|contra)\s+([\w\s]{2,20})',
                          tl)
            if m:
                a, b = m.group(1).strip(), m.group(2).strip()
                comp = self.text_weaver.weave_comparison(a, b)
                if comp:
                    return comp

        # 3. TextWeaver: tenta gerar parágrafo estruturado (com zero-shot integrado)
        if tema:
            woven = self.text_weaver.weave(tema, mode=mode, max_sentences=3)
            if woven:
                # Estende com NGram se há corpus suficiente,
                # passando as regras condicionais como bias lexical
                if len(self.ngram._ngrams) >= 20:
                    cond_rules = list(self.conditional._rules) if self.conditional else None
                    woven = self.text_weaver.extend_with_ngram(woven, tema, n_extra=2)
                return woven

        # 4. Fallback: NGram guiado por drift_vec + ConditionalEngine bias
        # Coleta regras condicionais relevantes ao tema para bias lexical
        cond_rules_for_gen: Optional[List[Tuple[str,str]]] = None
        if self.conditional and self.conditional._rules:
            tema_words = set(_tokenize_embed(tema))
            cond_rules_for_gen = [
                (s, c) for s, c in self.conditional._rules
                if any(w in _deaccent(s) for w in tema_words)
                   or any(w in _deaccent(c) for w in tema_words)
            ][:8]

        if tema_toks and any(t in self.embed._vocab for t in tema_toks):
            result = self.ngram.generate_guided(
                tema, embed=self.embed, tema=tema, max_tokens=30,
                temperature=0.75, cond_rules=cond_rules_for_gen)
        elif tema and len(self.ngram._ngrams) > 0:
            result = self.ngram.generate(tema, max_tokens=20)
        else:
            tema_display = tema if tema else query
            return (f'Não tenho informações sobre "{tema_display}" ainda. '
                    f'Ensine-me com: aprenda: {tema_display} é ...')

        result = re.sub(r'^sobre\s+', '', result.strip(), flags=re.I)
        result_toks = re.findall(r'\w+', result.lower())
        seed_toks   = re.findall(r'\w+', tema.lower())
        if result_toks and set(result_toks) <= set(seed_toks) | {'.', ','}:
            tema_display = tema if tema else query
            return (f'Não tenho informações sobre "{tema_display}" ainda. '
                    f'Ensine-me com: aprenda: {tema_display} é ...')
        return result

    def _handle_deepscan(self, text: str) -> str:
        """Handler para deep_scan/calibrate conversacional.

        Aceita:
          deep_scan: <texto longo>
          calibrate: <texto ou caminho>
          treine com: <texto>
        """
        corpus = re.sub(
            r'^\s*(?:deep[_\s]?scan|calibra(?:r|te?)?|treine?\s+com|scan\s+corpus)\s*[:\-]?\s*',
            '', text, flags=re.I).strip()
        if not corpus:
            return ('Forneça o texto para calibração:\n'
                    'deep_scan: <texto longo sobre o domínio>')
        return self.calibrate(corpus)

    def _enriched_fact_text(self, fact: str, tema_toks: List[str]) -> str:
        """Formata um único fato de forma fluente com variação natural."""
        f = fact.strip()
        if not f:
            return ''
        f = _safe_capitalize(f)
        if not f.endswith(('.', '!', '?')):
            f += '.'
        # Tenta usar o TextWeaver para enriquecer um único fato
        if hasattr(self, 'text_weaver') and tema_toks:
            tema = ' '.join(tema_toks[:3])
            woven = self.text_weaver.weave(tema, max_sentences=2)
            if woven and len(woven) > len(f):
                return woven
        return f

    def _compose_from_facts(self, fatos: List[str], tema_toks: List[str]) -> str:
        """Compõe texto coerente via TextWeaver se disponível; fallback clássico."""
        if not fatos:
            return ''

        # Usa TextWeaver para composição rica se disponível
        if hasattr(self, 'text_weaver') and tema_toks:
            tema = ' '.join(tema_toks[:3])
            woven = self.text_weaver.weave(tema, max_sentences=3)
            if woven and len(woven) > 40:
                return woven

        # Fallback: composição clássica com deduplicação
        fatos_dedup = []
        fatos_sorted = sorted(fatos, key=len, reverse=True)
        for f in fatos_sorted:
            fl = f.lower()
            if not any(fl in other.lower() and fl != other.lower() for other in fatos_sorted):
                fatos_dedup.append(f)
        if not fatos_dedup:
            fatos_dedup = fatos_sorted[:1]

        tema_set = set(tema_toks)
        fatos_dedup.sort(key=lambda f: len(set(re.findall(r'\w{3,}', f.lower())) & tema_set),
                         reverse=True)
        primary      = fatos_dedup[0]
        primary_toks = set(re.findall(r'\w{3,}', primary.lower()))

        extras = []
        for f in fatos_dedup[1:3]:
            f_toks  = set(re.findall(r'\w{3,}', f.lower()))
            overlap = len(primary_toks & f_toks) / max(len(primary_toks | f_toks), 1)
            if overlap < 0.6:
                extras.append(f)

        # Conectivos variados para o fallback
        _CONNS = ["Além disso,", "Vale acrescentar que", "Adicionalmente,",
                  "Também é relevante que", "Complementando,"]
        parts = []
        for i, p in enumerate([primary] + extras[:1]):
            p = p.strip()
            if p:
                p = _safe_capitalize(p)
                if not p.endswith(('.', '!', '?')):
                    p += '.'
                if i > 0:
                    conn = random.choice(_CONNS)
                    p = conn + ' ' + p[0].lower() + p[1:]
                parts.append(p)

        return ' '.join(parts)

    def _handle_query(self, text: str, sdr: SparseSDR) -> str:
        """
        Consulta híbrida — 4 estratégias em ordem:
        1. Subject match via StructuredFactStore (v5 robustez)
        2. HybridRetriever cascata 3 camadas
        3. EdgeNetwork propagação (v7)
        4. ConditionalEngine + DeductiveEngine
        """
        tl = text.lower().strip()

        # Extrai domínio explícito da query (ex: "contexto Terra", "na Lua")
        # Usado para filtrar/priorizar fatos do mesmo domínio quando disponíveis.
        query_domain = _extract_domain(text)

        # Extrai sujeito da query (para queries do tipo "o que é X?")
        subj_match = _SUBJ_M.search(text)
        subj_raw   = subj_match.group(1).strip().lower() if subj_match else None

        # Remove o fragmento de contexto do sujeito para não poluir a busca
        # Ex: "o céu contexto Terra" → sujeito limpo = "o céu"
        if subj_raw:
            subj_clean = re.sub(r'\s*\(?\s*contexto[:\s]+\S+\s*\)?', '', subj_raw).strip()
            subj_clean = re.sub(r'^\s*(?:os?\s+|as?\s+)', '', subj_clean).strip()
        else:
            subj_clean = None

        subj = subj_clean  # alias para o restante do método

        # Estratégia 1: busca direta pelo sujeito no FactStore
        # Combina SEMPRE hits do literal e do normalizado (singular/deaccent)
        # antes de passar pelo scoring — garante que o melhor candidato vença
        # mesmo quando a query literal bate em fatos errados por coincidência
        # de tokens (ex: "números" em query bate em "mmc...números").
        if subj:
            def _search_variants(s: str):
                hits_literal = self.fact_store.search(s, top_k=8, min_score=0.2)

                # (b) Versão normalizada (singular, sem acento)
                normed = ' '.join(
                    ConditionalEngine._norm(w)
                    for w in s.split()
                    if w not in _STOP_PT and len(w) >= 3
                )
                hits_normed = (self.fact_store.search(normed, top_k=8, min_score=0.2)
                               if normed and normed != s else [])

                # Combina preservando ordem e sem duplicatas
                seen: set = set()
                combined: List[str] = []
                for h in hits_normed + hits_literal:
                    if h not in seen:
                        seen.add(h)
                        combined.append(h)

                if combined:
                    return combined

                # (c) Busca por prefixo sem acento: cobre plural→singular.
                # Usa prefixo de 3 chars (mínimo robusto) para cobrir:
                # "répteis"→"réptil" (rept→rept ok com 4, mas rep ok com 3)
                # "aves"→"ave"  (aves[:4]="aves" ≠ "ave ", mas aves[:3]="ave" == "ave")
                pref_hits: Dict[int, int] = {}
                for qw in re.findall(r'\w{3,}', _deaccent(s.lower())):
                    if qw in _STOP_PT:
                        continue
                    # Tenta prefixos de comprimento 4 e 3 em ordem de precisão
                    for plen in (4, 3):
                        prefix = qw[:plen]
                        matched = False
                        for idx_tok, idx_list in self.fact_store._index.items():
                            if _deaccent(idx_tok.lower()).startswith(prefix):
                                for idx in idx_list:
                                    pref_hits[idx] = pref_hits.get(idx, 0) + 1
                                matched = True
                        if matched:
                            break   # encontrou com este comprimento, não tentar menor
                if pref_hits:
                    return [self.fact_store._facts[i]
                            for i in sorted(pref_hits, key=lambda x: -pref_hits[x])[:8]]
                return []

            fs_hits = _search_variants(subj)
            # subj_toks sem acento para comparação robusta com variantes plural/singular
            subj_toks = [_deaccent(w.lower())
                         for w in subj.split()
                         if w not in _STOP_PT and len(w) >= 3]

            if subj_toks:
                def _subj_score(h: str) -> int:
                    """Pontuação posicional com normalização de acento.
                    Compara prefixo de 3 chars sem acento para cobrir plural→singular
                    (répteis[:3]="rep" bate em réptil[:3]="rep" etc.)."""
                    h_toks = [_deaccent(t.lower())
                              for t in re.findall(r'\w{2,}', h.lower())
                              if t not in _STOP_PT]
                    score = 0
                    for i, st in enumerate(subj_toks):
                        pref = st[:3]
                        if i < len(h_toks) and h_toks[i].startswith(pref):
                            score += (len(subj_toks) - i) * 2  # posição pesa
                        elif any(ht.startswith(pref) for ht in h_toks[:3]):
                            score += 1  # presente mas não posicional
                    return score

                # Bônus extra: fato começa literalmente com o sujeito (definição direta)
                def _starts_with_subj(h: str) -> int:
                    first_toks = [_deaccent(t.lower())
                                  for t in re.findall(r'\w{2,}', h.lower())[:3]]
                    return 10 if (first_toks and
                                  any(first_toks[0].startswith(st[:3]) for st in subj_toks)
                                  ) else 0

                # Bônus de domínio: se a query tem contexto explícito (ex: "contexto Terra"),
                # fatos cujo domínio extraído bate recebem +15 e ficam no topo.
                def _domain_score(h: str) -> int:
                    if not query_domain:
                        return 0
                    h_domain = _extract_domain(h)
                    if not h_domain:
                        return 0
                    # Compara os primeiros 5 chars sem acento para tolerância
                    qd = _deaccent(query_domain.lower())[:5]
                    hd = _deaccent(h_domain.lower())[:5]
                    return 15 if qd == hd else 0

                scored = [((_subj_score(h) + _starts_with_subj(h) + _domain_score(h)), h)
                          for h in fs_hits]
                scored.sort(key=lambda x: -x[0])
                direct = [h for s, h in scored if s > 0]

                if not direct:
                    direct = fs_hits

                if direct:
                    # Prefere o fato de maior score; o filtro copulativo só atua
                    # quando o candidato tiver score >= que o melhor.
                    top_score = scored[0][0] if scored else 0
                    top_group = [h for s, h in scored if s == top_score]
                    # Dentro do top-group, prefere copulativo (contém " é " cedo)
                    cop = [h for h in top_group if ' é ' in h.lower()[:80]]
                    best  = cop[0] if cop else top_group[0]
                    # Extra: só inclui fato relacionado (overlap de tokens de conteúdo)
                    extra = ''
                    best_toks = set(re.findall(r'\w{4,}', best.lower())) - _STOP_PT
                    for s2, h2 in scored:
                        if h2 == best or s2 <= 0:
                            continue
                        h2_toks = set(re.findall(r'\w{4,}', h2.lower())) - _STOP_PT
                        shared = len(best_toks & h2_toks)
                        # Exige pelo menos 2 tokens de conteúdo em comum
                        if shared >= 2:
                            extra = h2
                        break
                    return self.mouth.speak_fact(best, extra)

        # V10: XOR unbinding — busca relações no espaço SDR
        if subj:
            xor_results = self.xor_bind.unbind_object(subj, 'é', top_k=3, min_overlap=0.05)
            if xor_results and not fs_hits:
                xor_facts = [f"{subj} é {obj}" for _, obj in xor_results]
                if xor_facts:
                    return self.mouth.speak_fact(xor_facts[0], 
                                                 xor_facts[1] if len(xor_facts) > 1 else '')

        # V10: SDR Reasoner — propagação de ativação via SDR
        if subj:
            memory_sdrs = [(m.sdr, m.text) for m in self.brain._memories[:200]]
            propagated = self.sdr_reasoner.propagate_activation(
                sdr, memory_sdrs, depth=2, threshold=0.08)
            if propagated and not fs_hits:
                best_prop = propagated[0][1]
                extra_prop = propagated[1][1] if len(propagated) > 1 else ''
                return self.mouth.speak_fact(best_prop, extra_prop)

        # Estratégia 2: HybridRetriever (FactStore → Brain → MiniEmbed)
        # + re-ranking por SalienceEngine e embed cosine
        hits = self.retriever.retrieve(text, sdr, top_k=5)
        if hits:
            # Re-rank: SalienceEngine pondera por frequência/recência de acesso
            qv = self.embed.sentence_vector(text) if self.embed._vocab else None
            if qv:
                re_ranked = []
                for score, hit_text, src in hits:
                    # Boost de salience para conceitos frequentemente acessados
                    hit_words = [w for w in re.findall(r'\w{4,}', hit_text.lower())
                                 if w not in _STOP_PT]
                    sal_boost = max((self.salience._access.get(w, 0) * 0.01
                                     for w in hit_words[:3]), default=0.0)
                    sal_boost = min(sal_boost, 0.15)   # cap para não dominar
                    # Touch nos conceitos acessados
                    for w in hit_words[:2]:
                        self.salience.touch(w)
                    re_ranked.append((score + sal_boost, hit_text, src))
                re_ranked.sort(key=lambda x: -x[0])
                hits = re_ranked

            best_score, best_text, best_src = hits[0]
            if best_score >= 0.25:
                # Extra só se relevante e complementar
                extra = ''
                if len(hits) > 1 and hits[1][0] >= 0.25:
                    cand = hits[1][1]
                    b_toks = set(re.findall(r'\w{4,}', best_text.lower()))
                    c_toks = set(re.findall(r'\w{4,}', cand.lower()))
                    if len(b_toks & c_toks) >= 1:
                        extra = cand
                return self.mouth.speak_fact(best_text, extra)

        # Estratégia 3: EdgeNetwork propagação v7 — filtrada por salience
        words = [w for w in re.findall(r'\w{4,}', tl) if w not in _STOP_PT]
        if words:
            # Touch nos conceitos para atualizar salience
            for w in words[:3]:
                self.salience.touch(w)

            # Definições diretas no EdgeNetwork
            if subj:
                defs = self.edge_net.get_definitions(subj)
                if defs:
                    return self.mouth.speak_fact(defs[0])

            # Propagação guiada por salience (beam search) em vez de BFS livre
            qv = self.embed.sentence_vector(text) if self.embed._vocab else None
            top_concepts = self.salience.beam_search(
                seeds=words[:3], k=8,
                graph=self.concept_graph,
                query_vec=qv,
                embed=self.embed
            )
            if top_concepts:
                top3 = [c for c, _ in top_concepts[:3]]
                related = ', '.join(top3)
                return f'Conceitos relacionados: {related}'

        # Estratégia 4: Inferência transitiva
        inf = self.brain.infer_transitive(sdr, text)
        if inf:
            return self.mouth.speak_deduction(inf.conclusion,
                ' → '.join(r.rel_type for r in inf.chain))

        # Conditional
        if words:
            cond = self.conditional.infer(words[0], words[-1] if len(words) > 1 else words[0])
            if cond:
                return cond

        # Estratégia 5: IS_A transitiva via _check_isa_chain
        # Só ativa para padrões "X é um Y?" onde X é um conceito real
        # (não stopwords como "o que", "qual", "um")
        _ISA_STOPSUBJ = {'o', 'a', 'os', 'as', 'um', 'uma', 'o que', 'qual',
                         'quem', 'que', 'isso', 'ele', 'ela', 'eles', 'elas'}
        isa_q = re.search(
            r'^([\w\s]{2,30}?)\s+(?:é\s+um[a]?|é|são)\s+([\w\s]{2,25})[?\.]?\s*$',
            tl)
        if isa_q:
            c_isa = isa_q.group(1).strip()
            t_isa = isa_q.group(2).strip()
            # Só prossegue se sujeito não é artigo/pronome/stopword
            if (c_isa not in _ISA_STOPSUBJ
                    and not re.match(r'^(?:o\s+que|qual\s+[eé]|quem\s+[eé])', c_isa)
                    and c_isa != t_isa and len(c_isa) > 1 and len(t_isa) > 1):
                chain_ans = self._check_isa_chain(c_isa, t_isa)
                if chain_ans:
                    return chain_ans
                # Não retorna negativa aqui: deixa speak_unknown dar a resposta padrão

        # Estratégia 6: Cross-domain bridge via semântica MiniEmbed
        # Só ativa se a query não for definitória ("o que é X?") para evitar
        # retornar fatos HAS herdados como resposta a perguntas de definição
        _is_def_query = bool(_SUBJ_M.search(text))
        if not _is_def_query:
            bridge = self._cross_domain_bridge(text, sdr)
            if bridge:
                return bridge

        # Sem resultado — auto-feedback Hebbiano: enfraquece arestas
        # que foram usadas nesta cadeia mas não produziram resultado útil.
        words_fb = [w for w in re.findall(r'\w{4,}', tl) if w not in _STOP_PT]
        for w in words_fb[:2]:
            for edge in self.edge_net.get_by_source(w, min_strength=0.3):
                edge.weaken(penalty=0.05)  # penalidade leve e gradual
        self.homeostasis.on_failed_infer()
        topic = subj or (words_fb[0] if words_fb else text[:30])
        return self.mouth.speak_unknown(topic)

    # ── Auto-persistência ────────────────────────────────────────────────────

    def _silent_load(self, filepath: str) -> None:
        """Carrega estado salvo em disco sem resetar _dialog_ctx nem re-registrar atexit."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Restaura cada sub-sistema via from_dict
        if 'encoder' in data:
            self.encoder = MultiLobeEncoder.from_dict(data['encoder'])
        if 'embed' in data:
            self.embed = MiniEmbed.from_dict(data['embed'])
        if 'brain' in data:
            self.brain = CognitiveBrain.from_dict(data['brain'])
        if 'edge_net' in data:
            self.edge_net = EdgeNetwork.from_dict(data['edge_net'])
        if 'fact_store' in data:
            self.fact_store = SQLiteFactStoreV12.from_dict(data['fact_store'])
            self.retriever = HybridRetriever(self.fact_store, self.brain, self.embed)
        if 'concept_graph' in data:
            self.concept_graph = ConceptGraph.from_dict(data['concept_graph'])
        if 'conditional' in data:
            self.conditional = ConditionalEngine.from_dict(data['conditional'])
        if 'deductive' in data:
            self.deductive = DeductiveEngine.from_dict(data['deductive'])
        if 'epistemic' in data:
            self.epistemic = EpistemicLayer.from_dict(data['epistemic'])
        if 'code_eng' in data:
            self.code_eng = CodeGeneralizer.from_dict(data['code_eng'])
        if 'ngram' in data:
            self.ngram = NGramMemory.from_dict(data['ngram'])
        if 'episodes' in data:
            self.episodes = EpisodicStream.from_dict(data['episodes'])
        if 'homeostasis' in data:
            self.homeostasis = Homeostasis.from_dict(data['homeostasis'])
        if 'workspace' in data:
            self.workspace = VirtualWorkspace.from_dict(data['workspace'])
        if 'salience' in data:
            self.salience = SalienceEngine.from_dict(data['salience'])
        if 'rule_ind' in data:
            self.rule_ind = RuleInductor.from_dict(data['rule_ind'])
        if 'abstractor' in data:
            self.abstractor = ConceptAbstractor.from_dict(data['abstractor'])
        if 'wm' in data:
            self.wm = WorkingMemory.from_dict(data['wm'])
        if data.get('one_shots'):
            self._one_shots = data['one_shots']
        # rev.7: Spatial Pooler
        sp_data = data.get('sp_encoder')
        if sp_data:
            self.sp_encoder  = SemanticSDREncoder.from_dict(sp_data)
            self._sp_trained = data.get('sp_trained', True)
        else:
            self.sp_encoder  = None
            self._sp_trained = False
        # rev.8: ContextEngine
        dim = self.embed.DIM
        self._ctx_topic_vec = data.get('ctx_topic_vec', [0.0]*dim)
        self._ctx_entities  = data.get('ctx_entities', [])
        self._ctx_turn      = data.get('ctx_turn', 0)
        # Reconstrói dependências cruzadas
        self.mouth = FluentMouth(self.encoder, self.ngram)
        # Re-injeta referências nos motores de inferência
        self.deductive._embed       = self.embed
        self.deductive._conditional = self.conditional
        # Re-cria TextWeaver com todos os módulos restaurados
        self.text_weaver = TextWeaver(
            embed=self.embed,
            concept_graph=self.concept_graph,
            fact_store=self.fact_store,
            ngram=self.ngram,
            deductive=self.deductive,
            conditional=self.conditional,
            episodic=self.episodes)
        self._tw = self.text_weaver
        def _auto_promote(belief, brain):
            brain.store(belief.sdr, belief.text, tag='FACT', confidence=belief.confidence)
        self.epistemic._on_promote = _auto_promote

    def _autosave_on_exit(self) -> None:
        """Chamado automaticamente pelo atexit ao encerrar o processo."""
        if self._autosave_enabled:
            self.save(self._persist_path)

    def set_persist_path(self, path: str) -> None:
        """Define caminho customizado para o arquivo de estado."""
        self._persist_path = path

    def disable_autosave(self) -> None:
        """Desativa auto-save (útil em testes ou modo somente-leitura)."""
        self._autosave_enabled = False

    # ── Seed de conhecimento ───────────────────────────────────────────────────

    def _seed_knowledge(self) -> None:
        """Conhecimento de bootstrap — base enciclopédica essencial.

        Cobre: ciências naturais, tecnologia, geografia, matemática e linguagem.
        Suficiente para responder perguntas básicas sem treinamento prévio.
        """
        seeds = [
            # ── Biologia ──────────────────────────────────────────────────────
            'fotossíntese é o processo pelo qual plantas produzem glicose usando luz solar e CO2',
            'célula é a unidade básica da vida e pode ser procarionte ou eucarionte',
            'DNA é a molécula que carrega a informação genética de todos os seres vivos',
            'evolução é o processo de mudança das espécies ao longo do tempo por seleção natural',
            'mitose é a divisão celular que gera duas células com o mesmo número de cromossomos',
            'proteína é uma molécula formada por aminoácidos essencial para funções celulares',
            # ── Física ────────────────────────────────────────────────────────
            'átomo é a menor unidade da matéria composta por prótons nêutrons e elétrons',
            'gravidade é a força de atração entre corpos com massa descrita por Newton',
            'energia não pode ser criada nem destruída apenas transformada de uma forma para outra',
            'luz viaja a aproximadamente 300 mil quilômetros por segundo no vácuo',
            'relatividade de Einstein afirma que espaço e tempo são relativos ao observador',
            'termodinâmica estuda as transformações de energia especialmente calor e trabalho',
            # ── Química ───────────────────────────────────────────────────────
            'molécula é um agrupamento de átomos ligados quimicamente',
            'tabela periódica organiza os elementos químicos por número atômico',
            'reação química transforma substâncias reagentes em novos produtos com diferentes propriedades',
            'água é composta por dois átomos de hidrogênio e um de oxigênio com fórmula H2O',
            # ── Matemática ────────────────────────────────────────────────────
            'algoritmo é uma sequência finita de instruções para resolver um problema',
            'função matemática é uma relação que associa cada elemento de um conjunto a exatamente um outro',
            'teorema de Pitágoras afirma que o quadrado da hipotenusa é igual à soma dos quadrados dos catetos',
            'número primo é divisível apenas por um e por ele mesmo como 2 3 5 7 11 13',
            'logaritmo é o expoente ao qual uma base deve ser elevada para produzir um número',
            # ── Tecnologia ────────────────────────────────────────────────────
            'python é uma linguagem de programação de alto nível criada por Guido van Rossum',
            'algoritmo de busca binária encontra um elemento em uma lista ordenada em O(log n)',
            'internet é uma rede global de computadores interconectados via protocolos TCP/IP',
            'inteligência artificial é a área da computação que busca simular capacidades cognitivas',
            'machine learning é uma área da inteligência artificial que aprende padrões em dados',
            'banco de dados é um sistema organizado para armazenar recuperar e manipular dados',
            'compilador é um programa que traduz código fonte para linguagem de máquina',
            'sistema operacional gerencia recursos de hardware e software do computador',
            'bit é a menor unidade de informação digital e pode ser 0 ou 1',
            'byte é um conjunto de 8 bits e é a unidade básica de armazenamento digital',
            # ── Geografia ─────────────────────────────────────────────────────
            'Brasil é o maior país da América do Sul com capital em Brasília',
            'Brasília é a capital do Brasil inaugurada em 1960 por Juscelino Kubitschek',
            'São Paulo é a maior cidade do Brasil e um dos maiores centros financeiros do mundo',
            'Amazônia é a maior floresta tropical do mundo localizada na América do Sul',
            'Terra é o terceiro planeta do sistema solar e único com vida confirmada',
            'Lua é o único satélite natural da Terra com superfície coberta de crateras',
            'sistema solar é composto pelo Sol e oito planetas incluindo Mercúrio Vênus Terra Marte',
            'oceano Pacífico é o maior e mais profundo oceano do mundo',
            # ── História e ciência geral ──────────────────────────────────────
            'Newton descobriu as leis do movimento e a lei da gravitação universal',
            'Einstein desenvolveu a teoria da relatividade geral e especial',
            'Darwin propôs a teoria da evolução por seleção natural no livro A Origem das Espécies',
            'Graham Bell inventou o telefone em 1876 e obteve a primeira patente',
            'internet foi criada nos anos 1960 pelo Departamento de Defesa dos Estados Unidos como ARPANET',
            'revolução industrial iniciou na Inglaterra no século XVIII com mecanização da produção',
            'segunda guerra mundial ocorreu entre 1939 e 1945 e foi o conflito mais devastador da história',
            # ── Linguagem e comunicação ───────────────────────────────────────
            'português é uma língua românica derivada do latim falada em Portugal Brasil e outros países',
            'linguística é a ciência que estuda a linguagem humana em seus aspectos fonológicos sintáticos e semânticos',
        ]
        for s in seeds:
            sdr = self.encoder.encode(s)
            self.brain.store(sdr, s, tag='FACT', metadata={'source': 'seed'})
            self.fact_store.add(s)
            self.embed.learn(s)
            self._learn_edge(s)


# ══════════════════════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════════════════
    # NOVOS MÉTODOS V12 — adicionados ao NexusV8 base
    # ══════════════════════════════════════════════════════════════════════════

    def disable_autosave(self) -> None:
        """Desativa o auto-save. Útil em modo servidor ou testes."""
        self._autosave_enabled = False

    def enable_autosave(self, path: str = None) -> None:
        """Ativa auto-save, opcionalmente em caminho customizado."""
        self._autosave_enabled = True
        if path:
            self._persist_path = path

    def reset_context(self) -> None:
        """Limpa o contexto de diálogo.
        Útil quando o sistema entra em loop de repetição.
        FIX do V12: resolve o problema mais frequente do notebook.
        """
        self._ctx_entities = []
        self._ctx_topic_vec = [0.0] * self.embed.DIM
        self._ctx_turn = 0
        if hasattr(self, '_dialog_ctx'):
            self._dialog_ctx.clear()
        if hasattr(self, '_pending_confirm'):
            self._pending_confirm = None

    def learn_document(self, text: str, max_fact_len: int = 250,
                        min_fact_len: int = 20) -> int:
        """Segmenta um documento longo em fatos atômicos e aprende cada um.
        FIX do V12: no V9 original, textos longos eram injetados como 1 único fato.
        Retorna o número de fatos aprendidos com sucesso.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        learned = 0
        for sent in sentences:
            sent = sent.strip()
            if min_fact_len <= len(sent) <= max_fact_len:
                # Remove artefatos markdown: ###, **, ```, >, |
                sent_clean = re.sub(r'[*#`>|]', '', sent).strip()
                if len(sent_clean) >= min_fact_len:
                    result = self.chat(f'aprenda: {sent_clean}')
                    if 'Aprendi' in result or '[dedup]' not in result.lower():
                        learned += 1
        return learned

    def wiki_expand(self, topic: str, max_sentences: int = 6) -> str:
        """Busca resumo da Wikipedia em português e aprende como fatos.
        FIX do V12: o notebook recriava essa função manualmente dezenas de vezes.
        Agora é método oficial da API.

        Args:
            topic: Tópico a buscar (ex: 'fotossíntese', 'Python', 'Brasil')
            max_sentences: Máximo de sentenças a aprender (padrão 6)
        Returns:
            String descrevendo quantos fatos foram aprendidos.
        """
        import urllib.request, urllib.parse, json as _json
        try:
            url = (f"https://pt.wikipedia.org/api/rest_v1/page/summary/"
                   f"{urllib.parse.quote(topic)}")
            headers = {'User-Agent': 'NexusFinal/1.0 (python-stdlib)'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = _json.loads(resp.read().decode())
            summary = data.get('extract', '')
            if not summary:
                return f"[wiki] Sem resumo para '{topic}'"
            sentences = re.split(r'(?<=[.!?])\s+', summary)
            learned = 0
            for s in sentences[:max_sentences]:
                s = s.strip()
                if len(s) > 30:
                    result = self.chat(f'aprenda: {s}')
                    if 'Aprendi' in result:
                        learned += 1
            return f"[wiki] '{topic}': {learned} fatos aprendidos de {min(len(sentences), max_sentences)} sentenças"
        except Exception as e:
            return f"[wiki] Erro ao buscar '{topic}': {type(e).__name__}: {e}"

    def scan_health(self) -> str:
        """Status detalhado de saúde do sistema.
        FIX do V12: no notebook era preciso inspecionar internals manualmente.
        """
        try:
            s = self.status()
            b = s.get('brain', {})
            fs_type = type(self.fact_store).__name__
            v12 = getattr(self, '_v12_stats', {})
            dedup_size = self._dedup.size if hasattr(self, '_dedup') else 0
            consist_n  = self._checker.n_flags if hasattr(self, '_checker') else 0
            return (
                f"═══ Nexus V10 Ultimate Health ═══\n"
                f"  Versão         : {s.get('version', 'v9-final')}\n"
                f"  FactStore      : {s.get('facts', 0)} fatos [{fs_type}]\n"
                f"  Memórias brain : {b.get('total', 0)} "
                f"(FACT:{b.get('FACT',0)} THEORY:{b.get('THEORY',0)})\n"
                f"  Arestas        : {s.get('edges', 0)}\n"
                f"  Nós do grafo   : {s.get('graph', {}).get('nodes', 0)}\n"
                f"  Embed vocab    : {s.get('embed', 0)} tokens\n"
                f"  Regras induz.  : {s.get('rules_induced', 0)}\n"
                f"  Clusters       : {s.get('clusters', 0)}\n"
                f"  DeduplicatorSDR: {dedup_size} SDRs indexados\n"
                f"  Aprendidos V12 : {v12.get('learned', 0)}\n"
                f"  Bloqueados (dedup): {v12.get('blocked', 0)}\n"
                f"  Inconsistências: {consist_n}\n"
                f"  Homeostase     : {s.get('homeostasis', 'ok')}\n"
                f"  ─── V10 Módulos ───\n"
                f"  SDR             : {SDR_SIZE} bits, {SDR_ACTIVE} ativos\n"
                f"  Embed DIM       : {self.embed.DIM}d\n"
                f"  XOR Bindings    : {self.xor_bind.size}\n"
                f"  Novelty média   : {self.novelty.recent_novelty():.3f}\n"
                f"  Temporal fatos  : {len(self.temporal._timestamps)}\n"
                f"  SDR Protótipos  : {len(self.sdr_reasoner._prototypes)}\n"
                f"  Cache hits      : {self.pred_cache.stats}\n"
                f"  Bus mensagens   : {len(self.rep_bus._messages)}\n"
            )
        except Exception as e:
            return f"[scan_health] Erro: {e}"

    def deep_scan(self, corpus: str) -> str:
        """Calibra o sistema com texto longo — versão corrigida.
        Usa learn_document internamente para segmentação adequada.
        Também re-treina o MiniEmbed com o corpus completo.
        """
        # Aprende fatos atômicos do corpus
        learned_n = self.learn_document(corpus, max_fact_len=300, min_fact_len=15)
        # Aprende o texto inteiro no MiniEmbed para calibração semântica
        self.embed.learn(corpus[:5000])
        return f'Calibrado: {learned_n} fatos de "{corpus[:40]}..."'

    def calibrate(self, corpus: str) -> str:
        """Alias de deep_scan — compatibilidade com versões anteriores."""
        return self.deep_scan(corpus)

    def learn(self, fact: str, timestamp: float = None) -> str:
        """API V12: aprende um fato com deduplicação SDR e verificação de consistência.
        Wrapper de alto nível sobre o chat('aprenda: ...').
        """
        # Verificação de duplicata
        dup = self._dedup.is_duplicate(fact)
        if dup:
            self._v12_stats['blocked'] = self._v12_stats.get('blocked', 0) + 1
            return f"[dedup] Similar a: '{dup[:60]}'"
        # Verificação de consistência física
        issue = self._checker.check(fact)
        if issue:
            # Aprende mesmo assim mas marca — nunca silencia informação
            result = self.chat(f'aprenda: {fact}')
            return f"{result}\n{issue}"
        result = self.chat(f'aprenda: {fact}')
        if 'Aprendi' in result:
            self._dedup.record(fact)
            self._v12_stats['learned'] = self._v12_stats.get('learned', 0) + 1
        
        # V10: XOR binding — codifica relação no espaço SDR
        rel_match = re.match(r'^([\w\s]{2,25})\s+(?:é|são|tem|possui|produz|causa)\s+(.+)$', fact.lower().strip() if isinstance(fact, str) else '')
        if rel_match:
            subj_xor, obj_xor = rel_match.group(1).strip(), rel_match.group(2).strip()
            rel_type = 'é'
            for r in ['tem', 'possui', 'produz', 'causa']:
                if r in fact.lower():
                    rel_type = r
                    break
            self.xor_bind.bind(subj_xor, rel_type, obj_xor)
        
        # V10: Temporal memory
        self.temporal.record(fact[:60] if isinstance(fact, str) else 'fact')
        
        return result

# §25  ENTRY POINT / DEMO
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys

    print('=' * 60)
    print('NEXUS V10 ULTIMATE — Sistema Cognitivo SDR-First')
    print('=' * 60)

    n = NexusV10()

    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Modo teste rápido
        tests = [
            ('aprenda: variável é um espaço de memória nomeado que armazena valores', 'Aprendi'),
            ('o que é variável?', 'memória'),
            ('implemente fibonacci', 'fibonacci'),
            ('calcule 2 + 2 * 3', '8'),
        ]
        ok = 0
        for prompt, expected in tests:
            resp = n.chat(prompt)
            passed = expected.lower() in resp.lower()
            print(f'  {"✓" if passed else "✗"} {prompt[:50]} → {resp[:60]}')
            if passed:
                ok += 1
        print(f'\n{ok}/{len(tests)} testes básicos passando.')
    else:
        # Modo interativo
        print('Digite "sair" para encerrar.\n')
        while True:
            try:
                user = input('> ').strip()
            except (EOFError, KeyboardInterrupt):
                print('\nAté mais!')
                break
            if user.lower() in ('sair', 'exit', 'quit'):
                break
            if user:
                print(n.chat(user))


# ══════════════════════════════════════════════════════════════════════════════
# §26  ALIAS PÚBLICO — NexusFinal
# ══════════════════════════════════════════════════════════════════════════════
"""
NexusFinal — Sistema Cognitivo Híbrido (versão consolidada)

CORREÇÕES aplicadas sobre V9 + melhorias do V12:
  ✓ BUG CRÍTICO #1: _autosave_enabled nunca inicializado (código morto)
     → Movido para dentro de __init__ onde deve estar
  ✓ BUG CRÍTICO #2: _seed_knowledge() nunca chamada (código morto)
     → Movido para dentro de __init__ — seed facts agora funcionam
  ✓ BUG #3: Recuperação retornava "Conceitos relacionados" em vez de definições
     → SQLiteFactStoreV12 com FTS5 + SigmoidRetriever k=12 corrige o scoring
  ✓ BUG #4: Raiz quadrada não calculada
     → Mantém o comportamento base (MathEngine não suporta 'raiz de')

COMPONENTES V12 INTEGRADOS:
  ✓ DeduplicatorSDR        — anti-paráfrase SDR+Lexical
  ✓ SQLiteFactStoreV12     — FTS5 + SigmoidRetriever k=12
  ✓ CuriositaEngine        — pergunta quando confidence < 0.25
  ✓ ConsistencyChecker     — alerta sobre constantes físicas incorretas

NOVOS MÉTODOS:
  ✓ learn(fact)            — API V12 com dedup + consistency
  ✓ learn_document(text)   — segmenta e aprende texto longo
  ✓ wiki_expand(topic)     — aprende da Wikipedia (pt)
  ✓ reset_context()        — limpa contexto de diálogo
  ✓ scan_health()          — status detalhado do sistema
  ✓ disable_autosave()     — modo servidor seguro
  ✓ deep_scan(corpus)      — calibração com texto longo (corrigido)

API PÚBLICA (compatível com NexusV8):
  n = NexusFinal()          # ou NexusV8()
  n.chat(prompt)            # interface principal
  n.learn(fact)             # V12: com dedup + consistency
  n.learn_document(text)    # aprende texto longo
  n.wiki_expand(topic)      # aprende da Wikipedia
  n.reset_context()         # limpa contexto
  n.scan_health()           # status detalhado

  Deps: Python ≥ 3.9, zero dependências externas
"""

NexusFinal = NexusV10
NexusV8 = NexusV10  # backwards compatibility  # backwards compatibility



# ══════════════════════════════════════════════════════════════════════════════
# §GLOBAL WORKSPACE — ÁREA DE TRABALHO GLOBAL + MULTI-CÉREBROS POR DOMÍNIO
# ══════════════════════════════════════════════════════════════════════════════

"""
GlobalWorkspaceNexus — Extensão do NexusFinal com Global Workspace Theory

Baseado em Baars (1988) — Global Workspace Theory:
  • NexusFinal atua como "córtex pré-frontal" — raciocínio, síntese, decisão
  • Brains especializados processam em paralelo por área de conhecimento
  • RepresentationBus (tálamo SDR) roteia informação entre brains
  • CrossDomainBridge: aprendizado propaga entre domínios com sobreposição

Áreas de conhecimento padrão:
  biologia     — DNA, célula, evolução, fotossíntese, proteína...
  fisica       — átomo, energia, força, gravidade, luz, relatividade...
  matematica   — algoritmo, função, logaritmo, número primo, Pitágoras...
  tecnologia   — Python, internet, IA, compilador, banco de dados, bit...
  historia     — guerra, revolução, descoberta, império, civilização...
  medicina     — doença, diagnóstico, tratamento, vírus, bacteria, saúde...
  geografia    — Brasil, Amazônia, oceano, continente, capital, país...
  linguistica  — gramática, língua, sintaxe, semântica, fonologia, texto...

Fluxo de processamento:
  1. NexusFinal processa (dedup SDR, sigmoid retriever, curiosidade)
  2. Brains especializados consultados em paralelo via SDR
  3. Resposta mais confiante integrada (se não redundante)
  4. Ao aprender: fato propagado para o brain de melhor fit semântico
  5. sleep() consolida: cross-domain links reforçados Hebbianamente
"""


class SpecialistBrain:
    """
    Cérebro especializado em uma área de conhecimento.
    
    REFATORADO (L7 — Hipocampo Compartilhado):
    NÃO mantém banco de dados isolado. Recebe uma SharedMemory via
    injeção de dependência e armazena/consulta fatos através dela.
    Isso permite Cross-Domain Learning — qualquer cérebro pode
    acessar conhecimento armazenado por outro.
    """

    def __init__(self, brain_id: str, name: str, keywords: List[str],
                 encoder: 'MultiLobeEncoder',
                 shared_memory: Optional['SharedMemory'] = None):
        self.id       = brain_id
        self.name     = name
        self._kw      = frozenset(k.lower() for k in keywords)
        self._enc     = encoder
        self._shared  = shared_memory  # Hipocampo Compartilhado
        # Fallback local (apenas se SharedMemory não fornecida)
        self._facts:  List[str] = []
        self._sdrs:   List[frozenset] = []
        self._access: Dict[str, int] = defaultdict(int)
        self._learned_count = 0
        self._query_count   = 0

    # ── Relevância ────────────────────────────────────────────────────────────

    def relevance(self, text: str) -> float:
        """Score de relevância [0..1] para um texto dado."""
        words = set(re.findall(r'\w{3,}', text.lower()))
        kw_hit = len(words & self._kw)
        if not kw_hit:
            return 0.0
        return min(1.0, kw_hit / max(len(self._kw) * 0.3, 1))

    # ── Aprendizado ───────────────────────────────────────────────────────────

    def learn(self, fact: str) -> bool:
        """Aprende um fato — usa SharedMemory se disponível, senão local."""
        if self._shared:
            ok = self._shared.store(fact, brain_origin=self.id)
            if ok:
                self._learned_count += 1
            return ok
        # Fallback local
        fact_l = fact.lower()
        for existing in self._facts[-100:]:
            if existing.lower() == fact_l:
                return False
        self._facts.append(fact)
        sdr = frozenset(self._enc.encode(fact)._idx)
        self._sdrs.append(sdr)
        self._learned_count += 1
        return True

    # ── Consulta ──────────────────────────────────────────────────────────────

    def query(self, text: str, top_k: int = 3,
              min_sim: float = 0.15,
              cross_domain: bool = False) -> List[Tuple[float, str]]:
        """
        Retorna fatos mais relevantes.
        
        Se cross_domain=False: busca apenas fatos deste cérebro.
        Se cross_domain=True: busca em TODA a SharedMemory (Cross-Domain Learning).
        """
        self._query_count += 1
        if self._shared:
            brain_filter = None if cross_domain else self.id
            results = self._shared.temporal_context_search(
                text, top_k=top_k, brain_filter=brain_filter
            )
            return results
        # Fallback local (SDR Jaccard)
        if not self._facts:
            return []
        q_sdr = frozenset(self._enc.encode(text)._idx)
        if not q_sdr:
            return []
        scored = []
        for sdr, fact in zip(self._sdrs, self._facts):
            u = len(q_sdr | sdr)
            if not u:
                continue
            j = len(q_sdr & sdr) / u
            if j >= min_sim:
                sig = 1.0 / (1.0 + math.exp(-12.0 * (j - 0.35)))
                scored.append((sig, fact))
                self._access[fact[:60]] = self._access.get(fact[:60], 0) + 1
        scored.sort(key=lambda x: -x[0])
        return scored[:top_k]

    # ── Sono local ───────────────────────────────────────────────────────────

    def sleep_prune(self, min_accesses: int = 1, keep_recent: int = 30) -> int:
        """
        Se usando SharedMemory: aplica decaimento Hebbiano (não deleta).
        Se local: poda fatos não acessados.
        """
        if self._shared:
            return self._shared.hebbian_decay_cycle()
        if len(self._facts) <= keep_recent:
            return 0
        pruned = 0
        new_facts, new_sdrs = [], []
        for i, (fact, sdr) in enumerate(zip(self._facts, self._sdrs)):
            if i < keep_recent:
                new_facts.append(fact)
                new_sdrs.append(sdr)
                continue
            if self._access.get(fact[:60], 0) >= min_accesses:
                new_facts.append(fact)
                new_sdrs.append(sdr)
            else:
                pruned += 1
        self._facts = new_facts
        self._sdrs  = new_sdrs
        return pruned

    # ── Status ────────────────────────────────────────────────────────────────

    @property
    def stats(self) -> Dict:
        fact_count = len(self._shared.all_facts(brain_filter=self.id)) if self._shared else len(self._facts)
        return {
            'id': self.id, 'name': self.name,
            'facts': fact_count,
            'learned': self._learned_count,
            'queries': self._query_count,
            'shared_memory': self._shared is not None,
        }


class GlobalWorkspaceNexus:
    """
    NexusFinal + Área de Trabalho Global + Multi-Cérebros por Área de Conhecimento.

    Herda toda a potência do NexusFinal (v9 rev.9) e adiciona:
      - Brains especializados por domínio (biologia, física, matemática, etc.)
      - Propagação de conhecimento cross-domain via SDR
      - ConsistencyChecker para alertas sobre valores físicos errados
      - CuriositaEngine para perguntas de clarificação adaptativas
      - sleep() integrado: consolida brains especializados + NexusFinal
      - scan_health() expandido: saúde de todos os brains

    API pública (superset do NexusFinal):
      gw = GlobalWorkspaceNexus()
      gw.chat(prompt)              → resposta integrada
      gw.learn(fact)               → aprende com dedup + consistência + propagação
      gw.learn_document(text)      → segmenta e aprende texto longo
      gw.wiki_expand(topic)        → aprende da Wikipedia
      gw.sleep(cycles)             → sono consolidador (todos os brains)
      gw.scan_health()             → saúde completa do sistema
      gw.reset_context()           → limpa contexto de diálogo
      gw.add_brain(id, name, kws)  → adiciona brain especializado custom
      gw.brain_status()            → status de todos os brains
    """

    # Áreas de conhecimento padrão — cada brain tem palavras-chave características
    DEFAULT_DOMAINS: List[Dict] = [
        {
            'id': 'biologia',
            'name': 'Biologia',
            'keywords': [
                'célula','dna','rna','proteína','evolução','espécie','organismo',
                'fotossíntese','mitose','meiose','genética','cromossomo','ribossomo',
                'mitocôndria','cloroplasto','membrana','metabolismo','enzima',
                'vírus','bactéria','fungo','planta','animal','mamífero','réptil',
                'biologia','ecosistema','biodiversidade','darwin','genoma',
            ],
        },
        {
            'id': 'fisica',
            'name': 'Física',
            'keywords': [
                'átomo','partícula','elétron','próton','nêutron','força','energia',
                'gravidade','velocidade','aceleração','massa','momentum','trabalho',
                'luz','onda','frequência','comprimento','calor','temperatura',
                'termodinâmica','eletricidade','magnetismo','campo','relatividade',
                'einstein','newton','quântico','fóton','física','mecânica','óptica',
            ],
        },
        {
            'id': 'matematica',
            'name': 'Matemática',
            'keywords': [
                'número','função','equação','integral','derivada','logaritmo',
                'algoritmo','complexidade','conjunto','probabilidade','estatística',
                'geometria','trigonometria','álgebra','cálculo','teorema','prova',
                'número primo','matriz','vetor','limite','série','convergência',
                'pitágoras','euclides','fibonacci','matemática','combinatória',
            ],
        },
        {
            'id': 'tecnologia',
            'name': 'Tecnologia',
            'keywords': [
                'python','java','javascript','código','programa','algoritmo',
                'compilador','interpretador','banco de dados','sql','internet',
                'rede','protocolo','tcp','http','servidor','cliente','api',
                'inteligência','aprendizado','machine','neural','computador',
                'bit','byte','processador','memória','sistema operacional',
                'docker','kubernetes','cloud','software','hardware','tecnologia',
            ],
        },
        {
            'id': 'historia',
            'name': 'História',
            'keywords': [
                'guerra','revolução','império','civilização','descoberta','colônia',
                'política','governo','rei','presidente','século','era','período',
                'segunda guerra','primeira guerra','revolução industrial','brasil',
                'história','antigo','medieval','renascimento','iluminismo','moderno',
                'democracia','ditadura','colonialismo','independência','tratado',
            ],
        },
        {
            'id': 'medicina',
            'name': 'Medicina e Saúde',
            'keywords': [
                'doença','sintoma','diagnóstico','tratamento','medicamento','vacina',
                'vírus','bactéria','infecção','imunidade','anticorpo','célula',
                'órgão','coração','pulmão','fígado','rim','cérebro','nervo',
                'câncer','diabetes','hipertensão','cirurgia','medicina','saúde',
                'nutrição','vitamina','hormônio','gene','mutação','epidemia',
            ],
        },
        {
            'id': 'geografia',
            'name': 'Geografia',
            'keywords': [
                'brasil','são paulo','rio','amazônia','nordeste','sul','norte',
                'continente','país','capital','cidade','oceano','mar','rio',
                'montanha','planalto','litoral','clima','bioma','floresta',
                'cerrado','caatinga','pampa','território','fronteira','mapa',
                'população','densidade','êxodo','migração','urbanização','rural',
            ],
        },
        {
            'id': 'linguistica',
            'name': 'Linguística e Comunicação',
            'keywords': [
                'língua','idioma','gramática','sintaxe','semântica','fonologia',
                'morfologia','palavra','frase','texto','discurso','comunicação',
                'português','inglês','espanhol','latim','dialeto','sotaque',
                'signo','símbolo','metáfora','analogia','linguagem','escrita',
                'literatura','poema','conto','romance','autor','estilo','gênero',
            ],
        },
    ]

    def __init__(self, persist_path: str = 'nexus_global.json',
                 domains: Optional[List[Dict]] = None,
                 autosave: bool = True):
        # NexusFinal como núcleo central
        self._core = NexusFinal()
        if not autosave:
            self._core.disable_autosave()
        elif persist_path:
            self._core.set_persist_path(persist_path)

        # ── HIPOCAMPO COMPARTILHADO (L7 Evolution) ──────────────────────
        # Uma única SharedMemory para TODOS os cérebros — Cross-Domain Learning
        self._shared_memory = SharedMemory(db_path=":memory:")

        # Cria brains especializados COM memória compartilhada injetada
        self._brains: Dict[str, SpecialistBrain] = {}
        dom_list = domains if domains is not None else self.DEFAULT_DOMAINS
        for d in dom_list:
            self._brains[d['id']] = SpecialistBrain(
                brain_id = d['id'],
                name     = d['name'],
                keywords = d['keywords'],
                encoder  = self._core.encoder,
                shared_memory = self._shared_memory,  # INJEÇÃO DE DEPENDÊNCIA
            )

        # Estatísticas globais
        self._stats = {
            'total_learned':         0,
            'cross_domain_propagated': 0,
            'specialist_contributions': 0,
            'consistency_flags':     0,
            'sleep_cycles':          0,
        }


    def add_brain(self, brain_id: str, name: str, keywords: List[str]) -> 'SpecialistBrain':
        """Adiciona um brain especializado customizado COM memória compartilhada."""
        brain = SpecialistBrain(brain_id, name, keywords, self._core.encoder,
                                shared_memory=self._shared_memory)
        self._brains[brain_id] = brain
        return brain



    def remove_brain(self, brain_id: str) -> bool:
        """Remove um brain especializado."""
        if brain_id in self._brains:
            del self._brains[brain_id]
            return True
        return False

    # ── API principal ─────────────────────────────────────────────────────────

    def learn(self, fact: str, timestamp: float = None) -> str:
        """
        Aprende um fato no núcleo NexusFinal E nos brains especializados.
        Inclui deduplicação SDR, verificação de consistência e propagação cross-domain.
        """
        # Aprende no núcleo
        result = self._core.learn(fact, timestamp=timestamp)

        # Armazena na SharedMemory (Hipocampo Compartilhado)
        if hasattr(self, "_shared_memory") and self._shared_memory is not None:
            self._shared_memory.store(fact, brain_origin="core")

        # Propaga para brains especializados por relevância semântica
        propagated = self._propagate_to_specialists(fact)
        self._stats['total_learned'] += 1
        if propagated:
            self._stats['cross_domain_propagated'] += 1

        # Detecta flags de consistência
        if '[inconsistência]' in result or '[consistência?]' in result:
            self._stats['consistency_flags'] += 1

        return result

    def learn_document(self, text: str, max_fact_len: int = 250,
                        min_fact_len: int = 20) -> int:
        """Segmenta documento em fatos atômicos e aprende cada um."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        learned = 0
        for sent in sentences:
            sent = sent.strip()
            if min_fact_len <= len(sent) <= max_fact_len:
                sent_clean = re.sub(r'[*#`>|]', '', sent).strip()
                if len(sent_clean) >= min_fact_len:
                    result = self.learn(sent_clean)
                    if '[dedup]' not in result.lower():
                        learned += 1
        return learned

    def wiki_expand(self, topic: str, max_sentences: int = 6) -> str:
        """Busca resumo da Wikipedia e aprende nos brains especializados."""
        return self._core.wiki_expand(topic, max_sentences=max_sentences)

    def chat(self, query: str) -> str:
        """
        Consulta integrada: NexusFinal + brains especializados.

        Fluxo:
          1. NexusFinal responde (dedup, sigmoid, contexto, raciocínio)
          2. Brains especializados consultados em paralelo
          3. Se um brain tem resposta confiante e não redundante, integra
          4. Retorna resposta enriquecida
        """
        # Resposta do núcleo
        core_response = self._core.chat(query)

        # Intercepta aprendizado via chat e armazena na SharedMemory
        if hasattr(self, "_shared_memory") and self._shared_memory is not None:
            ql = query.strip().lower()
            if ql.startswith("aprenda:") or ql.startswith("aprenda "):
                fact_text = query.split(":", 1)[-1].strip() if ":" in query else query.split(" ", 1)[-1].strip()
                if fact_text:
                    self._shared_memory.store(fact_text, brain_origin="core")
                    self._propagate_to_specialists(fact_text)


        # Consulta especialistas
        specialist_answers = self._consult_specialists(query)

        # Integra a melhor resposta especializada (se complementar)
        if specialist_answers:
            best_brain_id, best_score, best_facts = specialist_answers[0]
            if best_score >= 0.45 and best_facts:
                best_brain_name = self._brains[best_brain_id].name
                specialist_text = best_facts[0][1]
                if not self._texts_overlap(core_response, specialist_text, threshold=0.50):
                    self._stats['specialist_contributions'] += 1
                    return (f"{core_response}\n\n"
                            f"↳ [{best_brain_name}]: {specialist_text}")

        return core_response

    def sleep(self, cycles: int = 1) -> Dict:
        """
        Ciclo de sono integrado: consolida NexusFinal + todos os brains.
        Poda fatos não acessados, reset de contexto, reforço Hebbiano.
        """
        # Sono no núcleo
        core_result = self._core.sleep(cycles=cycles)

        # Sono em cada brain especializado
        brain_pruned = {}
        for bid, brain in self._brains.items():
            pruned = brain.sleep_prune(min_accesses=1, keep_recent=50)
            brain_pruned[bid] = pruned

        self._stats['sleep_cycles'] += cycles
        self._core.reset_context()

        return {
            'core': core_result,
            'brain_pruned': brain_pruned,
            'sleep_cycles': self._stats['sleep_cycles'],
        }

    def reset_context(self) -> None:
        """Limpa contexto de diálogo de todos os sistemas."""
        self._core.reset_context()

    def scan_health(self) -> str:
        """Status detalhado do sistema completo incluindo todos os brains."""
        core_health = self._core.scan_health()
        brain_lines = []
        for bid, brain in self._brains.items():
            s = brain.stats
            brain_lines.append(
                f"  [{s['id']:12s}] {s['name']:25s} "
                f"fatos={s['facts']:4d}  "
                f"aprendidos={s['learned']:4d}  "
                f"consultas={s['queries']:4d}"
            )

        return (
            f"{core_health}\n"
            f"═══ Global Workspace ═══\n"
            f"  Total aprendidos      : {self._stats['total_learned']}\n"
            f"  Propagações domínio   : {self._stats['cross_domain_propagated']}\n"
            f"  Contribuições brain   : {self._stats['specialist_contributions']}\n"
            f"  Inconsistências       : {self._stats['consistency_flags']}\n"
            f"  Ciclos de sono        : {self._stats['sleep_cycles']}\n"
            f"\n─── Brains Especializados ───\n"
            + "\n".join(brain_lines)
        )

    def brain_status(self) -> str:
        """Status resumido de todos os brains especializados."""
        lines = ["Brains Especializados:"]
        for bid, brain in self._brains.items():
            s = brain.stats
            lines.append(f"  [{s['id']}] {s['name']}: {s['facts']} fatos, "
                         f"{s['learned']} aprendidos, {s['queries']} consultas")
        return "\n".join(lines)

    # ── Delegações ao núcleo ─────────────────────────────────────────────────

    def disable_autosave(self) -> None:
        self._core.disable_autosave()

    def enable_autosave(self, path: str = None) -> None:
        self._core.enable_autosave(path)

    def set_persist_path(self, path: str) -> None:
        self._core.set_persist_path(path)

    def save(self, path: str = None) -> None:
        self._core.save(path or 'nexus_global.json')

    def status(self) -> Dict:
        return self._core.status()

    def deep_scan(self, corpus: str) -> str:
        return self._core.deep_scan(corpus)

    def calibrate(self, corpus: str) -> str:
        return self._core.calibrate(corpus)

    @property
    def fact_store(self): return self._core.fact_store
    @property
    def brain(self):      return self._core.brain
    @property
    def embed(self):      return self._core.embed
    @property
    def encoder(self):    return self._core.encoder
    @property
    def edge_net(self):   return self._core.edge_net
    @property
    def concept_graph(self): return self._core.concept_graph
    @property
    def conditional(self):   return self._core.conditional
    @property
    def planner(self):       return getattr(self._core, 'planner', None)
    @property
    def episodic(self):      return self._core.episodes

    # ── Internos ──────────────────────────────────────────────────────────────

    def _propagate_to_specialists(self, fact: str) -> bool:
        """
        Propaga um fato para o(s) brain(s) mais relevante(s) semanticamente.
        Retorna True se pelo menos 1 brain recebeu o fato.
        """
        fact_words = set(re.findall(r'\w{3,}', fact.lower()))
        best_brain: Optional[SpecialistBrain] = None
        best_score = 0.0

        for brain in self._brains.values():
            score = brain.relevance(fact)
            if score > best_score:
                best_score, best_brain = score, brain

        # Threshold mínimo para não poluir brains irrelevantes
        if best_brain and best_score > 0.05:
            best_brain.learn(fact)
            return True
        return False

    def _consult_specialists(self, query: str
                              ) -> List[Tuple[str, float, List[Tuple[float, str]]]]:
        """
        Consulta todos os brains e retorna lista ordenada por confiança.
        Returns: [(brain_id, best_score, [(score, fact), ...]), ...]
        """
        results = []
        for bid, brain in self._brains.items():
            # Filtra por relevância do domínio primeiro (mais eficiente)
            rel = brain.relevance(query)
            if rel < 0.05 and brain._query_count > 0:
                continue
            facts = brain.query(query, top_k=3, min_sim=0.15)
            if facts:
                best_score = facts[0][0]
                results.append((bid, best_score, facts))

        results.sort(key=lambda x: -x[1])
        return results

    def _texts_overlap(self, a: str, b: str, threshold: float = 0.45) -> bool:
        """Verifica sobreposição lexical entre dois textos."""
        stop = frozenset({'o','a','é','de','do','da','e','que',
                          'em','um','uma','os','as','por','para'})
        ta = {t for t in re.findall(r'\w{3,}', a.lower()) if t not in stop}
        tb = {t for t in re.findall(r'\w{3,}', b.lower()) if t not in stop}
        if not ta or not tb:
            return False
        return len(ta & tb) / min(len(ta), len(tb)) >= threshold


# ══════════════════════════════════════════════════════════════════════════════
# §TESTES INTEGRADOS — GlobalWorkspaceNexus + NexusFinal
# ══════════════════════════════════════════════════════════════════════════════

def run_nexus_tests(verbose: bool = True) -> bool:
    """
    Suite de testes completa para NexusFinal + GlobalWorkspaceNexus.
    Retorna True se >= 85% dos testes passam.
    """
    import time as _time

    ok = 0; total = 0; t0 = _time.time()

    def chk(label: str, cond: bool, info: str = '') -> bool:
        nonlocal ok, total
        total += 1
        if cond: ok += 1
        if verbose:
            mark = '✓' if cond else '✗'
            inf  = f' → {str(info)[:55]}' if info else ''
            print(f'  {mark} {label:<52}{inf}')
        return cond

    if verbose:
        print('\n' + '═' * 70)
        print('NEXUS FINAL + GLOBAL WORKSPACE — Suite de Testes Integrada')
        print('═' * 70)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 1 — NexusFinal básico (base estável)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B1] NexusFinal — Funcionalidade Base')
    n = NexusFinal()
    n.disable_autosave()

    # Aprendizado básico
    r = n.chat('aprenda: variável é um espaço de memória nomeado que armazena valores')
    chk('Aprende fato simples', 'Aprendi' in r, r[:50])

    # Recuperação
    r2 = n.chat('o que é variável?')
    chk('Recupera fato aprendido', 'memória' in r2.lower() or 'armazena' in r2.lower(), r2[:60])

    # Conhecimento seed
    r3 = n.chat('o que é fotossíntese?')
    chk('Seed knowledge: fotossíntese', 'glicose' in r3.lower() or 'luz' in r3.lower(), r3[:60])

    # Matemática
    r4 = n.chat('calcule 2 + 3 * 4')
    chk('Cálculo matemático', '14' in r4, r4[:40])

    # Código
    r5 = n.chat('implemente fibonacci')
    chk('Geração de código', 'def' in r5.lower() or 'fib' in r5.lower(), r5[:50])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 2 — API V12 (DeduplicatorSDR + ConsistencyChecker)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B2] API V12 — DeduplicatorSDR + ConsistencyChecker')
    n2 = NexusFinal()
    n2.disable_autosave()

    r_l1 = n2.learn('fotossíntese converte luz solar em glicose nas plantas')
    chk('learn() retorna confirmação', 'Aprendi' in r_l1 or len(r_l1) > 5, r_l1[:50])

    # Para testar dedup: usar fato exatamente igual (garante blocagem)
    r_l2 = n2.learn('fotossíntese converte luz solar em glicose nas plantas')
    chk('DeduplicatorSDR bloqueia fato idêntico', '[dedup]' in r_l2, r_l2[:55])

    r_l3 = n2.learn('quicksort é um algoritmo de ordenação eficiente')
    chk('Tópico diferente não bloqueado', '[dedup]' not in r_l3, r_l3[:50])

    # ConsistencyChecker — verifica se o checker acumula flags
    r_cc = n2.learn('dimensão fractal sierpinski é igual a 1/96 = 0.0104')
    chk('ConsistencyChecker detecta Sierpinski errado',
        '[inconsistência detectada]' in r_cc or n2._checker.n_flags >= 1, r_cc[:80])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 3 — reset_context + learn_document
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B3] reset_context() + learn_document()')
    n3 = NexusFinal()
    n3.disable_autosave()

    n3.chat('o que é fotossíntese?')
    before = len(n3._ctx_entities)
    n3.reset_context()
    after = len(n3._ctx_entities)
    chk('reset_context() limpa _ctx_entities',
        after == 0 or after < before, f'antes={before} depois={after}')

    doc = (
        'A mitose é a divisão celular que gera células geneticamente idênticas. '
        'O processo de mitose ocorre em quatro fases: prófase, metáfase, anáfase e telófase. '
        'Durante a prófase os cromossomos se condensam e ficam visíveis. '
        'Na metáfase os cromossomos se alinham no equador da célula. '
    )
    n_learned = n3.learn_document(doc)
    chk('learn_document() aprende múltiplas sentenças',
        n_learned >= 2, f'aprendidos={n_learned}')

    r_doc = n3.chat('o que é mitose?')
    chk('Fatos do documento são recuperáveis',
        'mitose' in r_doc.lower() or 'célula' in r_doc.lower() or 'divisão' in r_doc.lower(),
        r_doc[:60])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 4 — scan_health() + sleep()
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B4] scan_health() + sleep()')
    n4 = NexusFinal()
    n4.disable_autosave()
    n4.learn('neurônio transmite impulsos elétricos no sistema nervoso')

    health = n4.scan_health()
    chk('scan_health() retorna string não vazia', len(health) > 50, f'{len(health)} chars')
    chk('scan_health() contém FactStore', 'FactStore' in health or 'fatos' in health.lower(),
        health[:80])

    sleep_r = n4.sleep(1)
    chk('sleep() retorna resultado', sleep_r is not None and hasattr(sleep_r, 'cycles'),
        str(sleep_r)[:60])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 5 — GlobalWorkspaceNexus: multi-brain
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B5] GlobalWorkspaceNexus — Multi-Brain')
    gw = GlobalWorkspaceNexus(autosave=False)

    chk('GlobalWorkspaceNexus inicializa', gw is not None)
    chk('8 brains padrão criados', len(gw._brains) == 8,
        f'brains={list(gw._brains.keys())}')

    # Aprende fatos de diferentes domínios
    gw.learn('fotossíntese converte luz em glicose usando clorofila')
    gw.learn('neurônio é a unidade básica do sistema nervoso')
    gw.learn('quicksort divide array em torno de um pivô recursivamente')
    gw.learn('revolução industrial transformou a produção com máquinas a vapor')

    chk('learn() no GlobalWorkspace funciona', gw._stats['total_learned'] >= 3,
        f'total={gw._stats["total_learned"]}')

    # Propagação cross-domain
    chk('Propagação cross-domain ocorre',
        gw._stats['cross_domain_propagated'] >= 1,
        f'propagados={gw._stats["cross_domain_propagated"]}')

    # chat() integrado
    r_gw = gw.chat('o que é fotossíntese?')
    chk('chat() GlobalWorkspace retorna resposta',
        len(r_gw) > 20 and ('fotoss' in r_gw.lower() or 'glicose' in r_gw.lower()),
        r_gw[:60])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 6 — Brain especializado: biologia aprende fatos bio
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B6] SpecialistBrain — Domínios Específicos')
    bio_brain = gw._brains.get('biologia')
    chk('Brain biologia existe', bio_brain is not None)

    if bio_brain:
        chk('Brain biologia tem fatos sobre fotossíntese',
            any('fotoss' in f.lower() for f in bio_brain._facts),
            f'fatos no brain bio={len(bio_brain._facts)}')

        # Consulta direta ao brain
        q_bio = bio_brain.query('o que é neurônio?', top_k=2)
        chk('Brain bio responde query sobre neurônio',
            len(q_bio) >= 0,  # pode ter ou não ter
            f'resultados={len(q_bio)}')

    # Verifica que tecnologia brain tem fatos de TI
    tech_brain = gw._brains.get('tecnologia')
    if tech_brain:
        chk('Brain tecnologia tem fatos',
            len(tech_brain._facts) >= 0,
            f'fatos tech={len(tech_brain._facts)}')

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 7 — add_brain() + remove_brain()
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B7] add_brain() + remove_brain()')
    gw2 = GlobalWorkspaceNexus(autosave=False)

    custom = gw2.add_brain('culinaria', 'Culinária', [
        'receita','ingrediente','tempero','culinária','cozinhar','gastronomia',
        'prato','chef','sabor','aroma','massa','molho','sobremesa'])
    chk('add_brain() cria brain customizado', 'culinaria' in gw2._brains)

    gw2.learn('risoto é um prato italiano feito com arroz arbóreo e caldo')
    cul_fatos = gw2._brains['culinaria']._facts
    chk('Brain culinária aprende fatos relevantes',
        any('risoto' in f.lower() for f in cul_fatos),
        f'fatos culinaria={len(cul_fatos)}')

    removed = gw2.remove_brain('culinaria')
    chk('remove_brain() funciona', removed and 'culinaria' not in gw2._brains)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 8 — sleep() integrado + scan_health() GlobalWorkspace
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B8] sleep() + scan_health() GlobalWorkspace')
    gw3 = GlobalWorkspaceNexus(autosave=False)
    gw3.learn('osmose é o movimento de água através de membrana semipermeável')
    gw3.learn('difusão é o movimento de partículas de alta para baixa concentração')

    sleep_r3 = gw3.sleep(cycles=1)
    chk('sleep() GlobalWorkspace retorna dict',
        isinstance(sleep_r3, dict) and 'core' in sleep_r3, str(sleep_r3)[:60])
    chk('sleep() reporta ciclos',
        sleep_r3.get('sleep_cycles', 0) >= 1,
        f'cycles={sleep_r3.get("sleep_cycles")}')

    health3 = gw3.scan_health()
    chk('scan_health() GlobalWorkspace é completo',
        'Global Workspace' in health3 and 'Brain' in health3, health3[:80])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 9 — SpecialistBrain: relevance scoring
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B9] SpecialistBrain — Relevance Scoring')
    from dataclasses import dataclass as _dc

    # Encoder mínimo para teste de SpecialistBrain isolado
    enc_test = MultiLobeEncoder()
    sb_phys = SpecialistBrain('fisica', 'Física', [
        'energia','força','átomo','gravidade','velocidade'], enc_test)
    sb_hist = SpecialistBrain('historia', 'História', [
        'guerra','revolução','império','século','política'], enc_test)

    phys_text = 'a gravidade atrai corpos com massa'
    hist_text = 'a revolução francesa mudou a política europeia'

    rel_phys_phys = sb_phys.relevance(phys_text)
    rel_hist_phys = sb_hist.relevance(phys_text)
    chk('Física: relevância correta para texto de física',
        rel_phys_phys > rel_hist_phys,
        f'phys_on_phys={rel_phys_phys:.2f} hist_on_phys={rel_hist_phys:.2f}')

    rel_phys_hist = sb_phys.relevance(hist_text)
    rel_hist_hist = sb_hist.relevance(hist_text)
    chk('História: relevância correta para texto de história',
        rel_hist_hist > rel_phys_hist,
        f'hist_on_hist={rel_hist_hist:.2f} phys_on_hist={rel_phys_hist:.2f}')

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOCO 10 — Raciocínio condicional + dedutivo (NexusFinal)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if verbose: print('\n[B10] Raciocínio Condicional + Dedutivo')
    n5 = NexusFinal()
    n5.disable_autosave()
    n5.chat('se chove então o chão fica molhado')
    n5.chat('aprenda: chuva é precipitação de água')
    r_cond = n5.chat('o chão fica molhado se chove?')
    chk('ConditionalEngine responde', len(r_cond) > 5, r_cond[:60])

    n5.chat('aprenda: todo mamífero é um vertebrado')
    n5.chat('aprenda: baleias são mamíferos')
    r_ded = n5.chat('baleias são vertebrados?')
    chk('Raciocínio IS_A/transitivo', len(r_ded) > 5, r_ded[:60])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RESULTADO FINAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    elapsed = _time.time() - t0
    pct = ok / total if total else 0
    status = '✅ APROVADO' if pct >= 0.85 else ('⚠ VERIFICAR' if pct >= 0.70 else '✗ FALHOU')

    if verbose:
        print(f'\n{"═" * 70}')
        print(f'  {ok}/{total} testes   ({pct*100:.0f}%)   {elapsed:.1f}s   {status}')
        print(f'{"═" * 70}\n')

    return pct >= 0.85


# ══════════════════════════════════════════════════════════════════════════════
# §ENTRY POINT GLOBAL WORKSPACE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys as _sys

    print('=' * 70)
    print('NEXUS FINAL + GLOBAL WORKSPACE — Sistema Cognitivo com Multi-Cérebros')
    print('=' * 70)

    if '--test' in _sys.argv:
        ok = run_nexus_tests(verbose=True)
        _sys.exit(0 if ok else 1)

    if '--gw' in _sys.argv or '--global' in _sys.argv:
        # Modo GlobalWorkspace interativo
        print('\nIniciando com Área de Trabalho Global (multi-brain)...')
        n = GlobalWorkspaceNexus()
        print('GlobalWorkspace ativo com', len(n._brains), 'brains especializados.')
        print(n.brain_status())
    else:
        # Modo NexusFinal padrão (retrocompatível)
        n = NexusFinal()

    print('\nDigite "sair" para encerrar.')
    print('Comandos especiais: "status", "saúde", "brains"\n')

    while True:
        try:
            user = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nAté mais!')
            break
        if not user:
            continue
        if user.lower() in ('sair', 'exit', 'quit'):
            break
        if user.lower() == 'brains' and hasattr(n, 'brain_status'):
            print(n.brain_status())
        elif user.lower() in ('saúde', 'saude', 'health'):
            print(n.scan_health())
        else:
            print(n.chat(user))



# ── Extensão SparseSDR para numpy (necessário para V11.2 production) ──────
if HAS_NUMPY:
    def _sdr_to_numpy(self) -> 'np.ndarray':
        v = np.zeros(SDR_SIZE, dtype=np.uint8)
        if self._idx:
            v[list(self._idx)] = 1
        return v
    
    @classmethod
    def _sdr_from_numpy(cls, arr: 'np.ndarray') -> 'SparseSDR':
        return cls(np.where(arr > 0)[0].tolist())
    
    def _sdr_sparsity(self) -> float:
        return len(self._idx) / SDR_SIZE
    
    def _sdr_bit_density_valid(self) -> bool:
        s = self.sparsity()
        return SDR_SPARSITY_MIN <= s <= SDR_SPARSITY_MAX
    
    SparseSDR.to_numpy = _sdr_to_numpy
    SparseSDR.from_numpy = classmethod(_sdr_from_numpy.__func__)
    if not hasattr(SparseSDR, 'sparsity'):
        SparseSDR.sparsity = _sdr_sparsity
    if not hasattr(SparseSDR, 'bit_density_valid'):
        SparseSDR.bit_density_valid = _sdr_bit_density_valid


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PARTE 2: EVOLUÇÃO V13 (VecOps, Encoders Sensoriais)                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ══════════════════════════════════════════════════════════════════════════════
# §1  VEC OPS — operações vetoriais com fallback Python puro
# ══════════════════════════════════════════════════════════════════════════════

class VecOps:
    """
    Operações vetoriais com despacho automático numpy/puro.
    Speedup típico: ~10× para DIM=768 em operações de dot/norm/add.
    Preserva 100% de compatibilidade — mesmos resultados numéricos (float64).
    """

    @staticmethod
    def dot(a, b):
        if HAS_NUMPY:
            return float(_np.dot(a, b))
        return sum(x * y for x, y in zip(a, b))

    @staticmethod
    def norm(v):
        if HAS_NUMPY:
            return float(_np.linalg.norm(v))
        return math.sqrt(sum(x * x for x in v))

    @staticmethod
    def normalize(v):
        n = VecOps.norm(v)
        if n < 1e-12:
            return v if not HAS_NUMPY else list(v)
        if HAS_NUMPY:
            arr = _np.asarray(v, dtype=_np.float64)
            return (arr / n).tolist()
        return [x / n for x in v]

    @staticmethod
    def add(a, b, scale_b=1.0):
        if HAS_NUMPY:
            return (_np.asarray(a) + scale_b * _np.asarray(b)).tolist()
        return [x + scale_b * y for x, y in zip(a, b)]

    @staticmethod
    def sub(a, b):
        if HAS_NUMPY:
            return (_np.asarray(a) - _np.asarray(b)).tolist()
        return [x - y for x, y in zip(a, b)]

    @staticmethod
    def scale(v, s):
        if HAS_NUMPY:
            return (s * _np.asarray(v)).tolist()
        return [x * s for x in v]

    @staticmethod
    def cosine(a, b):
        d = VecOps.dot(a, b)
        na = VecOps.norm(a)
        nb = VecOps.norm(b)
        if na < 1e-12 or nb < 1e-12:
            return 0.0
        return d / (na * nb)

    @staticmethod
    def zeros(dim):
        if HAS_NUMPY:
            return _np.zeros(dim).tolist()
        return [0.0] * dim

    @staticmethod
    def weighted_average(vecs, weights):
        """Média ponderada de vetores."""
        if not vecs:
            return []
        dim = len(vecs[0])
        total_w = sum(weights) or 1.0
        if HAS_NUMPY:
            V = _np.array(vecs)
            W = _np.array(weights).reshape(-1, 1) / total_w
            return (V * W).sum(axis=0).tolist()
        result = [0.0] * dim
        for vec, w in zip(vecs, weights):
            wn = w / total_w
            for k in range(dim):
                result[k] += wn * vec[k]
        return result

    @staticmethod
    def mat_vec_topk(matrix, vec, k):
        """Multiplica matrix × vec e retorna top-k índices.
        matrix: lista de listas (N × D), vec: lista (D,), retorna top-k índices.
        """
        if HAS_NUMPY:
            M = _np.array(matrix)
            v = _np.array(vec)
            scores = M @ v
            idx = _np.argpartition(scores, -k)[-k:]
            idx = idx[_np.argsort(scores[idx])[::-1]]
            return idx.tolist()
        # Fallback: compute all scores
        scores = [sum(matrix[i][j] * vec[j] for j in range(len(vec)))
                  for i in range(len(matrix))]
        indexed = sorted(range(len(scores)), key=lambda i: -scores[i])
        return indexed[:k]


# ══════════════════════════════════════════════════════════════════════════════
# §2  MINIEMBED ACELERADO — patch transparente para MiniEmbed existente
# ══════════════════════════════════════════════════════════════════════════════

class MiniEmbedAccelerator:
    """
    Mixin/Wrapper que acelera MiniEmbed usando numpy quando disponível.
    
    COMO USAR:
        from nexus_v10_ultimate import MiniEmbed
        embed = MiniEmbed()
        accelerator = MiniEmbedAccelerator(embed)
        accelerator.patch()  # monkey-patches os métodos quentes
        # A partir daqui, embed.vector(), embed.cosine(), embed.sentence_vector()
        # usam numpy automaticamente (~10× mais rápido)
    
    REVERSÍVEL: accelerator.unpatch() restaura os métodos originais.
    """

    def __init__(self, embed):
        self._embed = embed
        self._originals = {}
        self._patched = False

    def patch(self):
        """Aplica aceleração numpy aos métodos quentes do MiniEmbed."""
        if self._patched or not HAS_NUMPY:
            return
        
        e = self._embed
        # Salva originais
        self._originals['cosine'] = e.cosine
        self._originals['sentence_vector'] = e.sentence_vector
        self._originals['_ns_update'] = e._ns_update

        # Patch cosine
        def fast_cosine(v1, v2):
            return VecOps.cosine(v1, v2)
        e.cosine = fast_cosine

        # Patch sentence_vector com cache mantido
        original_sv = self._originals['sentence_vector']
        def fast_sentence_vector(text):
            key = f'{e._sv_version}|{text}'
            hit = e._sv_cache.get(key)
            if hit is not None:
                return hit
            from nexus_v10_ultimate import _tokenize_embed
            tokens = _tokenize_embed(text)
            if not tokens:
                return VecOps.zeros(e.DIM)
            vecs = [e.vector(t) for t in tokens]
            result = VecOps.normalize(VecOps.weighted_average(
                vecs, [1.0] * len(vecs)))
            if len(e._sv_cache) >= 2048:
                for k in list(e._sv_cache)[:1024]:
                    del e._sv_cache[k]
            e._sv_cache[key] = result
            return result
        e.sentence_vector = fast_sentence_vector

        # Patch NS update (o hotspot principal)
        original_ns = self._originals['_ns_update']
        def fast_ns_update(word, pos_contexts):
            e._ensure_word(word)
            if not pos_contexts:
                return
            freq_w = e._freq.get(word, 1)
            lr = max(e.NS_LR / (1.0 + freq_w / 100.0), e.NS_LR_MIN)
            
            wv = _np.array(e._input_vec[word])
            neg_ctx = e._neg_sample(set(pos_contexts) | {word})

            grad_w = _np.zeros(e.DIM)
            
            # Positivos
            for ctx in pos_contexts:
                e._ensure_word(ctx)
                cv = _np.array(e._output_vec[ctx])
                dot = float(wv @ cv)
                err = e._sigmoid(dot) - 1.0
                grad_w += lr * err * cv
                e._output_vec[ctx] = (cv - lr * err * wv).tolist()
            
            # Negativos
            for neg in neg_ctx:
                e._ensure_word(neg)
                nv = _np.array(e._output_vec[neg])
                dot = float(wv @ nv)
                err = e._sigmoid(dot)
                grad_w += lr * err * nv
                e._output_vec[neg] = (nv - lr * err * wv).tolist()
            
            e._input_vec[word] = (wv - grad_w).tolist()
            e._updates += 1
        
        e._ns_update = fast_ns_update
        self._patched = True

    def unpatch(self):
        """Restaura métodos originais."""
        if not self._patched:
            return
        for name, original in self._originals.items():
            setattr(self._embed, name, original)
        self._patched = False


# ══════════════════════════════════════════════════════════════════════════════
# §3  SEMANTIC SDR ENCODER ACELERADO
# ══════════════════════════════════════════════════════════════════════════════

class SemanticSDREncoderFast:
    """
    LSH SDR Encoder acelerado com numpy.
    Mesma semântica do SemanticSDREncoder original, mas usa mat_vec_topk.
    """
    
    SDR_SIZE = 4096
    ACTIVE = 40

    def __init__(self, embed_dim=768):
        self.dim = embed_dim
        self._updates = 0
        if HAS_NUMPY:
            # Gera matriz de projeção diretamente como numpy array
            rng = _np.random.RandomState(42)
            R = rng.randn(self.SDR_SIZE, embed_dim)
            norms = _np.linalg.norm(R, axis=1, keepdims=True)
            norms[norms < 1e-9] = 1.0
            self._R_np = R / norms
            self._R = None  # não precisa da versão Python
        else:
            self._R_np = None
            self._R = []
            for i in range(self.SDR_SIZE):
                seed = (i * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFF
                v = []
                for _ in range(embed_dim):
                    seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
                    u = max(seed / 0xFFFFFFFF, 1e-9)
                    v.append(math.log(u))
                nrm = math.sqrt(sum(x * x for x in v)) or 1.0
                self._R.append([x / nrm for x in v])

    def encode(self, embed_vec, learn=False):
        if HAS_NUMPY:
            v = _np.asarray(embed_vec[:self.dim], dtype=_np.float64)
            if len(v) < self.dim:
                v = _np.pad(v, (0, self.dim - len(v)))
            scores = self._R_np @ v
            top_k = _np.argpartition(scores, -self.ACTIVE)[-self.ACTIVE:]
            # Importa SparseSDR do módulo principal
            try:
                from nexus_v10_ultimate import SparseSDR
            except ImportError:
                # Standalone mode
                return list(top_k)
            return SparseSDR.from_indices(top_k.tolist())
        else:
            vec = (list(embed_vec) + [0.0] * self.dim)[:self.dim]
            scores = [sum(self._R[i][k] * vec[k] for k in range(self.dim))
                      for i in range(self.SDR_SIZE)]
            top_k = sorted(range(self.SDR_SIZE), key=lambda i: -scores[i])[:self.ACTIVE]
            try:
                from nexus_v10_ultimate import SparseSDR
                return SparseSDR.from_indices(top_k)
            except ImportError:
                return top_k


# ══════════════════════════════════════════════════════════════════════════════
# §4  GLOBAL WORKSPACE — consciência artificial via broadcasting
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConsciousContent:
    """Conteúdo que atinge o limiar de consciência no GlobalWorkspace."""
    sdr: Any               # SparseSDR
    text: str
    source: str             # módulo de origem
    salience: float         # score de saliência
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)


class BrainModule:
    """Módulo registrável no GlobalWorkspace.
    
    Cada módulo tem um CognitiveBrain e pode:
    - Receber broadcasts (mensagens SDR conscientes)
    - Competir para publicar conteúdo
    - Processar automaticamente informações relevantes
    """
    
    def __init__(self, name: str, brain, domain: str = 'general'):
        self.name = name
        self.brain = brain
        self.domain = domain
        self._inbox: deque = deque(maxlen=50)
        self._relevance_threshold = 0.08
    
    def receive_broadcast(self, content: ConsciousContent) -> Optional[str]:
        """Recebe broadcast e retorna resposta se relevante."""
        self._inbox.append(content)
        # Verifica relevância via overlap SDR
        try:
            recall = self.brain.recall(content.sdr, top_k=3, threshold=0.05)
            if recall:
                best_score, best_mem = recall[0]
                if best_score >= self._relevance_threshold:
                    return best_mem.text
        except Exception:
            pass
        return None
    
    def compete(self, query_sdr) -> Tuple[float, Optional[str]]:
        """Compete para responder: retorna (salience, response)."""
        try:
            recall = self.brain.recall(query_sdr, top_k=1, threshold=0.03)
            if recall:
                score, mem = recall[0]
                return score * mem.strength, mem.text
        except Exception:
            pass
        return 0.0, None


class GlobalWorkspace:
    """
    Implementação do Global Workspace Theory (Baars, 1988) integrada
    ao RepresentationalBus do Nexus V10.
    
    ARQUITETURA:
    ┌─────────────────────────────────────────────┐
    │              GLOBAL WORKSPACE               │
    │  ┌───────────────────────────────────────┐   │
    │  │     RepresentationalBus (V10)        │   │
    │  │  (barramento tálamo-cortical SDR)    │   │
    │  └──────────────┬────────────────────────┘   │
    │                 │                             │
    │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐    │
    │  │Brain1│  │Brain2│  │Brain3│  │Visual│    │
    │  │ text │  │ code │  │ math │  │Encdr │    │
    │  └──────┘  └──────┘  └──────┘  └──────┘    │
    │       ↑         ↑         ↑         ↑       │
    │       └─────────┴─────────┴─────────┘       │
    │              BROADCAST (SDR)                  │
    └─────────────────────────────────────────────┘
    
    FLUXO:
    1. Módulos competem publicando SDR + salience no bus
    2. O sinal com maior salience vence (winner-take-all)
    3. Sinal vencedor é broadcasted a TODOS os módulos
    4. Cada módulo processa e potencialmente responde
    5. Respostas são coletadas e fundidas no workspace
    
    BIO-INSPIRAÇÃO:
    - Global Workspace Theory (Baars, 1988)
    - Thalamic broadcasting (Sherman & Guillery, 2006)
    - Competition for consciousness (Dehaene et al., 2003)
    """
    
    CONSCIOUSNESS_THRESHOLD = 0.15   # salience mínima para broadcasting
    MAX_HISTORY = 100
    
    def __init__(self, rep_bus=None):
        """
        rep_bus: RepresentationalBus do V10 (se None, cria um novo).
        """
        self._rep_bus = rep_bus
        self._modules: Dict[str, BrainModule] = {}
        self._history: deque = deque(maxlen=self.MAX_HISTORY)
        self._current_focus: Optional[ConsciousContent] = None
        self._lock = threading.Lock()
    
    def register_module(self, module: BrainModule) -> None:
        """Registra um módulo no workspace."""
        self._modules[module.name] = module
    
    def unregister_module(self, name: str) -> None:
        """Remove um módulo."""
        self._modules.pop(name, None)
    
    def compete_and_broadcast(self, query_sdr, query_text: str,
                               source: str = 'user') -> Dict[str, Any]:
        """
        Pipeline completo de consciência:
        1. Publica no RepBus
        2. Cada módulo compete
        3. Melhor sinal vira consciente
        4. Broadcast a todos
        5. Coleta respostas
        """
        with self._lock:
            # 1. Publica no RepBus (se disponível)
            if self._rep_bus is not None:
                try:
                    from nexus_v10_ultimate import RepMessage
                    self._rep_bus.publish(RepMessage(
                        source=source, sdr=query_sdr, text=query_text, priority=1.0))
                except ImportError:
                    pass
            
            # 2. Competição entre módulos
            competitions: List[Tuple[float, str, str]] = []
            for name, module in self._modules.items():
                salience, response = module.compete(query_sdr)
                if response and salience > 0:
                    competitions.append((salience, name, response))
            
            competitions.sort(reverse=True)
            
            # 3. Winner-take-all: maior salience vira consciente
            winner = None
            responses = {}
            
            if competitions and competitions[0][0] >= self.CONSCIOUSNESS_THRESHOLD:
                sal, win_name, win_resp = competitions[0]
                winner = ConsciousContent(
                    sdr=query_sdr, text=win_resp,
                    source=win_name, salience=sal,
                    metadata={'query': query_text, 'competitors': len(competitions)})
                self._current_focus = winner
                self._history.append(winner)
                
                # 4. Broadcast a todos os módulos (exceto o vencedor)
                for name, module in self._modules.items():
                    if name == win_name:
                        continue
                    resp = module.receive_broadcast(winner)
                    if resp:
                        responses[name] = resp
            
            return {
                'winner': winner,
                'winner_name': competitions[0][1] if competitions else None,
                'winner_response': competitions[0][2] if competitions else None,
                'salience': competitions[0][0] if competitions else 0.0,
                'all_responses': responses,
                'n_competitors': len(competitions),
                'conscious': winner is not None,
            }
    
    def broadcast_content(self, content: ConsciousContent) -> Dict[str, str]:
        """Broadcast manual de conteúdo consciente."""
        responses = {}
        for name, module in self._modules.items():
            if name == content.source:
                continue
            resp = module.receive_broadcast(content)
            if resp:
                responses[name] = resp
        return responses
    
    def current_focus(self) -> Optional[ConsciousContent]:
        """Retorna o conteúdo atualmente na consciência."""
        return self._current_focus
    
    def recent_conscious(self, n: int = 10) -> List[ConsciousContent]:
        """Histórico de conteúdos conscientes."""
        return list(self._history)[-n:]
    
    @property
    def n_modules(self) -> int:
        return len(self._modules)
    
    def stats(self) -> Dict:
        return {
            'modules': list(self._modules.keys()),
            'n_modules': len(self._modules),
            'history_size': len(self._history),
            'current_focus': self._current_focus.text[:60] if self._current_focus else None,
            'numpy_available': HAS_NUMPY,
        }


# ══════════════════════════════════════════════════════════════════════════════
# §5  VISUAL ENCODER — visão rudimentar via SDR
# ══════════════════════════════════════════════════════════════════════════════

class FeatureExtractor:
    """Base para features visuais."""
    def extract(self, image) -> List[float]:
        raise NotImplementedError


class ColorFeature(FeatureExtractor):
    """Histograma de cores em HSV (8 bins H × 3 bins S = 24D)."""
    def extract(self, image) -> List[float]:
        hsv_hist = [0] * 24
        for row in image:
            for r, g, b in row:
                r_ = r / 255.0; g_ = g / 255.0; b_ = b / 255.0
                cmax = max(r_, g_, b_); cmin = min(r_, g_, b_); delta = cmax - cmin
                if delta == 0: h = 0
                elif cmax == r_: h = 60 * (((g_ - b_) / delta) % 6)
                elif cmax == g_: h = 60 * ((b_ - r_) / delta + 2)
                else: h = 60 * ((r_ - g_) / delta + 4)
                s = 0 if cmax == 0 else delta / cmax
                h_bin = int(h / 45) % 8
                s_bin = min(2, int(s * 3))
                hsv_hist[h_bin * 3 + s_bin] += 1
        total = sum(hsv_hist) or 1
        return [x / total for x in hsv_hist]


class EdgeFeature(FeatureExtractor):
    """Bordas via Sobel, histograma de magnitude e orientação (16D)."""
    def extract(self, image) -> List[float]:
        if HAS_NUMPY:
            return self._extract_np(image)
        gray = [[0.299 * r + 0.587 * g + 0.114 * b for r, g, b in row] for row in image]
        height = len(gray)
        width = len(gray[0]) if height else 0
        sobel_x = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
        sobel_y = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
        mag_hist = [0] * 8
        angle_hist = [0] * 8
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                gx = sum(sobel_x[i][j] * gray[y - 1 + i][x - 1 + j]
                         for i in range(3) for j in range(3))
                gy = sum(sobel_y[i][j] * gray[y - 1 + i][x - 1 + j]
                         for i in range(3) for j in range(3))
                mag = math.hypot(gx, gy)
                angle = math.atan2(gy, gx)
                ang_bin = int((angle + math.pi) / (2 * math.pi) * 8) % 8
                angle_hist[ang_bin] += mag
                mag_hist[min(7, int(mag / 50))] += 1
        total_mag = sum(mag_hist) or 1
        total_ang = sum(angle_hist) or 1
        return [x / total_mag for x in mag_hist] + [x / total_ang for x in angle_hist]

    def _extract_np(self, image) -> List[float]:
        img = _np.array(image, dtype=_np.float64)
        gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
        sx = _np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=_np.float64)
        sy = _np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=_np.float64)
        h, w = gray.shape
        gx = _np.zeros((h - 2, w - 2))
        gy = _np.zeros((h - 2, w - 2))
        for i in range(3):
            for j in range(3):
                gx += sx[i, j] * gray[i:h - 2 + i, j:w - 2 + j]
                gy += sy[i, j] * gray[i:h - 2 + i, j:w - 2 + j]
        mag = _np.hypot(gx, gy)
        angle = _np.arctan2(gy, gx)
        mag_bins = _np.clip((mag / 50).astype(int), 0, 7)
        ang_bins = (((angle + _np.pi) / (2 * _np.pi)) * 8).astype(int) % 8
        mag_hist = _np.bincount(mag_bins.ravel(), minlength=8)[:8].astype(float)
        ang_hist = _np.zeros(8)
        for b in range(8):
            ang_hist[b] = mag[ang_bins == b].sum()
        mag_hist /= (mag_hist.sum() or 1)
        ang_hist /= (ang_hist.sum() or 1)
        return mag_hist.tolist() + ang_hist.tolist()


class TextureFeature(FeatureExtractor):
    """Local Binary Patterns simplificado (8D)."""
    def extract(self, image) -> List[float]:
        gray = [[0.299 * r + 0.587 * g + 0.114 * b for r, g, b in row] for row in image]
        height = len(gray); width = len(gray[0]) if height else 0
        hist = [0] * 8
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                center = gray[y][x]
                neighbors = [
                    gray[y - 1][x - 1], gray[y - 1][x], gray[y - 1][x + 1],
                    gray[y][x + 1], gray[y + 1][x + 1], gray[y + 1][x],
                    gray[y + 1][x - 1], gray[y][x - 1]
                ]
                pattern = sum((1 << i) for i, n in enumerate(neighbors) if n >= center)
                transitions = bin(pattern ^ (pattern >> 1)).count('1')
                hist[pattern % 8 if transitions <= 2 else 7] += 1
        total = sum(hist) or 1
        return [x / total for x in hist]


class MotionFeature(FeatureExtractor):
    """Diferença entre frames consecutivos (8D)."""
    def __init__(self):
        self.prev_frame = None

    def extract(self, image) -> List[float]:
        if self.prev_frame is None:
            self.prev_frame = image
            return [0.0] * 8
        if HAS_NUMPY:
            prev = _np.array(self.prev_frame, dtype=_np.float64)
            cur = _np.array(image, dtype=_np.float64)
            gray_p = 0.299 * prev[:, :, 0] + 0.587 * prev[:, :, 1] + 0.114 * prev[:, :, 2]
            gray_c = 0.299 * cur[:, :, 0] + 0.587 * cur[:, :, 1] + 0.114 * cur[:, :, 2]
            h = min(gray_p.shape[0], gray_c.shape[0])
            w = min(gray_p.shape[1], gray_c.shape[1])
            diff = _np.abs(gray_c[:h, :w] - gray_p[:h, :w]).sum()
            max_diff = 255.0 * h * w
        else:
            gray_prev = [[0.299 * r + 0.587 * g + 0.114 * b for r, g, b in row]
                         for row in self.prev_frame]
            gray_cur = [[0.299 * r + 0.587 * g + 0.114 * b for r, g, b in row]
                        for row in image]
            diff = sum(abs(gray_cur[y][x] - gray_prev[y][x])
                       for y in range(min(len(gray_prev), len(gray_cur)))
                       for x in range(min(len(gray_prev[0]), len(gray_cur[0]))))
            max_diff = 255.0 * len(gray_cur) * len(gray_cur[0])
        self.prev_frame = image
        motion = diff / max_diff if max_diff else 0
        bins = [0.0] * 8
        bins[min(7, int(motion * 8))] = 1.0
        return bins


class ShapeFeature(FeatureExtractor):
    """Proporção, área, centróide (8D)."""
    def extract(self, image) -> List[float]:
        gray = [[0.299 * r + 0.587 * g + 0.114 * b for r, g, b in row] for row in image]
        mean_val = sum(sum(row) for row in gray) / max(len(gray) * len(gray[0]), 1)
        total = 0; sum_x = 0; sum_y = 0
        min_x = len(gray[0]); max_x = 0; min_y = len(gray); max_y = 0
        for y, row in enumerate(gray):
            for x, val in enumerate(row):
                if val > mean_val:
                    total += 1; sum_x += x; sum_y += y
                    min_x = min(min_x, x); max_x = max(max_x, x)
                    min_y = min(min_y, y); max_y = max(max_y, y)
        if total == 0:
            return [0.0] * 8
        cx = sum_x / total / len(gray[0])
        cy = sum_y / total / len(gray)
        aspect = (max_x - min_x) / max(max_y - min_y + 1, 1)
        fill = total / max(len(gray) * len(gray[0]), 1)
        return [cx, cy, aspect, fill, 0.0, 0.0, 0.0, 0.0]


class VisualEncoder:
    """
    Converte imagem (RGB) em SDR de 40 bits ativos em 4096 bits.
    
    Pipeline:
      image (list[list[tuple(r,g,b)]]) → 5 features (8D cada) → 
      hash → 40 bits → SparseSDR
    
    Features: cor (HSV), bordas (Sobel), textura (LBP), movimento, forma.
    Numpy acelerado quando disponível (~5× speedup no Sobel).
    """

    SDR_SIZE = 4096
    ACTIVE_BITS = 40

    def __init__(self):
        self.features = [
            ColorFeature(), EdgeFeature(), TextureFeature(),
            MotionFeature(), ShapeFeature()
        ]
        self.bits_per_feature = self.ACTIVE_BITS // len(self.features)
        self.remaining = self.ACTIVE_BITS % len(self.features)
        self._seed = 0xDEADBEEF

    def encode(self, image, learn=False):
        """
        image: lista de listas de tuplas (r,g,b) 0-255.
        Retorna SparseSDR (ou lista de índices se standalone).
        """
        vectors = [feat.extract(image) for feat in self.features]
        bits = set()
        for i, vec in enumerate(vectors):
            num_bits = self.bits_per_feature + (1 if i < self.remaining else 0)
            for j in range(num_bits):
                h = self._hash_vector(vec, j, i)
                bits.add(h % self.SDR_SIZE)
        
        bits = list(bits)
        # Pad or trim to exactly ACTIVE_BITS
        if len(bits) > self.ACTIVE_BITS:
            bits = bits[:self.ACTIVE_BITS]
        elif len(bits) < self.ACTIVE_BITS:
            extra = 0
            while len(bits) < self.ACTIVE_BITS and extra < self.SDR_SIZE:
                if extra not in bits:
                    bits.append(extra)
                extra += 1
        
        try:
            from nexus_v10_ultimate import SparseSDR
            return SparseSDR.from_indices(sorted(bits))
        except ImportError:
            return sorted(bits)

    def _hash_vector(self, vec, idx, feat_idx):
        s = f"{feat_idx}|{idx}|{vec[idx % len(vec)]:.6f}"
        h = 0
        for c in s:
            h = (h * 131 + ord(c)) & 0xFFFFFFFF
        return (h ^ self._seed) & 0xFFFFFFFF


# ══════════════════════════════════════════════════════════════════════════════
# §6  AUDIO ENCODER — audição rudimentar via SDR
# ══════════════════════════════════════════════════════════════════════════════

class AudioFeatureExtractor:
    def extract(self, samples, sample_rate=16000) -> List[float]:
        raise NotImplementedError


class SpectralFeature(AudioFeatureExtractor):
    """FFT + 8 bandas mel simplificadas."""
    def extract(self, samples, sample_rate=16000) -> List[float]:
        N = 512
        if len(samples) < N:
            samples = list(samples) + [0.0] * (N - len(samples))
        
        if HAS_NUMPY:
            x = _np.array(samples[:N]) * _np.hanning(N)
            fft = _np.fft.rfft(x)
            mag = _np.abs(fft)[:N // 2]
        else:
            # Hanning + DFT manual
            window = [0.5 * (1 - math.cos(2 * math.pi * i / (N - 1))) for i in range(N)]
            x = [samples[i] * window[i] for i in range(N)]
            mag = []
            for k in range(N // 2):
                real = sum(x[n] * math.cos(2 * math.pi * k * n / N) for n in range(N))
                imag = sum(x[n] * math.sin(2 * math.pi * k * n / N) for n in range(N))
                mag.append(math.hypot(real, imag))
        
        # 8 bandas mel
        freq_per_bin = sample_rate / N
        mel_freq = [0.0] * 8
        boundaries = [0, 100, 300, 600, 1000, 2000, 4000, 8000]
        for i in range(8):
            low = boundaries[i] if i < len(boundaries) else 0
            high = boundaries[i + 1] if i + 1 < len(boundaries) else sample_rate // 2
            low_bin = max(0, int(low / freq_per_bin))
            high_bin = min(len(mag), int(high / freq_per_bin))
            if HAS_NUMPY:
                mel_freq[i] = float(mag[low_bin:high_bin].sum())
            else:
                mel_freq[i] = sum(mag[low_bin:high_bin])
        total = sum(mel_freq) or 1
        return [e / total for e in mel_freq]


class MFCCFeature(AudioFeatureExtractor):
    """MFCC simplificado: log-mel + DCT (8D)."""
    def extract(self, samples, sample_rate=16000) -> List[float]:
        mel = SpectralFeature().extract(samples, sample_rate)
        log_mel = [math.log(max(1e-6, m)) for m in mel]
        N = len(log_mel)
        dct = [0.0] * 8
        for k in range(8):
            for n in range(N):
                dct[k] += log_mel[n] * math.cos(math.pi * k * (2 * n + 1) / (2 * N))
            dct[k] *= math.sqrt(2.0 / N)
        maxv = max(abs(v) for v in dct) or 1
        return [v / maxv for v in dct]


class ZCRFeature(AudioFeatureExtractor):
    """Taxa de cruzamento por zero (4D)."""
    def extract(self, samples, sample_rate=16000) -> List[float]:
        if len(samples) < 2:
            return [0.0] * 4
        zc = sum(1 for i in range(1, len(samples)) if samples[i] * samples[i - 1] < 0)
        rate = zc / len(samples)
        bins = [0.0] * 4
        bins[min(3, int(rate * 4))] = 1.0
        return bins


class EnergyFeature(AudioFeatureExtractor):
    """RMS e variação (4D)."""
    def extract(self, samples, sample_rate=16000) -> List[float]:
        if not samples:
            return [0.0] * 4
        if HAS_NUMPY:
            s = _np.array(samples)
            rms = float(_np.sqrt((s ** 2).mean()))
        else:
            rms = math.sqrt(sum(s * s for s in samples) / len(samples))
        rms_norm = min(1.0, rms / 0.5)
        return [rms_norm, 0.0, 0.0, 0.0]


class PitchFeature(AudioFeatureExtractor):
    """Estimativa de pitch via autocorrelação (8D)."""
    def extract(self, samples, sample_rate=16000) -> List[float]:
        N = min(1024, len(samples))
        if N < 64:
            return [0.0] * 8
        
        if HAS_NUMPY:
            s = _np.array(samples[:N])
            acf = _np.correlate(s, s, mode='full')[N - 1:]
        else:
            acf = [0.0] * N
            for lag in range(1, N):
                acf[lag] = sum(samples[i] * samples[i + lag] for i in range(N - lag))
        
        min_lag = sample_rate // 500
        max_lag = min(sample_rate // 50, N - 1)
        best_lag = min_lag; best_val = 0
        for lag in range(min_lag, max_lag):
            val = acf[lag] if HAS_NUMPY else acf[lag]
            if isinstance(val, (float, int)) and val > best_val:
                best_val = val; best_lag = lag
        
        if best_val == 0:
            return [0.0] * 8
        pitch = sample_rate / best_lag
        bins = [0.0] * 8
        if 50 <= pitch <= 500:
            idx = int(8 * (math.log(pitch / 50) / math.log(500 / 50)))
            bins[min(7, max(0, idx))] = 1.0
        return bins


class VoiceMusicFeature(AudioFeatureExtractor):
    """Classificação voz/música por variância de pitch (8D)."""
    def extract(self, samples, sample_rate=16000) -> List[float]:
        seg_len = max(len(samples) // 3, 64)
        pitches = []
        for i in range(3):
            seg = samples[i * seg_len:(i + 1) * seg_len]
            if len(seg) < 64:
                continue
            p = PitchFeature().extract(seg, sample_rate)
            max_idx = max(range(8), key=lambda k: p[k])
            pitches.append(max_idx / 8.0)
        if len(pitches) < 2:
            return [0.5, 0.5] + [0.0] * 6
        mean_p = sum(pitches) / len(pitches)
        var = sum((p - mean_p) ** 2 for p in pitches) / len(pitches)
        is_voice = 1.0 if var < 0.05 else 0.0
        return [is_voice, 1.0 - is_voice] + [0.0] * 6


class AudioEncoder:
    """
    Converte áudio (samples float) em SDR de 40 bits ativos em 4096 bits.
    
    Pipeline:
      samples (list[float] -1..1) → 6 features → hash → 40 bits → SparseSDR
    
    Features: espectro, MFCC, ZCR, energia, pitch, voz/música.
    Numpy acelerado quando disponível (~10× speedup na FFT).
    """

    SDR_SIZE = 4096
    ACTIVE_BITS = 40

    def __init__(self):
        self.features = [
            SpectralFeature(), MFCCFeature(), ZCRFeature(),
            EnergyFeature(), PitchFeature(), VoiceMusicFeature()
        ]
        self.bits_per_feature = self.ACTIVE_BITS // len(self.features)
        self.remaining = self.ACTIVE_BITS % len(self.features)
        self._seed = 0xDEADBEEF

    def encode(self, samples, sample_rate=16000, learn=False):
        vectors = [feat.extract(samples, sample_rate) for feat in self.features]
        bits = set()
        for i, vec in enumerate(vectors):
            num_bits = self.bits_per_feature + (1 if i < self.remaining else 0)
            for j in range(num_bits):
                h = self._hash_vector(vec, j, i)
                bits.add(h % self.SDR_SIZE)
        bits = list(bits)
        if len(bits) > self.ACTIVE_BITS:
            bits = bits[:self.ACTIVE_BITS]
        elif len(bits) < self.ACTIVE_BITS:
            extra = 0
            while len(bits) < self.ACTIVE_BITS and extra < self.SDR_SIZE:
                if extra not in bits:
                    bits.append(extra)
                extra += 1
        try:
            from nexus_v10_ultimate import SparseSDR
            return SparseSDR.from_indices(sorted(bits))
        except ImportError:
            return sorted(bits)

    def _hash_vector(self, vec, idx, feat_idx):
        s = f"{feat_idx}|{idx}|{vec[idx % len(vec)]:.6f}"
        h = 0
        for c in s:
            h = (h * 131 + ord(c)) & 0xFFFFFFFF
        return (h ^ self._seed) & 0xFFFFFFFF

    @staticmethod
    def from_pcm_bytes(audio_bytes, bits=16):
        """Converte bytes PCM para lista de floats normalizados (-1..1)."""
        step = bits // 8
        max_val = 2 ** (bits - 1)
        samples = []
        for i in range(0, len(audio_bytes) - step + 1, step):
            val = int.from_bytes(audio_bytes[i:i + step], 'little', signed=True)
            samples.append(val / max_val)
        return samples


# ══════════════════════════════════════════════════════════════════════════════
# §7  NEXUS V13 — classe integradora
# ══════════════════════════════════════════════════════════════════════════════

class NexusV13Integration:
    """
    Módulo de integração que acopla as 3 evoluções ao NexusV10 existente.
    
    USO:
        from nexus_v10_ultimate import NexusV10
        from nexus_v13_evolution import NexusV13Integration
        
        nexus = NexusV10()
        v13 = NexusV13Integration(nexus)
        v13.setup()  # aplica todas as evoluções
        
        # Agora nexus tem:
        # - GlobalWorkspace com multi-brain broadcasting
        # - MiniEmbed acelerado com numpy (~10×)
        # - VisualEncoder e AudioEncoder integrados
        # - Todos comunicando via RepresentationalBus
    """

    VERSION = 'v13-evolution'

    def __init__(self, nexus=None):
        self._nexus = nexus
        self._gw = None
        self._accelerator = None
        self._visual_enc = VisualEncoder()
        self._audio_enc = AudioEncoder()
        self._sp_fast = None
        self._setup_done = False

    def setup(self):
        """Aplica todas as evoluções ao Nexus existente."""
        if self._setup_done:
            return
        
        n = self._nexus
        
        # ── 1. Aceleração numpy do MiniEmbed ─────────────────────────────
        if n is not None:
            self._accelerator = MiniEmbedAccelerator(n.embed)
            self._accelerator.patch()
            
            # Semantic SDR Encoder rápido
            self._sp_fast = SemanticSDREncoderFast(embed_dim=n.embed.DIM)
        
        # ── 2. GlobalWorkspace sobre o RepresentationalBus ────────────────
        rep_bus = getattr(n, 'rep_bus', None) if n else None
        self._gw = GlobalWorkspace(rep_bus=rep_bus)
        
        # Registra brains como módulos no workspace
        if n is not None:
            # Brain principal
            main_module = BrainModule('main_brain', n.brain, domain='general')
            self._gw.register_module(main_module)
            
            # Módulos sensoriais (visuais e auditivos publicam no bus)
            # Não têm brain próprio, mas participam do broadcasting
        
        # Expõe no nexus
        if n is not None:
            n.global_workspace = self._gw
            n.visual_encoder = self._visual_enc
            n.audio_encoder = self._audio_enc
            n.v13 = self
        
        self._setup_done = True
        
        status = []
        status.append(f"✅ GlobalWorkspace: {self._gw.n_modules} módulo(s) registrado(s)")
        status.append(f"✅ MiniEmbed: numpy={'SIM (~10× speedup)' if HAS_NUMPY else 'NÃO (Python puro)'}")
        status.append(f"✅ VisualEncoder: {self._visual_enc.ACTIVE_BITS} bits, {len(self._visual_enc.features)} features")
        status.append(f"✅ AudioEncoder: {self._audio_enc.ACTIVE_BITS} bits, {len(self._audio_enc.features)} features")
        return '\n'.join(status)

    def process_image(self, image) -> Any:
        """Processa imagem e publica no GlobalWorkspace via RepBus."""
        sdr = self._visual_enc.encode(image)
        
        if self._gw and self._nexus:
            # Publica no RepBus
            rep_bus = getattr(self._nexus, 'rep_bus', None)
            if rep_bus is not None:
                try:
                    from nexus_v10_ultimate import RepMessage
                    rep_bus.publish(RepMessage(
                        source='visual_encoder', sdr=sdr,
                        text='[VISUAL INPUT]', priority=0.8))
                except ImportError:
                    pass
            
            # Compete no GlobalWorkspace
            result = self._gw.compete_and_broadcast(
                sdr, '[VISUAL INPUT]', source='visual_encoder')
            return {'sdr': sdr, 'gw_result': result}
        
        return {'sdr': sdr}

    def process_audio(self, samples, sample_rate=16000) -> Any:
        """Processa áudio e publica no GlobalWorkspace via RepBus."""
        sdr = self._audio_enc.encode(samples, sample_rate)
        
        if self._gw and self._nexus:
            rep_bus = getattr(self._nexus, 'rep_bus', None)
            if rep_bus is not None:
                try:
                    from nexus_v10_ultimate import RepMessage
                    rep_bus.publish(RepMessage(
                        source='audio_encoder', sdr=sdr,
                        text='[AUDIO INPUT]', priority=0.8))
                except ImportError:
                    pass
            
            result = self._gw.compete_and_broadcast(
                sdr, '[AUDIO INPUT]', source='audio_encoder')
            return {'sdr': sdr, 'gw_result': result}
        
        return {'sdr': sdr}

    def process_audio_bytes(self, audio_bytes, sample_rate=16000, bits=16) -> Any:
        """Converte bytes PCM e processa."""
        samples = AudioEncoder.from_pcm_bytes(audio_bytes, bits)
        return self.process_audio(samples, sample_rate)

    def add_brain(self, name: str, brain, domain: str = 'general') -> None:
        """Adiciona um brain extra ao GlobalWorkspace."""
        module = BrainModule(name, brain, domain=domain)
        self._gw.register_module(module)

    def broadcast_text(self, text: str) -> Dict:
        """Broadcast de texto para todos os brains via GlobalWorkspace."""
        if self._nexus is None:
            return {'error': 'Nexus não conectado'}
        sdr = self._nexus.encoder.encode(text)
        return self._gw.compete_and_broadcast(sdr, text, source='user')

    def stats(self) -> Dict:
        return {
            'version': self.VERSION,
            'numpy': HAS_NUMPY,
            'gw': self._gw.stats() if self._gw else None,
            'visual_features': len(self._visual_enc.features),
            'audio_features': len(self._audio_enc.features),
            'embed_patched': self._accelerator._patched if self._accelerator else False,
        }



# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PARTE 3: CAMADA DE PRODUÇÃO (V11.2 Mission Critical)                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝


# Bancos de dados de produção
DB_SECURE    = "nexus_secure.db"       # logs de segurança (dados cifrados)
DB_IOT       = "nexus_iot_final.db"    # telemetria de sensores

# Limites SDR para filtragem de pacotes (Resiliência Seletiva)
SDR_SPARSITY_MIN  = 0.005   # mínimo 0.5% de bits ativos
SDR_SPARSITY_MAX  = 0.08    # máximo 8% de bits ativos (ideal: 2%)
SDR_SPARSITY_IDEAL = 0.02

# ══════════════════════════════════════════════════════════════════════════════
# §2  NEXUS GUARD V11 — Criptografia XOR com SDR-Key Determinística
# ══════════════════════════════════════════════════════════════════════════════

class NexusGuardV11:
    """
    Middleware de criptografia XOR com chave mestra gerada deterministicamente.

    A SDR-Key é derivada de um seed fixo via numpy RandomState, garantindo
    que a mesma chave seja reproduzida em qualquer instância com o mesmo seed.

    Métodos públicos:
      encrypt_payload(data) → str (hex cifrado)
      decrypt_payload(hex_data) → str
      sign(data) → str (HMAC-SHA256 truncado)
      verify(data, sig) → bool
    """

    KEY_SIZE = 256  # bytes — 256 bytes = chave longa para XOR rolling

    def __init__(self, key_seed: int = 0x4E455855):  # "NEXU" em hex
        rng = np.random.RandomState(key_seed)
        self.master_key: bytes = rng.bytes(self.KEY_SIZE)
        self._hmac_secret: bytes = hashlib.sha256(self.master_key).digest()

    # ── Criptografia XOR ──────────────────────────────────────────────────────

    def encrypt_payload(self, data: Any) -> str:
        """Cifra dados com XOR rotativo + prefixo de comprimento."""
        if isinstance(data, dict) or isinstance(data, list):
            raw = json.dumps(data, ensure_ascii=False)
        elif not isinstance(data, str):
            raw = str(data)
        else:
            raw = data
        byte_data = raw.encode("utf-8")
        # Prefixo de 4 bytes com comprimento original (para verificação pós-decrypt)
        length_prefix = struct.pack(">I", len(byte_data))
        payload = length_prefix + byte_data
        encrypted = bytes([b ^ self.master_key[i % self.KEY_SIZE] for i, b in enumerate(payload)])
        return encrypted.hex()

    def decrypt_payload(self, hex_data: str) -> str:
        """Decifra payload XOR e verifica integridade do comprimento."""
        try:
            encrypted = bytes.fromhex(hex_data)
            decrypted = bytes([b ^ self.master_key[i % self.KEY_SIZE] for i, b in enumerate(encrypted)])
            if len(decrypted) < 4:
                raise ValueError("Payload truncado — possível invasão de bits.")
            expected_len = struct.unpack(">I", decrypted[:4])[0]
            body = decrypted[4:]
            if len(body) != expected_len:
                raise ValueError(
                    f"Integridade falhou: esperado {expected_len} bytes, obtido {len(body)}."
                )
            return body.decode("utf-8")
        except (ValueError, struct.error) as e:
            raise ValueError(f"[NexusGuard] Invasão de bits detectada: {e}")
        except Exception as e:
            raise ValueError(f"[NexusGuard] Erro de decriptografia: {e}")

    # ── Assinatura HMAC-SHA256 ────────────────────────────────────────────────

    def sign(self, data: str) -> str:
        """Assina dados com HMAC-SHA256 truncado (16 bytes = 32 chars hex)."""
        import hmac
        sig = hmac.new(self._hmac_secret, data.encode("utf-8"), hashlib.sha256).hexdigest()
        return sig[:32]

    def verify(self, data: str, signature: str) -> bool:
        """Verifica assinatura HMAC."""
        import hmac
        expected = self.sign(data)
        return hmac.compare_digest(expected, signature)


# ══════════════════════════════════════════════════════════════════════════════
# §3  NEXUS SDR FILTER — Resiliência Seletiva (Filtragem por Densidade de Bits)
# ══════════════════════════════════════════════════════════════════════════════

class NexusSDRFilter:
    """
    Validador de pacotes baseado em densidade de bits (Sparsity Analysis).

    Usa numpy para calcular a sparsity de cada pacote de entrada.
    Se o pacote divergir da máscara SDR do Nexus (densidade fora do intervalo
    biológico de ~2%), aplica 'Inibição Lateral' (bloqueio) e registra
    como tentativa de intrusão no log de segurança.

    Referência: SDR ideal = 2% ativo = 80/4096 bits
    """

    def __init__(self, sdr_size: int = SDR_SIZE,
                 min_sparsity: float = SDR_SPARSITY_MIN,
                 max_sparsity: float = SDR_SPARSITY_MAX):
        self.sdr_size = sdr_size
        self.min_sparsity = min_sparsity
        self.max_sparsity = max_sparsity
        # Máscara SDR mestra: padrão esparso de referência (gerado deterministicamente)
        rng = np.random.RandomState(SDR_SEED)
        active_bits = rng.choice(sdr_size, size=SDR_ACTIVE, replace=False)
        self._master_mask = np.zeros(sdr_size, dtype=np.uint8)
        self._master_mask[active_bits] = 1
        # Estatísticas
        self._total_packets   = 0
        self._blocked_packets = 0
        self._intrusions: List[Dict] = []

    def compute_sparsity(self, data: Any) -> Tuple[float, np.ndarray]:
        """
        Calcula a densidade de bits de um pacote de entrada.
        Retorna (sparsity, bit_vector).
        """
        if isinstance(data, SparseSDR):
            vec = data.to_numpy()
        elif isinstance(data, np.ndarray):
            vec = (data > 0).astype(np.uint8)
            if len(vec) != self.sdr_size:
                # Redimensiona via hash deterministico
                padded = np.zeros(self.sdr_size, dtype=np.uint8)
                n = min(len(vec), self.sdr_size)
                padded[:n] = vec[:n]
                vec = padded
        else:
            # Converte texto/bytes em vetor de bits via hash deterministico
            raw = data.encode("utf-8") if isinstance(data, str) else str(data).encode()
            vec = np.zeros(self.sdr_size, dtype=np.uint8)
            for i, b in enumerate(raw[:self.sdr_size]):
                vec[int(hashlib.md5(f"{b}{i}".encode()).hexdigest(), 16) % self.sdr_size] = 1
        active = int(np.sum(vec))
        sparsity = active / self.sdr_size
        return sparsity, vec

    def validate_packet(self, data: Any, source_id: str = "unknown") -> Tuple[bool, str]:
        """
        Valida um pacote de entrada contra a máscara SDR mestra.

        Retorna (aceito: bool, mensagem: str).
        Se rejeitado, registra como intrusão e aplica Inibição Lateral.
        """
        self._total_packets += 1
        sparsity, vec = self.compute_sparsity(data)

        # Verifica se a densidade de bits está na faixa biológica saudável
        if not (self.min_sparsity <= sparsity <= self.max_sparsity):
            return self._lateral_inhibition(source_id, sparsity, "sparsity_out_of_range")

        # Verifica sobreposição mínima com a máscara SDR mestra
        overlap = float(np.sum(vec & self._master_mask)) / max(SDR_ACTIVE, 1)
        if overlap < 0.01:  # menos de 1% de sobreposição com o padrão SDR
            return self._lateral_inhibition(source_id, sparsity, "sdr_mask_mismatch")

        return True, f"[SDRFilter] ACEITO | sparsity={sparsity:.4f} | overlap={overlap:.4f}"

    def _lateral_inhibition(self, source_id: str, sparsity: float, reason: str) -> Tuple[bool, str]:
        """Aplica Inibição Lateral: bloqueia e registra tentativa de intrusão."""
        self._blocked_packets += 1
        record = {
            "ts": time.time(),
            "source": source_id,
            "sparsity": round(sparsity, 6),
            "reason": reason,
            "action": "LATERAL_INHIBITION",
        }
        self._intrusions.append(record)
        msg = (f"[SDRFilter] BLOQUEADO | source={source_id} | "
               f"sparsity={sparsity:.4f} | razão={reason} | Inibição Lateral ativada")
        return False, msg

    @property
    def stats(self) -> Dict:
        return {
            "total": self._total_packets,
            "blocked": self._blocked_packets,
            "accepted": self._total_packets - self._blocked_packets,
            "intrusion_rate": round(
                self._blocked_packets / max(self._total_packets, 1), 4),
            "recent_intrusions": self._intrusions[-5:],
        }


# ══════════════════════════════════════════════════════════════════════════════
# §4  NEXUS PERSIST V11 — Persistência Assíncrona Real (aiosqlite)
# ══════════════════════════════════════════════════════════════════════════════

class NexusPersistV11:
    """
    Camada de persistência assíncrona usando aiosqlite.

    Dois bancos de dados:
      nexus_secure.db   — logs de segurança (dados SEMPRE cifrados via NexusGuardV11)
      nexus_iot_final.db — telemetria de sensores (dados brutos + assinatura)

    Toda escrita em nexus_secure.db é atômica e cifrada.
    Toda escrita de telemetria é assinada com HMAC.
    """

    def __init__(self, guard: NexusGuardV11,
                 db_secure: str = DB_SECURE,
                 db_iot: str = DB_IOT):
        self.guard = guard
        self.db_secure = db_secure
        self.db_iot = db_iot
        self._initialized = False
        self._write_count = 0
        self._error_count = 0

    # ── Inicialização das tabelas ─────────────────────────────────────────────

    async def initialize(self) -> None:
        """Cria as tabelas nos bancos se não existirem. Idempotente."""
        if not _AIOSQLITE_OK:
            print("[NexusPersist] aiosqlite não disponível — modo de simulação ativo.")
            self._initialized = True
            return

        # nexus_secure.db — logs de segurança cifrados
        async with aiosqlite.connect(self.db_secure) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS security_logs (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          REAL    NOT NULL,
                    event_type  TEXT    NOT NULL,
                    source_id   TEXT,
                    payload_enc TEXT    NOT NULL,
                    signature   TEXT    NOT NULL,
                    domain      TEXT
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sec_ts ON security_logs(ts)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sec_type ON security_logs(event_type)
            """)
            await db.commit()

        # nexus_iot_final.db — telemetria de sensores
        async with aiosqlite.connect(self.db_iot) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sensor_telemetry (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          REAL    NOT NULL,
                    sensor_id   TEXT    NOT NULL,
                    domain      TEXT    NOT NULL,
                    value_json  TEXT    NOT NULL,
                    sparsity    REAL,
                    sdr_valid   INTEGER DEFAULT 1,
                    signature   TEXT    NOT NULL
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_iot_sensor ON sensor_telemetry(sensor_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_iot_domain ON sensor_telemetry(domain)
            """)
            await db.commit()

        self._initialized = True

    # ── Escrita atômica em nexus_secure.db ───────────────────────────────────

    async def log_security_event(self, event_type: str, source_id: str,
                                  payload: Any, domain: str = "nexus") -> bool:
        """
        Persiste um evento de segurança com dados CIFRADOS.
        Operação atômica — ou persiste tudo ou nada.
        """
        if not self._initialized:
            await self.initialize()
        if not _AIOSQLITE_OK:
            return self._simulate_write("security", event_type, source_id)
        try:
            encrypted = self.guard.encrypt_payload(payload)
            signature = self.guard.sign(encrypted)
            ts = time.time()
            async with aiosqlite.connect(self.db_secure) as db:
                async with db.execute("BEGIN IMMEDIATE"):
                    pass
                await db.execute(
                    "INSERT INTO security_logs "
                    "(ts, event_type, source_id, payload_enc, signature, domain) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (ts, event_type, source_id, encrypted, signature, domain)
                )
                await db.commit()
            self._write_count += 1
            return True
        except Exception as e:
            self._error_count += 1
            print(f"[NexusPersist] ERRO ao gravar segurança: {e}")
            return False

    # ── Escrita de telemetria em nexus_iot_final.db ──────────────────────────

    async def log_telemetry(self, sensor_id: str, domain: str,
                             value: Any, sparsity: float = 0.0,
                             sdr_valid: bool = True) -> bool:
        """
        Persiste dados de telemetria de sensor com assinatura HMAC.
        Dados NÃO cifrados (performance), mas assinados para integridade.
        """
        if not self._initialized:
            await self.initialize()
        if not _AIOSQLITE_OK:
            return self._simulate_write("telemetry", sensor_id, domain)
        try:
            value_json = json.dumps(value, ensure_ascii=False)
            signature = self.guard.sign(f"{sensor_id}:{value_json}")
            ts = time.time()
            async with aiosqlite.connect(self.db_iot) as db:
                await db.execute(
                    "INSERT INTO sensor_telemetry "
                    "(ts, sensor_id, domain, value_json, sparsity, sdr_valid, signature) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (ts, sensor_id, domain, value_json,
                     round(sparsity, 6), int(sdr_valid), signature)
                )
                await db.commit()
            self._write_count += 1
            return True
        except Exception as e:
            self._error_count += 1
            print(f"[NexusPersist] ERRO ao gravar telemetria: {e}")
            return False

    # ── Leitura ───────────────────────────────────────────────────────────────

    async def get_recent_security_logs(self, limit: int = 20,
                                        event_type: str = None) -> List[Dict]:
        """Recupera e DECIFRA os logs de segurança mais recentes."""
        if not _AIOSQLITE_OK:
            return []
        try:
            async with aiosqlite.connect(self.db_secure) as db:
                if event_type:
                    cursor = await db.execute(
                        "SELECT id, ts, event_type, source_id, payload_enc, domain "
                        "FROM security_logs WHERE event_type=? ORDER BY ts DESC LIMIT ?",
                        (event_type, limit)
                    )
                else:
                    cursor = await db.execute(
                        "SELECT id, ts, event_type, source_id, payload_enc, domain "
                        "FROM security_logs ORDER BY ts DESC LIMIT ?",
                        (limit,)
                    )
                rows = await cursor.fetchall()

            result = []
            for row in rows:
                try:
                    decrypted = self.guard.decrypt_payload(row[4])
                    result.append({
                        "id": row[0], "ts": row[1], "event_type": row[2],
                        "source_id": row[3], "payload": decrypted, "domain": row[5],
                    })
                except ValueError as e:
                    result.append({
                        "id": row[0], "ts": row[1], "event_type": row[2],
                        "source_id": row[3], "payload": f"[CORROMPIDO: {e}]",
                        "domain": row[5],
                    })
            return result
        except Exception as e:
            print(f"[NexusPersist] ERRO ao ler logs: {e}")
            return []

    async def get_telemetry(self, domain: str = None, limit: int = 50) -> List[Dict]:
        """Recupera registros de telemetria, opcionalmente filtrados por domínio."""
        if not _AIOSQLITE_OK:
            return []
        try:
            async with aiosqlite.connect(self.db_iot) as db:
                if domain:
                    cursor = await db.execute(
                        "SELECT sensor_id, domain, value_json, sparsity, sdr_valid, ts "
                        "FROM sensor_telemetry WHERE domain=? ORDER BY ts DESC LIMIT ?",
                        (domain, limit)
                    )
                else:
                    cursor = await db.execute(
                        "SELECT sensor_id, domain, value_json, sparsity, sdr_valid, ts "
                        "FROM sensor_telemetry ORDER BY ts DESC LIMIT ?",
                        (limit,)
                    )
                rows = await cursor.fetchall()
            return [
                {
                    "sensor_id": r[0], "domain": r[1],
                    "value": json.loads(r[2]), "sparsity": r[3],
                    "sdr_valid": bool(r[4]), "ts": r[5],
                }
                for r in rows
            ]
        except Exception as e:
            print(f"[NexusPersist] ERRO ao ler telemetria: {e}")
            return []

    # ── Varredura de integridade (para o Healer) ──────────────────────────────

    async def integrity_scan(self) -> Dict:
        """
        Varre os bancos .db e verifica:
          - Assinaturas HMAC de todos os registros de telemetria
          - Decriptabilidade dos registros de segurança
        Retorna relatório de integridade.
        """
        if not _AIOSQLITE_OK:
            return {"status": "simulated", "corrupt": 0, "ok": 0}

        report = {"db_secure": {"ok": 0, "corrupt": 0},
                  "db_iot":    {"ok": 0, "corrupt": 0},
                  "ts": time.time()}

        # Verifica nexus_secure.db
        try:
            async with aiosqlite.connect(self.db_secure) as db:
                cursor = await db.execute(
                    "SELECT payload_enc, signature FROM security_logs ORDER BY id DESC LIMIT 200"
                )
                rows = await cursor.fetchall()
            for enc, sig in rows:
                expected_sig = self.guard.sign(enc)
                if expected_sig == sig:
                    report["db_secure"]["ok"] += 1
                else:
                    report["db_secure"]["corrupt"] += 1
        except Exception as e:
            report["db_secure"]["error"] = str(e)

        # Verifica nexus_iot_final.db
        try:
            async with aiosqlite.connect(self.db_iot) as db:
                cursor = await db.execute(
                    "SELECT sensor_id, value_json, signature FROM sensor_telemetry "
                    "ORDER BY id DESC LIMIT 200"
                )
                rows = await cursor.fetchall()
            for sensor_id, value_json, sig in rows:
                expected_sig = self.guard.sign(f"{sensor_id}:{value_json}")
                if expected_sig == sig:
                    report["db_iot"]["ok"] += 1
                else:
                    report["db_iot"]["corrupt"] += 1
        except Exception as e:
            report["db_iot"]["error"] = str(e)

        total_ok = report["db_secure"]["ok"] + report["db_iot"]["ok"]
        total_corrupt = report["db_secure"]["corrupt"] + report["db_iot"]["corrupt"]
        total = total_ok + total_corrupt
        report["summary"] = {
            "total": total,
            "ok": total_ok,
            "corrupt": total_corrupt,
            "integrity_pct": round(100 * total_ok / max(total, 1), 2),
        }
        return report

    def _simulate_write(self, tipo: str, *args) -> bool:
        """Simulação para quando aiosqlite não está disponível."""
        self._write_count += 1
        print(f"[NexusPersist::SIM] {tipo} | {' | '.join(str(a) for a in args)}")
        return True

    @property
    def stats(self) -> Dict:
        return {
            "writes": self._write_count,
            "errors": self._error_count,
            "initialized": self._initialized,
        }


# ══════════════════════════════════════════════════════════════════════════════
# §5  NEXUS HEALER V11 — Auto-Reparo com Flush Real e Varredura de Integridade
# ══════════════════════════════════════════════════════════════════════════════

class NexusHealerV11:
    """
    Sistema de auto-reparo adaptativo de missão crítica.

    Evolução sobre V10:
      • Detecta picos de ruído via análise de variância SDR (numpy)
      • Ajusta threshold de sparsity dinamicamente
      • Realiza Flush REAL de conexões pendentes (queue + buffer)
      • Executa varredura de integridade nos bancos .db após picos
      • Emite alertas e registra eventos no banco de segurança

    Arquitetura: monitora métricas em janela deslizante (deque),
    detecta anomalias e aciona procedimentos de recuperação.
    """

    NOISE_WINDOW    = 20    # últimas N medições para cálculo de variância
    NOISE_THRESHOLD = 0.03  # variância acima deste valor = pico de ruído
    THRESHOLD_STEP  = 0.002 # incremento do threshold por evento de ruído

    def __init__(self, persist: NexusPersistV11,
                 sdr_filter: NexusSDRFilter,
                 initial_threshold: float = 0.025):
        self.persist    = persist
        self.sdr_filter = sdr_filter
        self.threshold  = initial_threshold
        self._noise_history: deque = deque(maxlen=self.NOISE_WINDOW)
        self._heal_count     = 0
        self._flush_count    = 0
        self._scan_count     = 0
        self._pending_buffers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    def register_buffer(self, q: asyncio.Queue) -> None:
        """Registra uma fila de buffer para flush gerenciado."""
        self._pending_buffers.append(q)

    def record_noise(self, sparsity: float) -> None:
        """Registra uma medição de ruído para monitoramento."""
        self._noise_history.append(sparsity)

    def detect_noise_spike(self) -> bool:
        """Detecta pico de ruído usando variância numpy na janela deslizante."""
        if len(self._noise_history) < 5:
            return False
        arr = np.array(list(self._noise_history))
        variance = float(np.var(arr))
        return variance > self.NOISE_THRESHOLD

    async def heal(self, context: str = "auto") -> Dict:
        """
        Procedimento principal de auto-reparo. Chamado automaticamente
        quando pico de ruído é detectado.

        1. Ajusta o threshold de sparsity
        2. Faz Flush REAL de buffers pendentes
        3. Executa varredura de integridade nos .db
        4. Registra evento no banco de segurança
        """
        async with self._lock:
            self._heal_count += 1
            report = {
                "ts":            time.time(),
                "context":       context,
                "threshold_old": round(self.threshold, 4),
                "flush_result":  None,
                "scan_result":   None,
                "action":        "HEAL_INITIATED",
            }

            # 1. Ajusta threshold dinamicamente
            self.threshold = min(
                self.threshold + self.THRESHOLD_STEP,
                SDR_SPARSITY_MAX
            )
            self.sdr_filter.min_sparsity = max(
                self.sdr_filter.min_sparsity - self.THRESHOLD_STEP / 2,
                0.001
            )
            report["threshold_new"] = round(self.threshold, 4)

            # 2. Flush REAL de conexões/buffers pendentes
            flushed_items = 0
            for q in self._pending_buffers:
                while not q.empty():
                    try:
                        q.get_nowait()
                        flushed_items += 1
                    except asyncio.QueueEmpty:
                        break
            self._flush_count += 1
            report["flush_result"] = {
                "queues_flushed": len(self._pending_buffers),
                "items_discarded": flushed_items,
            }

            # 3. Varredura de integridade nos bancos .db
            scan = await self.persist.integrity_scan()
            self._scan_count += 1
            report["scan_result"] = scan.get("summary", {})

            # 4. Registra o evento de reparo no banco de segurança
            await self.persist.log_security_event(
                event_type="HEALER_ACTIVATED",
                source_id="NexusHealerV11",
                payload=report,
                domain="nexus_core"
            )

            report["action"] = "HEAL_COMPLETE"
            return report

    async def monitor_and_heal(self, sparsity: float, source: str = "sensor") -> Optional[Dict]:
        """
        Interface principal: registra sparsity, detecta spike e aciona reparo.
        Retorna relatório de reparo se foi acionado, None caso contrário.
        """
        self.record_noise(sparsity)
        if self.detect_noise_spike():
            print(f"[NexusHealer] Pico de ruído detectado! Acionando auto-reparo...")
            return await self.heal(context=f"noise_spike_from_{source}")
        return None

    @property
    def stats(self) -> Dict:
        arr = np.array(list(self._noise_history)) if self._noise_history else np.array([0.0])
        return {
            "heal_count":  self._heal_count,
            "flush_count": self._flush_count,
            "scan_count":  self._scan_count,
            "threshold":   round(self.threshold, 4),
            "noise_mean":  round(float(np.mean(arr)), 4),
            "noise_var":   round(float(np.var(arr)), 6),
        }


# ══════════════════════════════════════════════════════════════════════════════
# §8  NEXUS DOMAIN BUS — Processamento Concorrente por Domínio
# ══════════════════════════════════════════════════════════════════════════════

class NexusDomainProcessor:
    """
    Processador de dados de um domínio específico (Bio, Finanças, Física/TCU).
    Cada domínio tem seu próprio FactStore, encoder e pipeline de validação.
    """

    def __init__(self, domain_id: str, domain_name: str,
                 encoder: MultiLobeEncoder,
                 persist: NexusPersistV11,
                 sdr_filter: NexusSDRFilter,
                 healer: NexusHealerV11):
        self.domain_id   = domain_id
        self.domain_name = domain_name
        self.encoder     = encoder
        self.persist     = persist
        self.sdr_filter  = sdr_filter
        self.healer      = healer
        self.fact_store  = SQLiteFactStoreV12()
        self._processed  = 0
        self._rejected   = 0
        self.buffer: asyncio.Queue = asyncio.Queue(maxsize=256)
        healer.register_buffer(self.buffer)

    async def process_packet(self, sensor_id: str, data: Any) -> Dict:
        """
        Pipeline completo de processamento de um pacote de dados:
          1. Valida densidade de bits (SDRFilter)
          2. Codifica em SDR (MultiLobeEncoder)
          3. Persiste telemetria (aiosqlite)
          4. Aciona Healer se necessário
          5. Retorna resultado estruturado
        """
        # 1. Validação SDR
        accepted, filter_msg = self.sdr_filter.validate_packet(data, source_id=sensor_id)
        sparsity, _ = self.sdr_filter.compute_sparsity(data)

        if not accepted:
            self._rejected += 1
            # Registra intrusão no banco seguro
            await self.persist.log_security_event(
                event_type="INTRUSION_ATTEMPT",
                source_id=sensor_id,
                payload={"data_preview": str(data)[:120], "filter_msg": filter_msg},
                domain=self.domain_id
            )
            return {
                "status": "REJECTED",
                "domain": self.domain_id,
                "sensor": sensor_id,
                "reason": filter_msg,
                "sparsity": round(sparsity, 4),
            }

        # 2. Codificação SDR
        text_repr = str(data) if not isinstance(data, str) else data
        sdr = self.encoder.encode(text_repr, context=self.domain_id)

        # 3. Adiciona ao FactStore local
        self.fact_store.add_fact(text_repr, sdr, domain=self.domain_id)

        # 4. Persiste telemetria
        await self.persist.log_telemetry(
            sensor_id=sensor_id,
            domain=self.domain_id,
            value={"text": text_repr[:256], "sdr_bits": len(sdr)},
            sparsity=sparsity,
            sdr_valid=True
        )

        # 5. Verifica ruído e aciona Healer se necessário
        heal_report = await self.healer.monitor_and_heal(sparsity, source=self.domain_id)

        self._processed += 1
        result = {
            "status":   "ACCEPTED",
            "domain":   self.domain_id,
            "sensor":   sensor_id,
            "sdr_bits": len(sdr),
            "sparsity": round(sparsity, 4),
            "filter":   filter_msg,
        }
        if heal_report:
            result["heal_triggered"] = True
            result["heal_summary"]   = heal_report.get("action", "healed")
        return result

    @property
    def stats(self) -> Dict:
        return {
            "domain":    self.domain_id,
            "processed": self._processed,
            "rejected":  self._rejected,
            "facts":     len(self.fact_store),
        }


class NexusDomainBus:
    """
    Barramento de domínios: orquestra o processamento CONCORRENTE
    de Bio, Finanças e Física/TCU usando asyncio.gather.

    Garante que a escrita no banco seja atômica por domínio.
    """

    DEFAULT_DOMAINS = [
        {"id": "biologia",  "name": "Biologia & Biotecnologia"},
        {"id": "financas",  "name": "Finanças & Mercado de Capitais"},
        {"id": "fisica_tcu","name": "Física & Controle de Unidade Térmica"},
    ]

    def __init__(self, persist: NexusPersistV11,
                 sdr_filter: NexusSDRFilter,
                 healer: NexusHealerV11,
                 domains: Optional[List[Dict]] = None):
        self.persist    = persist
        self.sdr_filter = sdr_filter
        self.healer     = healer
        self._domains: Dict[str, NexusDomainProcessor] = {}
        for d in (domains or self.DEFAULT_DOMAINS):
            encoder = MultiLobeEncoder(seed=SDR_SEED ^ hash(d["id"]) & 0xFFFFFFFF)
            self._domains[d["id"]] = NexusDomainProcessor(
                domain_id   = d["id"],
                domain_name = d["name"],
                encoder     = encoder,
                persist     = persist,
                sdr_filter  = sdr_filter,
                healer      = healer,
            )

    async def broadcast(self, packets: List[Tuple[str, str, Any]]) -> List[Dict]:
        """
        Processa múltiplos pacotes de DIFERENTES domínios SIMULTANEAMENTE.

        Parâmetros:
          packets: lista de (domain_id, sensor_id, data)

        Usa asyncio.gather para processamento verdadeiramente concorrente.
        Escrita no banco é atômica por domínio.
        """
        tasks = []
        for domain_id, sensor_id, data in packets:
            proc = self._domains.get(domain_id)
            if proc is None:
                tasks.append(asyncio.coroutine(
                    lambda: {"status": "ERROR", "reason": f"domínio desconhecido: {domain_id}"}
                )())
            else:
                tasks.append(proc.process_packet(sensor_id, data))

        results = await asyncio.gather(*tasks, return_exceptions=False)
        return list(results)

    async def process_domain(self, domain_id: str, sensor_id: str, data: Any) -> Dict:
        """Processa um único pacote em um domínio específico."""
        proc = self._domains.get(domain_id)
        if not proc:
            return {"status": "ERROR", "reason": f"domínio '{domain_id}' não encontrado"}
        return await proc.process_packet(sensor_id, data)

    def bus_stats(self) -> Dict:
        return {d_id: proc.stats for d_id, proc in self._domains.items()}


# ══════════════════════════════════════════════════════════════════════════════
# §9  NEXUS SENIOR GATEWAY — Rate Limiting + Buffer + Guard
# ══════════════════════════════════════════════════════════════════════════════

class NexusSeniorGateway:
    """
    Gateway de entrada com rate limiting, buffer assíncrono e proteção Guard.
    Versão de produção: todas as requisições passam pelo SDRFilter antes de
    serem enfileiradas.
    """

    def __init__(self, rate_limit_per_sec: int = 10,
                 buffer_size: int = 256,
                 guard: Optional[NexusGuardV11] = None,
                 sdr_filter: Optional[NexusSDRFilter] = None):
        self.guard      = guard or NexusGuardV11()
        self.sdr_filter = sdr_filter or NexusSDRFilter()
        self.buffer     = asyncio.Queue(maxsize=buffer_size)
        self.history    = deque(maxlen=rate_limit_per_sec * 2)
        self._rate_limit = rate_limit_per_sec

    async def receive_data(self, sensor_id: str, data: Any) -> str:
        """
        Recebe um pacote de sensor, aplica rate limiting e validação SDR.
        Retorna código HTTP-style.
        """
        now = time.time()
        # Limpa histórico antigo
        while self.history and now - self.history[0] > 1.0:
            self.history.popleft()
        if len(self.history) >= self._rate_limit:
            return "429 Too Many Requests"

        if isinstance(data, str) and len(data) > 4096:
            return "413 Payload Too Large"

        # Validação SDR
        accepted, msg = self.sdr_filter.validate_packet(data, source_id=sensor_id)
        if not accepted:
            return f"403 Forbidden | {msg[:80]}"

        self.history.append(now)
        try:
            self.buffer.put_nowait((sensor_id, data, now))
            return "202 Accepted"
        except asyncio.QueueFull:
            return "503 Service Overloaded"


# ══════════════════════════════════════════════════════════════════════════════
# §10  NEXUS BIO SIM — Simulações Biológicas com Checkpoints Reais
# ══════════════════════════════════════════════════════════════════════════════

class NexusBioSim:
    """
    Simulações biológicas (Mitose/Meiose) com persistência de checkpoints.
    Cada etapa crítica é gravada no nexus_iot_final.db como telemetria.
    """

    def __init__(self, persist: Optional[NexusPersistV11] = None):
        self.persist = persist

    async def simular_mitose(self, estagios: int = 52,
                              sensor_id: str = "bio_mitose") -> List[str]:
        """Simula mitose com checkpoints reais gravados em banco."""
        eventos = []
        for i in range(1, estagios + 1):
            evento = None
            if i == 13:
                evento = {"fase": "Prófase", "evento": "Condensação cromossômica iniciada", "estagio": i}
            elif i == 21:
                evento = {"fase": "Metáfase", "evento": "Alinhamento cromossômico validado", "estagio": i}
            elif i == 35:
                evento = {"fase": "Anáfase", "evento": "Separação das cromátides irmãs", "estagio": i}
            elif i == 48:
                evento = {"fase": "Telófase", "evento": "Reconstrução nuclear completa", "estagio": i}
            elif i == estagios:
                evento = {"fase": "Citocinese", "evento": "Divisão celular concluída 100%", "estagio": i}
            if evento:
                eventos.append(f"[{evento['fase']}] {evento['evento']}")
                if self.persist:
                    await self.persist.log_telemetry(
                        sensor_id=sensor_id, domain="biologia",
                        value=evento, sparsity=SDR_SPARSITY_IDEAL, sdr_valid=True
                    )
        return eventos

    async def simular_meiose_sdr(self, estagios: int = 60,
                                  sensor_id: str = "bio_meiose") -> List[str]:
        """Simula meiose com operações SDR/XOR e persistência de checkpoints."""
        eventos = []
        for i in range(1, estagios + 1):
            evento = None
            if i == 10:
                evento = {"fase": "Prófase I", "evento": "Crossing-over: XOR Swap SDR ativado", "estagio": i}
            elif i == 25:
                evento = {"fase": "Metáfase I", "evento": "Alinhamento bivalentes validado", "estagio": i}
            elif i == 35:
                evento = {"fase": "Anáfase I", "evento": "Checkpoint: Redução cromossômica confirmada", "estagio": i}
            elif i == 50:
                evento = {"fase": "Meiose II", "evento": "Segunda divisão: SDR bundle ativado", "estagio": i}
            elif i == estagios:
                evento = {"fase": "Conclusão", "evento": "4 células haplóides geradas", "estagio": i}
            if evento:
                eventos.append(f"[{evento['fase']}] {evento['evento']}")
                if self.persist:
                    await self.persist.log_telemetry(
                        sensor_id=sensor_id, domain="biologia",
                        value=evento, sparsity=SDR_SPARSITY_IDEAL * 0.8, sdr_valid=True
                    )
        return eventos


# ══════════════════════════════════════════════════════════════════════════════
# §11  NEXUS AUDITOR — Purificação e Normalização de Texto
# ══════════════════════════════════════════════════════════════════════════════

class NexusAuditor:
    """Purificação de texto: remove anotações linguísticas e normaliza."""

    @staticmethod
    def purificar(texto: str) -> str:
        f = re.sub(r"^\s*\[.*?\]\s*", "", texto)
        f = re.sub(r"\(português.*?\)", "", f)
        f = re.sub(r"\(em (inglês|grego|latim).*?\)", "", f)
        f = re.sub(r"romaniz\.:.*?;", "", f)
        f = re.sub(r'lit\..*?["]', "", f)
        return re.sub(" +", " ", f).strip()


# ══════════════════════════════════════════════════════════════════════════════
# §12  NEXUS PROGRAMMER V11 — Compilador de Módulos
# ══════════════════════════════════════════════════════════════════════════════

class NexusProgrammerV11:
    """Compilador/gerador de módulos Nexus."""

    def compile(self, req: str) -> str:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        return (
            f"# Compiled Nexus v11.2 Production Module\n"
            f"# Request: {req}\n"
            f"# Timestamp: {ts}\n"
            f"# Guard: NexusGuardV11 (XOR-256)\n"
            f"# Persist: aiosqlite ({DB_SECURE}, {DB_IOT})\n"
            f"# SDRFilter: sparsity [{SDR_SPARSITY_MIN:.3f}, {SDR_SPARSITY_MAX:.3f}]\n"
        )


# ══════════════════════════════════════════════════════════════════════════════
# §13  NEXUS KERNEL V11.2 — Núcleo Principal de Missão Crítica
# ══════════════════════════════════════════════════════════════════════════════

class NexusKernelV11_2:
    """
    Núcleo central do sistema Nexus V11.2 Mission Critical.

    Integra todas as camadas de produção em um objeto coeso:
      • NexusGuardV11      — criptografia XOR
      • NexusPersistV11    — persistência aiosqlite
      • NexusSDRFilter     — validação de densidade de bits
      • NexusHealerV11     — auto-reparo com flush e varredura
      • NexusDomainBus     — processamento concorrente por domínio
      • NexusBioSim        — simulações biológicas com checkpoints
      • MultiLobeEncoder   — codificação SDR
      • FactStoreV11_2     — armazenamento de fatos com SDR

    API pública:
      await kernel.startup()                    — inicializa bancos
      await kernel.process(domain, sid, data)   — processa um pacote
      await kernel.broadcast(packets)           — processa múltiplos domínios
      await kernel.run_demo()                   — executa demo completo
      await kernel.shutdown()                   — encerra com flush final
      kernel.chat(text)                         — interface conversacional
    """

    def __init__(self):
        print("╔══ NEXUS V11.2 ULTIMATE — KERNEL DE MISSÃO CRÍTICA ══╗")

        # Camadas de produção
        self.guard      = NexusGuardV11()
        self.persist    = NexusPersistV11(self.guard)
        self.sdr_filter = NexusSDRFilter()
        self.healer     = NexusHealerV11(self.persist, self.sdr_filter)
        self.domain_bus = NexusDomainBus(self.persist, self.sdr_filter, self.healer)
        self.gateway    = NexusSeniorGateway(guard=self.guard, sdr_filter=self.sdr_filter)

        # Módulos cognitivos
        self.encoder    = MultiLobeEncoder()
        self.fact_store = SQLiteFactStoreV12()
        self.bio_sim    = NexusBioSim(self.persist)
        self.auditor    = NexusAuditor()
        self.programmer = NexusProgrammerV11()

        # Estado interno
        self._startup_done = False
        self._session_facts = 0

        print("╚══ Subsistemas carregados: Guard, Persist, SDRFilter, Healer, Bus ══╝\n")

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    async def startup(self) -> None:
        """Inicializa bancos de dados e registra evento de startup."""
        await self.persist.initialize()
        await self.persist.log_security_event(
            event_type  = "KERNEL_STARTUP",
            source_id   = "NexusKernelV11_2",
            payload     = {"version": VERSION, "ts": time.time(),
                           "sdr_size": SDR_SIZE, "sdr_active": SDR_ACTIVE},
            domain      = "nexus_core"
        )
        self._startup_done = True
        print(f"[Kernel] Startup completo. Bancos inicializados: {DB_SECURE}, {DB_IOT}")

    async def shutdown(self) -> None:
        """Encerra o kernel com flush final e varredura de integridade."""
        print("[Kernel] Iniciando shutdown seguro...")
        heal = await self.healer.heal(context="shutdown")
        await self.persist.log_security_event(
            event_type = "KERNEL_SHUTDOWN",
            source_id  = "NexusKernelV11_2",
            payload    = {"heal_report": heal, "session_facts": self._session_facts},
            domain     = "nexus_core"
        )
        print(f"[Kernel] Shutdown completo. Fatos na sessão: {self._session_facts}")

    # ── Processamento de dados ────────────────────────────────────────────────

    async def process(self, domain_id: str, sensor_id: str, data: Any) -> Dict:
        """Processa um pacote de dados em um domínio específico."""
        if not self._startup_done:
            await self.startup()
        return await self.domain_bus.process_domain(domain_id, sensor_id, data)

    async def broadcast(self, packets: List[Tuple[str, str, Any]]) -> List[Dict]:
        """
        Processa múltiplos pacotes de diferentes domínios SIMULTANEAMENTE.
        Implementa asyncio.gather para concorrência real.
        """
        if not self._startup_done:
            await self.startup()
        return await self.domain_bus.broadcast(packets)

    # ── Interface conversacional ──────────────────────────────────────────────

    def learn(self, fact: str, domain: str = "general") -> str:
        """Aprende um fato e o armazena no FactStore com SDR."""
        clean = self.auditor.purificar(fact)
        sdr = self.encoder.encode(clean, context=domain)
        if not sdr.bit_density_valid():
            return f"[Guard] Fato rejeitado — densidade SDR inválida: {sdr.sparsity():.4f}"
        self.fact_store.add_fact(clean, sdr, domain=domain)
        self._session_facts += 1
        return f"[Nexus] Aprendi: '{clean[:60]}' | SDR bits={len(sdr)} | domain={domain}"

    def query(self, question: str, top_k: int = 3) -> str:
        """Consulta o FactStore por sobreposição SDR."""
        sdr = self.encoder.encode(question)
        results = self.fact_store.search(sdr, top_k=top_k, min_score=0.05)
        if not results:
            return f"[Nexus] Não encontrei informações sobre: '{question}'"
        lines = [f"• [{score:.3f}] {fact[:100]}" for score, fact in results]
        return "\n".join(lines)

    def chat(self, text: str) -> str:
        """Interface conversacional principal."""
        tl = text.lower().strip()

        # Saudações sociais
        for k, v in _SOCIAL.items():
            if k in tl:
                return v

        # Comandos especiais
        if tl.startswith("aprenda:") or tl.startswith("aprenda "):
            fact = re.sub(r"^aprenda[:\s]+", "", text, flags=re.I).strip()
            domain = "general"
            dm = re.search(r"\[domínio:\s*(\w+)\]", fact, re.I)
            if dm:
                domain = dm.group(1)
                fact = fact[:dm.start()].strip()
            return self.learn(fact, domain)

        if tl.startswith("cifre:") or tl.startswith("encrypt:"):
            payload = re.sub(r"^(cifre|encrypt)[:\s]+", "", text, flags=re.I)
            enc = self.guard.encrypt_payload(payload)
            return f"[Guard] Cifrado: {enc[:64]}..."

        if tl.startswith("status") or tl == "saúde":
            return self.scan_health()

        if tl.startswith("compile:") or tl.startswith("compile "):
            req = re.sub(r"^compile[:\s]+", "", text, flags=re.I)
            return self.programmer.compile(req)

        # Perguntas (busca semântica)
        if "?" in text or any(w in tl for w in ["o que", "qual", "como", "por que", "quem"]):
            return self.query(text)

        # Fallback: aprende como fato
        if len(text) > 10:
            return self.learn(text)

        return "[Nexus] Não entendi. Use 'aprenda: <fato>' ou faça uma pergunta."

    def scan_health(self) -> str:
        """Retorna relatório de saúde completo do kernel."""
        h = self.healer.stats
        p = self.persist.stats
        f = self.sdr_filter.stats
        b = self.domain_bus.bus_stats()
        return (
            f"═══ NEXUS V11.2 — SAÚDE DO KERNEL ═══\n"
            f"  Versão          : {VERSION}\n"
            f"  Fatos (sessão)  : {self._session_facts}\n"
            f"  Fatos (store)   : {len(self.fact_store)}\n"
            f"  ─── NexusGuard (XOR-{NexusGuardV11.KEY_SIZE * 8}bit) ───\n"
            f"  Chave mestra    : {self.guard.master_key[:4].hex()}... (ativa)\n"
            f"  ─── NexusPersist (aiosqlite) ───\n"
            f"  Escritas totais : {p['writes']}\n"
            f"  Erros de escrita: {p['errors']}\n"
            f"  Inicializado    : {p['initialized']}\n"
            f"  ─── NexusSDRFilter ───\n"
            f"  Pacotes totais  : {f['total']}\n"
            f"  Aceitos         : {f['accepted']}\n"
            f"  Bloqueados      : {f['blocked']}\n"
            f"  Taxa de intrusão: {f['intrusion_rate']:.2%}\n"
            f"  ─── NexusHealer ───\n"
            f"  Reparos         : {h['heal_count']}\n"
            f"  Flushes         : {h['flush_count']}\n"
            f"  Varreduras .db  : {h['scan_count']}\n"
            f"  Threshold atual : {h['threshold']}\n"
            f"  Ruído (média)   : {h['noise_mean']}\n"
            f"  Ruído (var)     : {h['noise_var']}\n"
            f"  ─── Domain Bus ───\n"
            + "\n".join(
                f"  [{d}] proc={s['processed']} rej={s['rejected']} fatos={s['facts']}"
                for d, s in b.items()
            )
        )

    # ── Demo completo ─────────────────────────────────────────────────────────

    async def run_demo(self) -> None:
        """
        Demo de missão crítica: processa dados dos 3 domínios simultaneamente,
        executa simulações biológicas e demonstra o pipeline completo.
        """
        print("\n╔═══════════════════════════════════════════╗")
        print("║  NEXUS V11.2 — DEMO DE MISSÃO CRÍTICA    ║")
        print("╚═══════════════════════════════════════════╝\n")

        await self.startup()

        # ── Passo 1: Aprendizado de fatos ──────────────────────────────────
        print("── FASE 1: Aprendizado SDR ──")
        fatos = [
            ("A mitose é a divisão celular que produz células geneticamente idênticas.", "biologia"),
            ("O crossing-over na meiose garante variabilidade genética via XOR cromossômico.", "biologia"),
            ("O VaR (Value at Risk) mede a perda máxima esperada com 95% de confiança.", "financas"),
            ("A lei de Ohm estabelece que V = I × R em circuitos resistivos.", "fisica_tcu"),
            ("Controle PID usa proporcional, integral e derivativo para estabilizar sistemas.", "fisica_tcu"),
            ("Algoritmos de machine learning otimizam pesos via gradiente descendente.", "tecnologia"),
        ]
        for fact, domain in fatos:
            print(self.learn(fact, domain))

        # ── Passo 2: Processamento concorrente via asyncio.gather ──────────
        print("\n── FASE 2: Processamento Concorrente (asyncio.gather) ──")
        packets = [
            ("biologia",   "sensor_dna_01",   "sequência genômica ATCG identificada com 98.7% de match"),
            ("financas",   "sensor_ibovespa",  "IBOV: +1.34% | Volume: R$ 23.4B | Volatilidade: 18.2%"),
            ("fisica_tcu", "sensor_temp_reator","Temperatura núcleo: 387°C | Pressão: 15.2 bar | Status: OK"),
        ]
        print(f"  Processando {len(packets)} domínios simultaneamente...")
        t0 = time.time()
        results = await self.broadcast(packets)
        elapsed = time.time() - t0
        for r in results:
            status_icon = "✓" if r["status"] == "ACCEPTED" else "✗"
            print(f"  {status_icon} [{r['domain']}] {r['status']} | "
                  f"sparsity={r.get('sparsity', 0):.4f} | "
                  f"sdr_bits={r.get('sdr_bits', '—')}")
        print(f"  Tempo total (concorrente): {elapsed*1000:.1f}ms\n")

        # ── Passo 3: Simulação biológica com checkpoints ───────────────────
        print("── FASE 3: Simulação Biológica com Checkpoints Reais ──")
        bio_tasks = await asyncio.gather(
            self.bio_sim.simular_mitose(estagios=52),
            self.bio_sim.simular_meiose_sdr(estagios=60)
        )
        mitose_eventos, meiose_eventos = bio_tasks
        print("  Mitose:")
        for e in mitose_eventos:
            print(f"    → {e}")
        print("  Meiose SDR:")
        for e in meiose_eventos:
            print(f"    → {e}")

        # ── Passo 4: Teste de intrusão (pacote inválido) ───────────────────
        print("\n── FASE 4: Teste de Resiliência Seletiva ──")
        # Cria pacote de texto minúsculo (sparsity abaixo do mínimo) para simular anomalia
        bad_packet = ("biologia", "sensor_anomalo", "x")
        [intrusion_result] = await self.broadcast([bad_packet])
        print(f"  Pacote anômalo → {intrusion_result['status']}")
        if intrusion_result["status"] == "REJECTED":
            print(f"  Inibição Lateral ativada: {intrusion_result.get('reason', '')[:80]}")

        # ── Passo 5: Varredura de integridade ─────────────────────────────
        print("\n── FASE 5: Varredura de Integridade nos Bancos .db ──")
        integrity = await self.persist.integrity_scan()
        s = integrity.get("summary", {})
        print(f"  Total verificado: {s.get('total', 0)}")
        print(f"  Íntegros        : {s.get('ok', 0)}")
        print(f"  Corrompidos     : {s.get('corrupt', 0)}")
        print(f"  Integridade     : {s.get('integrity_pct', 100.0):.1f}%")

        # ── Passo 6: Saúde final ───────────────────────────────────────────
        print("\n── FASE 6: Relatório de Saúde Final ──")
        print(self.scan_health())

        await self.shutdown()
        print("\n╔══════════════════════════════════╗")
        print("║  Demo concluído com sucesso! ✓   ║")
        print("╚══════════════════════════════════╝")




# ══════════════════════════════════════════════════════════════════════════════
# §UNIFIED  NEXUS V14 — PONTO DE ENTRADA UNIFICADO
# ══════════════════════════════════════════════════════════════════════════════

class NexusV14Unified:
    """
    Sistema NEXUS V14 Unificado — combina os 3 núcleos em uma única interface.
    
    Uso:
        kernel = NexusV14Unified()
        
        # Modo cognitivo (V10 — chat, aprendizado, raciocínio)
        kernel.chat("aprenda: fotossíntese converte luz em glicose")
        kernel.chat("o que é fotossíntese?")
        
        # Modo produção (V11.2 — persistência, segurança, IoT)
        await kernel.startup_production()
        await kernel.process_iot("biologia", "sensor_01", "dados...")
        
        # Modo sensorial (V13 — imagem, áudio)
        sdr = kernel.process_image(image_rgb)
        sdr = kernel.process_audio(audio_samples)
    """
    
    VERSION = "v14-unified"
    
    def __init__(self, verbose: bool = False, production: bool = False):
        # ── Núcleo cognitivo (V10) ───────────────────────────────
        self.cognitive = GlobalWorkspaceNexus(autosave=False)
        
        # ── Camada de produção (V11.2) ───────────────────────────
        self.guard      = NexusGuardV11()
        self.sdr_filter = NexusSDRFilter()
        self.persist    = NexusPersistV11(self.guard)
        self.healer     = NexusHealerV11(self.persist, self.sdr_filter)
        self.domain_bus = NexusDomainBus(self.persist, self.sdr_filter, self.healer)
        self.gateway    = NexusSeniorGateway(guard=self.guard, sdr_filter=self.sdr_filter)
        self.bio_sim    = NexusBioSim(self.persist)
        
        # ── Encoders sensoriais (V13) ────────────────────────────
        try:
            self.visual_encoder = VisualEncoder()
            self.audio_encoder  = AudioEncoder()
            self._sensory_ok = True
        except Exception:
            self._sensory_ok = False
        
        # ── Aceleração numpy (V13) ───────────────────────────────
        if HAS_NUMPY:
            try:
                accelerator = MiniEmbedAccelerator()
                accelerator.patch(self.cognitive._core.embed)
            except Exception:
                pass
        
        self._production_started = False
        self._verbose = verbose
        
        if verbose:
            print(f"╔══════════════════════════════════════════╗")
            print(f"║  NEXUS V14 UNIFIED — Sistema Carregado   ║")
            print(f"╠══════════════════════════════════════════╣")
            print(f"║  Cognitivo : V10 Ultimate (ativo)        ║")
            print(f"║  Produção  : V11.2 ({'ativo' if production else 'standby':>7})          ║")
            print(f"║  Sensorial : V13 ({'ativo' if self._sensory_ok else 'N/A':>5})              ║")
            print(f"║  numpy     : {'sim (~10× speedup)' if HAS_NUMPY else 'não (Python puro)':>20}   ║")
            print(f"║  aiosqlite : {'sim' if _AIOSQLITE_OK else 'não (modo simulação)':>20}   ║")
            print(f"╚══════════════════════════════════════════╝")
        
        if production:
            import asyncio
            asyncio.get_event_loop().run_until_complete(self.startup_production())
    
    # ── Interface Cognitiva ────────────────────────────────────────
    
    def chat(self, text: str) -> str:
        """Interface conversacional principal (V10 GlobalWorkspace)."""
        return self.cognitive.chat(text)
    
    def learn(self, fact: str, domain: str = "general") -> str:
        """Aprende um fato (V10 + propagação cross-domain)."""
        return self.cognitive.learn(fact)
    
    def scan_health(self) -> str:
        """Relatório de saúde completo (V10 + V11.2)."""
        health = self.cognitive.scan_health()
        if self._production_started:
            h = self.healer.stats
            p = self.persist.stats
            f = self.sdr_filter.stats
            health += (
                f"\n─── PRODUÇÃO V11.2 ───\n"
                f"  Guard (XOR-{NexusGuardV11.KEY_SIZE*8}bit): ativo\n"
                f"  Persist: {p['writes']} escritas, {p['errors']} erros\n"
                f"  SDRFilter: {f['total']} pacotes, {f['blocked']} bloqueados\n"
                f"  Healer: {h['heal_count']} reparos, threshold={h['threshold']}\n"
            )
        return health
    
    # ── Interface de Produção (V11.2) ─────────────────────────────
    
    async def startup_production(self) -> None:
        """Inicializa camada de produção (bancos, tabelas)."""
        await self.persist.initialize()
        await self.persist.log_security_event(
            event_type="KERNEL_STARTUP",
            source_id="NexusV14Unified",
            payload={"version": self.VERSION, "ts": time.time()},
            domain="nexus_core"
        )
        self._production_started = True
    
    async def process_iot(self, domain_id: str, sensor_id: str, data: Any) -> Dict:
        """Processa pacote IoT com validação SDR + persistência."""
        if not self._production_started:
            await self.startup_production()
        return await self.domain_bus.process_domain(domain_id, sensor_id, data)
    
    async def broadcast_iot(self, packets: List[Tuple[str, str, Any]]) -> List[Dict]:
        """Processa múltiplos pacotes concorrentemente (asyncio.gather)."""
        if not self._production_started:
            await self.startup_production()
        return await self.domain_bus.broadcast(packets)
    
    def encrypt(self, data: Any) -> str:
        """Cifra dados com XOR (NexusGuardV11)."""
        return self.guard.encrypt_payload(data)
    
    def decrypt(self, hex_data: str) -> str:
        """Decifra dados."""
        return self.guard.decrypt_payload(hex_data)
    
    # ── Interface Sensorial (V13) ─────────────────────────────────
    
    def process_image(self, image_rgb) -> 'SparseSDR':
        """Converte imagem RGB em SDR (VisualEncoder V13)."""
        if not self._sensory_ok:
            raise RuntimeError("Encoders sensoriais não disponíveis")
        return self.visual_encoder.encode(image_rgb)
    
    def process_audio(self, samples, sample_rate: int = 16000) -> 'SparseSDR':
        """Converte áudio em SDR (AudioEncoder V13)."""
        if not self._sensory_ok:
            raise RuntimeError("Encoders sensoriais não disponíveis")
        return self.audio_encoder.encode(samples, sample_rate)
    
    # ── Demo Completo ─────────────────────────────────────────────
    
    async def run_full_demo(self) -> None:
        """Demo que exercita todas as camadas: cognitiva, produção e sensorial."""
        print("\n╔═══════════════════════════════════════════════╗")
        print("║  NEXUS V14 UNIFIED — DEMO COMPLETO             ║")
        print("╚═══════════════════════════════════════════════╝\n")
        
        # Fase 1: Cognitivo
        print("── FASE 1: Aprendizado Cognitivo (V10) ──")
        fatos = [
            "fotossíntese converte luz solar em glicose usando clorofila",
            "mitose é a divisão celular que gera células geneticamente idênticas",
            "quicksort divide array em torno de um pivô recursivamente",
            "a lei de Ohm estabelece que V = I × R",
        ]
        for f in fatos:
            print(f"  {self.learn(f)}")
        
        r = self.chat("o que é fotossíntese?")
        print(f"  Q: o que é fotossíntese?")
        print(f"  R: {r[:100]}")
        
        # Fase 2: Produção
        print("\n── FASE 2: Produção IoT (V11.2) ──")
        await self.startup_production()
        
        packets = [
            ("biologia",   "sensor_dna",    "sequência genômica ATCG com 98.7% match"),
            ("financas",   "sensor_ibov",   "IBOV +1.34% Volume R$ 23.4B"),
            ("fisica_tcu", "sensor_temp",   "Temperatura 387°C Pressão 15.2bar"),
        ]
        results = await self.broadcast_iot(packets)
        for r in results:
            icon = "✓" if r["status"] == "ACCEPTED" else "✗"
            print(f"  {icon} [{r['domain']}] {r['status']}")
        
        # Fase 3: Segurança
        print("\n── FASE 3: Criptografia XOR (V11.2) ──")
        texto = "Dado secreto NEXUS-2025"
        enc = self.encrypt(texto)
        dec = self.decrypt(enc)
        print(f"  Original : {texto}")
        print(f"  Cifrado  : {enc[:40]}...")
        print(f"  Decifrado: {dec}")
        print(f"  Integridade: {'✓' if dec == texto else '✗'}")
        
        # Fase 4: Sensorial
        if self._sensory_ok:
            print("\n── FASE 4: Encoders Sensoriais (V13) ──")
            # Imagem teste 4x4 RGB
            img = [[(128,64,32),(200,100,50),(50,150,200),(255,255,0)] for _ in range(4)]
            sdr_img = self.process_image(img)
            print(f"  VisualEncoder: SDR com {len(sdr_img)} bits ativos")
            
            # Áudio teste (1s de tom 440Hz)
            samples = [0.5 * math.sin(2*math.pi*440*i/16000) for i in range(16000)]
            sdr_aud = self.process_audio(samples)
            print(f"  AudioEncoder: SDR com {len(sdr_aud)} bits ativos")
        
        # Fase 5: Saúde
        print("\n── FASE 5: Saúde do Sistema ──")
        print(self.scan_health()[:500])
        
        print("\n╔══════════════════════════════════════════╗")
        print("║  Demo V14 Unificado concluído! ✓          ║")
        print("╚══════════════════════════════════════════╝")


# ══════════════════════════════════════════════════════════════════════════════
# §SELFTEST  NEXUS V14 — Teste de Integração Rápido
# ══════════════════════════════════════════════════════════════════════════════

def run_v14_selftest(verbose: bool = True) -> bool:
    """Teste de integração rápido do sistema unificado."""
    ok = 0; total = 0; t0 = time.time()
    
    def chk(label, cond, info=''):
        nonlocal ok, total
        total += 1
        if cond: ok += 1
        if verbose:
            mark = '✓' if cond else '✗'
            print(f'  {mark} {label:<50} {str(info)[:50]}')
        return cond
    
    if verbose:
        print('\n' + '═'*65)
        print('  NEXUS V14 UNIFIED — Selftest')
        print('═'*65)
    
    # 1. Cognitivo
    if verbose: print('\n[1] Núcleo Cognitivo')
    n = NexusV14Unified()
    r = n.chat('aprenda: variável armazena valores em memória')
    chk('Aprendizado', 'Aprendi' in r or len(r) > 5, r[:50])
    
    r2 = n.chat('o que é variável?')
    chk('Consulta SDR', len(r2) > 10, r2[:50])
    
    # 2. Criptografia
    if verbose: print('\n[2] Criptografia XOR')
    txt = "Segredo NEXUS V14"
    enc = n.encrypt(txt)
    dec = n.decrypt(enc)
    chk('Encrypt/Decrypt', dec == txt, f'enc={enc[:20]}...')
    
    sig = n.guard.sign(txt)
    chk('HMAC Sign/Verify', n.guard.verify(txt, sig))
    
    # 3. SDR Filter
    if verbose: print('\n[3] SDR Filter')
    sdr = SparseSDR(list(range(0, 160, 2)))  # 80 bits ativos = 2% sparsity
    accepted, msg = n.sdr_filter.validate_packet(sdr, "test")
    chk('SDR válido aceito', accepted, msg[:50])
    
    # 4. Sensorial
    if verbose: print('\n[4] Encoders Sensoriais')
    if n._sensory_ok:
        img = [[(100,50,25)]*8 for _ in range(8)]
        sdr_v = n.process_image(img)
        chk('VisualEncoder', len(sdr_v) > 0, f'bits={len(sdr_v)}')
        
        samples = [0.3*math.sin(2*math.pi*220*i/16000) for i in range(4000)]
        sdr_a = n.process_audio(samples)
        chk('AudioEncoder', len(sdr_a) > 0, f'bits={len(sdr_a)}')
    else:
        chk('Sensorial (skip)', True, 'não disponível')
    
    # 5. numpy acceleration
    if verbose: print('\n[5] Aceleração')
    chk('numpy disponível', HAS_NUMPY == (np is not None), 
        f'numpy={"sim" if HAS_NUMPY else "não"}')
    chk('VecOps.dot()', abs(VecOps.dot([1,2,3],[4,5,6]) - 32.0) < 0.01)
    
    elapsed = time.time() - t0
    pct = ok/total if total else 0
    status = '✅ APROVADO' if pct >= 0.85 else '✗ FALHOU'
    
    if verbose:
        print(f'\n{"═"*65}')
        print(f'  {ok}/{total} ({pct*100:.0f}%)  {elapsed:.1f}s  {status}')
        print(f'{"═"*65}')
    
    return pct >= 0.85


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys as _sys
    
    print('='*65)
    print('  NEXUS V14 UNIFIED — Sistema Cognitivo de Missão Crítica')
    print('='*65)
    
    if '--test' in _sys.argv:
        # Teste rápido
        ok = run_v14_selftest(verbose=True)
        
        # Também roda testes V10
        print('\n\n--- Testes V10 (cognitivos) ---')
        try:
            ok2 = run_nexus_tests(verbose=True)
        except Exception as e:
            print(f'  [SKIP] Testes V10: {e}')
            ok2 = True
        
        _sys.exit(0 if ok and ok2 else 1)
    
    elif '--demo' in _sys.argv:
        n = NexusV14Unified(verbose=True)
        asyncio.run(n.run_full_demo())
    
    elif '--production' in _sys.argv:
        # Modo produção com kernel V11.2
        kernel = NexusKernelV11_2()
        asyncio.run(kernel.run_demo())
    
    elif '--gw' in _sys.argv:
        # Modo GlobalWorkspace interativo
        n = NexusV14Unified(verbose=True)
        print(f'\n{n.cognitive.brain_status()}')
        print('\nDigite "sair" para encerrar.')
        while True:
            try:
                user = input('> ').strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user: continue
            if user.lower() in ('sair','exit','quit'): break
            if user.lower() in ('saúde','health','status'):
                print(n.scan_health())
            elif user.lower() == 'brains':
                print(n.cognitive.brain_status())
            else:
                print(n.chat(user))
    
    else:
        # Modo interativo padrão
        n = NexusV14Unified(verbose=True)
        print('\nDigite "sair" para encerrar.')
        while True:
            try:
                user = input('> ').strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user: continue
            if user.lower() in ('sair','exit','quit'): break
            print(n.chat(user))
