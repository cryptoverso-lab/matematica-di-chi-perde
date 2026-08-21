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
# # Calcolatore 2 — I costi, sui tuoi numeri
#
# *Quaderno del capitolo «I costi che ti mangiano vivo» di **La matematica di chi perde**.*
#
# Tre risposte, con i tuoi parametri: quanto ti costano i costi in un anno, quale
# rendimento lordo ti serve **solo per pareggiarli**, e quanto ti sarebbe rimasto
# operando a quella frequenza su una serie reale.
#
# Il numero che quasi nessuno conosce è il secondo.
#
# ---
#
# > **EN** — *Calculator 2 — Costs, on your own numbers.* Notebook for the
# > chapter "The costs that eat you alive". Three answers, with your own
# > parameters: what costs take out of a year, what gross return you need
# > **just to break even on them**, and what would have been left trading at
# > that frequency on a real series. The number almost nobody knows is the
# > second one.

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

from cvbook.dati import carica
from cvbook.lingua import t
from cvbook.metriche import equity, rendimenti

# %% [markdown]
# ## 1. I tuoi tre numeri
#
# Se non conosci il tuo costo per giro, il capitolo spiega come misurarlo: prendi
# dieci operazioni chiuse, confronta il prezzo che avevi visto con quello
# ottenuto, somma le commissioni. Quasi tutti scoprono di stare più vicini allo
# 0,25% che allo 0,06%.
#
# ---
#
# > **EN** — *1. Your three numbers.* If you don't know your own round-trip
# > cost, the chapter explains how to measure it: take ten closed trades,
# > compare the price you saw with the price you got, add the commissions.
# > Almost everyone finds themselves closer to 0.25% than to 0.06%.

# %%
CAPITALE = 10_000.0   # ← il capitale impegnato, in euro
                      # PROVA / TRY: il tuo capitale reale — cambia solo la
                      # scala, non le percentuali qui sotto
COSTO_GIRO = 0.0012   # ← costo tutto compreso di un giro completo (0,12%)
                      # PROVA / TRY: 0,0006 (scontato) · 0,0012 · 0,0025 (al dettaglio)
OPERAZIONI_ANNO = 52  # ← quanti giri completi fai in un anno
                      # PROVA / TRY: la tua frequenza reale, contata sull'estratto conto

speso = CAPITALE * COSTO_GIRO * OPERAZIONI_ANNO
pareggio = (1 + COSTO_GIRO) ** OPERAZIONI_ANNO - 1

print(t("in un anno paghi:        ", "in a year you pay:       ") + f"{speso:10,.2f}"
      + t(" euro", " euros"))
print(t("cioe' il:                ", "that is:                 ") + f"{speso / CAPITALE:10.2%}"
      + t(" del capitale", " of capital"))
print(t("rendimento lordo per     ", "gross return to          "))
print(t("NON perdere nulla:       ", "lose NOTHING:            ") + f"{pareggio:10.2%}")

# %% [markdown]
# ## 2. La soglia, al variare della frequenza
#
# La riga tratteggiata è, come nel libro, il rendimento medio storico di lungo
# periodo di un indice azionario ampio. Tutto ciò che sta sopra è territorio in
# cui il costo si mangia più di quanto un mercato intero abbia mai reso.
#
# ---
#
# > **EN** — *2. The threshold, as frequency varies.* The dashed line is, as
# > in the book, the long-run historical average return of a broad equity
# > index. Everything above it is territory where cost eats more than an
# > entire market has ever returned.

# %%
FREQUENZE = np.array([12, 26, 52, 125, 250, 500])
COSTI = [0.0006, 0.0012, 0.0025]

with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(9, 5))
    for c in COSTI:
        soglia = ((1 + c) ** FREQUENZE - 1) * 100
        ax.plot(FREQUENZE, soglia, marker="o", label=t(f"costo {c:.2%} a giro", f"cost {c:.2%} per round trip"))

    # Riferimento in grigio, con l'etichetta in legenda invece che sul grafico:
    # una scritta appoggiata sulle curve e' il modo piu' rapido di rendere
    # illeggibile una figura che dice una cosa semplice.
    # Grey reference, labelled in the legend rather than on the chart: text
    # sitting on top of the curves is the fastest way to make an otherwise
    # simple figure unreadable.
    ax.axhline(
        10,
        linestyle="--",
        linewidth=1.2,
        color="#8C8C8C",
        zorder=0,
        label=t("~10% annuo: media storica di un indice azionario",
                 "~10% a year: historical average of an equity index"),
    )

    ax.set_xscale("log")
    ax.set_xticks(FREQUENZE)
    ax.set_xticklabels([str(f) for f in FREQUENZE])
    ax.set_xlabel(t("Operazioni complete all'anno", "Round trips per year"))
    ax.set_ylabel(t("Rendimento lordo necessario per pareggiare (%)", "Gross return needed to break even (%)"))
    ax.set_ylim(0, None)
    ax.legend(loc="upper left")
    plt.show()

for c in COSTI:
    print(t(f"costo {c:.2%}: ", f"cost {c:.2%}: ") + "  ".join(
        f"{f}op→{((1 + c) ** f - 1):.1%}" for f in FREQUENZE))

# %% [markdown]
# ## 3. Cosa sarebbe rimasto, su dati reali
#
# Stessa esposizione, stesso asset, stesso periodo. L'unica cosa che cambia è
# **quante volte** si chiude e si riapre la stessa posizione. Nessuna previsione
# diversa, nessuna decisione diversa.
#
# ---
#
# > **EN** — *3. What would have been left, on real data.* Same exposure,
# > same asset, same period. The only thing that changes is **how many times**
# > the same position is closed and reopened. No different forecast, no
# > different decision.

# %%
SERIE = "btcusdt"  # ← PROVA / TRY: "ethusdt" · "solusdt" (le tre preparate nel setup)
                   # per un'altra delle 11 serie in codice/dati/registro.json
                   # aggiungila anche a avvio.prepara([...]) qui sopra

r = rendimenti(carica(SERIE).sort("data")["chiusura"].to_numpy())
n = len(r)


def con_frequenza(rend: np.ndarray, ogni_n_giorni: int | None, costo: float) -> float:
    """Capitale finale restando sempre investiti ma rientrando ogni N giorni."""
    operazioni = np.zeros(len(rend))
    if ogni_n_giorni is not None:
        operazioni[::ogni_n_giorni] = 1.0
    return float(equity(rend - operazioni * costo)[-1])


print(f"{SERIE} · {n}" + t(" giorni\n", " days\n"))
print(f"{t('frequenza', 'frequency'):>22s} " + " ".join(f"{c:>10.2%}" for c in COSTI))
for ogni, etichetta in [
    (None, t("mai (compra e tieni)", "never (buy and hold)")),
    (365, t("una volta l'anno", "once a year")),
    (30, t("una volta al mese", "once a month")),
    (7, t("una volta a settimana", "once a week")),
    (1, t("ogni giorno", "every day")),
]:
    valori = " ".join(f"{con_frequenza(r, ogni, c):10.3f}x" for c in COSTI)
    print(f"{etichetta:>22s} {valori}")

# %% [markdown]
# ### Esercizi
#
# 1. **Metti la tua frequenza reale** in `OPERAZIONI_ANNO`: contale sull'estratto
#    conto dell'ultimo anno, non a memoria. Poi confronta la soglia di pareggio
#    con quello che pensavi di poter ottenere.
# 2. Raddoppia `COSTO_GIRO` e riesegui tutto. Se una strategia sopravvive solo al
#    costo ottimistico, quel vantaggio appartiene a chi ha costi bassi, non a te.
# 3. Nella terza cella cambia serie. La colonna del compra-e-tieni cambia molto;
#    il **rapporto** fra le righe quasi per niente: il costo della frequenza non
#    dipende da quale asset hai scelto.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. **Enter your real frequency** in `OPERAZIONI_ANNO`: count it from last
# >    year's statement, not from memory. Then compare the break-even
# >    threshold with what you thought you could get.
# > 2. Double `COSTO_GIRO` and rerun everything. If a strategy only survives
# >    at the optimistic cost, that edge belongs to whoever has low costs, not
# >    to you.
# > 3. In the third cell, change the series. The buy-and-hold column changes a
# >    lot; the **ratio** between the rows barely at all: the cost of
# >    frequency doesn't depend on which asset you picked.
