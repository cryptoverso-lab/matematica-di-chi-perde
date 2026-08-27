# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Lab 12 — Un backtest onesto, riga per riga
#
# *Quaderno del capitolo «Che cos'è davvero un backtest» di
# **La matematica di chi perde**.*
#
# Due cose. La prima è un backtest scritto per essere **letto**: ogni passaggio
# commentato, i costi dentro, il calcolo causale. Si può seguire anche senza
# saper programmare.
#
# La seconda è il generatore del **metro**: dato un qualunque insieme di regole,
# produce le mille strategie casuali confrontabili e ti dice in quale percentile
# ti trovi. È il pezzo di codice che consiglio di riusare più di ogni altro.
#
# ---
#
# > **EN** — *Lab 12 — An honest backtest, line by line.* Notebook for the
# > chapter "What a backtest really is". Two things. The first is a backtest
# > written to be **read**: every step commented, costs included, causal
# > computation. You can follow it even without knowing how to program. The
# > second is the **yardstick** generator: given any set of rules, it
# > produces a thousand comparable random strategies and tells you which
# > percentile you're in. It's the piece of code I recommend reusing more
# > than any other.

# %% [markdown]
# Le righe marcate **PROVA** sono quelle da cambiare: cambiale e riesegui per
# vedere l'effetto. Il resto — comprese le righe marcate **NON TOCCARE** —
# serve a mantenere il risultato confrontabile con quello stampato nel libro.
#
# The lines marked **TRY** are the ones to change: edit them and rerun to see
# the effect. Everything else — including lines marked **DO NOT CHANGE** —
# exists to keep the result comparable with the one printed in the book.

# %%
# Setup — esegui questa cella per prima.
# %pip install -q "polars>=1.0"
try:
    import avvio
except ModuleNotFoundError:
    import urllib.request

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/cryptoverso-lab/matematica-di-chi-perde/main/codice/lab/avvio.py",
        "avvio.py",
    )
    import avvio

avvio.prepara(["btcusdt", "ethusdt", "solusdt"])

# %%
import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for
from cvbook.dati import carica
from cvbook.metriche import drawdown_massimo
from cvbook.regole import compra_e_tieni, esegui, sopra_media

SERIE = "btcusdt"  # ← PROVA / TRY: "ethusdt" · "solusdt" (le tre preparate nel setup)
FINESTRA = 50      # PROVA / TRY: 20 · 100 · 200 (vedi esercizio 1)
COSTO = 0.0012     # PROVA / TRY: raddoppialo (vedi esercizio 2)

prezzi = carica(SERIE).sort("data")["chiusura"].to_numpy()

# %% [markdown]
# ## 1. Il backtest, un passaggio alla volta
#
# La regola: **resto dentro al mercato quando il prezzo chiude sopra la sua media
# degli ultimi cinquanta giorni, resto fuori quando è sotto.**
#
# ---
#
# > **EN** — *1. The backtest, one step at a time.* The rule: **stay in the
# > market when price closes above its fifty-day average, stay out when
# > below.**

# %%
# Passo 1 — la media mobile. Alla riga t contiene la media dei prezzi FINO a t.
finestra = FINESTRA
cumulata = np.concatenate([[0.0], np.cumsum(prezzi)])
media = np.full(len(prezzi), np.nan)
media[finestra - 1:] = (cumulata[finestra:] - cumulata[:-finestra]) / finestra

# Passo 2 — il segnale. Confronta la chiusura di oggi con la sua media di oggi.
segnale = np.nan_to_num(np.where(prezzi > media, 1.0, 0.0))

# Passo 3 — LA RIGA CHE CONTA. La posizione di oggi usa il segnale di IERI.
# Senza questo sfasamento staremmo decidendo con un'informazione che, al momento
# della decisione, non esisteva ancora.
# NON TOCCARE / DO NOT CHANGE: questo sfasamento è la causalità del backtest.
# L'esercizio 3 ti invita a romperlo apposta per vedere il risultato
# spettacolare e falso che ne esce — non per lasciarlo rotto dopo.
# This lag is the backtest's causality. Exercise 3 invites you to break it on
# purpose to see the spectacular, fake result that comes out — not to leave
# it broken afterwards.
posizione = np.zeros(len(prezzi))
posizione[1:] = segnale[:-1]

# Passo 4 — il risultato, con i costi applicati a ogni cambio di posizione.
risultato = esegui(prezzi, posizione, costo=COSTO)

print(f"{SERIE}, media a {FINESTRA} giorni, costi {COSTO:.2%} per operazione\n")
print(f"capitale finale:      {risultato['finale']:8.2f}x")
print(f"al lordo dei costi:   {risultato['finale_lordo']:8.2f}x")
print(f"operazioni:           {risultato['operazioni']:8.0f}")
print(f"tempo dentro:         {risultato['esposizione']:8.1%}")
print(f"calo massimo:         {drawdown_massimo(risultato['curva']):8.1%}")

riferimento = esegui(prezzi, compra_e_tieni(prezzi), costo=COSTO)
print(f"\ncompra e tieni:       {riferimento['finale']:8.2f}x  "
      f"(calo massimo {drawdown_massimo(riferimento['curva']):.1%})")

# %% [markdown]
# ## 2. La verifica di causalità, che si fa in tre righe
#
# Il controllo meccanico e definitivo: calcola la posizione su tutta la serie,
# poi su una serie troncata a metà, e confronta la parte comune. **Devono essere
# identiche.** Se cambiano, il calcolo sta usando dati successivi.
#
# ---
#
# > **EN** — *2. The causality check, done in three lines.* The mechanical
# > and definitive test: compute the position over the whole series, then
# > over one truncated in half, and compare the common part. **They must be
# > identical.** If they change, the calculation is using future data.

# %%
completa = sopra_media(prezzi, FINESTRA)
for taglio in (500, 1500, 2500):  # PROVA / TRY: aggiungi un altro punto di taglio
    parziale = sopra_media(prezzi[:taglio], FINESTRA)
    uguali = np.allclose(parziale, completa[:taglio])
    esito_test = "SI" if uguali else "NO, c'e' un lookahead"
    print(f"troncando a {taglio:5d} giorni: posizioni identiche? {esito_test}")

# %% [markdown]
# ## 3. Il metro: rispetto a cosa?
#
# Non lo zero, non il compra-e-tieni. **Mille strategie che stanno dentro al
# mercato lo stesso numero di giorni, fanno lo stesso numero di operazioni e
# pagano gli stessi costi, ma scelgono i momenti a caso.**
#
# È il confronto che risponde alla domanda giusta: *serviva davvero un metodo?*
#
# ---
#
# > **EN** — *3. The yardstick: compared to what?* Not zero, not
# > buy-and-hold. **A thousand strategies that stay in the market the same
# > number of days, make the same number of trades and pay the same costs,
# > but choose their moments at random.** It's the comparison that answers
# > the right question: *did it really take a method?*

# %%
N_CASUALI = 1000


def _ripartisci(totale: int, parti: int, rng) -> np.ndarray:
    """Divide `totale` in `parti` addendi casuali, ciascuno almeno 1."""
    if parti == 1:
        return np.array([totale])
    libero = totale - parti
    tagli = np.sort(rng.integers(0, libero + 1, size=parti - 1))
    return np.diff(np.concatenate([[0], tagli, [libero]])) + 1


def posizione_casuale(n: int, giorni_dentro: int, n_operazioni: int, rng) -> np.ndarray:
    """Entra ed esce a caso, con gli STESSI giorni dentro e le stesse operazioni.

    Allineare solo le operazioni non basta: due strategie con lo stesso numero
    di entrate possono stare dentro al mercato per meta' del tempo o per il
    doppio, e su un asset che sale il tempo di esposizione vale piu' di
    qualunque bravura. Il metro deve tenere fissi tutti e due i numeri.
    """
    blocchi = max(n_operazioni // 2, 1)
    dentro = _ripartisci(giorni_dentro, blocchi, rng)
    fuori = _ripartisci(n - giorni_dentro, blocchi + 1, rng)
    pos = np.zeros(n)
    i = 0
    for b in range(blocchi):
        i += int(fuori[b])
        pos[i:i + int(dentro[b])] = 1.0
        i += int(dentro[b])
    return pos


def metro_del_caso(prezzi: np.ndarray, posizione: np.ndarray, *,
                   n_casuali: int = N_CASUALI, costo: float = COSTO,
                   seme: str = "metro-del-caso") -> dict:
    # NON TOCCARE / DO NOT CHANGE: «metro-del-caso» e' il seme della figura
    # stampata nel capitolo. Con quello — stesse mille strategie, stessi giorni
    # dentro, stesse operazioni — questa cella ridisegna l'istogramma del libro
    # e stampa il suo percentile. Con un seme qualunque il quaderno resta
    # corretto ma risponde con un numero diverso da quello in pagina, ed e'
    # esattamente la promessa che il libro fa in copertina.
    # This is the seed of the figure printed in the chapter: with it the cell
    # redraws the book's histogram and prints its percentile.
    """Quale percentile occupa questa posizione, fra tante casuali equivalenti?"""
    vera = esegui(prezzi, posizione, costo=costo)
    n_op = int(vera["operazioni"])
    giorni_dentro = int(np.asarray(posizione).sum())
    rng = np.random.default_rng(seed_for(seme))
    casuali = np.array([
        esegui(prezzi, posizione_casuale(len(prezzi), giorni_dentro, n_op, rng),
               costo=costo)["finale"]
        for _ in range(n_casuali)
    ])
    return {
        "risultato": vera["finale"],
        "operazioni": n_op,
        "giorni_dentro": giorni_dentro,
        "casuali": casuali,
        "percentile": float((casuali < vera["finale"]).mean() * 100),
    }


esito = metro_del_caso(prezzi, posizione)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.hist(esito["casuali"], bins=60)
    ax.axvline(esito["risultato"], linewidth=2.5, color="black")
    ax.set_xscale("log")
    ax.set_xlabel("Capitale finale (volte, scala log)")
    ax.set_ylabel(f"Su {N_CASUALI} strategie casuali")
    ax.set_title(f"La regola sta al {esito['percentile']:.0f}esimo percentile")
    plt.show()

print(f"la regola: {esito['risultato']:.2f}x con {esito['operazioni']} operazioni")
print(f"mediana delle casuali: {np.median(esito['casuali']):.2f}x")
print(f"percentile della regola: {esito['percentile']:.1f}")

# %% [markdown]
# ## 4. Riusa il metro sulla tua regola
#
# Sostituisci `posizione` con la tua e riesegui. È la parte del quaderno che vale
# la pena copiare altrove.
#
# ---
#
# > **EN** — *4. Reuse the yardstick on your own rule.* Replace `posizione`
# > with your own and rerun. It's the part of the notebook worth copying
# > elsewhere.

# %%
for altra_serie in ("ethusdt", "solusdt"):
    p = carica(altra_serie).sort("data")["chiusura"].to_numpy()
    e = metro_del_caso(p, sopra_media(p, FINESTRA), n_casuali=300,
                       seme=f"metro-{altra_serie}")
    print(f"{altra_serie}: {e['risultato']:7.2f}x  →  percentile {e['percentile']:5.1f}")

# %% [markdown]
# ### Un avvertimento importante
#
# Il risultato di questo quaderno è forte, e **non vale niente**. Il numero
# cinquanta della media non è stato scelto prima: è stato scelto guardando i
# dati. Il capitolo «Ottimizzare è ingannarsi» smonta questo stesso risultato, e
# il Lab 15 te lo fa smontare a te.
#
# È esattamente così che si presenta un risultato viziato: non con dati falsi, ma
# con dati veri e una scelta fatta guardando quei dati.
#
# ### Esercizi
#
# 1. Cambia `FINESTRA` da 50 a 20, 100, 200. Il percentile balla parecchio. Quale
#    di quei valori avresti scelto **prima** di vedere i risultati?
# 2. Raddoppia `COSTO`. Il percentile scende: un vantaggio che sopravvive solo a
#    costi ottimistici appartiene a chi ha costi bassi, non a te.
# 3. Nella cella 2, prova a togliere lo sfasamento del passo 3 (metti
#    `posizione = segnale`) e riesegui tutto. Il risultato diventa spettacolare e
#    la verifica di causalità fallisce. È una riga.
#
# ---
#
# > **EN** — *An important warning.* This notebook's result is strong, and
# > **worthless**. The fifty-day window wasn't chosen beforehand: it was
# > chosen looking at the data. The chapter "Optimizing is fooling yourself"
# > takes this very result apart, and Lab 15 makes you take it apart
# > yourself. This is exactly how a tainted result presents itself: not with
# > fake data, but with real data and a choice made while looking at it.
# >
# > *Exercises.*
# > 1. Change `FINESTRA` from 50 to 20, 100, 200. The percentile swings a
# >    lot. Which of those values would you have chosen **before** seeing the
# >    results?
# > 2. Double `COSTO`. The percentile drops: an edge that only survives at
# >    optimistic costs belongs to whoever has low costs, not to you.
# > 3. In cell 2, try removing the step-3 lag (set `posizione = segnale`) and
# >    rerun everything. The result becomes spectacular and the causality
# >    check fails. It's one line.
