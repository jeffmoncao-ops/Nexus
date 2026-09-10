#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NEXUS V14 UNIFIED — SERVIDOR HTTP (REST API + UI)                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Expõe o kernel cognitivo Nexus V14 como serviço HTTP:

  GET  /                      UI web (dashboard single-page, sem dependências)
  GET  /api/health            relatório de saúde (texto) + status estruturado
  GET  /api/status            métricas do sistema (fatos, brains, vocabulário)
  GET  /api/brains            status dos cérebros especializados
  POST /api/chat              {text} → resposta cognitiva (com estado epistêmico)
  POST /api/learn             {fact, domain?} → aprendizado de fato
  POST /api/document          {text} → segmentação e aprendizado de documento
  POST /api/search            {query, top_k?} → busca no hipocampo compartilhado
  POST /api/sleep             ciclo de consolidação (sono)
  POST /api/reset             limpa o contexto de diálogo
  POST /api/iot               {domain, sensor, data} → pipeline de produção V11.2
  GET  /api/domains           estatísticas dos domínios IoT
  POST /api/crypto            {text, mode: encrypt|decrypt} → NexusGuardV11
  POST /api/code              {request} → geração de código (CodeGeneralizer)
  POST /api/sensory/image     {image?, size?} → SDR visual (V13)
  POST /api/sensory/audio     {frequency?, seconds?} → SDR auditivo (V13)

Uso:
    python nexus_server.py [porta]         # padrão: 8000
    python nexus_v14_shared_hippocampus.py --serve 8000

Dependências: fastapi, uvicorn (opcionais para o kernel, obrigatórias aqui).

OBS: todas as rotas da UI usam caminhos relativos (/api/...), portanto a
interface funciona atrás de qualquer proxy reverso (inclusive o preview do
ambiente de execução), sem hardcode de host ou porta.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - caminho de ambiente sem deps
    raise SystemExit(
        "Este módulo requer fastapi + uvicorn:\n"
        "  pip install -r requirements-server.txt\n"
        f"(import falhou: {exc})"
    )

from nexus_core import NexusV14Unified

# ══════════════════════════════════════════════════════════════════════════════
# ESTADO GLOBAL — uma instância do kernel compartilhada pelo servidor
# ══════════════════════════════════════════════════════════════════════════════

VERSION = "v14-unified"
_kernel: Optional[NexusV14Unified] = None
_lock = threading.Lock()          # o núcleo cognitivo não é thread-safe
_started_at = time.time()
_turn_count = 0


def get_kernel() -> NexusV14Unified:
    """Instância única (lazy) do kernel cognitivo."""
    global _kernel
    if _kernel is None:
        with _lock:
            if _kernel is None:
                _kernel = NexusV14Unified()
                _seed_remote_knowledge(_kernel)
    return _kernel


def _seed_remote_knowledge(k: NexusV14Unified) -> None:
    """Semeia o sistema com conhecimento inicial para a demo/UI não nascer vazia."""
    base = [
        "fotossíntese é o processo pelo qual plantas produzem glicose usando luz solar e clorofila",
        "a mitocôndria é a organela responsável pela respiração celular e produção de ATP",
        "DNA é a molécula que carrega a informação genética de todos os seres vivos",
        "a lei de Ohm estabelece que a tensão é igual à corrente multiplicada pela resistência",
        "quicksort é um algoritmo de ordenação recursivo que usa um pivô para dividir a lista",
        "a revolução industrial transformou a produção com a máquina a vapor no século XVIII",
    ]
    for fact in base:
        try:
            k.learn(fact)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# MODELOS DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

class ChatIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


class LearnIn(BaseModel):
    fact: str = Field(..., min_length=2, max_length=4000)
    domain: Optional[str] = None


class DocumentIn(BaseModel):
    text: str = Field(..., min_length=2, max_length=200_000)


class SearchIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=25)
    cross_domain: bool = False


class IotIn(BaseModel):
    domain: str = Field("biologia")
    sensor: str = Field("sensor_01")
    data: Any = Field(...)


class CryptoIn(BaseModel):
    text: str = Field(..., max_length=100_000)
    mode: str = Field("encrypt")


class CodeIn(BaseModel):
    request: str = Field(..., min_length=2, max_length=2000)


class ImageIn(BaseModel):
    size: int = Field(8, ge=2, le=64)


class AudioIn(BaseModel):
    frequency: float = Field(440.0, gt=0, le=20000)
    seconds: float = Field(0.25, gt=0, le=5)


# ══════════════════════════════════════════════════════════════════════════════
# APLICAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="Nexus V14 Unified", version=VERSION,
              description="Kernel neuro-simbólico SDR/HDC — API cognitiva e de produção")

# A UI é servida pela mesma origem das chamadas /api/*, mas liberamos CORS para
# permitir integração a partir de outros hosts (drones, robôs, dashboards).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    """Dashboard single-page (HTML/CSS/JS inline, sem dependências externas)."""
    return HTMLResponse(_INDEX_HTML)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    k = get_kernel()
    with _lock:
        report = k.scan_health()
        status = k.status()
    return {
        "version": VERSION,
        "uptime_s": round(time.time() - _started_at, 2),
        "turns": _turn_count,
        "report": report,
        "status": status,
    }


@app.get("/api/status")
def status() -> Dict[str, Any]:
    k = get_kernel()
    with _lock:
        st = k.status()
    return {
        "version": VERSION,
        "uptime_s": round(time.time() - _started_at, 2),
        "turns": _turn_count,
        "facts": st.get("facts", 0),
        "memories": st.get("brain", 0),
        "edges": st.get("edges", 0),
        "graphs": st.get("graph", {}),
        "embed_vocab": st.get("embed", 0),
        "brains": len(k.cognitive._brains),
    }


@app.get("/api/brains")
def brains() -> Dict[str, Any]:
    k = get_kernel()
    with _lock:
        shared = k.cognitive._shared_memory
        data = []
        for bid, brain in k.cognitive._brains.items():
            s = brain.stats
            data.append({
                "id": bid,
                "name": s.get("name", bid),
                "facts": s.get("facts", 0),
                "learned": s.get("learned", 0),
                "queries": s.get("queries", 0),
            })
        memory = shared.stats() if shared is not None else {}
    return {"brains": data, "shared_memory": memory}


@app.post("/api/chat")
def chat(payload: ChatIn) -> Dict[str, Any]:
    global _turn_count
    k = get_kernel()
    with _lock:
        try:
            response = k.chat(payload.text)
        except Exception as exc:                     # pragma: no cover
            raise HTTPException(status_code=500, detail=f"falha no núcleo: {exc}")
        _turn_count += 1
    return {"response": response, "turns": _turn_count}


@app.post("/api/learn")
def learn(payload: LearnIn) -> Dict[str, Any]:
    k = get_kernel()
    with _lock:
        result = k.learn(payload.fact)
        if payload.domain:
            brain = k.cognitive._brains.get(payload.domain)
            if brain is not None:
                brain.learn(payload.fact)
    # O deduplicador SDR (V12) devolve "[dedup] Similar a: …" quando o fato já
    # existe — expomos a flag para o cliente distinguir aprendizado novo.
    return {"result": result, "learned": not result.lstrip().startswith("[dedup]")}


@app.post("/api/document")
def learn_document(payload: DocumentIn) -> Dict[str, Any]:
    k = get_kernel()
    with _lock:
        learned = k.cognitive.learn_document(payload.text)
    return {"learned": learned}


@app.post("/api/search")
def search(payload: SearchIn) -> Dict[str, Any]:
    k = get_kernel()
    with _lock:
        shared = k.cognitive._shared_memory
        if shared is None:
            return {"results": []}
        results = shared.temporal_context_search(
            payload.query, top_k=payload.top_k, brain_filter=None,
        )
        # busca léxica complementar no FactStore (FTS5)
        lexical = k.cognitive.fact_store.search(
            payload.query, top_k=payload.top_k, min_score=0.2)
    merged: List[Dict[str, Any]] = []
    seen = set()
    for score, fact in results:
        if fact in seen:
            continue
        seen.add(fact)
        merged.append({"score": round(float(score), 4), "fact": fact, "source": "sdr"})
    for fact in lexical:
        if fact in seen:
            continue
        seen.add(fact)
        merged.append({"score": None, "fact": fact, "source": "fts"})
    return {"results": merged[:payload.top_k]}


@app.post("/api/sleep")
def sleep() -> Dict[str, Any]:
    k = get_kernel()
    with _lock:
        report = k.cognitive.sleep(cycles=1)
    core = report.get("core")
    return {
        "result": "Consolidação concluída",
        "cycles": report.get("sleep_cycles"),
        "core": str(core),
        "brain_pruned": report.get("brain_pruned", {}),
    }


@app.post("/api/reset")
def reset() -> Dict[str, Any]:
    k = get_kernel()
    with _lock:
        k.cognitive.reset_context()
    return {"result": "Contexto de diálogo reiniciado"}


@app.post("/api/iot")
async def iot(payload: IotIn) -> Dict[str, Any]:
    k = get_kernel()
    result = await k.process_iot(payload.domain, payload.sensor, payload.data)
    return result


@app.get("/api/domains")
async def domains() -> Dict[str, Any]:
    k = get_kernel()
    if not k._production_started:
        await k.startup_production()
    return {"domains": k.domain_bus.bus_stats(),
            "sdr_filter": {key: value for key, value in k.sdr_filter.stats.items()
                           if key != "recent_intrusions"},
            "recent_intrusions": k.sdr_filter.stats.get("recent_intrusions", [])}


@app.post("/api/crypto")
def crypto(payload: CryptoIn) -> Dict[str, Any]:
    k = get_kernel()
    mode = payload.mode.lower().strip()
    if mode == "decrypt":
        try:
            return {"mode": mode, "result": k.decrypt(payload.text)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    return {"mode": "encrypt", "result": k.encrypt(payload.text)}


@app.post("/api/code")
def code(payload: CodeIn) -> Dict[str, Any]:
    k = get_kernel()
    with _lock:
        result = k.cognitive._core.code_eng.run(payload.request)
    return {
        "code": result.get("code", ""),
        "success": bool(result.get("success")),
        "source": result.get("source", ""),
        "stdout": result.get("stdout", ""),
        "error": result.get("error", ""),
    }


@app.post("/api/sensory/image")
def sensory_image(payload: ImageIn) -> Dict[str, Any]:
    k = get_kernel()
    size = payload.size
    image = [[((x * 37) % 256, (y * 53) % 256, ((x + y) * 17) % 256)
              for x in range(size)] for y in range(size)]
    with _lock:
        sdr = k.process_image(image)
    bits = sorted(sdr.to_list()) if hasattr(sdr, "to_list") else []
    return {
        "shape": f"{size}x{size}",
        "active_bits": len(bits),
        "sparsity": round(len(bits) / 4096, 4),
        "bit_preview": bits[:24],
    }


@app.post("/api/sensory/audio")
def sensory_audio(payload: AudioIn) -> Dict[str, Any]:
    import math as _math
    k = get_kernel()
    rate = 16000
    n = int(rate * payload.seconds)
    samples = [0.5 * _math.sin(2 * _math.pi * payload.frequency * i / rate)
               for i in range(n)]
    with _lock:
        sdr = k.process_audio(samples, rate)
    bits = sorted(sdr.to_list()) if hasattr(sdr, "to_list") else []
    return {
        "frequency_hz": payload.frequency,
        "samples": n,
        "active_bits": len(bits),
        "sparsity": round(len(bits) / 4096, 4),
        "bit_preview": bits[:24],
    }


# ══════════════════════════════════════════════════════════════════════════════
# UI — DASHBOARD SINGLE-PAGE
# ══════════════════════════════════════════════════════════════════════════════

_INDEX_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nexus V14 Unified — Kernel Neuro-Simbólico</title>
<style>
  :root{
    --bg:#070b12; --panel:#0d1420; --panel-2:#111a29; --line:#1e2b3f;
    --txt:#e6edf7; --muted:#8ba0bb; --accent:#38e8c8; --accent-2:#5aa9ff;
    --warn:#ffb84d; --err:#ff6b6b; --ok:#3ddc97;
  }
  *{box-sizing:border-box}
  body{margin:0;background:radial-gradient(1200px 600px at 20% -10%,#13243a 0%,var(--bg) 55%);
       color:var(--txt);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
  header{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;
         padding:18px 22px;border-bottom:1px solid var(--line);background:rgba(9,14,22,.8);
         backdrop-filter:blur(8px);position:sticky;top:0;z-index:5}
  .brand{display:flex;align-items:center;gap:12px}
  .logo{width:34px;height:34px;border-radius:10px;background:
        conic-gradient(from 210deg,var(--accent),var(--accent-2),#a06bff,var(--accent));
        box-shadow:0 0 22px rgba(56,232,200,.35)}
  h1{font-size:17px;margin:0;letter-spacing:.4px}
  .sub{color:var(--muted);font-size:12px}
  .pills{display:flex;gap:8px;flex-wrap:wrap}
  .pill{border:1px solid var(--line);background:var(--panel);padding:5px 11px;border-radius:999px;
        font-size:12px;color:var(--muted)}
  .pill b{color:var(--accent)}
  main{display:grid;grid-template-columns:1.25fr .95fr;gap:16px;padding:18px;max-width:1400px;margin:auto}
  @media (max-width:960px){main{grid-template-columns:1fr}}
  .card{background:linear-gradient(180deg,var(--panel) 0%,var(--panel-2) 100%);
        border:1px solid var(--line);border-radius:14px;padding:16px}
  .card h2{margin:0 0 12px;font-size:13px;text-transform:uppercase;letter-spacing:1.2px;color:var(--muted)}
  .chatlog{height:340px;overflow:auto;display:flex;flex-direction:column;gap:10px;padding-right:4px}
  .msg{padding:10px 12px;border-radius:12px;max-width:88%;white-space:pre-wrap;word-wrap:break-word}
  .me{align-self:flex-end;background:#15294a;border:1px solid #23407a}
  .nx{align-self:flex-start;background:#0b1a17;border:1px solid #1c4438;color:#d9fff4}
  .row{display:flex;gap:8px;margin-top:12px}
  input,textarea,select{flex:1;background:#0a111c;border:1px solid var(--line);color:var(--txt);
        border-radius:10px;padding:10px 12px;font:inherit;outline:none}
  input:focus,textarea:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 2px rgba(56,232,200,.12)}
  button{background:linear-gradient(180deg,#1f4a44,#153a35);color:#dffff6;border:1px solid #2b6f63;
        border-radius:10px;padding:10px 16px;font:inherit;cursor:pointer;transition:.15s}
  button:hover{filter:brightness(1.15)}
  button.ghost{background:#101a29;border-color:var(--line);color:var(--muted)}
  pre{margin:0;background:#080d15;border:1px solid var(--line);border-radius:10px;padding:12px;
      overflow:auto;max-height:260px;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#bcd3ef}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{text-align:left;padding:7px 6px;border-bottom:1px solid var(--line)}
  th{color:var(--muted);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.8px}
  .ok{color:var(--ok)} .err{color:var(--err)} .warn{color:var(--warn)}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  @media (max-width:560px){.grid2{grid-template-columns:1fr}}
  .hint{color:var(--muted);font-size:12px;margin-top:8px}
  .tag{display:inline-block;font-size:11px;border:1px solid var(--line);border-radius:6px;
       padding:1px 6px;color:var(--muted);margin-right:4px}
</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="logo"></div>
    <div>
      <h1>Nexus V14 Unified</h1>
      <div class="sub">Kernel neuro-simbólico SDR/HDC · 4096 bits · hipocampo compartilhado</div>
    </div>
  </div>
  <div class="pills">
    <span class="pill">estado <b id="p-status">…</b></span>
    <span class="pill">fatos <b id="p-facts">0</b></span>
    <span class="pill">brains <b id="p-brains">0</b></span>
    <span class="pill">turnos <b id="p-turns">0</b></span>
    <span class="pill">uptime <b id="p-uptime">0s</b></span>
  </div>
</header>

<main>
  <section class="card">
    <h2>Diálogo cognitivo</h2>
    <div class="chatlog" id="chatlog"></div>
    <div class="row">
      <input id="chat-input" placeholder='Ex.: "o que é fotossíntese?" ou "aprenda: o sol é uma estrela"'
             autocomplete="off">
      <button onclick="sendChat()">Enviar</button>
    </div>
    <div class="hint">
      <span class="tag">aprenda: &lt;fato&gt;</span>
      <span class="tag">calcule 2+2*3</span>
      <span class="tag">implemente fibonacci</span>
      <span class="tag">se chover então o chão fica molhado</span>
    </div>
  </section>

  <section class="card">
    <h2>Hipocampo compartilhado</h2>
    <div class="row">
      <input id="search-input" placeholder="buscar fatos (SDR + FTS5)" autocomplete="off">
      <button class="ghost" onclick="doSearch()">Buscar</button>
      <button class="ghost" onclick="doSleep()">Sono</button>
    </div>
    <pre id="search-out">—</pre>
  </section>

  <section class="card">
    <h2>Cérebros especializados</h2>
    <table>
      <thead><tr><th>Domínio</th><th>Fatos</th><th>Aprendidos</th><th>Consultas</th></tr></thead>
      <tbody id="brains-body"><tr><td colspan="4" class="sub">carregando…</td></tr></tbody>
    </table>
  </section>

  <section class="card">
    <h2>Produção V11.2 — pipeline IoT</h2>
    <div class="grid2">
      <select id="iot-domain">
        <option value="biologia">biologia</option>
        <option value="financas">finanças</option>
        <option value="fisica_tcu">física / TCU</option>
      </select>
      <input id="iot-sensor" value="sensor_01">
    </div>
    <div class="row">
      <input id="iot-data" value="sequência genômica ATCG identificada com 98.7% de match">
      <button onclick="sendIot()">Enviar pacote</button>
    </div>
    <div class="hint">Pacotes curtos/anômalos (ex.: "x") são bloqueados por Inibição Lateral do SDRFilter.</div>
    <pre id="iot-out">—</pre>
  </section>

  <section class="card">
    <h2>Segurança — NexusGuard V11</h2>
    <div class="row">
      <input id="crypto-input" value="dado classificado do enxame">
      <button class="ghost" onclick="doCrypto('encrypt')">Cifrar</button>
      <button class="ghost" onclick="doCrypto('decrypt')">Decifrar</button>
    </div>
    <pre id="crypto-out">—</pre>
  </section>

  <section class="card">
    <h2>Encoders sensoriais V13</h2>
    <div class="row">
      <button class="ghost" onclick="doSensory('image')">Imagem 16×16 → SDR</button>
      <button class="ghost" onclick="doSensory('audio')">Tom 440 Hz → SDR</button>
    </div>
    <pre id="sensory-out">—</pre>
  </section>

  <section class="card">
    <h2>Geração de código — CodeGeneralizer</h2>
    <div class="row">
      <input id="code-input" value="ordenar uma lista de números" autocomplete="off">
      <button onclick="doCode()">Gerar</button>
    </div>
    <div class="hint">
      <span class="tag">fibonacci</span>
      <span class="tag">ordenar lista</span>
      <span class="tag">busca binária</span>
      <span class="tag">número primo</span>
    </div>
    <pre id="code-out">—</pre>
  </section>

  <section class="card" style="grid-column:1/-1">
    <h2>Saúde do sistema</h2>
    <pre id="health-out">—</pre>
  </section>
</main>

<script>
const $ = (id) => document.getElementById(id);

function esc(s){ return String(s).replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c])); }

function push(role, text){
  const d = document.createElement('div');
  d.className = 'msg ' + (role === 'me' ? 'me' : 'nx');
  d.textContent = (role === 'me' ? '› ' : '⚛ ') + text;
  $('chatlog').appendChild(d);
  $('chatlog').scrollTop = $('chatlog').scrollHeight;
}

async function api(path, body){
  const opts = body === undefined ? {} :
    {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)};
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({detail:'resposta inválida'}));
  if(!r.ok) throw new Error(data.detail || ('HTTP ' + r.status));
  return data;
}

async function sendChat(){
  const text = $('chat-input').value.trim();
  if(!text) return;
  $('chat-input').value = '';
  push('me', text);
  try{
    const d = await api('/api/chat', {text});
    push('nx', d.response || '(sem resposta)');
  }catch(e){ push('nx', 'erro: ' + e.message); }
  refresh();
}

async function doSearch(){
  const query = $('search-input').value.trim();
  if(!query) return;
  try{
    const d = await api('/api/search', {query, top_k:6});
    $('search-out').textContent = d.results.length
      ? d.results.map(r => '• ' + (r.score !== null ? '[' + r.score.toFixed(3) + '] ' : '[fts] ')
                           + r.fact).join('\n')
      : 'nenhum fato encontrado';
  }catch(e){ $('search-out').textContent = 'erro: ' + e.message; }
}

async function doSleep(){
  try{
    const d = await api('/api/sleep', {});
    $('search-out').textContent = JSON.stringify(d, null, 2);
  }catch(e){ $('search-out').textContent = 'erro: ' + e.message; }
  refresh();
}

async function sendIot(){
  try{
    const d = await api('/api/iot', {
      domain: $('iot-domain').value,
      sensor: $('iot-sensor').value || 'sensor_01',
      data:   $('iot-data').value
    });
    const cls = d.status === 'ACCEPTED' ? 'ok' : (d.status === 'REJECTED' ? 'err' : 'warn');
    $('iot-out').innerHTML = '<span class="' + cls + '">' + esc(d.status) + '</span>\n'
      + esc(JSON.stringify(d, null, 2));
  }catch(e){ $('iot-out').textContent = 'erro: ' + e.message; }
  loadDomains();
}

async function loadDomains(){
  try{
    const d = await api('/api/domains');
    const s = d.sdr_filter;
    $('iot-out').dataset.domains = JSON.stringify(d.domains);
  }catch(e){ /* silencioso */ }
}

async function doCrypto(mode){
  const text = $('crypto-input').value;
  try{
    const d = await api('/api/crypto', {text, mode});
    $('crypto-out').textContent = mode + ' → ' + d.result;
    if(mode === 'encrypt') $('crypto-input').value = d.result;
  }catch(e){ $('crypto-out').textContent = 'erro: ' + e.message; }
}

async function doSensory(kind){
  try{
    const d = kind === 'image'
      ? await api('/api/sensory/image', {size:16})
      : await api('/api/sensory/audio', {frequency:440, seconds:0.25});
    $('sensory-out').textContent = JSON.stringify(d, null, 2);
  }catch(e){ $('sensory-out').textContent = 'erro: ' + e.message; }
}

async function doCode(){
  const request = $('code-input').value.trim();
  if(!request) return;
  try{
    const d = await api('/api/code', {request});
    const head = d.success
      ? '<!-- executado no sandbox AST: ' + esc(d.source) + ' -->\n'
      : '<!-- sem execução (' + esc(d.source || 'sem template') + ') -->\n';
    $('code-out').textContent = head + (d.code || d.error || '(nada gerado)')
      + (d.stdout ? '\n\n# stdout:\n' + d.stdout : '');
  }catch(e){ $('code-out').textContent = 'erro: ' + e.message; }
}

async function refresh(){
  try{
    const [st, br, he] = await Promise.all([api('/api/status'), api('/api/brains'), api('/api/health')]);
    $('p-facts').textContent  = st.facts;
    $('p-brains').textContent = st.brains;
    $('p-turns').textContent  = st.turns;
    $('p-uptime').textContent = st.uptime_s + 's';
    $('p-status').textContent = 'online';
    $('brains-body').innerHTML = br.brains.map(b =>
      '<tr><td>' + esc(b.name) + ' <span class="sub">(' + esc(b.id) + ')</span></td>' +
      '<td>' + b.facts + '</td><td>' + b.learned + '</td><td>' + b.queries + '</td></tr>').join('');
    $('health-out').textContent = he.report;
  }catch(e){
    $('p-status').textContent = 'offline';
  }
}

$('chat-input').addEventListener('keydown', e => { if(e.key === 'Enter') sendChat(); });
$('search-input').addEventListener('keydown', e => { if(e.key === 'Enter') doSearch(); });
$('code-input').addEventListener('keydown', e => { if(e.key === 'Enter') doCode(); });
push('nx', 'Kernel online. Pergunte algo — se eu não souber, eu admito e peço para aprender.');
refresh();
setInterval(refresh, 15000);
</script>
</body>
</html>
"""


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def serve(port: int = 8000, host: str = "0.0.0.0") -> None:  # noqa: A002
    """
    Sobe o servidor HTTP.

    `host` padrão 0.0.0.0: necessário para que o serviço seja acessível por
    proxies/containers (o preview do ambiente de execução expõe a porta).
    """
    import uvicorn
    print(f'╔══ NEXUS V14 — servidor HTTP em http://{host}:{port} ══╗')
    get_kernel()          # aquece o kernel (carrega seed + índices)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import sys
    _port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8000
    serve(port=_port)
