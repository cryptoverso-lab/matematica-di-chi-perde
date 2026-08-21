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
# *Quaderno del capitolo «Il rischio non è un numero» di **Non Fidarti di Me**.*
#
# Il rischio sono quattro domande diverse, e la volatilità risponde solo alla
# prima. Qui le calcoli tutte e quattro, e poi fai il conto che consiglio prima
# di aprire qualunque posizione: **quale dimensione sarebbe stata compatibile con
# la tua tolleranza**, nel periodo storico peggiore.
#
# Di solito è molto più piccola di quella che si aveva in mente.

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

from cvbook.dati import carica
from cvbook.metriche import drawdown, drawdown_massimo, equity, rendimenti, sharpe, volatilita

SERIE = "btcusdt"  # ← "btcusdt", "ethusdt", "solusdt"

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

# %%
print(f"{SERIE}  ·  {len(prezzi)} giorni  ·  {date[0]} → {date[-1]}\n")
print(f"1. Quanto oscilla?           volatilita' annualizzata  {volatilita(r):>8.1%}")
print(f"2. Quanto perdo in un colpo? giorno peggiore           {r.min():>8.1%}")
print(f"3. Quanto scendo in totale?  calo massimo dal picco    {drawdown_massimo(curva):>8.1%}")
print(f"4. Per quanto resto sotto?   vedi la tabella qui sotto")
print(f"\n   indicatore rendimento/rischio piu' usato al mondo: {sharpe(r):.2f}")

# %% [markdown]
# ## 2. Il rischio misurato in tempo
#
# La domanda che nessuno fa, ed è quella che determina se una persona reale
# esegue il piano fino in fondo.

# %%
with avvio.figura("schermo"):
    fig, (a, b) = plt.subplots(2, 1, figsize=(10, 6), height_ratios=[2, 1.4])
    a.fill_between(date, dd * 100, 0, step="mid")
    a.set_ylabel("Distanza dal massimo precedente (%)")

    soglie = np.arange(0, 0.91, 0.05)
    quote = [float((dd <= -s).mean()) * 100 for s in soglie]
    b.plot(soglie * 100, quote, marker="o")
    b.set_xlabel("Almeno questa distanza dal massimo (%)")
    b.set_ylabel("Quota del tempo (%)")
    plt.show()

for s in (0.10, 0.20, 0.50, 0.70, 0.80):
    quota = float((dd <= -s).mean())
    print(f"almeno {s:.0%} sotto il massimo: {quota:6.1%} dei giorni  "
          f"(~{quota * len(dd) / 365:.1f} anni su {len(dd) / 365:.1f})")

sotto_zero = int(np.sum(dd < -0.001))
print(f"\ngiorni al proprio massimo storico: {len(dd) - sotto_zero} su {len(dd)} "
      f"({1 - sotto_zero / len(dd):.1%} del tempo)")

# %% [markdown]
# ## 3. Quanto ci si mette a tornare a galla
#
# Non solo quanto si scende: **quanto dura**. È la statistica che manca in ogni
# scheda prodotto.

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
    durate.append(corrente)  # ancora in corso alla fine della serie

durate = np.array(durate)
print(f"episodi sotto il massimo: {len(durate)}")
print(f"durata mediana:  {np.median(durate):6.0f} giorni")
print(f"durata media:    {durate.mean():6.0f} giorni")
print(f"il piu' lungo:   {durate.max():6.0f} giorni  ({durate.max() / 365:.1f} anni)")

# %% [markdown]
# ## 4. Il conto da fare prima di aprire una posizione
#
# Metti il tuo capitale e la perdita che davvero non vuoi superare. Il calcolo
# risponde: **quanto potevi metterci**, se il periodo peggiore già accaduto si
# ripetesse identico.

# %%
CAPITALE = 20_000.0        # ← il tuo capitale totale, in euro
PERDITA_ACCETTABILE = 3_000.0  # ← quanto sei disposto a vedere sparire, in euro

peggiore = abs(drawdown_massimo(curva))
quota_massima = PERDITA_ACCETTABILE / (CAPITALE * peggiore)

print(f"calo massimo gia' accaduto su {SERIE}: {peggiore:.1%}")
print(f"perdita accettabile: {PERDITA_ACCETTABILE:,.0f} su {CAPITALE:,.0f} euro "
      f"({PERDITA_ACCETTABILE / CAPITALE:.1%} del capitale)\n")
print(f"posizione compatibile: {min(quota_massima, 1.0):.1%} del capitale, "
      f"cioe' {min(quota_massima, 1.0) * CAPITALE:,.0f} euro")
print(f"\nE ricordati che il peggio gia' visto NON e' il peggio possibile: e' il "
      f"peggio di una sola realizzazione. Con un margine del 20% la posizione "
      f"scende a {min(quota_massima / 1.2, 1.0) * CAPITALE:,.0f} euro.")

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
