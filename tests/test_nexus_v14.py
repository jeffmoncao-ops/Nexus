#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NEXUS V14 UNIFIED — SUITE DE TESTES (pytest)                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

Cobre as três camadas do sistema:

  • Cognitiva (V10)   — aprendizado, recall, estado epistêmico, raciocínio,
                        persistência JSON, multi-cérebros (hipocampo compartilhado)
  • Produção (V11.2)  — NexusGuard (cifra/HMAC/KDF), SDRFilter (densidade,
                        Inibição Lateral), persistência aiosqlite, healer,
                        pipeline de domínios concorrente, kernel de missão crítica
  • Evolução (V13)    — encoders sensoriais (imagem/áudio) e robustez de entrada

Execução:
    pytest -q                       # tudo
    pytest -q -m "not slow"         # sem os testes longos (demos)
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus_core import (                                    # noqa: E402
    AudioEncoder, GlobalWorkspaceNexus, MultiLobeEncoder, NexusGuardV11,
    NexusKernelV11_2, NexusSDRFilter, NexusV14Unified, SDR_ACTIVE, SDR_SIZE,
    SDR_SPARSITY_MAX, SDR_SPARSITY_MIN, SharedMemory, SparseSDR, VisualEncoder,
    run_nexus_tests, run_v14_selftest,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def nexus():
    """Kernel cognitivo isolado (sem autosave em disco)."""
    return NexusV14Unified()


@pytest.fixture(scope="module")
def workspace():
    """Global Workspace isolado para os testes de multi-cérebros."""
    return GlobalWorkspaceNexus(autosave=False)


@pytest.fixture()
def sdr_filter():
    return NexusSDRFilter()


# ══════════════════════════════════════════════════════════════════════════════
# 1. CAMADA COGNITIVA (V10)
# ══════════════════════════════════════════════════════════════════════════════

class TestNucleoCognitivo:

    def test_aprendizado_e_recall(self, nexus):
        nexus.chat("aprenda: a entropia mede a desordem de um sistema termodinâmico")
        resposta = nexus.chat("o que é entropia?")
        assert "entropia" in resposta.lower() or "desordem" in resposta.lower()

    def test_matematica(self, nexus):
        assert "84" in nexus.chat("calcule 12 * (3 + 4)")

    def test_geracao_de_codigo(self, nexus):
        resposta = nexus.chat("implemente fibonacci")
        assert "def fibonacci" in resposta

    def test_estado_epistemico_admite_ignorancia(self, nexus):
        """O sistema NUNCA deve inventar resposta para tema inexistente."""
        resposta = nexus.chat("o que é um quasar supermassivo distante?")
        assert "quasar" in resposta.lower()
        # Não pode responder com um fato não relacionado (ex.: teorema de Pitágoras)
        assert "pitágoras" not in resposta.lower()

    def test_scan_health_e_status(self, nexus):
        assert "Nexus V10" in nexus.scan_health()
        status = nexus.status()
        # Chaves reais do snapshot cognitivo (V14: version/brain/facts/edges/…)
        assert {"version", "facts", "brain", "sdr", "homeostasis"} <= set(status)
        assert status["version"].startswith("v14")

    def test_sleep_e_reset(self, nexus):
        relatorio = nexus.cognitive.sleep(cycles=1)
        assert "core" in relatorio and relatorio["sleep_cycles"] >= 1
        nexus.cognitive.reset_context()

    def test_save_e_load(self, nexus, tmp_path):
        destino = tmp_path / "estado.json"
        nexus.cognitive._core.save(str(destino))
        assert destino.exists() and destino.stat().st_size > 1000
        nexus.cognitive._core.load(str(destino))

    def test_aprendizado_de_documento(self, nexus):
        texto = ("O sol é uma estrela de classe G. "
                 "A lua reflete a luz solar para a terra. "
                 "Marte possui duas luas pequenas.")
        assert nexus.cognitive.learn_document(texto) >= 1


class TestMultiCerebros:

    def test_oito_dominios_padrao(self, workspace):
        assert len(workspace._brains) == 8
        assert {"biologia", "fisica", "matematica", "tecnologia"} <= set(workspace._brains)

    def test_atribuicao_hipocampo_compartilhado(self, workspace):
        """Fato aprendido precisa ser atribuído ao cérebro do domínio correto."""
        workspace.learn("a fotossíntese ocorre nos cloroplastos das células vegetais")
        workspace.learn("o algoritmo quicksort usa recursão e pivô para ordenar arrays")
        bio = workspace._shared_memory.all_facts(brain_filter="biologia")
        tech = workspace._shared_memory.all_facts(brain_filter="tecnologia")
        assert any("fotoss" in f.lower() for f in bio)
        assert any("quicksort" in f.lower() for f in tech)

    def test_query_por_brain(self, workspace):
        resultados = workspace._brains["biologia"].query("o que é fotossíntese?", top_k=3)
        assert resultados and resultados[0][0] > 0

    def test_cross_domain_learning(self, workspace):
        """Um fato pode pertencer a mais de um domínio (N:N)."""
        workspace.learn("o algoritmo genético se inspira na evolução biológica das espécies")
        bio = workspace._shared_memory.all_facts(brain_filter="biologia")
        tech = workspace._shared_memory.all_facts(brain_filter="tecnologia")
        alvo = [f for f in bio + tech if "algoritmo genético" in f.lower()]
        assert alvo, "fato interdisciplinar não foi atribuído a nenhum domínio"

    def test_add_remove_brain(self):
        gw = GlobalWorkspaceNexus(autosave=False)
        gw.add_brain("culinaria", "Culinária", [
            "receita", "ingrediente", "tempero", "culinária", "cozinhar",
            "gastronomia", "prato", "chef", "sabor", "aroma", "massa",
            "molho", "sobremesa"])
        gw.learn("risoto é um prato italiano com arroz arbóreo e caldo")
        fatos = gw._shared_memory.all_facts(brain_filter="culinaria")
        assert any("risoto" in f.lower() for f in fatos)
        assert gw.remove_brain("culinaria") is True
        assert "culinaria" not in gw._brains

    def test_brain_status(self, workspace):
        texto = workspace.brain_status()
        assert "biologia" in texto and "fatos" in texto


class TestPrimitivasSDR:

    def test_operacoes_de_conjunto(self):
        a = SparseSDR([1, 2, 3, 4])
        b = SparseSDR([3, 4, 5, 6])
        assert sorted((a | b).to_list()) == [1, 2, 3, 4, 5, 6]
        assert sorted((a & b).to_list()) == [3, 4]
        assert sorted((a ^ b).to_list()) == [1, 2, 5, 6]

    def test_sparsity_e_densidade(self):
        sdr = SparseSDR(range(SDR_ACTIVE))
        assert sdr.sparsity() == pytest.approx(SDR_ACTIVE / SDR_SIZE)
        assert sdr.bit_density_valid()

    def test_jaccard_e_bundle(self):
        a = SparseSDR([1, 2, 3, 4])
        assert a.jaccard(a) == 1.0
        assert a.jaccard(SparseSDR([5, 6, 7, 8])) == 0.0
        unido = SparseSDR.bundle([SparseSDR([1, 2]), SparseSDR([2, 3])])
        assert 2 in unido.to_list()

    def test_encoder_gera_sdr_valido(self):
        sdr = MultiLobeEncoder().encode("pacote de telemetria do sensor de pressão")
        assert SDR_SPARSITY_MIN <= sdr.sparsity() <= SDR_SPARSITY_MAX


# ══════════════════════════════════════════════════════════════════════════════
# 2. CAMADA DE PRODUÇÃO (V11.2)
# ══════════════════════════════════════════════════════════════════════════════

class TestNexusGuard:

    def test_roundtrip_de_texto_e_estruturas(self):
        guard = NexusGuardV11()
        for payload in ["dado secreto", {"temp": 42.5, "ok": True}, [1, 2, 3], 12345]:
            assert guard.decrypt_payload(guard.encrypt_payload(payload)) == (
                payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False))

    def test_hmac(self):
        guard = NexusGuardV11()
        assinatura = guard.sign("payload")
        assert guard.verify("payload", assinatura)
        assert not guard.verify("payload alterado", assinatura)

    def test_chave_deterministica_entre_instancias(self):
        assert NexusGuardV11().master_key == NexusGuardV11().master_key
        assert NexusGuardV11(seed := 0xABCDEF).master_key != NexusGuardV11(0x123456).master_key

    def test_payload_corrompido_e_detectado(self):
        guard = NexusGuardV11()
        cifrado = guard.encrypt_payload("conteúdo original")
        corrompido = ("ff" + cifrado[2:]) if not cifrado.startswith("ff") else ("00" + cifrado[2:])
        with pytest.raises(ValueError):
            guard.decrypt_payload(corrompido)


class TestSDRFilter:

    def test_pacote_real_aceito(self, sdr_filter):
        aceito, msg = sdr_filter.validate_packet(
            "sequência genômica ATCG identificada com 98.7% de match", "sensor_dna")
        assert aceito and "ACEITO" in msg

    def test_pacote_truncado_bloqueado(self, sdr_filter):
        aceito, msg = sdr_filter.validate_packet("x", "sensor_anomalo")
        assert not aceito and "sparsity_out_of_range" in msg

    def test_entrada_vazia_bloqueada(self, sdr_filter):
        aceito, _ = sdr_filter.validate_packet("", "sensor_vazio")
        assert not aceito

    def test_padrao_degenerado_bloqueado(self, sdr_filter):
        """Máscara periódica (bits só na 1ª zona) = payload sintético, não sinal."""
        degenerado = SparseSDR(list(range(0, 160, 2)))
        aceito, msg = sdr_filter.validate_packet(degenerado, "invasor")
        assert not aceito and "distribution_degenerate" in msg

    def test_sinal_do_encoder_aceito(self, sdr_filter):
        sdr = MultiLobeEncoder().encode("telemetria de temperatura e pressão do reator")
        aceito, _ = sdr_filter.validate_packet(sdr, "sensor_reator")
        assert aceito

    def test_determinismo_e_estatisticas(self, sdr_filter):
        resultados = {sdr_filter.validate_packet("IBOV +1.34% Volume R$ 23.4B")[1]
                      for _ in range(10)}
        assert len(resultados) == 1        # mesma entrada ⇒ mesma decisão
        assert sdr_filter.stats["total"] == 10

    def test_sem_falsos_positivos_em_texto_real(self, sdr_filter):
        random.seed(1234)
        letras = "abcdefghijklmnopqrstuvwxyz áéíóúçãõ0123456789"
        falsos = [s for _ in range(150)
                  if not sdr_filter.validate_packet(
                      s := "".join(random.choice(letras) for _ in range(random.randint(8, 300))))[0]]
        assert not falsos, f"{len(falsos)} pacotes legítimos rejeitados"


class TestPersistenciaEHealer:

    @pytest.mark.asyncio
    async def test_startup_producao_e_iot(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        kernel = NexusV14Unified()
        await kernel.startup_production()
        resultado = await kernel.process_iot("biologia", "sensor_01",
                                             "sequência genômica ATCG com 98.7% de match")
        assert resultado["status"] == "ACCEPTED"
        assert resultado["sdr_bits"] > 0

    @pytest.mark.asyncio
    async def test_broadcast_concorrente_e_dominio_invalido(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        kernel = NexusV14Unified()
        await kernel.startup_production()
        pacotes = [
            ("biologia", "s1", "checkpoint de mitose validado em 52 estágios"),
            ("financas", "s2", "VaR 95% calculado em 1.2 milhões de reais"),
            ("fisica_tcu", "s3", "temperatura do núcleo em 387 graus e pressão 15.2 bar"),
        ]
        resultados = await kernel.broadcast_iot(pacotes)
        assert [r["status"] for r in resultados] == ["ACCEPTED"] * 3
        invalido = await kernel.broadcast_iot([("quimica", "s1", "pacote desconhecido")])
        assert invalido[0]["status"] == "ERROR"

    @pytest.mark.asyncio
    async def test_varredura_de_integridade(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        kernel = NexusV14Unified()
        await kernel.startup_production()
        await kernel.process_iot("financas", "s2", "carteira rebalanceada com sucesso")
        relatorio = await kernel.persist.integrity_scan()
        assert relatorio["summary"]["corrupt"] == 0
        assert relatorio["summary"]["integrity_pct"] == 100.0

    @pytest.mark.asyncio
    async def test_healer_flush(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        kernel = NexusV14Unified()
        await kernel.startup_production()
        relatorio = await kernel.healer.heal(context="teste")
        assert relatorio["action"] == "HEAL_COMPLETE"
        assert relatorio["flush_result"]["queues_flushed"] >= 1

    @pytest.mark.asyncio
    async def test_gateway_rate_limit_e_payload_grande(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        kernel = NexusV14Unified()
        assert await kernel.gateway.receive_data("s1", "a" * 5000) == "413 Payload Too Large"
        for _ in range(12):
            resposta = await kernel.gateway.receive_data("s1", "telemetria válida do sensor")
        assert resposta in ("429 Too Many Requests", "202 Accepted")


class TestMemorySchema:

    def test_atribuicao_n_para_n(self):
        mem = SharedMemory(db_path=":memory:")
        assert mem.store("a mitocôndria produz ATP", brain_origin="biologia")
        assert mem.store("a mitocôndria produz ATP", brain_origin="medicina")
        assert mem.all_facts(brain_filter="biologia") == ["a mitocôndria produz ATP"]
        assert mem.all_facts(brain_filter="medicina") == ["a mitocôndria produz ATP"]
        assert len(mem) == 1                     # fato único, duas atribuições
        assert mem.stats()["by_brain"]["biologia"]["attributed"] == 1

    def test_funilamento_e_stopwords(self):
        enc = MultiLobeEncoder()
        sdr = enc.encode("conteúdo relevante")
        assert len(sdr) > 0
        assert enc._tokenize("teste") != []


# ══════════════════════════════════════════════════════════════════════════════
# 3. CAMADA SENSORIAL (V13)
# ══════════════════════════════════════════════════════════════════════════════

class TestEncodersSensoriais:

    def test_imagem_valida(self):
        imagem = [[(x * 7 % 256, y * 11 % 256, (x + y) * 3 % 256) for x in range(16)]
                  for y in range(16)]
        sdr = VisualEncoder().encode(imagem)
        assert isinstance(sdr, SparseSDR) and len(sdr) == 40

    @pytest.mark.parametrize("entrada", [[], [[]], "abc", None])
    def test_entradas_invalidas_sem_excecao(self, entrada):
        sdr = VisualEncoder().encode(entrada)
        assert isinstance(sdr, SparseSDR) and len(sdr) == 0

    def test_imagem_pequena_e_escala_de_cinza(self):
        assert len(VisualEncoder().encode([[(10, 20, 30)]])) == 40
        assert len(VisualEncoder().encode([[128] * 8 for _ in range(8)])) == 40

    def test_audio_valido_e_vazio(self):
        amostras = [0.5 * math.sin(2 * math.pi * 440 * i / 16000) for i in range(8000)]
        assert len(AudioEncoder().encode(amostras)) == 40
        assert isinstance(AudioEncoder().encode([]), SparseSDR)

    def test_process_image_do_kernel(self, nexus):
        sdr = nexus.process_image([[(i * 9 % 256, j * 5 % 256, 30) for j in range(8)]
                                   for i in range(8)])
        assert len(sdr) == 40


# ══════════════════════════════════════════════════════════════════════════════
# 4. KERNEL DE MISSÃO CRÍTICA + SUITES INTERNAS
# ══════════════════════════════════════════════════════════════════════════════

class TestKernelProducao:

    @pytest.mark.asyncio
    async def test_learn_query_chat(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        kernel = NexusKernelV11_2()
        await kernel.startup()
        resposta = kernel.learn("A lei de Ohm estabelece que V = I × R.", "fisica_tcu")
        assert "Aprendi" in resposta
        assert "Ohm" in kernel.query("lei de ohm")
        assert "Ohm" in kernel.chat("o que é a lei de ohm?")
        await kernel.shutdown()

    @pytest.mark.asyncio
    async def test_scan_health(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        kernel = NexusKernelV11_2()
        await kernel.startup()
        relatorio = kernel.scan_health()
        assert "SAÚDE DO KERNEL" in relatorio and "XOR" in relatorio
        await kernel.shutdown()

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_run_demo_completo(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        kernel = NexusKernelV11_2()
        await kernel.run_demo()
        saida = capsys.readouterr().out
        assert "Demo concluído com sucesso" in saida


class TestSuitesInternas:

    def test_selftest_v14(self):
        assert run_v14_selftest(verbose=False) is True

    @pytest.mark.slow
    def test_suite_cognitiva(self):
        assert run_nexus_tests(verbose=False) is True


# ══════════════════════════════════════════════════════════════════════════════
# 5. SERVIDOR HTTP (quando fastapi está disponível)
# ══════════════════════════════════════════════════════════════════════════════

class TestServidorHTTP:

    @pytest.fixture(scope="class")
    def client(self):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient
        import nexus_server
        with TestClient(nexus_server.app) as c:
            yield c

    def test_index_renderiza_ui(self, client):
        resposta = client.get("/")
        assert resposta.status_code == 200
        assert "Nexus V14 Unified" in resposta.text
        assert "/api/chat" in resposta.text

    def test_chat_e_aprendizado(self, client):
        client.post("/api/learn", json={"fact": "a célula é a unidade básica da vida"})
        resposta = client.post("/api/chat", json={"text": "o que é célula?"})
        assert resposta.status_code == 200
        assert "célula" in resposta.json()["response"].lower()

    def test_status_e_brains(self, client):
        status = client.get("/api/status").json()
        assert status["brains"] == 8
        brains = client.get("/api/brains").json()["brains"]
        assert len(brains) == 8

    def test_iot_pipeline(self, client):
        resposta = client.post("/api/iot", json={
            "domain": "biologia", "sensor": "sensor_01",
            "data": "sequência genômica ATCG identificada com 98.7% de match",
        }).json()
        assert resposta["status"] == "ACCEPTED"
        bloqueado = client.post("/api/iot", json={
            "domain": "biologia", "sensor": "sensor_anomalo", "data": "x",
        }).json()
        assert bloqueado["status"] == "REJECTED"

    def test_criptografia_e_sensorial(self, client):
        cifrado = client.post("/api/crypto", json={"text": "segredo", "mode": "encrypt"}).json()
        decifrado = client.post("/api/crypto",
                                json={"text": cifrado["result"], "mode": "decrypt"}).json()
        assert decifrado["result"] == "segredo"
        assert client.post("/api/sensory/image", json={"size": 8}).json()["active_bits"] == 40
        assert client.post("/api/sensory/audio",
                           json={"frequency": 440, "seconds": 0.1}).json()["active_bits"] == 40

    def test_endpoints_invalidos(self, client):
        assert client.post("/api/chat", json={"text": ""}).status_code == 422
        assert client.post("/api/crypto",
                           json={"text": "zz", "mode": "decrypt"}).status_code == 400
