# Nexus V14 Unified: Neuro-Symbolic AGI Kernel

**Codename “Chronos” · runtime version `v14-unified`.**

Nexus V14 Unified is a high-performance cognitive operating system kernel designed for edge computing, robotics, and advanced neural interfaces. Unlike traditional Large Language Models (LLMs) that rely on probabilistic token prediction, Nexus operates as a Neuro-Symbolic Kernel, utilizing Sparse Distributed Representations (SDR) and Hyperdimensional Computing (HDC) to achieve human-like reasoning with a fraction of the hardware requirements.

## 🌌 Core Philosophy: The Redemptive Thread

Nexus is built on the principle of Biological Mimicry. It processes information not as strings of text, but as geometric signatures in a 4096-dimensional space. This allows for:

* **Zero-Shot Learning:** Immediate integration of new facts without retraining (`aprenda: <fato>`).
* **Epistemic Validation:** A sandbox-driven "promotion" system where hypotheses only become "facts" after logical or functional verification — and where the kernel answers *"ainda não está na minha base. Me ensine."* instead of inventing something when it does not know. Retrieval is gated by content overlap with the question, so an unknown topic never returns an unrelated fact.
* **Energy Efficiency:** A million-fact memory runs on local hardware with minimal RAM overhead — no GPU, no transformer, no cloud.

## 🛠 Technical Architecture

### 1. Hippocampus (Memory)

Layered persistence for high-recall, high-precision memory:

* **L1 Cache (Intuition):** SQLite + **FTS5** lexical index for cheap, immediate recall of learned facts.
* **L2 Deep Store (Cognition):** full **4096-bit SDR BLOBs** (80 active bits ≈ 2% sparsity) for Jaccard similarity, XOR-based analogical reasoning, and an LSH-based semantic encoder (`locality-sensitive hashing`, no training required).
* **Shared Hippocampus (Multi-Brain):** `shared_facts` + `shared_fact_brains` tables give facts an **N:N attribution** to specialized cortices — an interdisciplinary fact (“algoritmo genético”) can belong to Tecnologia *and* Biologia at the same time.

### 2. HDCRoles (Algebraic Reasoning)

XOR Binding + Cyclic Permutation encode structural relationships. Subject, Relation, and Object are separated by rotating bit-vectors, which prevents the "semantic soup" effect of simpler vector databases. Unbinding is *verified* against the stored subject before it is spoken, so a query about an unknown subject cannot return another subject’s definition.

### 3. MultiBrain & Global Workspace

A "Thalamus-Cortex" model:

* **Specialized Cortices:** eight default domains (Biologia, Física, Matemática, Tecnologia, História, Medicina, Geografia, Linguística) plus `add_brain()` / `remove_brain()` for custom domains.
* **Global Workspace:** a central hub that manages lateral inhibition, consultation, sleep consolidation and cross-domain propagation — the most relevant cortex takes control of the output.

### 4. Production Layer (V11.2)

Mission-critical path used by the IoT/telemetry pipeline:

* **NexusGuardV11:** XOR-stream cipher + HMAC-SHA256 signatures, deterministic SHA-256 key derivation.
* **NexusSDRFilter:** Lateral Inhibition gate — validates sparsity (0.5 %–8 %), distribution and mask signature, blocking truncated/anomalous packets (`sensor=“x”` → `REJECTED`).
* **NexusPersistV11 / NexusHealerV11 / NexusSeniorGateway:** async SQLite persistence, integrity scans, self-healing of queues/stores, rate limiting (429) and payload limits (413). All async paths run with `aiosqlite` when installed and fall back to simulation otherwise.
* **NexusDomainBus:** concurrent multi-domain packet processing (biologia / financas / fisica_tcu).

### 5. Sensory Encoders (V13)

Deterministic image (RGB → 40 active bits) and audio (PCM → spectral SDR) encoders, with safe handling of empty/malformed input.

## 📥 Installation

The kernel runs on **Python 3.9+ with no mandatory third-party dependency** — every optional subsystem has a pure-Python fallback. Install the extras to enable the fast paths:

```bash
pip install -r requirements.txt          # numpy (vector speed) + aiosqlite (real async persistence)
pip install -r requirements-server.txt   # fastapi + uvicorn → HTTP API + dashboard
pip install -r requirements-dev.txt      # pytest + httpx → test suite
```

> In environments with an externally managed Python you may need `pip install --break-system-packages -r …` or a virtualenv.

Check what is available at any moment:

```bash
python3 nexus_v14_shared_hippocampus.py --selfcheck
# nexus v14-unified | numpy=sim | aiosqlite=sim | fastapi=sim
```

## 🚀 Quick Start

### Command line

```bash
python3 nexus_v14_shared_hippocampus.py            # interactive chat
python3 nexus_v14_shared_hippocampus.py --demo     # full demo: cognitive + IoT + crypto + sensory
python3 nexus_v14_shared_hippocampus.py --production  # V11.2 mission-critical kernel demo
python3 nexus_v14_shared_hippocampus.py --gw       # chat with the Global Workspace (multi-brain)
python3 nexus_v14_shared_hippocampus.py --test     # integrated suite (V14 selftest + V10 + basics)
python3 nexus_v14_shared_hippocampus.py --v10-test # fast V10 core tests
python3 nexus_v14_shared_hippocampus.py --health   # system health report
python3 nexus_v14_shared_hippocampus.py --serve 8000  # HTTP REST API + dashboard
```

### Python API

```python
from nexus_core import NexusV14Unified

nexus = NexusV14Unified()
print(nexus.chat("aprenda: a lei de Ohm estabelece que V = I × R"))
print(nexus.chat("o que é a lei de ohm?"))
print(nexus.chat("calcule 12 * (3 + 4)"))          # = 84
print(nexus.chat("o que é entropia?"))             # honest: not in the knowledge base yet
print(nexus.scan_health())
```

Production layer (async):

```python
import asyncio
from nexus_core import NexusV14Unified

async def main():
    nexus = NexusV14Unified(production=True)       # boots Guard, Filter, Persist, Gateway, DomainBus
    result = await nexus.process_iot(
        "biologia", "sensor_01", "sequência genômica ATCG com 98.7% de match")
    print(result)                                   # status: ACCEPTED, 80 SDR bits

asyncio.run(main())
```

### HTTP API + Dashboard

```bash
python3 nexus_v14_shared_hippocampus.py --serve 8000   # or: python3 nexus_server.py 8000
# dashboard → http://localhost:8000   (single-page UI, no external assets)
```

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/` | Dashboard (chat, hippocampus, brains, IoT, crypto, sensory, code, health) |
| GET | `/api/health` · `/api/status` · `/api/brains` · `/api/domains` | Health report, metrics, cortex status, IoT stats |
| POST | `/api/chat` · `/api/learn` · `/api/document` · `/api/search` · `/api/sleep` · `/api/reset` | Cognitive operations |
| POST | `/api/iot` | V11.2 production pipeline (SDRFilter + DomainBus) |
| POST | `/api/crypto` | NexusGuardV11 encrypt/decrypt |
| POST | `/api/code` | Code generation/execution (CodeGeneralizer) |
| POST | `/api/sensory/image` · `/api/sensory/audio` | V13 encoders → SDR |

The UI uses relative `/api/...` paths, so it works behind any reverse proxy or container preview without host/port hardcoding.

### Tests

```bash
python3 nexus_v14_shared_hippocampus.py --test   # 11/11 selftest · 34/34 integrated · 4/4 basics
pytest -q                                        # 55 tests: kernel, production layer, HTTP server
```

## 📂 Repository Layout

| Path | Contents |
| --- | --- |
| `nexus_v14_shared_hippocampus.py` | The unified kernel (V10 cognitive core · V11.2 production · V13 sensory) + CLI |
| `nexus_core.py` | Facade module — public API (`NexusV14Unified`, `NexusKernel`, …) |
| `nexus_server.py` | FastAPI HTTP layer + single-page dashboard |
| `tests/` | pytest suite (`test_nexus_v14.py`) |
| `requirements*.txt` | Optional kernel / server / dev dependencies |
| `nexus_v2_*.tar.gz`, `nexus_v4_final.tar.gz` | Archived earlier generations (untouched) |

## 🔭 Future Applications

The Nexus Kernel is designed for integration where latency, privacy, and local autonomy are critical:

* **Autonomous Drones:** semantic navigation and swarm intelligence without cloud dependency or GPS reliance.
* **Robotics:** on-the-fly code generation via the CodeGeneralizer to solve novel mechanical problems through real-time Python sandboxing.
* **Neural Prosthetics:** mapping neural intent to SDR signatures for organic-feeling bio-feedback loops and predictive movement.

## ⚖ License

© 2026 Jeferson Monção — viewing and collaboration only. See [LICENSE](LICENSE).
