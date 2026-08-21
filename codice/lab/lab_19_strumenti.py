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
# # Lab 19 — Le cinque prove del tuo strumento
#
# *Quaderno del capitolo «La cassetta degli attrezzi» di **Non Fidarti di Me**.*
#
# Questo quaderno **non serve a insegnarti Python**. Serve a mostrarti in trenta
# secondi cosa vuol dire, in pratica, avere le cinque capacità del capitolo —
# così puoi confrontarle con quello che il tuo strumento attuale ti permette di
# fare, invece di fidarti del mio confronto.
#
# Cinque celle, una per prova. Eseguile e poi chiediti, per ciascuna: *questo,
# con lo strumento che uso, quanto ci metterei?*

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

avvio.prepara(["btcusdt", "ethusdt", "solusdt", "lunausdt", "fttusdt"])

# %%
import hashlib
import time

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from cvbook import seed_for
from cvbook.dati import carica, leggi_registro
from cvbook.metriche import cagr, drawdown_massimo, rendimenti, sharpe, volatilita
from cvbook.simulazioni import bootstrap_traiettorie

ASSET = ["btcusdt", "ethusdt", "solusdt", "lunausdt", "fttusdt"]

# %% [markdown]
# ## Prova 1 — La stessa metrica su tutti gli asset, in una tabella
#
# Non cinque grafici da guardare uno per uno: **una tabella, ordinabile**.
# Se il tuo strumento non lo fa, il capitolo sul cimitero dei token è un capitolo
# che non avresti potuto scrivere.

# %%
inizio = time.perf_counter()

righe = []
for nome in ASSET:
    d = carica(nome).sort("data")
    p = d["chiusura"].to_numpy()
    r = rendimenti(p)
    curva = np.concatenate([[1.0], np.cumprod(1 + r)])
    righe.append({
        "asset": nome,
        "giorni": len(p),
        "dal": str(d["data"][0]),
        "al": str(d["data"][-1]),
        "finale": round(float(p[-1] / p[0]), 3),
        "cagr": round(cagr(curva), 4),
        "volatilita": round(volatilita(r), 3),
        "calo_massimo": round(drawdown_massimo(curva), 3),
        "sharpe": round(sharpe(r), 2),
    })

tabella = pl.DataFrame(righe).sort("calo_massimo")
print(tabella)
print(f"\ntempo impiegato: {time.perf_counter() - inizio:.2f} secondi")

# %% [markdown]
# ## Prova 2 — Mille percorsi alternativi, e dove cade il tuo
#
# È l'operazione che trasforma «è andata così» in «così com'è andata sta nel
# trenta per cento peggiore dei casi possibili». Quasi nessuna piattaforma da
# trading la fa, e la sua assenza è la ragione per cui quasi nessuno se la chiede.

# %%
r = rendimenti(carica("btcusdt").sort("data")["chiusura"].to_numpy())
rng = np.random.default_rng(seed_for("lab-strumenti"))
percorsi = bootstrap_traiettorie(r, n_traiettorie=2000, rng=rng, a_blocchi=20)

reale = float(np.prod(1 + r))
finali = percorsi[:, -1]
percentile = float((finali < reale).mean() * 100)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.hist(finali, bins=70)
    ax.axvline(reale, linewidth=2.5, color="black")
    ax.set_xscale("log")
    ax.set_xlabel("Capitale finale (volte, scala log)")
    ax.set_ylabel("Su 2.000 percorsi possibili")
    plt.show()

print(f"la storia capitata: {reale:.2f}x  →  percentile {percentile:.0f}")
print(f"mediana dei possibili: {np.median(finali):.2f}x")

# %% [markdown]
# ## Prova 3 — Esportare i dati grezzi
#
# Non il grafico: **i numeri**. Se non puoi, stai delegando a quello strumento
# non solo l'esecuzione ma anche la verifica.

# %%
percorso = "esportazione.csv"
tabella.write_csv(percorso)
with open(percorso, "rb") as f:
    impronta = hashlib.sha256(f.read()).hexdigest()

print(f"file scritto: {percorso}")
print(f"impronta SHA-256: {impronta[:32]}…")
print("\nDa questo momento chiunque puo' verificare che i tuoi numeri siano "
      "esattamente questi. Non e' pignoleria: e' la differenza fra un risultato "
      "e il ricordo di un risultato.")

# %% [markdown]
# ## Prova 4 — Rieseguire e ottenere lo stesso identico numero
#
# Il lavoro di sei mesi fa si rifà con un comando? Se vive in una sequenza di
# clic, la risposta è no per costruzione.

# %%
registro = leggi_registro()
print(f"{'serie':>10s} {'righe':>7s} {'estratta il':>13s} {'impronta':>18s}")
for nome in ASSET:
    voce = registro[nome]
    print(f"{nome:>10s} {voce.righe:7d} {voce.estratto:>13s} {voce.sha256[:16]:>18s}…")

print("\nI dati di questo libro sono congelati e firmati. Se qualcuno modificasse "
      "un file, il codice si RIFIUTEREBBE di eseguire — provaci: apri uno "
      "snapshot, cambia un byte, e riesegui la prima cella.")

# %% [markdown]
# ## Prova 5 — Quanto ci metti a rifare tutto cambiando un parametro
#
# Se la risposta è «mezz'ora», la maggior parte delle verifiche che dovresti fare
# non le farai. Se è «trenta secondi», le farai tutte.

# %%
from cvbook.regole import esegui, rottura

prezzi = carica("btcusdt").sort("data")["chiusura"].to_numpy()

inizio = time.perf_counter()
griglia = {int(f): esegui(prezzi, rottura(prezzi, int(f)), costo=0.0012)["finale"]
           for f in range(5, 121, 5)}
durata = time.perf_counter() - inizio

print(f"{len(griglia)} varianti complete, con costi, calcolate in {durata:.2f} secondi")
print(f"peggiore {min(griglia.values()):.2f}x   mediana "
      f"{np.median(list(griglia.values())):.2f}x   migliore {max(griglia.values()):.2f}x")
print("\nE' questo il punto del capitolo: non la velocita' del computer, ma il "
      "fatto che a questo prezzo le verifiche LE FAI. Il numero di verifiche che "
      "NON fai e' esattamente cio' che determina quanto ti stai ingannando.")

# %% [markdown]
# ### Il punteggio
#
# Rifai mentalmente le cinque prove con il tuo strumento attuale e conta quante
# ne supera.
#
# - **Cinque su cinque:** tienilo. La scelta migliore è quella che già usi bene.
# - **Tre o quattro:** sai dove sono i buchi, e adesso sai anche quanto costano.
# - **Meno di tre:** il problema non è che stai lavorando peggio di quanto
#   potresti. È che ci sono domande che non ti stanno venendo in mente, e per
#   definizione non puoi accorgertene dall'interno.
