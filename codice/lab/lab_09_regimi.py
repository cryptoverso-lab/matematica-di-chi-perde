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
# # Lab 9 — Il mercato non è sempre lo stesso mercato
#
# *Quaderno del capitolo «Il mercato non è sempre lo stesso mercato» di
# **La matematica di chi perde**.*
#
# La volatilità non è una costante dell'asset: è una serie storica. Qui la
# calcoli, ne guardi la forma, e verifichi che i periodi agitati **durano**
# invece di lampeggiare.
#
# I due esercizi finali valgono più della figura: uno mostra che una finestra
# lunga *nasconde* i regimi invece di misurarli, l'altro li fa sparire
# rimescolando i dati — e vedere sparire una struttura quando la si distrugge di
# proposito è il modo più diretto di convincersi che c'era.
#
# ---
#
# > **EN** — *Lab 9 — The market isn't always the same market.* Notebook for
# > the chapter "The market isn't always the same market". Volatility isn't a
# > constant of the asset: it's a time series. Here you compute it, look at
# > its shape, and verify that turbulent periods **persist** instead of
# > flickering. The two final exercises are worth more than the figure: one
# > shows that a long window *hides* regimes instead of measuring them, the
# > other makes them disappear by shuffling the data — and watching a
# > structure vanish when you destroy it on purpose is the most direct way to
# > convince yourself it was there.

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
from cvbook.metriche import GIORNI_ANNO, rendimenti

SERIE = "btcusdt"   # ← PROVA / TRY: "ethusdt" · "solusdt" (le tre preparate nel setup)
FINESTRA = 30       # ← giorni della finestra mobile
                    # PROVA / TRY: 10 · 30 · 250 (vedi esercizio 4 qui sotto)

df = carica(SERIE).sort("data")
r = rendimenti(df["chiusura"].to_numpy())
date = df["data"].to_list()[1:]


def volatilita_mobile(rend: np.ndarray, finestra: int) -> np.ndarray:
    """Deviazione standard annualizzata, causale: usa solo il passato."""
    return np.array([
        np.std(rend[i - finestra:i], ddof=1) * np.sqrt(GIORNI_ANNO)
        for i in range(finestra, len(rend) + 1)
    ])


vol = volatilita_mobile(r, FINESTRA)
date_v = date[FINESTRA - 1:]

# %% [markdown]
# ## 1. Il numero che descrive un mercato inesistente
#
# ---
#
# > **EN** — *1. The number that describes a non-existent market.*

# %%
alta = float(np.percentile(vol, 75))
media = float(vol.mean())

with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(date_v, 0, 1, where=vol > alta, transform=ax.get_xaxis_transform(),
                    step="mid", alpha=0.25, label="quarto piu' agitato")
    ax.plot(date_v, vol * 100, linewidth=1.0, label=f"volatilita' a {FINESTRA} giorni")
    ax.axhline(media * 100, linestyle="--", linewidth=1.2,
               label=f"media di periodo ({media:.0%})")
    ax.set_ylabel("Volatilita' annualizzata (%)")
    ax.legend(loc="upper right")
    fig.autofmt_xdate()
    plt.show()

vicino = float(np.mean((vol > media * 0.8) & (vol < media * 1.2)))
print(f"minimo  {vol.min():6.1%}")
print(f"massimo {vol.max():6.1%}   →  rapporto massimo/minimo: {vol.max() / vol.min():.1f} volte")
print(f"media   {media:6.1%}")
print(f"quota di tempo entro il ±20% dalla media: {vicino:.1%}")
print(f"\nIl mercato passa poco tempo vicino al numero che tutti chiamano "
      f"«la volatilita' storica».")

# %% [markdown]
# ## 2. La memoria: i regimi persistono
#
# Chiamiamo «agitato» un giorno in cui la volatilità sta nel quarto più alto.
# Per costruzione capita il 25% delle volte. Ora condizioniamo su com'è oggi.
#
# Nota la precauzione che rende credibile il numero: le due finestre — quella che
# misura oggi e quella che misura fra un mese — **non si sovrappongono**.
#
# ---
#
# > **EN** — *2. Memory: regimes persist.* We call a day "turbulent" when
# > volatility sits in the top quarter. By construction that happens 25% of
# > the time. Now we condition on today. Note the precaution that makes the
# > number credible: the two windows — the one measuring today and the one
# > measuring a month from now — **do not overlap**.

# %%
ORIZZONTE = FINESTRA  # non sovrapposte: nessun dato in comune fra le due misure

alto = vol > np.percentile(vol, 75)
oggi, dopo = alto[:-ORIZZONTE], alto[ORIZZONTE:]
base = float(alto.mean())
da_alto = float(dopo[oggi].mean())
da_calmo = float(dopo[~oggi].mean())

with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(6, 4))
    valori = [da_calmo * 100, base * 100, da_alto * 100]
    ax.bar(["oggi calmo", "senza memoria", "oggi agitato"], valori)
    for k, v in enumerate(valori):
        ax.annotate(f"{v:.0f}%", xy=(k, v), xytext=(0, 4), textcoords="offset points",
                    ha="center")
    ax.set_ylabel(f"Agitato fra {ORIZZONTE} giorni (%)")
    plt.show()

print(f"probabilita' di base:         {base:.1%}")
print(f"partendo da un giorno agitato: {da_alto:.1%}")
print(f"partendo da un giorno calmo:   {da_calmo:.1%}")
print(f"rapporto: {da_alto / da_calmo:.1f} volte")

# %% [markdown]
# ## 3. Quanto durano i periodi agitati
#
# Il confronto con un mondo in cui i giorni sono indipendenti — stessa
# percentuale complessiva di giorni agitati, ma sparsi a caso.
#
# ---
#
# > **EN** — *3. How long turbulent periods last.* The comparison with a
# > world where days are independent — same overall percentage of turbulent
# > days, but scattered at random.

# %%
def sequenze(maschera: np.ndarray) -> np.ndarray:
    lunghezze, corrente = [], 0
    for x in maschera:
        if x:
            corrente += 1
        elif corrente:
            lunghezze.append(corrente)
            corrente = 0
    if corrente:
        lunghezze.append(corrente)
    return np.array(lunghezze)


rng = np.random.default_rng(20260816)
# NON TOCCARE / DO NOT CHANGE: il seme fissa i numeri di episodi/mediana/il
# più lungo citati nel testo qui sotto e riusati nella cella 5.
vere = sequenze(alto)
finte = sequenze(rng.random(len(alto)) < base)

with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(8, 4))
    bordi = np.logspace(0, np.log10(max(vere.max(), finte.max()) + 1), 16)
    ax.hist(vere, bins=bordi, label="mercato vero")
    ax.hist(finte, bins=bordi, histtype="step", linewidth=1.8, linestyle="--",
            label="giorni indipendenti")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Durata del periodo agitato (giorni)")
    ax.set_ylabel("Quante volte")
    ax.legend()
    plt.show()

print(f"{'':>22s} {'episodi':>9s} {'mediana':>9s} {'il piu lungo':>14s}")
print(f"{'mercato vero':>22s} {len(vere):9d} {np.median(vere):9.0f} {vere.max():14d}")
print(f"{'giorni indipendenti':>22s} {len(finte):9d} {np.median(finte):9.0f} {finte.max():14d}")

# %% [markdown]
# ## 4. Esercizio: la finestra lunga nasconde i regimi
#
# ---
#
# > **EN** — *4. Exercise: the long window hides regimes.*

# %%
print(f"{'finestra':>10s} {'minimo':>9s} {'massimo':>9s} {'rapporto':>10s} {'entro ±20%':>12s}")
for f in (10, 30, 60, 120, 250):
    v = volatilita_mobile(r, f)
    dentro = float(np.mean((v > v.mean() * 0.8) & (v < v.mean() * 1.2)))
    print(f"{f:10d} {v.min():9.1%} {v.max():9.1%} {v.max() / v.min():9.1f}x {dentro:12.1%}")

print("\nCon finestre lunghe l'escursione si comprime e sembra che il mercato sia "
      "piu' stabile. Non lo e' diventato: lo stiamo guardando con meno risoluzione.")

# %% [markdown]
# ## 5. Esercizio: distruggi la struttura e guardala sparire
#
# ---
#
# > **EN** — *5. Exercise: destroy the structure and watch it disappear.*

# %%
rimescolati = rng.permutation(r)
vol_finta = volatilita_mobile(rimescolati, FINESTRA)
alto_finto = vol_finta > np.percentile(vol_finta, 75)
seq_finta = sequenze(alto_finto)

oggi_f, dopo_f = alto_finto[:-ORIZZONTE], alto_finto[ORIZZONTE:]

print("stessi identici rendimenti, in ordine casuale:\n")
print(f"  persistenza a {ORIZZONTE} giorni: {float(dopo_f[oggi_f].mean()):.1%} "
      f"contro {float(dopo_f[~oggi_f].mean()):.1%}   (nel mercato vero: "
      f"{da_alto:.1%} contro {da_calmo:.1%})")
print(f"  episodio agitato piu' lungo: {seq_finta.max()} giorni "
      f"(nel mercato vero: {vere.max()})")
print("\nLa struttura non era nei rendimenti presi uno per uno: era nel loro "
      "ORDINE. Rimescolarli la distrugge, ed e' la prova che c'era.")

# %% [markdown]
# ### Attenzione a cosa questo NON dice
#
# La persistenza riguarda **quanto** il mercato si muoverà, non **in che
# direzione**. Sapere che il prossimo mese sarà agitato non ti dice se salirà o
# scenderà, e chiunque ti presenti la prima informazione facendola passare per la
# seconda ti sta vendendo qualcosa.
#
# ---
#
# > **EN** — *Watch out for what this does NOT say.* Persistence is about
# > **how much** the market will move, not **in which direction**. Knowing
# > that next month will be turbulent doesn't tell you whether it will rise
# > or fall, and anyone who presents the first piece of information as if it
# > were the second is selling you something.
