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
# # Calcolatore 3 — Il rischio, misurato in tempo
#
# *Quaderno del capitolo «Il rischio non è un numero» di **La matematica di chi perde**.*
#
# Il rischio sono quattro domande diverse, e la volatilità risponde solo alla
# prima. Qui le calcoli tutte e quattro, e poi fai il conto che consiglio prima
# di aprire qualunque posizione: **quale dimensione sarebbe stata compatibile con
# la tua tolleranza**, nel periodo storico peggiore.
#
# Di solito è molto più piccola di quella che si aveva in mente.
#
# ---
#
# > **EN** — *Calculator 3 — Risk, measured in time.* Notebook for the
# > chapter "Risk is not a number". Risk is four different questions, and
# > volatility only answers the first. Here you compute all four, then make
# > the calculation I recommend before opening any position: **what size
# > would have been compatible with your tolerance**, in the worst historical
# > period. It's usually much smaller than the one you had in mind.

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
from cvbook.metriche import drawdown, drawdown_massimo, equity, rendimenti, sharpe, volatilita

SERIE = "btcusdt"  # ← PROVA / TRY: "ethusdt" · "solusdt" (le tre preparate nel setup)
                   # per un'altra delle 11 serie in codice/dati/registro.json
                   # aggiungila anche a avvio.prepara([...]) qui sopra

df = carica(SERIE).sort("data")
prezzi = df["chiusura"].to_numpy()
date = df["data"].to_list()
r = rendimenti(prezzi)
curva = equity(r)
dd = drawdown(curva)

# %% [markdown]
# ## 1. Le quattro domande
#
# Quattro numeri diversi, tutti chiamati «rischio». Il primo è quello che compare
# ovunque; il quarto è quello che decide se molli.
#
# ---
#
# > **EN** — *1. The four questions.* Four different numbers, all called
# > "risk". The first is the one that shows up everywhere; the fourth is the
# > one that decides whether you quit.

# %%
print(f"{SERIE}  ·  {len(prezzi)}" + t(" giorni  ·  ", " days  ·  ") + f"{date[0]} → {date[-1]}\n")
print(t("1. Quanto oscilla?           volatilita' annualizzata  ",
        "1. How much does it swing?  annualized volatility     ") + f"{volatilita(r):>8.1%}")
print(t("2. Quanto perdo in un colpo? giorno peggiore           ",
        "2. How much in one hit?     worst single day           ") + f"{r.min():>8.1%}")
print(t("3. Quanto scendo in totale?  calo massimo dal picco    ",
        "3. How far down in total?   max drawdown from peak     ") + f"{drawdown_massimo(curva):>8.1%}")
print(t("4. Per quanto resto sotto?   vedi la tabella qui sotto",
        "4. For how long am I down?  see the table below"))
print(t("\n   indicatore rendimento/rischio piu' usato al mondo: ",
        "\n   most widely used return/risk indicator in the world: ") + f"{sharpe(r):.2f}")

# %% [markdown]
# ## 2. Il rischio misurato in tempo
#
# La domanda che nessuno fa, ed è quella che determina se una persona reale
# esegue il piano fino in fondo.
#
# ---
#
# > **EN** — *2. Risk measured in time.* The question nobody asks, and the
# > one that determines whether a real person actually follows the plan
# > through to the end.

# %%
with avvio.figura("schermo"):
    fig, (a, b) = plt.subplots(2, 1, figsize=(10, 6), height_ratios=[2, 1.4])
    a.fill_between(date, dd * 100, 0, step="mid")
    a.set_ylabel(t("Distanza dal massimo precedente (%)", "Distance from previous peak (%)"))

    soglie = np.arange(0, 0.91, 0.05)
    quote = [float((dd <= -s).mean()) * 100 for s in soglie]
    b.plot(soglie * 100, quote, marker="o")
    b.set_xlabel(t("Almeno questa distanza dal massimo (%)", "At least this far from the peak (%)"))
    b.set_ylabel(t("Quota del tempo (%)", "Share of time (%)"))
    plt.show()

for s in (0.10, 0.20, 0.50, 0.70, 0.80):
    quota = float((dd <= -s).mean())
    print(t(f"almeno {s:.0%} sotto il massimo: {quota:6.1%} dei giorni  "
            f"(~{quota * len(dd) / 365:.1f} anni su {len(dd) / 365:.1f})",
            f"at least {s:.0%} below the peak: {quota:6.1%} of the days  "
            f"(~{quota * len(dd) / 365:.1f} years out of {len(dd) / 365:.1f})"))

sotto_zero = int(np.sum(dd < -0.001))
print(t(f"\ngiorni al proprio massimo storico: {len(dd) - sotto_zero} su {len(dd)} "
        f"({1 - sotto_zero / len(dd):.1%} del tempo)",
        f"\ndays at their all-time high: {len(dd) - sotto_zero} out of {len(dd)} "
        f"({1 - sotto_zero / len(dd):.1%} of the time)"))

# %% [markdown]
# ## 3. Quanto ci si mette a tornare a galla
#
# Non solo quanto si scende: **quanto dura**. È la statistica che manca in ogni
# scheda prodotto.
#
# ---
#
# > **EN** — *3. How long it takes to resurface.* Not just how far it drops:
# > **how long it lasts**. It's the statistic missing from every product
# > sheet.

# %%
picchi = np.maximum.accumulate(curva)
in_calo = curva < picchi - 1e-12

durate, corrente = [], 0
for x in in_calo:
    if x:
        corrente += 1
    elif corrente:
        durate.append(corrente)
        corrente = 0
if corrente:
    durate.append(corrente)  # ancora in corso alla fine della serie / still ongoing at the end of the series

durate = np.array(durate)
print(t(f"episodi sotto il massimo: {len(durate)}", f"episodes below the peak: {len(durate)}"))
print(t(f"durata mediana:  {np.median(durate):6.0f} giorni", f"median duration: {np.median(durate):6.0f} days"))
print(t(f"durata media:    {durate.mean():6.0f} giorni", f"mean duration:   {durate.mean():6.0f} days"))
print(t(f"il piu' lungo:   {durate.max():6.0f} giorni  ({durate.max() / 365:.1f} anni)",
        f"the longest:     {durate.max():6.0f} days  ({durate.max() / 365:.1f} years)"))

# %% [markdown]
# ## 4. Il conto da fare prima di aprire una posizione
#
# Metti il tuo capitale e la perdita che davvero non vuoi superare. Il calcolo
# risponde: **quanto potevi metterci**, se il periodo peggiore già accaduto si
# ripetesse identico.
#
# ---
#
# > **EN** — *4. The calculation to do before opening a position.* Enter your
# > capital and the loss you truly don't want to exceed. The calculation
# > answers: **how much you could put in**, if the worst period that already
# > happened repeated itself identically.

# %%
CAPITALE = 20_000.0        # ← il tuo capitale totale, in euro
                           # PROVA / TRY: il tuo capitale reale
PERDITA_ACCETTABILE = 3_000.0  # ← quanto sei disposto a vedere sparire, in euro
                                # PROVA / TRY: la tua soglia VERA, non quella
                                # che diresti a un amico (vedi esercizio 2)

peggiore = abs(drawdown_massimo(curva))
quota_massima = PERDITA_ACCETTABILE / (CAPITALE * peggiore)

print(t(f"calo massimo gia' accaduto su {SERIE}: {peggiore:.1%}",
        f"max drawdown already seen on {SERIE}: {peggiore:.1%}"))
print(t(f"perdita accettabile: {PERDITA_ACCETTABILE:,.0f} su {CAPITALE:,.0f} euro "
        f"({PERDITA_ACCETTABILE / CAPITALE:.1%} del capitale)\n",
        f"acceptable loss: {PERDITA_ACCETTABILE:,.0f} out of {CAPITALE:,.0f} euros "
        f"({PERDITA_ACCETTABILE / CAPITALE:.1%} of capital)\n"))
print(t(f"posizione compatibile: {min(quota_massima, 1.0):.1%} del capitale, "
        f"cioe' {min(quota_massima, 1.0) * CAPITALE:,.0f} euro",
        f"compatible position: {min(quota_massima, 1.0):.1%} of capital, "
        f"i.e. {min(quota_massima, 1.0) * CAPITALE:,.0f} euros"))
print(t(f"\nE ricordati che il peggio gia' visto NON e' il peggio possibile: e' il "
        f"peggio di una sola realizzazione. Con un margine del 20% la posizione "
        f"scende a {min(quota_massima / 1.2, 1.0) * CAPITALE:,.0f} euro.",
        f"\nAnd remember that the worst seen so far is NOT the worst possible: it's "
        f"the worst of a single realization. With a 20% margin the position "
        f"drops to {min(quota_massima / 1.2, 1.0) * CAPITALE:,.0f} euros."))

# %% [markdown]
# ### Esercizi
#
# 1. Cambia `SERIE`. Il calo massimo cambia, e con esso la posizione compatibile:
#    la stessa tolleranza produce dimensioni molto diverse su asset diversi.
#    È così che si confrontano gli asset, non guardando quanto sono saliti.
# 2. Nella quarta cella metti la tua perdita accettabile **vera** — quella dopo
#    la quale cambieresti comportamento, non quella che dichiareresti a un amico.
# 3. Guarda l'episodio più lungo della terza cella e chiediti la domanda del
#    capitolo: *quanto tempo posso restare sotto senza cambiare comportamento?*
#    Se la risposta è più corta di quel numero, il problema non è l'asset: è
#    l'accoppiamento fra lui e te.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. Change `SERIE`. The maximum drawdown changes, and with it the compatible
# >    position: the same tolerance produces very different sizes on
# >    different assets. That's how you compare assets — not by how much
# >    they've gone up.
# > 2. In the fourth cell, enter your **real** acceptable loss — the one past
# >    which you'd actually change behaviour, not the one you'd tell a friend.
# > 3. Look at the longest episode from the third cell and ask the chapter's
# >    question: *how long can I stay down without changing behaviour?* If
# >    the answer is shorter than that number, the problem isn't the asset:
# >    it's the pairing between it and you.
