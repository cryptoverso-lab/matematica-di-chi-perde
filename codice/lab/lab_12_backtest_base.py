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
# **Non Fidarti di Me**.*
#
# Due cose. La prima è un backtest scritto per essere **letto**: ogni passaggio
# commentato, i costi dentro, il calcolo causale. Si può seguire anche senza
# saper programmare.
#
# La seconda è il generatore del **metro**: dato un qualunque insieme di regole,
# produce le mille strategie casuali confrontabili e ti dice in quale percentile
# ti trovi. È il pezzo di codice che consiglio di riusare più di ogni altro.

# %%
# Setup — esegui questa cella per prima.
# %pip install -q "polars>=1.0"
try:
    import avvio
except ModuleNotFoundError:
    import urllib.request

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/cryptoverso-lab/non-fidarti-di-me/main/codice/lab/avvio.py",
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

SERIE = "btcusdt"
FINESTRA = 50
COSTO = 0.0012

prezzi = carica(SERIE).sort("data")["chiusura"].to_numpy()

# %% [markdown]
# ## 1. Il backtest, un passaggio alla volta
#
# La regola: **resto dentro al mercato quando il prezzo chiude sopra la sua media
# degli ultimi cinquanta giorni, resto fuori quando è sotto.**

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

# %%
completa = sopra_media(prezzi, FINESTRA)
for taglio in (500, 1500, 2500):
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

# %%
N_CASUALI = 1000


def posizione_casuale(n: int, n_operazioni: int, rng) -> np.ndarray:
    """Entra ed esce a caso, esattamente `n_operazioni` volte."""
    pos = np.zeros(n)
    punti = np.sort(rng.choice(n - 1, size=n_operazioni, replace=False))
    stato, precedente = 0.0, 0
    for i in punti:
        pos[precedente:i] = stato
        stato, precedente = 1.0 - stato, i
    pos[precedente:] = stato
    return pos


def metro_del_caso(prezzi: np.ndarray, posizione: np.ndarray, *,
                   n_casuali: int = N_CASUALI, costo: float = COSTO,
                   seme: str = "metro") -> dict:
    """Quale percentile occupa questa posizione, fra tante casuali equivalenti?"""
    vera = esegui(prezzi, posizione, costo=costo)
    n_op = int(vera["operazioni"])
    rng = np.random.default_rng(seed_for(seme))
    casuali = np.array([
        esegui(prezzi, posizione_casuale(len(prezzi), n_op, rng), costo=costo)["finale"]
        for _ in range(n_casuali)
    ])
    return {
        "risultato": vera["finale"],
        "operazioni": n_op,
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
