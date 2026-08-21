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
# # Lab 2 — Il caso vestito da bravura
#
# *Quaderno del capitolo «Il caso vestito da bravura» di **La matematica di chi perde**.*
#
# Questo quaderno genera curve di capitale che **non contengono nulla**: nessuna
# decisione, nessun segnale, vantaggio atteso esattamente zero. Poi fa quello che
# fa chiunque mostri i propri risultati: tiene le migliori e butta il resto.
#
# L'esercizio finale è il più utile del quaderno: ci metti dentro un risultato
# che hai visto in giro e ti dice quale percentuale di curve casuali fa meglio.
#
# ---
#
# > **EN** — *Lab 2 — Chance dressed up as skill.* Notebook for the chapter
# > "Chance dressed up as skill". This notebook generates capital curves that
# > **contain nothing**: no decisions, no signal, expected edge exactly zero.
# > Then it does what everyone who shows off their results does: keeps the
# > best and throws away the rest. The final exercise is the most useful one
# > in the notebook: plug in a result you've seen around and it tells you
# > what percentage of random curves do better.

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

avvio.prepara([])

# %%
import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for
from cvbook.metriche import drawdown_massimo
from cvbook.simulazioni import equity_casuali, migliori_per_caso

# %% [markdown]
# ## 1. Dodici curve. Indovina quali sono quelle brave
#
# Guardale prima di scorrere. Alcune ti sembreranno convincenti — e va bene così,
# è esattamente il punto del capitolo.
#
# ---
#
# > **EN** — *1. Twelve curves. Guess which ones are the skilled ones.* Look
# > at them before scrolling. Some will look convincing to you — and that's
# > fine, it's exactly the chapter's point.

# %%
GIORNI = 500          # ← due anni circa di operatività
VOLATILITA = 0.018    # ← oscillazione tipica per operazione
VANTAGGIO = 0.0       # ← lascialo a zero: è il punto

rng = np.random.default_rng(seed_for("lab-equity-casuali"))
curve = equity_casuali(12, GIORNI, rendimento_atteso=VANTAGGIO,
                       volatilita_periodo=VOLATILITA, rng=rng)

with avvio.figura("schermo"):
    fig, assi = plt.subplots(3, 4, figsize=(11, 6), sharex=True)
    for k, ax in enumerate(assi.flat):
        ax.plot(curve[k] * 100, linewidth=1.2)
        ax.axhline(100, linestyle=":", linewidth=0.8)
        ax.set_title(f"{chr(65 + k)}   {curve[k][-1]:.2f}x", fontsize=9)
        ax.set_xticks([])
    fig.suptitle("Dodici curve senza alcuna abilità dentro")
    plt.show()

# %% [markdown]
# Non ce ne sono. Sono dodici estrazioni dallo stesso generatore, con vantaggio
# atteso zero. Le due che ti sono piaciute hanno avuto una buona settimana.
#
# ---
#
# > **EN** — There aren't any. They are twelve draws from the same generator,
# > with zero expected edge. The two you liked just had a good week.

# %% [markdown]
# ## 2. Le migliori cinque su mille
#
# Adesso l'operazione che compie, senza dirlo, chiunque presenti i propri
# risultati: si generano mille tentativi e si mostrano i cinque migliori.
#
# ---
#
# > **EN** — *2. The five best out of a thousand.* Now the operation that
# > everyone who presents their own results performs, without saying so:
# > generate a thousand attempts and show the five best.

# %%
N = 1000
rng = np.random.default_rng(seed_for("migliori-per-caso"))
tutte = equity_casuali(N, GIORNI, rendimento_atteso=VANTAGGIO,
                       volatilita_periodo=VOLATILITA, rng=rng)
migliori = migliori_per_caso(tutte, 5)

with avvio.figura("schermo"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=(11, 4))
    for curva in migliori:
        sx.plot(curva * 100, linewidth=1.4)
    sx.axhline(100, linestyle=":", linewidth=0.9)
    sx.set_title(f"Le 5 migliori su {N}")
    sx.set_ylabel("Capitale (base 100)")

    dx.hist(tutte[:, -1] * 100, bins=60)
    dx.axvline(100, linestyle=":", linewidth=1.2)
    dx.set_title("Da dove sono state estratte")
    dx.set_xlabel("Capitale finale (base 100)")
    plt.show()

finali = tutte[:, -1]
print(f"mediana dei {N} risultati: {np.median(finali):.3f}x")
print(f"la migliore:               {finali.max():.3f}x  "
      f"(calo massimo {drawdown_massimo(migliori[0]):.1%})")
print(f"quota sopra 1,5x:          {(finali > 1.5).mean():.2%}")
print(f"quota sopra 2x:            {(finali > 2.0).mean():.2%}")
print(f"quota sopra 2x CON calo massimo sotto il 20%: "
      f"{np.mean((finali > 2) & (np.array([drawdown_massimo(c) for c in tutte]) > -0.20)):.2%}")

# %% [markdown]
# L'ultima riga è il numero del capitolo: **circa uno su cento**. Su diecimila
# persone che ci provano, cento producono un biennio da fuoriclasse senza avere
# assolutamente nulla dentro.
#
# ---
#
# > **EN** — The last line is the chapter's number: **about one in a
# > hundred**. Out of ten thousand people who try, a hundred produce a
# > standout two-year run with absolutely nothing inside.

# %% [markdown]
# ## 3. E adesso il tuo caso
#
# Prendi un risultato che ti ha colpito — un grafico, una pubblicità, una curva
# di un canale — e mettici i tre numeri qui sotto.
#
# ---
#
# > **EN** — *3. And now your own case.* Take a result that struck you — a
# > chart, an ad, a curve from some channel — and plug in the three numbers
# > below.

# %%
RISULTATO_DICHIARATO = 2.5   # ← capitale finale dichiarato, in volte (2,5 = +150%)
DURATA_GIORNI = 500          # ← su quanti giorni di operatività
VOLATILITA_TIPICA = 0.018    # ← oscillazione per operazione, se la conosci

rng = np.random.default_rng(seed_for("confronto-personale"))
prova = equity_casuali(5000, DURATA_GIORNI, rendimento_atteso=0.0,
                       volatilita_periodo=VOLATILITA_TIPICA, rng=rng)[:, -1]
meglio = float((prova >= RISULTATO_DICHIARATO).mean())

print(f"risultato dichiarato: {RISULTATO_DICHIARATO:.2f}x su {DURATA_GIORNI} giorni")
print(f"curve casuali che fanno altrettanto o meglio: {meglio:.2%}")
print(f"su 10.000 persone senza alcuna abilita', ne otterrebbero altrettanto: "
      f"{meglio * 10_000:.0f}")

# %% [markdown]
# ### Esercizi
#
# 1. Riduci `DURATA_GIORNI` a 125 (sei mesi) tenendo lo stesso risultato: la
#    percentuale crolla. Un risultato spettacolare su un periodo **corto** è più
#    difficile da ottenere per caso di uno spettacolare su un periodo lungo.
# 2. Alza `VOLATILITA_TIPICA` a 0,04. La stessa cifra diventa molto più facile da
#    ottenere per caso: **quanto oscilla** cambia il significato di quanto rende.
# 3. Metti `VANTAGGIO = 0.0005` nella prima cella. Ora un vantaggio c'è davvero.
#    Riesci a distinguerlo a occhio dalle curve senza vantaggio? Quasi nessuno ci
#    riesce, ed è il motivo per cui esiste il capitolo sulla potenza statistica.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. Reduce `DURATA_GIORNI` to 125 (six months) keeping the same result:
# >    the percentage collapses. A spectacular result over a **short**
# >    period is harder to get by chance than a spectacular one over a long
# >    period.
# > 2. Raise `VOLATILITA_TIPICA` to 0.04. The same figure becomes much easier
# >    to get by chance: **how much it swings** changes the meaning of how
# >    much it returns.
# > 3. Set `VANTAGGIO = 0.0005` in the first cell. Now there really is an
# >    edge. Can you tell it apart by eye from the curves with no edge?
# >    Almost nobody can, and that's why the chapter on statistical power
# >    exists.
