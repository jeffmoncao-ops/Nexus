#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NEXUS CORE — FACHADA OFICIAL DO KERNEL V14                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Ponto de importação estável e documentado do sistema. O kernel completo vive em
`nexus_v14_shared_hippocampus.py` (arquivo único, autossuficiente, sem
dependências obrigatórias); este módulo apenas reexporta sua API pública para
que o restante do projeto (servidor HTTP, testes, integrações) não dependa do
nome físico do monólito.

Uso:

    from nexus_core import NexusV14Unified

    nexus = NexusV14Unified()
    print(nexus.chat("aprenda: fotossíntese converte luz em glicose"))
    print(nexus.chat("o que é fotossíntese?"))
    print(nexus.scan_health())

Camadas expostas:

  Cognitiva (V10)      : NexusV10, GlobalWorkspaceNexus, MiniEmbed, SparseSDR,
                         ConceptGraph, TextWeaver, MathEngine, CodeGeneralizer…
  Proveniência         : ProvenanceStore, FactProvenance, SOURCE_CONFIDENCE
  Produção (V11.2)     : NexusGuardV11, NexusPersistV11, NexusSDRFilter,
                         NexusHealerV11, NexusDomainBus, NexusKernelV11_2…
  Evolução (V13)       : VecOps, VisualEncoder, AudioEncoder, MiniEmbedAccelerator
  Unificada (V14)      : NexusV14Unified, main() (CLI)

CLI equivalente:

  python nexus_core.py --demo
  python nexus_core.py --test
"""
from __future__ import annotations

import sys as _sys

from nexus_v14_shared_hippocampus import *                     # noqa: F401,F403
from nexus_v14_shared_hippocampus import (                     # noqa: F401
    # ── Núcleo unificado ────────────────────────────────────────────────────
    NexusV14Unified,
    VERSION,
    # ── Proveniência de fatos ───────────────────────────────────────────────
    ProvenanceStore,
    FactProvenance,
    SOURCE_CONFIDENCE,
    # ── Cognitivo (V10) ─────────────────────────────────────────────────────
    SparseSDR,
    MiniEmbed,
    MultiLobeEncoder,
    CognitiveBrain,
    StructuredFactStore,
    SQLiteFactStoreV12,
    ConceptGraph,
    NGramMemory,
    TextWeaver,
    ConditionalEngine,
    DeductiveEngine,
    EpistemicLayer,
    EpisodicStream,
    Homeostasis,
    SleepConsolidator,
    CodeGeneralizer,
    MathEngine,
    FluentMouth,
    SharedMemory,
    XORBinding,
    NoveltyDetector,
    TemporalMemory,
    SDRReasoner,
    RepresentationalBus,
    GlobalWorkspaceNexus,
    SpecialistBrain,
    NexusV10,
    NexusFinal,
    # ── Produção (V11.2) ────────────────────────────────────────────────────
    NexusGuardV11,
    NexusPersistV11,
    NexusSDRFilter,
    NexusHealerV11,
    NexusDomainBus,
    NexusDomainProcessor,
    NexusSeniorGateway,
    NexusBioSim,
    NexusAuditor,
    NexusProgrammerV11,
    NexusKernelV11_2,
    # ── Evolução (V13) ──────────────────────────────────────────────────────
    VecOps,
    VisualEncoder,
    AudioEncoder,
    MiniEmbedAccelerator,
    NexusV13Integration,
    # ── Constantes e utilidades ─────────────────────────────────────────────
    SDR_SIZE,
    SDR_ACTIVE,
    SDR_SEED,
    SDR_SPARSITY_MIN,
    SDR_SPARSITY_MAX,
    SDR_SPARSITY_IDEAL,
    DB_SECURE,
    DB_IOT,
    HAS_NUMPY,
    run_v14_selftest,
    run_nexus_tests,
    main,
)

# Aliases de compatibilidade (versões anteriores usavam outros nomes)
Nexus = NexusV14Unified
NexusKernel = NexusKernelV11_2
FactStore = SQLiteFactStoreV12


__all__ = [
    'NexusV14Unified', 'Nexus', 'VERSION', 'main',
    'SparseSDR', 'MiniEmbed', 'MultiLobeEncoder', 'CognitiveBrain',
    'StructuredFactStore', 'SQLiteFactStoreV12', 'FactStore', 'ConceptGraph',
    'NGramMemory', 'TextWeaver', 'ConditionalEngine', 'DeductiveEngine',
    'EpistemicLayer', 'EpisodicStream', 'Homeostasis', 'SleepConsolidator',
    'CodeGeneralizer', 'MathEngine', 'FluentMouth', 'SharedMemory',
    'XORBinding', 'NoveltyDetector', 'TemporalMemory', 'SDRReasoner',
    'RepresentationalBus', 'GlobalWorkspaceNexus', 'SpecialistBrain',
    'NexusV10', 'NexusFinal',
    'NexusGuardV11', 'NexusPersistV11', 'NexusSDRFilter', 'NexusHealerV11',
    'NexusDomainBus', 'NexusDomainProcessor', 'NexusSeniorGateway',
    'NexusBioSim', 'NexusAuditor', 'NexusProgrammerV11', 'NexusKernelV11_2',
    'NexusKernel',
    'VecOps', 'VisualEncoder', 'AudioEncoder', 'MiniEmbedAccelerator',
    'NexusV13Integration',
    'SDR_SIZE', 'SDR_ACTIVE', 'SDR_SEED', 'SDR_SPARSITY_MIN',
    'SDR_SPARSITY_MAX', 'SDR_SPARSITY_IDEAL', 'DB_SECURE', 'DB_IOT',
    'HAS_NUMPY', 'run_v14_selftest', 'run_nexus_tests',
    # Proveniência
    'ProvenanceStore', 'FactProvenance', 'SOURCE_CONFIDENCE',
]


if __name__ == '__main__':
    _sys.exit(main())
