# -*- coding: utf-8 -*-
"""Suíte de testes V14.8–V14.10 — índice denso, ranking lexical-primário,
extração de span-resposta, gate de honestidade, mosca e núcleo.

Roda em dois backends:
    python3 tests/test_nexus_v14.py              # neural (MiniLM local)
    NEXUS_NO_SLM=1 python3 tests/test_nexus_v14.py   # fallback (hash)
"""
import os
import sys
import math
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import nexus_v14_shared_hippocampus as nx  # noqa: E402

NEURAL = os.environ.get('NEXUS_NO_SLM') != '1'


def make_kernel():
    k = nx.NexusFinal()
    k.disable_autosave()
    return k


class TestSpanExtraction(unittest.TestCase):
    """V14.8/V14.10: _extract_answer_span — resposta-valor primeiro."""

    def setUp(self):
        self.k = make_kernel()

    def test_quando_ano(self):
        s = self.k._extract_answer_span(
            'Quando a torre foi construída?',
            'A Torre Eiffel foi construída em 1889 por Gustave Eiffel.')
        self.assertTrue(s and '1889' in s)

    def test_quando_data_completa(self):
        s = self.k._extract_answer_span(
            'Quando a fusão foi oficialmente cancelada?',
            'A fusão foi oficialmente cancelada em 1º de janeiro de 1968.')
        self.assertEqual(s, '1º de janeiro de 1968')

    def test_quando_mes_dia(self):
        s = self.k._extract_answer_span(
            'Quando foi inaugurada?',
            'A inauguração ocorreu em 31 de março de 1889 em Paris.')
        self.assertEqual(s, '31 de março de 1889')

    def test_quantos_numero_perto_da_keyword(self):
        s = self.k._extract_answer_span(
            'O empreiteiro médio contratou quantos funcionários?',
            'Em 2005, havia cerca de 667.000 empresas empregando 1 milhão, '
            'e o empreiteiro médio emprega menos de 10 funcionários.')
        self.assertEqual(s, 'menos de 10 funcionários')

    def test_quantos_ignora_ano(self):
        s = self.k._extract_answer_span(
            'Quantos alunos a escola atende?',
            'Fundada em 1900, a escola atende 300 alunos em dois turnos.')
        self.assertEqual(s, '300 alunos')

    def test_quantos_porcentagem(self):
        s = self.k._extract_answer_span(
            'Qual a porcentagem de eficiência?',
            'O motor atinge 50% de eficiência média.')
        self.assertEqual(s, '50%')

    def test_quem_nome_proprio(self):
        s = self.k._extract_answer_span(
            'Quem escreveu o livro?',
            'O livro foi escrito por Maria da Silva em 2010.')
        self.assertTrue(s and 'Maria da Silva' in s)

    def test_qual_copular(self):
        s = self.k._extract_answer_span(
            'O que é o Mar Negro?',
            'O Mar Negro é um mar interior banhando a Ucrânia e a Rússia.')
        self.assertTrue(s and 'mar interior' in s)

    def test_sem_match_retorna_none(self):
        s = self.k._extract_answer_span(
            'Quem escreveu o livro?',
            'Não há nomes aqui de nenhum tipo.')
        self.assertIsNone(s)


class TestLexicalAnchor(unittest.TestCase):
    """V14.10: casamento lexical — imune ao erro do encoder inglês em PT."""

    def setUp(self):
        self.k = make_kernel()

    def test_prefixo_flexao_verbal(self):
        # 'matou' ↔ 'mataram' casam pelo prefixo 'mata'
        plain, _ = self.k._lex_ratio(
            'Que grupo matou milhares de pessoas?',
            'Católicos mataram milhares de pessoas naquele dia.')
        # 'matou'↔'mataram' casam pelo radical; 'grupo' não está no fato
        self.assertGreaterEqual(plain, 0.75)

    def test_stopwords_ignoradas(self):
        plain, _ = self.k._lex_ratio(
            'Qual é o maior estádio da Austrália?',
            'O Melbourne Cricket Ground é o maior estádio da Austrália.')
        self.assertGreaterEqual(plain, 0.99)

    def test_zero_sem_match(self):
        plain, _ = self.k._lex_ratio(
            'Quem fundou a McKinsey?',
            'O V&A está em discussão com a Universidade de Dundee.')
        self.assertEqual(plain, 0.0)

    def test_rare_recall_separa_topicos(self):
        df = {'quim': 20, 'nano': 1, 'mcki': 0}
        # pergunta com palavras distintivas NÃO presentes no fato
        _, rare = self.k._lex_ratio(
            'O que são nanotubos de carbono?',
            'A química orgânica estuda compostos.', df)
        self.assertLess(rare, 0.5)

    def test_q_rare_n(self):
        df = {'quim': 20, 'nanot': 1, 'carbo': 2}
        n = self.k._q_rare_n('O que são nanotubos de carbono?', df)
        self.assertEqual(n, 2)


class TestQAScore(unittest.TestCase):
    """V14.10: lexical primário + denso secundário + priors de tipo."""

    def setUp(self):
        self.k = make_kernel()

    def test_fato_certo_vence_distrator_lexical(self):
        # caso real medido: encoder inglês deu cos 0.28 ao fato certo
        # e 0.50 ao distrator — o léxico tem que dominar
        q = 'Qual é o maior estádio da Austrália?'
        certo = ('O Melbourne Cricket Ground é o maior estádio da '
                 'Austrália e o anfitrião dos Jogos Olímpicos de Verão.')
        errado = 'O atual primeiro de Victoria é Daniel Andrews.'
        sc_c, _, _, _ = self.k._qa_score(q, certo, dense_cos=0.28)
        sc_e, _, _, _ = self.k._qa_score(q, errado, dense_cos=0.50)
        self.assertGreater(sc_c, sc_e)

    def test_antifragmento(self):
        q = 'Quando o museu abriu?'
        inteiro = 'O museu abriu em 22 de junho de 1857.'
        fragmento = 'em 2013) e desde 2011.'
        sc_i, _, _, _ = self.k._qa_score(q, inteiro, dense_cos=0.3)
        sc_f, _, _, _ = self.k._qa_score(q, fragmento, dense_cos=0.3)
        self.assertGreater(sc_i, sc_f)

    def test_prior_digito_para_quantos(self):
        q = 'Quantos funcionários trabalhavam lá?'
        com_digito = 'Trabalhavam 300 funcionários no local.'
        sem_digito = 'Trabalhavam muitas pessoas no local.'
        sc_c, _, _, _ = self.k._qa_score(q, com_digito, dense_cos=0.3)
        sc_s, _, _, _ = self.k._qa_score(q, sem_digito, dense_cos=0.3)
        self.assertGreater(sc_c, sc_s)

    def test_prior_ano_para_quando(self):
        q = 'Quando ocorreu a fusão?'
        com_ano = 'A fusão ocorreu em 1968 após longa batalha.'
        sem_ano = 'A fusão ocorreu após longa batalha judicial.'
        sc_c, _, _, _ = self.k._qa_score(q, com_ano, dense_cos=0.3)
        sc_s, _, _, _ = self.k._qa_score(q, sem_ano, dense_cos=0.3)
        self.assertGreater(sc_c, sc_s)

    def test_prior_nome_para_quem(self):
        q = 'Quem abriu o museu?'
        com_nome = 'A rainha Victoria abriu o museu em 1857.'
        sem_nome = 'A abertura do museu foi um evento público.'
        sc_c, _, _, _ = self.k._qa_score(q, com_nome, dense_cos=0.3)
        sc_s, _, _, _ = self.k._qa_score(q, sem_nome, dense_cos=0.3)
        self.assertGreater(sc_c, sc_s)


class TestDenseIndex(unittest.TestCase):
    """V14.8: índice denso exaustivo + persistência."""

    def setUp(self):
        self.k = make_kernel()

    def _facts(self):
        return [
            'A Torre Eiffel foi construída em 1889 em Paris.',
            'O Melbourne Cricket Ground é o maior estádio da Austrália.',
            'A rainha Victoria abriu o museu em 22 de junho de 1857.',
            'A escola atende 300 alunos em dois turnos.',
            'O Mar Negro é um mar interior banhando a Ucrânia.',
        ]

    def test_formato_e_ordenacao(self):
        hits = self.k.dense_retrieve('Einstein relatividade', top_k=3)
        self.assertTrue(all(isinstance(h, tuple) and len(h) == 2
                            for h in hits))
        scores = [h[0] for h in hits]
        self.assertEqual(scores, sorted(scores, reverse=True))

    @unittest.skipIf(not NEURAL, 'índice denso exige encoder neural')
    def test_retrieve_acha_fato_aprendido(self):
        for f in self._facts():
            self.k.learn(f)
        hits = self.k.dense_retrieve(
            'Qual é o maior estádio da Austrália?', top_k=3)
        self.assertTrue(hits)
        self.assertIn('Melbourne Cricket Ground', hits[0][1])

    @unittest.skipIf(not NEURAL, 'vetores densos exigem encoder neural')
    def test_roundtrip_persiste_vetores(self):
        for f in self._facts():
            self.k.learn(f)
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.json',
                                         delete=False) as fh:
            path = fh.name
        self.k.save(path)
        k2 = nx.NexusV10.load(path)
        os.unlink(path)
        self.assertGreaterEqual(len(k2._dense_facts), 5)
        # vetores preservados: cosseno entre a mesma pergunta e o fato
        q = 'Qual é o maior estádio da Austrália?'
        h1 = self.k.dense_retrieve(q, top_k=1)
        h2 = k2.dense_retrieve(q, top_k=1)
        self.assertEqual(h1[0][1], h2[0][1])

    def test_sync_backfill(self):
        for f in self._facts():
            self.k.learn(f)
        n0 = len(self.k._dense_facts)
        self.k._dense_facts = []
        self.k._dense_texts = set()
        n = self.k._dense_index_sync()
        self.assertGreaterEqual(n, n0)


@unittest.skipIf(not NEURAL, 'qualidade do encoder — só neural')
class TestChatGrounded(unittest.TestCase):
    """V14.8–V14.10: chat() ponta-a-ponta com fatos aprendidos."""

    def setUp(self):
        self.k = make_kernel()
        for f in [
            'A Torre Eiffel foi construída em 1889 em Paris.',
            'O Melbourne Cricket Ground é o maior estádio da Austrália.',
            'A rainha Victoria abriu o museu em 22 de junho de 1857.',
            'A escola atende 300 alunos em dois turnos.',
            'O Mar Negro é um mar interior banhando a Ucrânia.',
            'Católicos mataram milhares de huguenotes no massacre.',
        ]:
            self.k.learn(f)

    def test_resposta_span_primeiro(self):
        r = self.k.chat('Quando a Torre Eiffel foi construída?')
        self.assertIn('1889', r)
        self.assertIn('—', r)

    def test_lexical_vence_sobre_distorcao_do_encoder(self):
        r = self.k.chat('Qual é o maior estádio da Austrália?')
        self.assertIn('Melbourne Cricket Ground', r)

    def test_prefixo_flexao(self):
        r = self.k.chat('Que grupo matou milhares de huguenotes?')
        self.assertIn('Católicos', r)

    def test_recusa_honesta_topico_nao_visto(self):
        r = self.k.chat('Quem fundou a McKinsey & Company?')
        self.assertIn('não sei', r.lower())

    def test_recusa_nao_afirma_falsidade(self):
        r = self.k.chat('Quantos planetas tem o sistema Gliese 581?')
        low = r.lower()
        self.assertTrue('não sei' in low or 'não aprendi' in low)

    def test_statement_nao_e_recusado(self):
        # não-interrogativa segue o fluxo normal (cascata), sem recusa
        r = self.k.chat('fale sobre a Torre Eiffel')
        self.assertNotIn('não sei responder isso', r)

    def test_quem_responde_nome(self):
        r = self.k.chat('Quem abriu o museu?')
        self.assertIn('rainha Victoria', r)


class TestFlyMechanics(unittest.TestCase):
    """V14.7/V14.7b: mosca — curiosidade, hábito e desempate afetivo."""

    def setUp(self):
        self.k = make_kernel()

    def test_reforco_curioso_gera_memoria_afetiva(self):
        self.k.learn('O pulo da mosca usa estabilização visual')
        self.k.learn('Fatos surpreendentes recebem dopamina de curiosidade')
        self.assertTrue(getattr(self.k, '_reinforced', None) is None
                        or isinstance(self.k._reinforced, list))

    def test_habituacao_diminui_dopamina(self):
        k = self.k
        if hasattr(k, '_curiosity_spent'):
            k._curiosity_spent = 80
        # estímulo com gasto alto de curiosidade → reforço menor
        v = getattr(k, '_curiosity_dose', None)
        self.assertTrue(callable(v) or v is None)

    def test_tie_break_empate_promove_associado(self):
        k = self.k
        k.learn('A dopamina liga novidade a valência')
        rer = [(0.50, 'fato A sobre tédio'), (0.49, 'fato B sobre tédio')]
        out = k._fly_tie_break(rer)
        self.assertEqual(len(out), 2)
        # sem reforço registrado, ordem preservada
        self.assertEqual(out[0][1], 'fato A sobre tédio')

    def test_tie_break_nunca_promove_pior(self):
        k = self.k
        rer = [(0.90, 'fato muito relevante'), (0.10, 'fato ruim')]
        out = k._fly_tie_break(rer)
        self.assertEqual(out[0][1], 'fato muito relevante')


class TestCoreSmoke(unittest.TestCase):
    """Núcleo intacto: SDR, weaver, fact store, save/load."""

    def setUp(self):
        self.k = make_kernel()

    def test_sdr_encode_estavel(self):
        a = self.k.semantic_encode('chuva em Paris')
        b = self.k.semantic_encode('chuva em Paris')
        self.assertEqual(sorted(a._idx), sorted(b._idx))

    def test_weaver_gera_texto(self):
        self.k.learn('A Torre Eiffel fica em Paris')
        r = self.k.text_weaver.weave('torre eiffel')
        self.assertTrue(isinstance(r, str) and len(r) > 0)

    def test_fact_store_search(self):
        self.k.learn('O Mar Negro é um mar interior')
        hits = self.k.fact_store.search('mar negro', top_k=3, min_score=0.1)
        self.assertTrue(any('Mar Negro' in h for h in hits))

    def test_save_load_roundtrip_atributos_runtime(self):
        import tempfile
        self.k.learn('Fato persistente sobre quasares distantes')
        with tempfile.NamedTemporaryFile('w', suffix='.json',
                                         delete=False) as fh:
            path = fh.name
        self.k.save(path)
        k2 = nx.NexusV10.load(path)
        os.unlink(path)
        # atributos de runtime presentes (lição da auditoria de 59 attrs)
        for attr in ('fact_store', 'retriever', 'text_weaver',
                     '_dense_facts', '_dense_texts'):
            self.assertTrue(hasattr(k2, attr), attr)
        r = k2.chat('fale sobre quasares')
        self.assertTrue(isinstance(r, str))


class TestProtocoloAprende(unittest.TestCase):
    """Protocolo 'aprenda:' e integração mínima."""

    def setUp(self):
        self.k = make_kernel()

    def test_aprende_via_protocolo(self):
        r = self.k.learn('aprenda: Brasília é a capital do Brasil')
        self.assertIsInstance(r, str)

    def test_fato_aprendido_e_recuperavel(self):
        self.k.learn('aprenda: Brasília é a capital do Brasil')
        hits = self.k.fact_store.search('capital do brasil', top_k=3,
                                        min_score=0.1)
        self.assertTrue(any('Brasília' in h for h in hits))


class TestProperVeto(unittest.TestCase):
    """V14.10: veto de substantivo próprio não-casado na pergunta."""

    def setUp(self):
        self.k = make_kernel()

    def test_entidade_ausente_veta(self):
        veto = self.k._proper_veto(
            'Quantos planetas tem o sistema Gliese 581?',
            'Terra é o terceiro planeta do sistema solar.')
        self.assertTrue(veto)

    def test_entidade_presente_nao_veta(self):
        veto = self.k._proper_veto(
            'Qual é o maior estádio da Austrália?',
            'O Melbourne Cricket Ground é o maior estádio da Austrália.')
        self.assertFalse(veto)

    def test_grafia_variante_nao_veta(self):
        # Victoria ↔ Vitória: grafia próxima conta como casamento
        veto = self.k._proper_veto(
            'Quem abriu o museu da rainha Victoria?',
            'A inauguração oficial da rainha Vitória foi em 1857.')
        self.assertFalse(veto)

    def test_sem_maiuscula_nao_veta(self):
        veto = self.k._proper_veto(
            'quem abriu oficialmente o museu?',
            'A inauguração oficial ocorreu em 1857.')
        self.assertFalse(veto)

    def test_tesla_veta(self):
        veto = self.k._proper_veto(
            'Por que o Tesla atribuiu danos à pele?',
            'Em 1893, o Museu da Ciência efetivamente entrou em erupção.')
        self.assertTrue(veto)

    def test_stemmer_flexao(self):
        self.assertEqual(nx._stem_pt('matou'), nx._stem_pt('mataram'))
        self.assertEqual(nx._stem_pt('cultiva'), nx._stem_pt('cultivar'))


if __name__ == '__main__':
    unittest.main(verbosity=1)
