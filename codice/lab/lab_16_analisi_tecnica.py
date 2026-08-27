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
# # Lab 16 — L'analisi tecnica, misurata
#
# *Quaderno del capitolo «L'analisi tecnica, misurata» di **La matematica di chi perde**.*
#
# Le sei regole del capitolo, scritte tutte nella stessa forma, applicate
# all'asset e al periodo che scegli tu. Senza selezionare quali mostrare dopo
# aver visto i risultati.
#
# Poi i tre controlli sulla regola che vince: la forma della superficie, il metro
# del caso, e la correzione per il numero di tentativi.
#
# Nulla di quello che c'è qui dentro è un'indicazione operativa. È un modo di
# porre la domanda.
#
# ---
#
# > **EN** — *Lab 16 — Technical analysis, measured.* Notebook for the
# > chapter "Technical analysis, measured". The chapter's six rules, all
# > written in the same form, applied to the asset and period you choose.
# > Without cherry-picking which ones to show after seeing the results. Then
# > the three checks on the rule that wins: the shape of the surface, the
# > yardstick of chance, and the correction for the number of attempts.
# > Nothing in here is trading advice. It's a way of asking the question.

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
from cvbook.regole import CATALOGO, compra_e_tieni, esegui, rottura

SERIE = "btcusdt"   # ← PROVA / TRY: "ethusdt" · "solusdt" (le tre preparate nel setup)
COSTO = 0.0012      # ← il tuo costo per operazione
                    # PROVA / TRY: raddoppialo (vedi esercizio 1)

prezzi = carica(SERIE).sort("data")["chiusura"].to_numpy()

# %% [markdown]
# ## 1. Sei regole da manuale, tutte insieme
#
# Il vincolo che distingue una misura da una vetrina: **si mostrano tutte**.
#
# ---
#
# > **EN** — *1. Six textbook rules, all together.* The constraint that
# > separates a measurement from a showcase: **all of them are shown**.

# %%
riferimento = esegui(prezzi, compra_e_tieni(prezzi), costo=COSTO)

righe = []
for nome, regola in CATALOGO.items():
    e = esegui(prezzi, regola(prezzi), costo=COSTO)
    righe.append((nome, e["finale"], e["finale_lordo"], e["operazioni"],
                  e["esposizione"], drawdown_massimo(e["curva"])))
righe.sort(key=lambda x: x[1])

print(f"{SERIE}, costi {COSTO:.2%} per operazione\n")
print(f"{'regola':>22s} {'netto':>9s} {'lordo':>9s} {'oper.':>7s} "
      f"{'dentro':>8s} {'calo max':>10s}")
for nome, netto, lordo, op, esp, dd in righe:
    print(f"{nome:>22s} {netto:8.2f}x {lordo:8.2f}x {op:7.0f} {esp:8.0%} {dd:10.1%}")
print(f"{'compra e tieni':>22s} {riferimento['finale']:8.2f}x "
      f"{riferimento['finale_lordo']:8.2f}x {riferimento['operazioni']:7.0f} "
      f"{riferimento['esposizione']:8.0%} {drawdown_massimo(riferimento['curva']):10.1%}")

with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    y = np.arange(len(righe))
    ax.barh(y, [r[1] for r in righe])
    ax.axvline(riferimento["finale"], linewidth=2, linestyle="--", color="black")
    ax.annotate(f"compra e tieni: {riferimento['finale']:.1f}x",
                xy=(riferimento["finale"], len(righe) - 0.4),
                xytext=(6, 0), textcoords="offset points", va="center")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in righe])
    ax.set_xscale("log")
    ax.set_xlabel("Capitale finale, per ogni euro investito (scala log)")
    plt.show()

battono = sum(1 for r in righe if r[1] > riferimento["finale"])
print(f"\n{battono} regole su {len(righe)} hanno battuto il non far niente.")

# %% [markdown]
# ## 2. I costi decidono la classifica
#
# Guarda le colonne «netto» e «lordo» della tabella. Qualche regola cambia lato.
#
# ---
#
# > **EN** — *2. Costs decide the ranking.* Look at the "net" and "gross"
# > columns of the table. Some rules switch sides.

# %%
print(f"{'regola':>22s} " + "".join(f"{c:>11.2%}" for c in (0.0, 0.0006, 0.0012, 0.0025, 0.005)))
for nome, regola in CATALOGO.items():
    valori = "".join(f"{esegui(prezzi, regola(prezzi), costo=c)['finale']:10.2f}x"
                     for c in (0.0, 0.0006, 0.0012, 0.0025, 0.005))
    print(f"{nome:>22s} {valori}")
# Anche il compra-e-tieni ha un'operazione — il proprio ingresso — quindi la
# sua riga cambia con la colonna, di poco ma cambia. Stamparla costante era
# comodo e falso: diceva che il metro di confronto non paga i costi.
print(f"{'compra e tieni':>22s} " +
      "".join(f"{esegui(prezzi, compra_e_tieni(prezzi), costo=c)['finale']:10.2f}x"
              for c in (0.0, 0.0006, 0.0012, 0.0025, 0.005)))

print("\n«Quale regola e' migliore» dipende da quanto paghi. Chi pubblica un "
      "backtest senza costi non ha mentito su nessun numero: ha omesso una voce, "
      "e l'omissione puo' invertire la conclusione.")

# %% [markdown]
# ## 3. Il primo controllo: la forma della superficie
#
# Un altopiano largo è compatibile con un fenomeno reale. Un picco isolato quasi
# mai lo è.
#
# ---
#
# > **EN** — *3. The first check: the shape of the surface.* A wide plateau
# > is compatible with a real phenomenon. An isolated peak almost never is.

# %%
FINESTRE = np.arange(5, 121, 5)  # PROVA / TRY: allarga o restringi il passo
griglia = np.array([esegui(prezzi, rottura(prezzi, int(f)), costo=COSTO)["finale"]
                    for f in FINESTRE])

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.plot(FINESTRE, griglia, marker="o", linewidth=2)
    ax.axhline(riferimento["finale"], linestyle="--", linewidth=1.5, color="black",
               label="compra e tieni")
    ax.set_yscale("log")
    ax.set_xlabel("Finestra della rottura (giorni)")
    ax.set_ylabel("Capitale finale (volte, scala log)")
    ax.legend()
    plt.show()

print(f"valori che battono il compra-e-tieni: {int((griglia > riferimento['finale']).sum())} "
      f"su {len(griglia)}")
print(f"mediana della griglia: {np.median(griglia):.2f}x")

# %% [markdown]
# ## 4. Il secondo controllo: il metro del caso
#
# ---
#
# > **EN** — *4. The second check: the yardstick of chance.*

# %%
N_CASUALI = 1000  # PROVA / TRY: 200 (veloce) · 1000 · 10000 (percentile più preciso)
SCELTA = 20


def posizione_casuale(n: int, n_operazioni: int, rng) -> np.ndarray:
    pos = np.zeros(n)
    punti = np.sort(rng.choice(n - 1, size=n_operazioni, replace=False))
    stato, precedente = 0.0, 0
    for i in punti:
        pos[precedente:i] = stato
        stato, precedente = 1.0 - stato, i
    pos[precedente:] = stato
    return pos


scelta = esegui(prezzi, rottura(prezzi, SCELTA), costo=COSTO)
n_op = int(scelta["operazioni"])
rng = np.random.default_rng(seed_for("tecnica-verifica"))
# NON TOCCARE / DO NOT CHANGE: è il seme della figura stampata nel capitolo.
# Con quello — stesse mille posizioni casuali, stesse operazioni, stessi costi
# — questa cella ridisegna l'istogramma del libro e stampa il suo percentile.
# Con un seme qualunque il quaderno resta corretto ma risponde 98,9 dove la
# pagina dice 98: due numeri per la stessa domanda, ed è la cosa che questo
# libro promette di non fare.
# This is the seed of the figure printed in the chapter.
casuali = np.array([
    esegui(prezzi, posizione_casuale(len(prezzi), n_op, rng), costo=COSTO)["finale"]
    for _ in range(N_CASUALI)
])
percentile = float((casuali < scelta["finale"]).mean() * 100)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.hist(casuali, bins=50)
    ax.axvline(scelta["finale"], linewidth=2.5, color="black")
    ax.set_xscale("log")
    ax.set_xlabel("Capitale finale (volte, scala log)")
    ax.set_ylabel(f"Su {N_CASUALI} posizioni casuali")
    ax.set_title(f"La regola sta al {percentile:.0f}esimo percentile")
    plt.show()

print(f"la regola: {scelta['finale']:.2f}x con {n_op} operazioni")
print(f"mediana delle casuali: {np.median(casuali):.2f}x")
print(f"percentile: {percentile:.1f}")

# %% [markdown]
# ## 5. Il terzo controllo: quanti tentativi ci sono stati dietro
#
# Il controllo che quasi nessuno applica ai propri numeri.
#
# ---
#
# > **EN** — *5. The third check: how many attempts were behind it.* The
# > check almost nobody applies to their own numbers.

# %%
regole_provate = len(CATALOGO)
parametri_provati = len(FINESTRE)
tentativi = regole_provate + parametri_provati

p_singolo = 1 - percentile / 100
print(f"regole provate: {regole_provate}")
print(f"valori del parametro provati: {parametri_provati}")
print(f"tentativi complessivi (stima prudente): {tentativi}\n")
print(f"probabilita' che UN tentativo raggiunga questo percentile per caso: {p_singolo:.1%}")
print(f"probabilita' che almeno uno su {tentativi} lo faccia: "
      f"{1 - (1 - p_singolo) ** tentativi:.1%}")
print("\nI tentativi non sono del tutto indipendenti — finestre vicine danno "
      "risultati simili — quindi questa stima e' pessimistica. Ma il punto resta: "
      "un percentile, dopo trenta tentativi, non e' piu' quel percentile.")

# %% [markdown]
# ## 6. Altri mercati non sono altre prove
#
# ---
#
# > **EN** — *6. Other markets are not other trials.*

# %%
for altro in ("btcusdt", "ethusdt", "solusdt"):
    p = carica(altro).sort("data")["chiusura"].to_numpy()
    r = esegui(p, rottura(p, SCELTA), costo=COSTO)
    b = esegui(p, compra_e_tieni(p), costo=COSTO)
    print(f"{altro:>10s}: regola {r['finale']:8.2f}x   compra e tieni {b['finale']:8.2f}x   "
          f"rapporto {r['finale'] / b['finale']:5.2f}")

print("\nTre conferme? No. Il Lab 8 ha mostrato che questi tre mercati contengono "
      "poco piu' di UNA scommessa: una sola componente ne spiega quasi l'ottanta "
      "per cento dei movimenti. Un metodo che funziona sul fattore comune "
      "funziona su tutti e tre — non perche' sia stato confermato tre volte, ma "
      "perche' e' stato confermato una volta e conteggiato tre.")

# %% [markdown]
# ### Esercizi
#
# 1. Cambia `COSTO` e riesegui la seconda cella. Guarda l'ordine della classifica
#    cambiare: è la dimostrazione più rapida che «quale regola è migliore» non è
#    una proprietà della regola.
# 2. Aggiungi una regola tua al catalogo, seguendo il modello di `cvbook.regole`,
#    e sottoponila agli stessi tre controlli. Ricordati di **contarla** fra i
#    tentativi.
# 3. Il più istruttivo: esegui tutto su un mercato **non** digitale. Attenzione ai
#    giorni di borsa chiusa, che cambiano il conto dei periodi. Se il risultato si
#    ripete lì, hai una conferma vera; se non si ripete, hai imparato qualcosa di
#    più utile di una conferma.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. Change `COSTO` and rerun the second cell. Watch the ranking order
# >    change: it's the quickest demonstration that "which rule is better"
# >    isn't a property of the rule.
# > 2. Add your own rule to the catalogue, following the pattern in
# >    `cvbook.regole`, and put it through the same three checks. Remember to
# >    **count it** among the attempts.
# > 3. The most instructive one: run everything on a **non**-digital market.
# >    Watch out for closed trading days, which change the count of periods.
# >    If the result repeats there, you have a real confirmation; if it
# >    doesn't, you've learned something more useful than a confirmation.
