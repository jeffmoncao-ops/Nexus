# O Conectoma da Drosophila melanogaster como Referência para o Nexus

**Data da análise:** 2026-09-11 · **Dados:** FlyWire v783 — Female Adult Fly Brain (FAFB), CC-BY-4.0

Este documento resume a análise da estrutura e do funcionamento do cérebro da mosca-da-fruta
— o primeiro conectoma completo de um animal adulto capaz de comportamento complexo —
e como cada princípio arquitetural medido nos dados foi traduzido em modificações concretas
no kernel Nexus.

As estatísticas abaixo foram **medidas diretamente** a partir dos arquivos públicos do
FlyWire (`classification.csv`, `neurons.csv`, `connections.csv`), acessados via
[codex.flywire.ai](https://codex.flywire.ai). O destilado completo está em
[`data/drosophila_connectome_reference.json`](../data/drosophila_connectome_reference.json).

---

## 1. O que foi acessado e analisado

| Dataset | Descrição | Neurônios | Conexões |
|---|---|---|---|
| **FlyWire v783 (FAFB)** ← analisado | Cérebro adulto fêmea, completo | **139.255** | 3.869.878 pares / 34,15 M sinapses (na tabela); >50 M publicadas |
| BANC v888 | Cérebro + cordão nervoso (fêmea) | 158.262 | 3.037.361 |
| MANC v1.2.1 | Cordão nervoso (macho) | 23.665 | 5.305.638 |
| MCNS v1.0 | SNC completo (macho) | 166.700 | 6.242.118 |

Fontes: Dorkenwald et al. 2024 (Nature, conectoma FlyWire); Schlegel et al. 2024
(Nature, anotação whole-brain — 8.453 tipos celulares, 4.581 novos); contagens oficiais
dos datasets publicadas na página pública do Codex.

## 2. Estrutura global medida

- **139.255 neurônios** em **123 neuropilos** (regiões), **8.453 tipos celulares** anotados.
- **Dominância visual**: 55,8% dos neurônios são ópticos (o olho domina o cérebro da mosca).
- **85% dos neurônios são intrínsecos** — o cérebro fala principalmente consigo mesmo
  (feedback massivo), com 19.300 aferentes e 1.491 eferentes.
- **Simetria bilateral**: 69.959 à esquerda vs 69.093 à direita — tipos celulares
  estereotipados entre hemisférios.
- **Hubs**: distribuição de grau de cauda pesada (mediana de entrada 12, máx. 13.826);
  o **top-1% de hubs captura 19,4%** de todas as conexões aferentes ("rich club").
- **Reciprocidade**: **9,8%** dos pares conectados têm a aresta reversa — laços
  recorrentes em todas as escalas.
- **Sinapses por conexão**: mediana 6, média 8,8 (p99 = 56) — conexões são
  polasssinápticas e graduadas, não binárias.
- **Neurotransmissores** (predição para 119.597 neurônios):

| NT | Neurônios | % | Papel |
|---|---|---|---|
| ACH (colinérgico) | 82.298 | 59,1% | excitatório principal |
| GLUT (glutamatérgico) | 19.605 | 14,1% | excitatório/aversivo no MB |
| GABA (GABAérgico) | 16.017 | 11,5% | inibitório (inclui APL/GGN) |
| SER (serotoninérgico) | 1.021 | 0,73% | modulador global |
| DA (dopaminérgico) | 584 | 0,42% | **professor do aprendizado** |
| OCT (octopaminérgico) | 72 | 0,05% | modulador global (arousal) |

→ **Moduladores somam 1,2% do cérebro**: pouquíssimos neurônios controlam o estado
global (aprendizado, humor, arousabilidade). É o princípio do "ganho global escalar".

## 3. O corpo cogumelar (mushroom body) em números reais

O corpo cogumelar é o centro de aprendizado associativo da mosca — e o exemplo
biológico canônico de **codificação esparso-distribuída** (o mesmo paradigma do
espaço HDC/SDR de 10.000 bits do Nexus).

Circuito medido nos dados (por hemisfério, salvo indicação):

```
ALPN (342 neurônios de projeção do lobo antenal)
        │  projeção aleatória esparssa (cada KC amostra ~10 entradas)
        ▼
KC (2.588 células de Kenyon)  ←── APL (1 neurônio GABAérgico gigante,
        │                          recebe 13.402 sinapses dos KCs:
        │                          inibição por feedback global → ~5% ativos)
        ▼
MBON (96 células; por NT: 51 ACH, 23 GLUT, 17 GABA)  → valência: aproximar/evitar
        ▲
DAN (331 neurônios dopaminérgicos: PAM=recompensa, PPL1=punição)
        porta a plasticidade KC→MBON (regra de três vias: KC ∩ DAN ∩ MBON)
```

Números-chave medidos:

- **5.177 KCs** (2.588/hemisfério); cada KC recebe de **~10 parceiros distintos** (mediana 10, p90 14);
- **Cada PN mediano atinge apenas 60 KCs = 1,2% do pool** → o odor vira código esparso;
- **APL confirmado nos dados**: os dois maiores alvos dos KCs são MBINs GABAérgicos
  (13.402 e 13.330 sinapses recebidas) — um por hemisfério;
- **Saída valenciada**: 96 MBONs; glutamatérgicas codificam valência aversiva,
  colinérgicas a apetitiva (Aso et al.); 35 tipos na literatura (21 típicos + 14 atípicos);
- **Loo recursivo KC→DAN** (3.312 sinapses) — base da predição de recompensa;
- **Via dupla**: o mesmo input olfatório vai para o **lobo lateral** (inata, rápida,
  42 LHCENTs) **e** para o corpo cogumelar (aprendida, plástica).

## 4. Princípios → modificações no Nexus

| # | Princípio (evidência medida) | Implementação no Nexus |
|---|---|---|
| 1 | **Expandir & Esparsificar** — projeção aleatória esparssa (10 entradas/KC) + expansão ~8× + inibição APL → código ~5% ativo; Dasgupta et al. 2017 mostram que supera LSH para busca de similaridade | **`MushroomBody`**: 2.048 KCs, cada um amostra **10 bits** do espaço SDR de 10.000 (mediana real); disparo com ≥1 hit → **~5% ativos** naturalmente; `similarity()` = Jaccard dos códigos KC (fly-hash) |
| 2 | **Inibição por feedback global** (APL no MB, GGN no lobo antenal): 1 neurônio normaliza toda a população → k-winner-take-all | **`SpikingCortex`**: inibição lateral (k-WTA) — no máximo 25% da população dispara por passo; perdedores são shuntados (V_m × 0,5). Após treino massivo o código populacional continua esparso (antes: saturava em 43/50) |
| 3 | **Poucos professores globais** — 331 DANs (0,24%) portam a plasticidade KC→MBON; sem dopamina não há aprendizado (bloqueio experimental de DAN abole memória) | **`MushroomBody.learn()`** com portão dopaminérgico: `dopamine=0` → zero plasticidade (extinção); **`Neuromodulation`**: estado global DA/SER/OCT |
| 4 | **Valência de saída** — MBONs de NTs distintos codificam aproximar/evitar; decisão emerge da soma | **34 MBONs** no Nexus (17 apetitivos "PAM", 17 aversivos "PPL1"); `readout()` → `{valence, decision: approach/avoid/neutral}` |
| 5 | **Via dupla inata/aprendida** — lobo lateral (fixo) vs corpo cogumelar (plástico), mesma entrada | `perceive()` reporta as duas vias: **inata** (familiaridade via memória existente — CognitiveBrain) + **aprendida** (valência via corpo cogumelar) |
| 6 | **Generalização semântica** — conceitos que compartilham bits de entrada compartilham KCs ativos → herdam valência | Teste determinístico: reforço em "mamífero" → "gato" (25/60 bits) e "cachorro" (22/60) herdam valência positiva; "carro" (0/60) não |
| 7 | **Aprendizado tripartite** (regra de Aso: KC ∩ reforço ∩ compartimento) | `learn(sdr, reward)`: sinapses KC→MBON mudam apenas nos MBONs cuja valência casa com o sinal do reforço |
| 8 | **Modulação de estado** — DA/SER/OCT mudam limiar e ganho de aprendizado do cérebro todo | `SpikingCortex.step(..., modulation=(da, oct))`: octopamina baixa o limiar (arousal), dopamina amplifica o ganho Hebbiano |

## 5. Validação esperada (testes BLOCO 12)

- Esparsidade do código KC entre 3% e 8% (alvo biológico ~5%) ✓
- `similarity(gato, mamífero) > 4 × similarity(gato, carro)` ✓
- Valência neutra (0) antes de qualquer reforço ✓
- Reforço em "mamífero" → gato/cachorro com valência > +0,5; carro < 1/3 disso ✓
- Punição → decisão "avoid"; sem dopamina → nenhuma mudança sináptica ✓
- Serialização preserva sinapses KC→MBON ✓
- Córtex com inibição lateral: população ≤ 25% mesmo após treino intenso ✓

## 6. Fontes

- Dorkenwald, S. et al. (2024). *Nature* — conectoma completo do cérebro adulto (FlyWire). Coleção: [The FlyWire connectome](https://www.nature.com/immersive/d42859-024-00053-4/index.html)
- Schlegel, P. et al. (2024). [Whole-brain annotation and multi-connectome cell typing of Drosophila](https://www.nature.com/articles/s41586-024-07686-5). *Nature*.
- Li, F. et al. (2020). [A connectome of the learning and memory center in the adult Drosophila brain](https://elifesciences.org/articles/26975). *eLife*.
- Rubin, G. M. & Aso, Y. (2023). New genetic tools for mushroom body output neurons in *Drosophila*. *eLife*.
- Aso, Y. et al. (2014). Mushroom body output neurons encode valence and guide memory-based action selection. *eLife*.
- Dasgupta, S. et al. (2017). [A neural algorithm for a fundamental computing problem](https://www.science.org/doi/10.1126/science.aam9868). *Science*.
- Winding, M. et al. (2023). The connectome of an animal brain. *Science* (conectoma larval, 3.016 neurônios).
- Dados: [FlyWire Codex](https://codex.flywire.ai) (FlyWire Consortium / Princeton Neuroscience Institute), CC-BY-4.0.

*Reprodução da análise:* os arquivos `classification.csv`, `neurons.csv` e `connections.csv`
do FlyWire v783 foram processados localmente (contagens de grau, reciprocidade,
distribuições de sinapses, composição por classe/neurotransmissor e conectividade
específica dos KCs/MBONs/DANs). O script de análise é descrito no histórico de commits.
