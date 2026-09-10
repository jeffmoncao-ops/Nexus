# Nexus V14 Unified: Neuro-Symbolic Cognitive Kernel

**Codename “Chronos” · runtime version `v14-unified`.**

Nexus is a self-contained neuro-symbolic kernel written in pure Python: it stores
knowledge as text + 4096-bit Sparse Distributed Representations (SDR), reasons
over it with XOR bindings, graph propagation and rule engines, and — most
importantly — **admits when it does not know something** instead of inventing an
answer.

It is not a large language model, and it is not an AGI. It is a small, auditable,
dependency-free cognitive core: no GPU, no transformer, no cloud, no training.

> **Read this first:** the matrix below separates *what the code actually does
> today* from *what is a demonstration* and from *what is a research direction*.
> Earlier revisions of this README described all three as if they were the same
> thing. They are not.

## 🧭 Capability matrix

**✅ Works — implemented, covered by tests, verified in CI**

| Capability | Evidence |
| --- | --- |
| Learned facts with recall by definitional queries (`o que é X?`) | `--test` 34/34, `pytest tests` (112 tests) |
| Epistemic honesty: unknown topics are refused, never answered with an unrelated fact | gate tests + regression suite (quasar, entropia, napoleão, buraco negro) |
| SDR algebra (union/intersection/XOR/Jaccard), semantic LSH encoder | `TestPrimitivasSDR` |
| Multi-brain: 8 domains + custom, N:N fact attribution in a shared hippocampus | `TestMultiCerebros`, `TestMemorySchema` |
| Deterministic persistence: JSON state + SQLite provenance, `save_state`/`load_state` | `TestPersistencia`, save ≈5.3 MB |
| Provenance: origin, confidence, evidence and usage count per fact | `TestProveniencia`, `/api/provenance` |
| Corpus ingestion: files, directories, JSONL, Wikipedia, with real dedup | `TestIngestao`, `nexus_ingest.py` |
| Async production layer: HMAC integrity, SDR packet filter, healer, gateway, domain bus | `TestPersistenciaEHealer`, V11.2 tests |
| Runs with **zero** optional dependencies (pure-Python fallbacks) | CI job `kernel-sem-deps` on Python 3.9/3.11/3.12 |
| HTTP API + dashboard (chat, hippocampus, brains, IoT, sensory, code, knowledge) | `TestApiCompleta`, CI smoke test |
| Code generation from ~30 CBR templates executed in an AST sandbox | `TestProducaoERegressao` |

**🧪 Demonstration — runs end-to-end, but is not what the name suggests**

| Feature | Honest description |
| --- | --- |
| `NexusGuardV11` “encryption” | Deterministic XOR-stream **obfuscation**, not cryptography: fixed keystream, key derived from an in-source seed, no nonce, no authenticated encryption. Same plaintext → same ciphertext. Also tracked: a non-collision-resistant MAC construction (`sha256(payload)[:8]`-style truncation), which bounds forgery resistance to ~2³² guesses. Do not protect real secrets with it. |
| “Zero-shot learning” | Storing a sentence and retrieving it later. There is no generalisation across synonyms: teach “carro” and “automóvel” still returns “not in my knowledge base”. |
| “Reasoning” | Rule engines (conditional, deductive, transitive) and graph propagation over a *small* hand-fed base. They work; they do not discover rules from data at scale. |
| Sensory encoders (V13) | Deterministic RGB→40-bit and PCM→40-bit projections. They are feature hashes, not perception. |
| Code generation | Case-based retrieval from templates + repair loop in a sandbox. Ask for something outside the templates and it says so. |
| IoT pipeline | A well-built telemetry path (filter → domain bus → persistence) exercised by synthetic packets, not a deployed fleet. |

**🔭 Vision — stated as ambition, not as delivered functionality**

* Autonomous drones, robotics and neural prosthetics using this kernel.
* “Million-fact memory”: the architecture allows it; nobody has measured it.
* Associative, human-like recall at LLM quality without transformers.
* Global-workspace consciousness metaphors: useful as design vocabulary, not as
  an empirical claim about the software.

## 🛠 Architecture

* **Memory** — SQLite + FTS5 lexical index (fast recall) **plus** 4096-bit SDR
  blobs (80 active bits ≈ 2 % sparsity) for similarity, XOR unbinding and
  analogical reasoning. An LSH semantic encoder needs no training.
* **Shared hippocampus** — `shared_facts` + `shared_fact_brains` give every fact
  an N:N attribution to specialised cortices: an interdisciplinary fact
  (“algoritmo genético”) belongs to Tecnologia *and* Biologia.
* **Epistemic gate (anti-hallucination)** — before any candidate fact is spoken,
  it must share content roots with the question. Vector search always returns a
  nearest neighbour; the gate is what turns “nearest neighbour of an unknown
  topic” into an honest *“ainda não está na minha base. Me ensine.”*
* **Verified XOR unbinding** — `unbind_object_verified()` returns the *stored*
  subject alongside the object, so a query about an unknown subject can never
  borrow another subject’s definition.
* **Partial knowledge** — when a concept is known through relations but has no
  definition, the kernel says what it knows and asks to be taught the rest
  (`estimate_coverage()` quantifies this per query).
* **Provenance** — every learned fact carries source, confidence, evidence and
  usage counters; `explain('mitocôndria')` answers *“where did you get this?”*.
* **Ingestion** — `nexus_ingest.py` feeds the kernel from files, directories,
  JSONL or Wikipedia, counting new facts vs. real duplicates.
* **Production layer (V11.2)** — HMAC integrity checks, lateral-inhibition packet
  filter, healer, rate-limited gateway, concurrent domain bus. All async paths
  have pure-Python fallbacks.

## 📥 Installation

The kernel runs on **Python 3.9+ with no mandatory third-party dependency**.
Extras enable faster paths:

```bash
pip install -r requirements.txt          # numpy (vector speed) + aiosqlite (real async persistence)
pip install -r requirements-server.txt   # fastapi + uvicorn → HTTP API + dashboard
pip install -r requirements-dev.txt      # pytest + httpx → test suite
python3 nexus_v14_shared_hippocampus.py --selfcheck
# nexus v14-unified | numpy=não | aiosqlite=não | fastapi=não   ← also valid: pure Python
```

On externally-managed Python you may need `--break-system-packages` or a venv.

## 🚀 Usage

### CLI

```bash
python3 nexus_v14_shared_hippocampus.py            # interactive chat
python3 nexus_v14_shared_hippocampus.py --demo     # cognitive + IoT + crypto + sensory demo
python3 nexus_v14_shared_hippocampus.py --production  # V11.2 mission-critical kernel demo
python3 nexus_v14_shared_hippocampus.py --gw       # chat with the Global Workspace
python3 nexus_v14_shared_hippocampus.py --test     # selftest + 34 integrated tests + basics
python3 nexus_v14_shared_hippocampus.py --v10-test # fast V10 core tests
python3 nexus_v14_shared_hippocampus.py --health   # health report (incl. provenance coverage)
python3 nexus_v14_shared_hippocampus.py --serve 8000  # HTTP API + dashboard
python3 nexus_v14_shared_hippocampus.py --selfcheck   # which optional deps are available
```

### Python API

```python
from nexus_core import NexusV14Unified

nexus = NexusV14Unified()
print(nexus.chat("aprenda: a lei de Ohm estabelece que V = I × R"))
print(nexus.chat("o que é a lei de ohm?"))     # answers
print(nexus.chat("o que é entropia?"))         # honest: not in the knowledge base yet
print(nexus.explain("lei de ohm"))             # {'source': 'user', 'confidence': 0.95, ...}
print(nexus.scan_health())
```

### Feeding it real knowledge

```bash
python3 nexus_ingest.py --file manual.md --dir docs/ --wiki Fotossíntese \
                        --confidence 0.9 --report ingest.json
```

```python
import nexus_ingest
from nexus_core import NexusV14Unified

kernel = NexusV14Unified()
kernel.load_state("nexus_state.json")                       # accumulate across runs
print(nexus_ingest.ingest_text(kernel, open("aula.md").read(),
                               source="ingest", evidence="aula.md"))
kernel.save_state("nexus_state.json")
```

Re-ingesting the same corpus reports `0 new / N duplicates` — dedup is measured
against the real fact store, not against a message string.

### HTTP API + dashboard

```bash
python3 nexus_v14_shared_hippocampus.py --serve 8000   # or: python3 nexus_server.py 8000
```

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/` | Dashboard (chat, hippocampus, brains, IoT, crypto, sensory, code, knowledge, health) |
| GET | `/api/health` · `/api/status` · `/api/brains` · `/api/domains` | Health, metrics, cortices, IoT stats |
| POST | `/api/chat` · `/api/learn` · `/api/document` · `/api/search` · `/api/sleep` · `/api/reset` | Cognitive operations |
| POST | `/api/ingest` | Corpus ingestion with dedup + provenance |
| GET | `/api/provenance` · POST `/api/explain` · POST `/api/coverage` | Where knowledge came from, what is missing |
| POST | `/api/iot` · `/api/crypto` · `/api/code` · `/api/sensory/{image,audio}` | Production, obfuscation, code, sensory |

The UI uses relative `/api/...` paths, so it works behind any reverse proxy.

## 🧪 Tests and CI

```bash
python3 nexus_v14_shared_hippocampus.py --test   # 11/11 selftest · 34/34 integrated · 4/4 basics
pytest -q                                        # 112 tests (kernel, production, HTTP, ingest)
pytest -q -m "not slow"                          # skip the long demos
```

CI (`.github/workflows/ci.yml`) enforces the promises above:

* **`kernel-sem-deps`** (Python 3.9, 3.11, 3.12) — installs *nothing* optional and
  runs the full kernel suite, the demo, the production demo and a numpy-free
  cipher check; then runs `pytest` with only `pytest` installed (HTTP tests skip).
* **`completo`** — installs all requirements, runs the suite, boots the HTTP
  server and hits `/api/health` + `/api/chat`, and runs the ingestion pipeline.
* **`modularidade`** — verifies Python 3.9 syntax compatibility, that the kernel
  works **alone** (copied to an empty directory) and that satellite modules
  import (or fail with a clear message).

## 📂 Repository layout

| Path | Contents |
| --- | --- |
| `nexus_v14_shared_hippocampus.py` | The kernel: cognitive core + production layer + sensory encoders + CLI |
| `nexus_core.py` | Stable import façade for the public API |
| `nexus_server.py` | FastAPI HTTP layer + single-page dashboard |
| `nexus_ingest.py` | Corpus ingestion pipeline (files, JSONL, Wikipedia) with provenance |
| `tests/` | 112 tests: kernel, regressions, production, HTTP, ingestion |
| `requirements*.txt` · `.github/workflows/ci.yml` | Optional deps and CI |
| `nexus_v2_*.tar.gz`, `nexus_v4_final.tar.gz` | Archived earlier generations (untouched) |

**Why one big file?** The kernel is deliberately self-contained: copy
`nexus_v14_shared_hippocampus.py` anywhere and it runs (CI proves it). New
subsystems that do not need to be inside it live in satellite modules
(`nexus_core`, `nexus_server`, `nexus_ingest`) — that is the modularisation
strategy: extend outward, keep the single-file core portable. Extracting the
13 k-line core into a package is possible but would trade away that property;
it is not done.

## ⚠️ Known limitations

* **Not secure.** The XOR layer is obfuscation; see the matrix above before using
  it for anything sensitive.
* **Lexical epistemic gate.** Relevance uses shared content roots, so a fact
  mentioning one root of the question can pass (`cromossomo` → fact about
  `mitose`). It is conservative (false “I don’t know” is preferred over a false
  answer), but it is not semantic understanding.
* **No thread safety in the core.** The HTTP layer serialises access with a lock.
* **State size** ≈5.3 MB per 300-token vocabulary (vectors are base64 float32);
  a million facts has *not* been measured.
* **No packaging/lint/type-checking yet** (`pyproject.toml`, mypy, ruff are open
  work), and the abstract-method `NotImplementedError`s are by design.
* **Code generation is retrieval, not synthesis** — it declines politely outside
  its template library.

## 🔭 Roadmap

1. Semantic relevance stage on top of the lexical gate (embeddings alone are not
   trustworthy enough to gate answers today).
2. Packaging (`pyproject.toml`), type hints in the public surface, benchmarks for
   latency/memory at scale.
3. More ingestion sources (CSV/PDF, datasets) and coverage dashboards.
4. Replace the demo obfuscation with a real authenticated cipher **or** remove it.

## ⚖ License

© 2026 Jeferson Monção — viewing and collaboration only. See [LICENSE](LICENSE).
