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
# # Lab 15 — Ottimizzare è ingannarsi
#
# *Quaderno del capitolo «Ottimizzare è ingannarsi» di **La matematica di chi perde**.*
#
# Qui rifai l'esperimento che smonta il risultato del Lab 12: la stessa regola al
# variare del suo unico parametro, dentro e fuori campione. Poi provi a trovare
# un valore che vinca in **entrambe** le metà. È un esercizio frustrante nel modo
# giusto.
#
# E infine il pezzo che mi ha convinto più di ogni altro: si prende una regola
# **volutamente senza senso**, la si ottimizza, e si guarda che bel risultato in
# campione. Poi si guarda fuori.
#
# ---
#
# > **EN** — *Lab 15 — Optimizing is fooling yourself.* Notebook for the
# > chapter "Optimizing is fooling yourself". Here you redo the experiment
# > that takes apart Lab 12's result: the same rule across its one parameter,
# > in and out of sample. Then you try to find a value that wins in **both**
# > halves. It's frustrating in the right way. And finally the piece that
# > convinced me more than any other: take a rule **deliberately without
# > sense**, optimize it, and look at what a nice in-sample result you get.
# > Then look out of sample.

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
import polars as pl

from cvbook.dati import carica
from cvbook.metriche import drawdown_massimo
from cvbook.regole import compra_e_tieni, esegui, sopra_media

SERIE = "btcusdt"     # ← PROVA / TRY: "ethusdt" · "solusdt" (esercizio 1)
FINESTRE = np.arange(5, 121, 5)  # PROVA / TRY: allarga o restringi il passo
COSTO = 0.0012                   # PROVA / TRY: 0,0006 · 0,0012 · 0,0025

df = carica(SERIE).sort("data")
prezzi = df["chiusura"].to_numpy()
meta = len(prezzi) // 2
prima, seconda = prezzi[:meta], prezzi[meta:]

# %% [markdown]
# ## 1. La mappa, dentro e fuori campione
#
# ---
#
# > **EN** — *1. The map, in and out of sample.*

# %%
dentro = np.array([esegui(prima, sopra_media(prima, int(f)), costo=COSTO)["finale"]
                   for f in FINESTRE])
fuori = np.array([esegui(seconda, sopra_media(seconda, int(f)), costo=COSTO)["finale"]
                  for f in FINESTRE])

migliore_dentro = int(FINESTRE[np.argmax(dentro)])
migliore_fuori = int(FINESTRE[np.argmax(fuori)])

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.plot(FINESTRE, dentro, marker="o", linewidth=2, label="prima metà (usata per scegliere)")
    ax.plot(FINESTRE, fuori, marker="s", linewidth=2, linestyle="--",
            label="seconda metà (mai vista)")
    ax.axvline(migliore_dentro, linestyle=":", linewidth=1.2)
    ax.set_yscale("log")
    ax.set_xlabel("Lunghezza della media (giorni)")
    ax.set_ylabel("Capitale finale (volte, scala log)")
    ax.legend()
    plt.show()

scelto = int(np.argmax(dentro))
print(f"il valore migliore sulla PRIMA meta':  {migliore_dentro} giorni "
      f"→ {dentro[scelto]:.2f}x")
print(f"lo stesso valore sulla SECONDA meta':  {fuori[scelto]:.2f}x")
print(f"restringimento: un fattore {dentro[scelto] / fuori[scelto]:.1f}\n")
print(f"il valore migliore sulla SECONDA meta': {migliore_fuori} giorni "
      f"→ {fuori[np.argmax(fuori)]:.2f}x")
print("\nIl numero che sembrava una scoperta non e' nemmeno quello giusto a "
      "posteriori: era una proprieta' di quel campione.")

# %% [markdown]
# ## 2. Rispetto a cosa? Il confronto onesto sulla seconda metà
#
# Il paragone giusto per un risultato su una finestra è il non far niente **su
# quella stessa finestra**, non sull'intero periodo.
#
# ---
#
# > **EN** — *2. Compared to what? The honest comparison on the second
# > half.* The right comparison for a result on one window is doing nothing
# > **on that same window**, not over the entire period.

# %%
riferimento = esegui(seconda, compra_e_tieni(seconda), costo=COSTO)
regola = esegui(seconda, sopra_media(seconda, migliore_dentro), costo=COSTO)

print(f"seconda meta': {len(seconda)} giorni ({len(seconda) / 365:.1f} anni)\n")
print(f"{'':>16s} {'finale':>10s} {'calo massimo':>14s} {'tempo dentro':>14s}")
print(f"{'la regola':>16s} {regola['finale']:9.2f}x {drawdown_massimo(regola['curva']):14.1%} "
      f"{regola['esposizione']:14.0%}")
print(f"{'compra e tieni':>16s} {riferimento['finale']:9.2f}x "
      f"{drawdown_massimo(riferimento['curva']):14.1%} {1.0:14.0%}")

# %% [markdown]
# ## 3. Trova un valore che vinca in entrambe le metà
#
# L'esercizio frustrante nel modo giusto.
#
# ---
#
# > **EN** — *3. Find a value that wins in both halves.* The exercise that's
# > frustrating in the right way.

# %%
ranghi_dentro = np.argsort(np.argsort(-dentro)) + 1
ranghi_fuori = np.argsort(np.argsort(-fuori)) + 1

print(f"{'finestra':>9s} {'rango dentro':>13s} {'rango fuori':>12s}")
for k, f in enumerate(FINESTRE):
    if ranghi_dentro[k] <= 5 or ranghi_fuori[k] <= 5:
        print(f"{f:9d} {ranghi_dentro[k]:13d} {ranghi_fuori[k]:12d}")

correlazione = float(np.corrcoef(ranghi_dentro, ranghi_fuori)[0, 1])
print(f"\ncorrelazione fra i ranghi delle due meta': {correlazione:+.2f}")
print("Se fosse vicina a +1, il parametro migliore sul passato sarebbe anche "
      "quello migliore sul futuro. Non lo e'.")

# %% [markdown]
# ## 4. Una regola volutamente senza senso
#
# Compriamo in base al **giorno del mese**. Non c'è nessuna ragione perché
# funzioni, e infatti non ce n'è nessuna: ottimizziamola lo stesso.
#
# ---
#
# > **EN** — *4. A rule deliberately without sense.* We buy based on the
# > **day of the month**. There is no reason it should work, and indeed there
# > isn't one: let's optimize it anyway.

# %%
date = df["data"].to_list()
giorno_mese = np.array([d.day for d in date])
giorno_settimana = np.array([d.weekday() for d in date])

GIORNI_SETTIMANA = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi",
                    "sabato", "domenica", "nessuno"]


def regola_assurda(mese: np.ndarray, settimana: np.ndarray,
                   dal: int, al: int, escluso: int, invertita: bool) -> np.ndarray:
    """Investito nei giorni del mese fra `dal` e `al`, saltando un giorno della
    settimana. Nessun meccanismo la sostiene: e' scelta apposta perche' non ne ha.
    """
    dentro_finestra = (mese >= dal) & (mese <= al)
    if invertita:
        dentro_finestra = ~dentro_finestra
    segnale = (dentro_finestra & (settimana != escluso)).astype(float)
    posizione = np.zeros(len(segnale))
    posizione[1:] = segnale[:-1]
    return posizione


migliore, tentativi = (None, -np.inf), 0
for dal in range(1, 29):
    for al in range(dal, 29):
        for escluso in range(8):          # 0-6 = un giorno saltato, 7 = nessuno
            for invertita in (False, True):
                tentativi += 1
                valore = esegui(
                    prima,
                    regola_assurda(giorno_mese[:meta], giorno_settimana[:meta],
                                   dal, al, escluso, invertita),
                    costo=COSTO,
                )["finale"]
                if valore > migliore[1]:
                    migliore = ((dal, al, escluso, invertita), valore)

(dal, al, escluso, invertita), valore_dentro = migliore
valore_fuori = esegui(
    seconda,
    regola_assurda(giorno_mese[meta:], giorno_settimana[meta:], dal, al, escluso, invertita),
    costo=COSTO,
)["finale"]

print(f"combinazioni provate: {tentativi:,}")
print(f"la migliore: investire {'FUORI dal' if invertita else 'dal'} giorno {dal} "
      f"al giorno {al} del mese, saltando il {GIORNI_SETTIMANA[escluso]}")
print(f"  sulla prima meta':   {valore_dentro:8.2f}x   (compra e tieni: "
      f"{prima[-1] / prima[0]:.2f}x)")
print(f"  sulla seconda meta': {valore_fuori:8.2f}x   (compra e tieni: "
      f"{seconda[-1] / seconda[0]:.2f}x)")
print(f"\nrestringimento dentro→fuori: un fattore "
      f"{valore_dentro / max(valore_fuori, 1e-9):.1f}")
print("\nDentro campione e' una curva che si mostrerebbe volentieri, e sotto non "
      "c'e' alcun meccanismo: l'abbiamo scelta apposta senza senso.")
print("Fuori campione il risultato si restringe di piu' di un ordine di grandezza. "
      "Quel poco che avanza NON e' un vantaggio: e' l'effetto di stare fuori dal "
      "mercato una parte del tempo, che su un periodo agitato basta a evitare "
      "qualche giorno brutto. Il metro del caso del Lab 12 e' li' apposta per "
      "separare le due cose — provaci.")

# %% [markdown]
# ### Esercizi
#
# 1. Cambia `SERIE`. Il valore migliore sulla prima metà cambia da un mercato
#    all'altro. Se fosse una proprietà del mondo, non dovrebbe.
# 2. Nella prima cella, invece del massimo prendi il **centro dell'altopiano più
#    largo** — la regione in cui il risultato resta accettabile. Confronta i due
#    valori fuori campione: di solito il secondo regge meglio.
# 3. Nella quarta cella prova a spiegare a te stesso perché «dal giorno X al
#    giorno Y del mese» dovrebbe funzionare. Ci riuscirai: il cervello produce
#    spiegazioni per qualunque cosa, ed è esattamente il punto.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. Change `SERIE`. The best value on the first half changes from one
# >    market to another. If it were a property of the world, it shouldn't.
# > 2. In the first cell, instead of the maximum take the **center of the
# >    widest plateau** — the region where the result stays acceptable.
# >    Compare the two out-of-sample values: the second one usually holds up
# >    better.
# > 3. In the fourth cell try explaining to yourself why "from day X to day Y
# >    of the month" should work. You'll manage it: the brain produces
# >    explanations for anything, and that's exactly the point.
