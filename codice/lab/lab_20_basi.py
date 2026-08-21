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
# # Lab 20 — Le basi che ti servono davvero
#
# *Quaderno del capitolo «Le basi che ti servono davvero» di
# **Non Fidarti di Me**.*
#
# Cinque celle, una per ciascuna delle idee del capitolo. Non serve saper
# programmare per seguirle: serve leggere i commenti e cambiare i numeri.
#
# L'esercizio finale è togliere il seme dalla simulazione ed eseguirla tre volte.
# Vedere tre risultati diversi dalla stessa identica cella è il modo più rapido
# per capire perché la riproducibilità non è un dettaglio.

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
import time

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from cvbook.dati import carica, leggi_registro
from cvbook.metriche import drawdown, rendimenti

# %% [markdown]
# ## Uno — La riproducibilità
#
# Un lavoro è riproducibile se, eseguito di nuovo, dà lo stesso identico
# risultato. Sempre. Su un altro computer, fra un anno, eseguito da un'altra
# persona.
#
# Qui i dati sono **congelati**: salvati una volta, con la data di estrazione e
# un'impronta che ne verifica l'integrità.

# %%
voce = leggi_registro()["btcusdt"]
print(f"serie:      {voce.nome}")
print(f"fonte:      {voce.fonte}")
print(f"estratta:   {voce.estratto}")
print(f"periodo:    {voce.dal} → {voce.al}  ({voce.righe} righe)")
print(f"impronta:   {voce.sha256}")
print("\nSe qualcuno modificasse quel file, `carica()` si rifiuterebbe di "
      "eseguire. Non e' pignoleria: e' cio' che rende le figure del libro "
      "verificabili fra dieci anni.")

# %% [markdown]
# ## Due — Il seme del caso
#
# I computer non producono numeri davvero casuali: producono sequenze che
# sembrano casuali, generate a partire da un numero iniziale detto **seme**.
# Stesso seme, stessa sequenza.

# %%
print("con lo stesso seme, tre esecuzioni:")
for _ in range(3):
    rng = np.random.default_rng(42)
    print("   ", np.round(rng.normal(size=5), 4))

print("\nsenza fissare il seme, tre esecuzioni:")
for _ in range(3):
    rng = np.random.default_rng()   # ← nessun seme
    print("   ", np.round(rng.normal(size=5), 4))

print("\nQuando qualcuno mostra il risultato di una simulazione, CHIEDI se il "
      "seme e' fissato e qual e'. Se non lo e', quel risultato non si puo' "
      "ricontrollare — e se ha eseguito piu' volte scegliendo l'esecuzione che "
      "gli piaceva di piu', e' il capitolo sui test multipli applicato ai "
      "numeri casuali.")

# %% [markdown]
# ## Tre — La vettorizzazione
#
# Il modo intuitivo di elaborare tremila giorni è: prendi il primo, fai il conto;
# prendi il secondo, fai il conto. Funziona ed è lentissimo.
#
# Il modo giusto è pensare all'intera serie **come a un oggetto solo**.

# %%
prezzi = carica("btcusdt").sort("data")["chiusura"].to_numpy()

# Modo intuitivo: un giorno alla volta.
inizio = time.perf_counter()
lento = []
for i in range(1, len(prezzi)):
    lento.append(prezzi[i] / prezzi[i - 1] - 1)
tempo_lento = time.perf_counter() - inizio

# Modo vettorizzato: un'istruzione sola, applicata a tutto.
inizio = time.perf_counter()
veloce = prezzi[1:] / prezzi[:-1] - 1
tempo_veloce = time.perf_counter() - inizio

print(f"un giorno alla volta: {tempo_lento * 1000:8.2f} ms")
print(f"tutta la serie insieme:{tempo_veloce * 1000:8.3f} ms")
print(f"rapporto: {tempo_lento / max(tempo_veloce, 1e-9):.0f} volte")
print(f"risultati identici? {np.allclose(lento, veloce)}")

print("\nMa la velocita' non e' il punto vero. Il punto e' che CAMBIA LE DOMANDE "
      "che ti vengono in mente: chi pensa per serie intere si chiede "
      "naturalmente «quante volte e' successo, su tutti gli asset, in tutti i "
      "periodi». Chi pensa un giorno alla volta si ferma prima.")

# %% [markdown]
# ## Quattro — Ripetere su molte serie
#
# È il passaggio che apre le domande interessanti. Tre righe.

# %%
risposte = {}
for nome in ("btcusdt", "ethusdt", "solusdt"):
    p = carica(nome).sort("data")["chiusura"].to_numpy()
    dd = drawdown(np.concatenate([[1.0], np.cumprod(1 + rendimenti(p))]))
    risposte[nome] = float((dd < -0.5).mean())

for nome, quota in risposte.items():
    print(f"{nome:>10s}: {quota:5.1%} del tempo con meno della meta' del proprio massimo")

# %% [markdown]
# ## Cinque — Confrontare con il caso
#
# Generare percorsi casuali e posizionarci sopra il proprio risultato. È forse la
# singola capacità più utile di tutto il libro.

# %%
r = rendimenti(prezzi)
reale = float(np.prod(1 + r))


def esperimento(seme: int | None, percorsi: int = 400) -> float:
    """Quota di percorsi ricampionati che fanno meglio di quello vero.

    Attenzione a una sottigliezza che il capitolo sull'aritmetica ha gia'
    incontrato: **rimescolare** i rendimenti non cambia il capitale finale — la
    moltiplicazione e' commutativa. Per ottenere storie diverse bisogna
    ricampionare **con reinserimento**, cioe' costruire percorsi in cui alcuni
    periodi si ripetono e altri mancano.
    """
    generatore = np.random.default_rng(seme)
    indici = generatore.integers(0, len(r), size=(percorsi, len(r)))
    return float((np.prod(1 + r[indici], axis=1) > reale).mean())


print(f"il risultato vero: {reale:.2f}x\n")
print("con il seme fissato, tre esecuzioni:")
for _ in range(3):
    print(f"    {esperimento(2026):.3f}")

print("\nsenza seme, tre esecuzioni:")
for _ in range(3):
    print(f"    {esperimento(None):.3f}")

print("\nE' l'esercizio finale del capitolo: la stessa identica cella, tre "
      "risultati diversi. Se un numero cambia a ogni esecuzione, non si puo' "
      "ricontrollare — e quindi non e' una prova.")

# %% [markdown]
# ### Le quattro capacità, e basta
#
# 1. **Caricare dei dati e guardarli.** È il novanta per cento del lavoro reale.
# 2. **Fare un conto su un'intera serie.** Rendimenti, medie, distanze dal
#    massimo: tre righe ciascuna.
# 3. **Ripetere il conto su molte serie.** È il passaggio che apre le domande
#    interessanti.
# 4. **Confrontare con il caso.** La cella qui sopra.
#
# Non serve altro. Non servono le classi, le strutture dati avanzate, i modelli
# di apprendimento automatico. Il modo più rapido che conosco per cominciare non
# è studiare il linguaggio: è **modificare qualcosa che già funziona e guardare
# cosa cambia.** Questo quaderno è fatto per quello.
