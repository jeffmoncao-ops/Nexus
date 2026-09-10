#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NEXUS V14 — TESTES DE REGRESSÃO (bugs reais já encontrados)                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Princípio desta suíte: cada teste aqui existe porque um bug REAL aconteceu (ou
porque um comportamento crítico pode regredir silenciosamente). As suítes
antigas passavam enquanto o sistema alucinava, respondia "Aprendi" sem
armazenar, quebrava ao carregar estado e gravava 22 MB por save.

Ordem: memória → epistemicidade → persistência → produção → HTTP → ingestão.
"""
from __future__ import annotations

import asyncio
import json
import os

import pytest

from nexus_core import (                                    # noqa: E402
    NexusGuardV11, NexusV10, NexusV14Unified, ProvenanceStore,
    SOURCE_CONFIDENCE, SparseSDR, VERSION, run_nexus_tests,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture()
def kernel():
    """Kernel limpo com estado efêmero (proveniência em memória)."""
    k = NexusV14Unified()
    k.cognitive.set_provenance_path(':memory:')
    return k


# ══════════════════════════════════════════════════════════════════════════════
# 1. MEMÓRIA (SDR) — regressão do construtor que engolia iteráveis
# ══════════════════════════════════════════════════════════════════════════════

class TestSparseSDRRegressao:
    """SparseSDR(range(n)) retornava SDR vazio: bug silencioso de densidade."""

    @pytest.mark.parametrize("entrada", [
        range(80), (i for i in range(80)), {1, 2, 3}, frozenset({4, 5}),
        [7, 7, 7], (8, 9), tuple(range(5)),
    ])
    def test_aceita_qualquer_iteravel(self, entrada):
        sdr = SparseSDR(entrada)
        assert len(sdr) > 0, f'{type(entrada).__name__} foi descartado'

    def test_range_produz_densidade_correta(self):
        sdr = SparseSDR(range(80))
        assert len(sdr) == 80
        assert sdr.sparsity() == pytest.approx(80 / 4096)

    def test_duplicatas_e_ordem(self):
        assert SparseSDR([7, 7, 7]).to_list() == [7]

    def test_copia_de_outro_sdr(self):
        original = SparseSDR([1, 2, 3])
        copia = SparseSDR(original)
        assert copia.to_list() == original.to_list()
        copia |= SparseSDR([4])
        assert original.to_list() == [1, 2, 3], 'cópia mutou o original'

    def test_entrada_invalida_nao_estoura(self):
        assert len(SparseSDR(['a', 'b'])) == 0
        assert len(SparseSDR(None)) == 0
        assert len(SparseSDR('texto')) == 0


# ══════════════════════════════════════════════════════════════════════════════
# 2. EPISTEMICIDADE — o contrato anti-alucinação
# ══════════════════════════════════════════════════════════════════════════════

class TestGateEpistemico:
    """Quatro bugs reais: prefixo de 3 chars, XOR devolvendo outro sujeito,
    seleção fora do gate e eco da própria consulta."""

    FATOS = {
        'mitocôndria': 'a mitocôndria produz ATP nas células eucarióticas',
        'quicksort': 'o algoritmo quicksort ordena arrays usando um pivô e recursão',
        'ohm': 'a lei de Ohm estabelece que V = I × R',
    }

    @pytest.fixture()
    def k(self, kernel):
        for fato in self.FATOS.values():
            kernel.learn(fato)
        return kernel

    def test_gate_rejeita_radical_alheio(self, kernel):
        core = kernel.cognitive._core
        # fato sem nenhum radical em comum → rejeitado
        assert not core._fact_is_relevant('o que é um quasar?',
                                          'Lua é o único satélite natural da Terra')
        # "supermassivo" (quasar) NÃO pode casar com "superfície" (radical de 6)
        assert not core._fact_is_relevant(
            'o que é um quasar supermassivo?',
            'a superfície da Terra é coberta por água')
        # ...mas flexões legítimas continuam passando
        assert core._fact_is_relevant('o que é mitocôndria?',
                                      'a mitocôndria produz ATP nas células')
        assert core._fact_is_relevant('o que é um quasar?',
                                      'os quasares são núcleos galácticos ativos')

    def test_desconhecidos_nao_recebem_fato_alheio(self, k):
        for pergunta in ['o que é um quasar?', 'o que é entropia?',
                         'quem foi napoleão?', 'o que é um buraco negro?']:
            resp = k.chat(pergunta).lower()
            assert 'pitágoras' not in resp, f'{pergunta} → alucinou Pitágoras'
            assert not any(v.lower()[:24] in resp for v in self.FATOS.values()), \
                f'{pergunta} → devolveu fato não relacionado: {resp[:80]}'
            marcadores = ('não conheço', 'conheço', 'me ensine', 'conceito novo',
                          'ainda não está', 'quero saber mais', 'pode me explicar')
            assert any(m in resp for m in marcadores), \
                f'{pergunta} → não admitiu ignorância: {resp[:80]}'

    def test_conhecidos_continuam_respondendo(self, k):
        assert 'atp' in k.chat('o que é mitocôndria?').lower()
        assert 'pivô' in k.chat('o que é quicksort?').lower()
        assert 'v = i' in k.chat('o que é a lei de ohm?').lower()

    def test_xor_nao_responde_definicao_de_outro_sujeito(self, kernel):
        """bind('mitocôndria','é',…) respondia para "o que é ribossomo?"."""
        kernel.learn(self.FATOS['mitocôndria'])
        resp = kernel.chat('o que é o ribossomo?').lower()
        assert 'atp' not in resp, f'XOR devolveu definição alheia: {resp[:90]}'

    def test_xor_verificado_devolve_sujeito_armazenado(self, kernel):
        core = kernel.cognitive._core
        core.xor_bind.bind('mitocondria', 'é', 'organela que produz ATP')
        for _overlap, sujeito, _objeto in core.xor_bind.unbind_object_verified(
                'mitocondria', 'é', top_k=3, min_overlap=0.0):
            assert sujeito  # quem chama consegue validar o sujeito
            break
        # assinatura antiga preservada
        assert all(len(t) == 2 for t in core.xor_bind.unbind_object('mitocondria', 'é'))

    def test_cobertura_quantifica_o_que_falta(self, k):
        conhecida = k.cognitive._core.estimate_coverage('o que é mitocôndria?')
        desconhecida = k.cognitive._core.estimate_coverage('o que é um quark top?')
        assert conhecida['known'] is True and conhecida['score'] > 0.5
        assert desconhecida['known'] is False
        assert 'quark' in desconhecida['missing']

    def test_resposta_parcial_quando_conceito_e_conhecido(self, kernel):
        """Sem definição, mas com relações no grafo → resposta útil e honesta."""
        kernel.cognitive._core.concept_graph.add_edge(
            'ribossomo', 'sintetiza', 'proteínas', weight=0.8)
        resp = kernel.chat('o que é o ribossomo?')
        assert 'ribossomo' in resp.lower()
        assert 'não tenho' in resp.lower() or 'me ensine' in resp.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 3. PERSISTÊNCIA — 18 atributos ausentes + save de 22 MB + "Aprendi" falso
# ══════════════════════════════════════════════════════════════════════════════

class TestPersistencia:

    def test_load_restaura_todos_os_atributos(self, tmp_path):
        fresh = NexusV10()
        fresh.learn('aprenda: a mitocôndria produz ATP nas células eucarióticas')
        p = str(tmp_path / 'estado.json')
        assert fresh.save(p)
        carregado = NexusV10.load(p)
        faltando = set(vars(fresh)) - set(vars(carregado))
        assert not faltando, f'load não restaurou: {sorted(faltando)}'

    def test_chat_funciona_apos_load(self, tmp_path):
        """Antes, o primeiro chat() de um estado carregado estourava AttributeError."""
        k = NexusV10()
        k.learn('aprenda: o algoritmo quicksort ordena arrays usando um pivô e recursão')
        p = str(tmp_path / 'estado.json')
        k.save(p)
        carregado = NexusV10.load(p)
        assert 'pivô' in carregado.chat('o que é quicksort?').lower()
        assert '= 84' in carregado.chat('calcule 12 * (3 + 4)')

    def test_save_compacto(self, tmp_path):
        """Vetores em base64/float32: 22,8 MB → ~5,3 MB."""
        k = NexusV14Unified()
        for i in range(20):
            k.learn(f'fato sintético número {i} sobre sensores de pressão do reator')
        p = str(tmp_path / 'estado.json')
        k.save_state(p)
        tamanho_mb = os.path.getsize(p) / 1e6
        assert tamanho_mb < 8.0, f'save voltou a inchar: {tamanho_mb:.1f} MB'
        dados = json.load(open(p, encoding='utf-8'))
        assert dados['embed'].get('vec_fmt') == 'f32b64'

    def test_precisao_preservada_no_save(self, tmp_path):
        k = NexusV14Unified()
        k.learn('a clorofila absorve luz nas faixas azul e vermelha do espectro')
        p = str(tmp_path / 'estado.json')
        k.save_state(p)
        carregado = NexusV14Unified()
        assert carregado.load_state(p)
        v1 = k.cognitive._core.embed._input_vec['clorofila']
        v2 = carregado.cognitive._core.embed._input_vec['clorofila']
        assert max(abs(a - b) for a, b in zip(v1, v2)) < 1e-6

    def test_formatos_antigo_e_novo_de_vetor(self):
        embed = NexusV10().embed
        legado = {'dim': 768, 'vocab': ['x'], 'ctx_vec': {'x': [0.5, 0.25]}}
        assert embed.from_dict(legado)._ctx_vec['x'][:2] == [0.5, 0.25]

    def test_load_state_reatribui_brains(self, tmp_path):
        k = NexusV14Unified()
        k.cognitive.learn_document(
            'A mitocôndria produz ATP nas células eucarióticas. '
            'O algoritmo quicksort ordena arrays com um pivô.')
        p = str(tmp_path / 'estado.json')
        k.save_state(p)
        k2 = NexusV14Unified()
        assert k2.load_state(p)
        assert len(k2.cognitive._shared_memory.all_facts(brain_filter='biologia')) >= 1

    def test_learn_nao_mente_apos_load(self, tmp_path):
        """"Aprendi" só quando o fato realmente entrou no FactStore."""
        k = NexusV14Unified()
        fato = 'a mitocôndria produz ATP nas células eucarióticas'
        k.learn(fato)
        p = str(tmp_path / 'estado.json')
        k.save_state(p)
        k2 = NexusV14Unified()
        k2.load_state(p)
        antes = len(k2.cognitive.fact_store)
        msg = k2.learn(fato)
        assert 'Aprendi' not in msg, f'reportou aprendizado falso: {msg[:80]}'
        assert msg.lower().startswith('[dedup]')
        assert len(k2.cognitive.fact_store) == antes


# ══════════════════════════════════════════════════════════════════════════════
# 4. PROVENIÊNCIA — origem, confiança, evidência e uso
# ══════════════════════════════════════════════════════════════════════════════

class TestProveniencia:

    def test_origem_registrada_por_tipo_de_aprendizado(self, kernel):
        kernel.learn('o ciclo da água envolve evaporação e condensação',
                     source='document', evidence='hidrologia.md')
        ex = kernel.explain('ciclo da água')
        assert ex['known'] and ex['source'] == 'document'
        assert ex['evidence'] == 'hidrologia.md'
        assert ex['confidence'] == pytest.approx(SOURCE_CONFIDENCE['document'])

    def test_confianca_padrao_por_fonte(self):
        store = ProvenanceStore(':memory:')
        store.record('fato do usuário', source='user')
        store.record('fato da wiki', source='wikipedia')
        store.record('fato desconhecido', source='origem-inexistente')
        assert store.get('fato do usuário').confidence == SOURCE_CONFIDENCE['user']
        assert store.get('fato da wiki').confidence == SOURCE_CONFIDENCE['wikipedia']
        assert store.get('fato desconhecido').confidence < 1.0

    def test_dedup_nao_duplica_proveniencia(self, kernel):
        fato = 'a mitocôndria produz ATP nas células eucarióticas'
        kernel.learn(fato)
        total = len(kernel.cognitive.provenance)
        kernel.learn(fato)
        assert len(kernel.cognitive.provenance) == total

    def test_bump_de_uso_na_recuperacao(self, kernel):
        kernel.learn('a mitocôndria produz ATP nas células eucarióticas')
        kernel.chat('o que é mitocôndria?')
        assert kernel.explain('mitocôndria')['accesses'] >= 1

    def test_idempotencia_e_backfill(self, kernel):
        store = kernel.cognitive.provenance
        assert store.record('fato A') is True
        assert store.record('fato A') is False
        assert store.backfill(['fato A', 'fato B'], source='legacy') == 1

    def test_cobertura_e_estatisticas(self, kernel):
        rel = kernel.provenance_report()
        assert rel['tracked'] > 0
        assert 0.0 <= rel['coverage'] <= 1.0
        assert 'seed' in rel['sources']

    def test_migracao_ao_trocar_de_arquivo(self, kernel, tmp_path):
        kernel.cognitive.set_provenance_path(':memory:')
        kernel.learn('conhecimento novo para migrar')
        antes = len(kernel.cognitive.provenance)
        kernel.cognitive.set_provenance_path(str(tmp_path / 'prov.db'))
        assert len(kernel.cognitive.provenance) >= antes
        assert kernel.explain('conhecimento novo para migrar')['known']


# ══════════════════════════════════════════════════════════════════════════════
# 5. INGESTÃO — dedup real, relatório e fontes externas dubladas
# ══════════════════════════════════════════════════════════════════════════════

class TestIngestao:

    TEXTO = ('A mitocôndria é a organela responsável pela respiração celular. '
             'O núcleo contém o material genético da célula. '
             'x\n')

    def test_split_facts_limpa_e_filtra(self):
        import nexus_ingest
        fatos = nexus_ingest.split_facts(self.TEXTO)
        assert len(fatos) == 2
        assert all(len(f) >= 20 for f in fatos)
        assert not any('x' == f for f in fatos)

    def test_ingestao_conta_novos_e_duplicados(self, kernel):
        import nexus_ingest
        m1 = nexus_ingest.ingest_text(kernel, self.TEXTO, evidence='aula.md')
        assert m1['new'] == 2 and m1['duplicates'] == 0
        m2 = nexus_ingest.ingest_text(kernel, self.TEXTO, evidence='aula.md')
        assert m2['new'] == 0 and m2['duplicates'] == 2, 'dedup não bloqueou reingestão'

    def test_ingestao_registra_evidencia(self, kernel):
        import nexus_ingest
        nexus_ingest.ingest_text(kernel, self.TEXTO, evidence='aula.md')
        assert kernel.explain('mitocôndria')['evidence'] == 'aula.md'

    def test_jsonl_aceita_campos_opcionais(self, kernel, tmp_path):
        import nexus_ingest
        p = tmp_path / 'fatos.jsonl'
        p.write_text('\n'.join([
            json.dumps({'text': 'a clorofila absorve luz azul e vermelha',
                        'source': 'user', 'confidence': 0.9}),
            json.dumps({'fact': 'o ribossomo sintetiza proteínas no citoplasma'}),
            'linha inválida',
            json.dumps({'text': 'x'}),
        ]), encoding='utf-8')
        m = nexus_ingest.ingest_jsonl(kernel, str(p))
        assert m['new'] == 2
        assert kernel.explain('clorofila')['confidence'] == pytest.approx(0.9)

    def test_wiki_com_fetch_dublado(self, kernel):
        import nexus_ingest
        def fake_fetch(titulo):
            return {'extract': 'A fotossíntese converte luz solar em glicose nas plantas. '
                               'A clorofila é o pigmento responsável pela absorção de luz.',
                    'title': titulo}
        res = nexus_ingest.ingest_wiki(kernel, ['Fotossíntese'], fetch=fake_fetch)
        assert res[0]['new'] == 2
        assert res[0]['url'].startswith('https://pt.wikipedia.org/')
        assert kernel.explain('fotossíntese')['source'] == 'wikipedia'

    def test_wiki_offline_falha_sem_derrubar(self, kernel):
        import nexus_ingest
        def fetch_quebrado(_t):
            raise OSError('sem rede')
        res = nexus_ingest.ingest_wiki(kernel, ['Qualquer'], fetch=fetch_quebrado)
        assert res[0]['error'] and res[0]['new'] == 0

    def test_cli_gera_relatorio(self, kernel, tmp_path, monkeypatch, capsys):
        import nexus_ingest
        arquivo = tmp_path / 'corpus.md'
        arquivo.write_text(self.TEXTO, encoding='utf-8')
        rel = tmp_path / 'rel.json'
        estado = tmp_path / 'estado.json'
        monkeypatch.chdir(tmp_path)
        code = nexus_ingest.main(['--file', str(arquivo), '--report', str(rel),
                                  '--state', str(estado), '--quiet'])
        capsys.readouterr()
        assert code == 0
        dados = json.load(open(rel, encoding='utf-8'))
        assert dados['schema'] == 'nexus.ingest.report/1'
        assert dados['totals']['new_facts'] == 2
        assert dados['state']['saved'] is True

    def test_cli_idempotente_entre_execucoes(self, tmp_path, monkeypatch, capsys):
        """Reingerir o mesmo corpus não pode duplicar conhecimento."""
        import nexus_ingest
        arquivo = tmp_path / 'corpus.md'
        arquivo.write_text(self.TEXTO, encoding='utf-8')
        estado = tmp_path / 'estado.json'
        monkeypatch.chdir(tmp_path)
        nexus_ingest.main(['--file', str(arquivo), '--state', str(estado), '--quiet'])
        capsys.readouterr()
        nexus_ingest.main(['--file', str(arquivo), '--report', 'r2.json',
                           '--state', str(estado), '--quiet'])
        capsys.readouterr()
        dados = json.load(open('r2.json', encoding='utf-8'))
        assert dados['totals']['new_facts'] == 0
        assert dados['totals']['duplicates_skipped'] == 2


# ══════════════════════════════════════════════════════════════════════════════
# 6. PRODUÇÃO / SEGURANÇA — determinismo, limites, código
# ══════════════════════════════════════════════════════════════════════════════

class TestProducaoERegressao:

    def test_cifra_e_deterministica_e_roundtrip(self):
        """Determinismo é um CONTRATO CONHECIDO (e uma limitação declarada):
        mesma entrada → mesma saída. Se isto mudar, a doc precisa mudar."""
        g = NexusGuardV11()
        assert g.encrypt_payload('segredo') == NexusGuardV11().encrypt_payload('segredo')
        assert g.decrypt_payload(g.encrypt_payload('segredo')) == 'segredo'

    @pytest.mark.parametrize("payload", [
        '', 'a', 'x' * 1000, 'acentuação çãõ é', '{"json": true}', '1234567890',
    ])
    def test_cifra_roundtrip_varios_tamanhos(self, payload):
        g = NexusGuardV11()
        assert g.decrypt_payload(g.encrypt_payload(payload)) == payload

    def test_cifra_detecta_truncamento(self):
        g = NexusGuardV11()
        with pytest.raises(ValueError):
            g.decrypt_payload('00')

    def test_gateway_limites(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        async def corrida():
            k = NexusV14Unified(production=True)
            grande = await k.gateway.receive_data('s1', 'a' * 5000)
            resposta = None
            for _ in range(15):
                resposta = await k.gateway.receive_data('s1', 'telemetria válida do sensor')
            return grande, resposta
        grande, resposta = asyncio.run(corrida())
        assert grande == '413 Payload Too Large'
        assert resposta == '429 Too Many Requests'

    def test_code_generalizer_pedidos_genericos(self, kernel):
        core = kernel.cognitive._core
        r = core.code_eng.run('ordenar uma lista de números')
        assert r['success'] and 'sort' in r['code'].lower(), r['code'][:60]
        # pedido sem relação com nenhum template deve ser honesto
        r2 = core.code_eng.run('fazer um bolo de chocolate com cobertura')
        assert r2['success'] is False, r2['code'][:60]
        assert 'não encontrado' in r2['error'].lower()

    @pytest.mark.slow
    def test_suite_interna_continua_verde(self):
        assert run_nexus_tests(verbose=False) is True


# ══════════════════════════════════════════════════════════════════════════════
# 7. HTTP — contrato completo das rotas (incl. proveniência e ingestão)
# ══════════════════════════════════════════════════════════════════════════════

class TestApiCompleta:

    @pytest.fixture(scope="class")
    def client(self):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient
        import nexus_server
        with TestClient(nexus_server.app) as c:
            yield c

    def test_rotas_de_leitura(self, client):
        assert client.get('/').status_code == 200
        for rota in ['/api/health', '/api/status', '/api/brains',
                     '/api/domains', '/api/provenance']:
            assert client.get(rota).status_code == 200, rota

    def test_status_tem_metricas_reais(self, client):
        st = client.get('/api/status').json()
        assert st['version'] == VERSION
        assert st['facts'] > 0 and st['brains'] == 8
        prov = st.get('provenance') or {}
        assert prov.get('tracked', 0) > 0, 'status deve expor a proveniência'
        assert 0.0 < prov.get('coverage', 0) <= 1.0

    def test_ingestao_pela_api(self, client):
        d = client.post('/api/ingest', json={
            'text': 'O ribossomo sintetiza proteínas a partir do RNA mensageiro. '
                    'A membrana plasmática regula a troca de substâncias.',
            'source': 'ingest', 'evidence': 'aula.md'}).json()
        assert d['ingest']['new'] >= 1
        assert d['provenance']['tracked'] > 0

    def test_explain_e_coverage(self, client):
        client.post('/api/learn', json={'fact': 'a fotossíntese produz glicose',
                                        'source': 'user'})
        ex = client.post('/api/explain', json={'fact': 'fotossíntese'}).json()
        assert ex['known'] and ex['source'] == 'user'
        cov = client.post('/api/coverage', json={'query': 'o que é fotossíntese?'}).json()
        assert cov['known'] is True and 'missing' in cov

    def test_erros_controlados(self, client):
        assert client.post('/api/learn', json={'fact': 'x'}).status_code == 422
        assert client.post('/api/coverage', json={'query': ''}).status_code == 422
        assert client.post('/api/crypto',
                           json={'text': 'zz', 'mode': 'decrypt'}).status_code == 400

    def test_ui_expoe_os_paineis_novos(self, client):
        html = client.get('/').text
        for marcador in ['doIngest', 'doExplain', 'api/chat', 'api/iot']:
            assert marcador in html, marcador
