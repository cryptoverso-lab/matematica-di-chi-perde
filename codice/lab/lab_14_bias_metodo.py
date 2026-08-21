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
# # Lab 14 — Come mente un backtest: il metodo
#
# *Quaderno del capitolo «Come mente un backtest — il metodo» di
# **La matematica di chi perde**.*
#
# Gli errori del capitolo precedente stanno nel codice e si trovano. Questi no:
# stanno nel modo in cui hai lavorato, non lasciano traccia e non falliscono
# nessun controllo automatico.
#
# Qui li rendiamo visibili con delle simulazioni, e alla fine c'è il correttore
# per test multipli: gli dici quanti tentativi hai fatto e ti restituisce la
# soglia che avresti dovuto usare.
#
# ---
#
# > **EN** — *Lab 14 — How a backtest lies: the method.* Notebook for the
# > chapter "How a backtest lies — the method". The previous chapter's errors
# > live in the code and can be found. These don't: they live in how you
# > worked, leave no trace, and fail no automated check. Here we make them
# > visible with simulations, and at the end there's the multiple-testing
# > corrector: tell it how many attempts you made and it gives back the
# > threshold you should have used.

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
from math import erf, sqrt

import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for
from cvbook.dati import carica
from cvbook.regole import esegui, rottura, sopra_media

ALFA = 0.05


def quantile_normale(p: float) -> float:
    basso, alto = -10.0, 10.0
    for _ in range(200):
        mezzo = (basso + alto) / 2
        if 0.5 * (1 + erf(mezzo / sqrt(2))) < p:
            basso = mezzo
        else:
            alto = mezzo
    return (basso + alto) / 2


# %% [markdown]
# ## 1. Venti idee che non funzionano, e quella che passa
#
# ---
#
# > **EN** — *1. Twenty ideas that don't work, and the one that passes.*

# %%
IDEE = 20
OSSERVAZIONI = 400

rng = np.random.default_rng(seed_for("lab-metodo-venti"))
soglia = quantile_normale(1 - ALFA)

statistiche = []
for _ in range(IDEE):
    campione = rng.normal(0.0, 0.03, OSSERVAZIONI)  # vantaggio ESATTAMENTE zero
    statistiche.append(campione.mean() / (campione.std(ddof=1) / np.sqrt(OSSERVAZIONI)))

statistiche = np.array(statistiche)
passate = statistiche > soglia

with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(np.arange(1, IDEE + 1), statistiche)
    ax.axhline(soglia, linestyle="--", linewidth=1.5,
               label=f"soglia del test standard ({soglia:.2f})")
    ax.set_xlabel("Idea provata")
    ax.set_ylabel("Statistica t")
    ax.legend()
    plt.show()

print(f"{int(passate.sum())} idee su {IDEE} hanno superato il test.")
print("Nessuna di esse aveva un vantaggio: era zero, messo li' da noi.")

# %% [markdown]
# ## 2. La tabella che cambia il significato di ogni risultato
#
# ---
#
# > **EN** — *2. The table that changes the meaning of every result.*

# %%
print(f"{'idee provate':>13s} {'prob. che almeno una passi':>28s}")
for n in (1, 5, 10, 20, 50, 100):
    print(f"{n:13d} {1 - (1 - ALFA) ** n:27.1%}")

print("\nChi prova cento configurazioni TROVERA' qualcosa che supera il test. "
      "E non sapra' di aver trovato niente, perche' il risultato finale ha "
      "esattamente lo stesso aspetto di una scoperta vera.")

# %% [markdown]
# ## 3. I tentativi che non conti
#
# Il capitolo elenca le scelte che non compaiono in nessun conteggio: quale
# asset, quale periodo, quale regola, quando fermarsi. Qui le contiamo davvero,
# su dati veri.
#
# ---
#
# > **EN** — *3. The attempts you don't count.* The chapter lists the
# > choices that show up in no tally: which asset, which period, which rule,
# > when to stop. Here we actually count them, on real data.

# %%
SERIE = ["btcusdt", "ethusdt", "solusdt"]
REGOLE = {
    "sopra la media 50": lambda p: sopra_media(p, 50),
    "sopra la media 100": lambda p: sopra_media(p, 100),
    "sopra la media 200": lambda p: sopra_media(p, 200),
    "rottura a 20": lambda p: rottura(p, 20),
    "rottura a 55": lambda p: rottura(p, 55),
}
PARTENZE = [0, 365, 730]

risultati = []
for nome_serie in SERIE:
    p_intero = carica(nome_serie).sort("data")["chiusura"].to_numpy()
    for nome_regola, regola in REGOLE.items():
        for partenza in PARTENZE:
            p = p_intero[partenza:]
            if len(p) < 400:
                continue
            finale = esegui(p, regola(p), costo=0.0012)["finale"]
            riferimento = float(p[-1] / p[0])
            risultati.append((nome_serie, nome_regola, partenza,
                              finale, finale / riferimento))

print(f"combinazioni provate: {len(risultati)}  "
      f"({len(SERIE)} serie × {len(REGOLE)} regole × {len(PARTENZE)} date d'inizio)\n")

rapporti = np.array([r[4] for r in risultati])
migliore = risultati[int(np.argmax(rapporti))]
print(f"la migliore: {migliore[1]} su {migliore[0]} partendo dal giorno {migliore[2]}")
print(f"  → {migliore[3]:.2f}x, cioe' {migliore[4]:.2f} volte il compra-e-tieni\n")
print(f"quante battono il compra-e-tieni: {int((rapporti > 1).sum())} su {len(rapporti)} "
      f"({(rapporti > 1).mean():.0%})")
print(f"mediana del rapporto: {np.median(rapporti):.2f}")
print("\nSe pubblicassi solo la prima riga, non avrei mentito su nessun numero. "
      "Avrei omesso il denominatore.")

# %% [markdown]
# ## 4. Il correttore per test multipli
#
# Applicalo ai tuoi risultati passati. Con una certa cautela emotiva.
#
# ---
#
# > **EN** — *4. The multiple-testing corrector.* Apply it to your past
# > results. With some emotional caution.

# %%
def soglia_corretta(tentativi: int, alfa: float = ALFA) -> float:
    """Correzione conservativa: il rischio accettato si divide per i tentativi."""
    return quantile_normale(1 - alfa / tentativi)


TUOI_TENTATIVI = len(risultati)  # ← metti il numero dal TUO registro delle ipotesi
TUA_STATISTICA = 2.4             # ← la statistica t del tuo risultato migliore

print(f"tentativi dichiarati: {TUOI_TENTATIVI}")
print(f"soglia non corretta:  {quantile_normale(1 - ALFA):.2f}")
print(f"soglia corretta:      {soglia_corretta(TUOI_TENTATIVI):.2f}")
print(f"\nil tuo {TUA_STATISTICA:.2f} " +
      ("SUPERA" if TUA_STATISTICA > soglia_corretta(TUOI_TENTATIVI) else "NON supera") +
      " la soglia corretta.")

# %% [markdown]
# ## 5. Il registro delle ipotesi
#
# Tutte le difese di questo capitolo si riducono a una pratica sola, che costa
# dieci minuti e vale più di qualunque tecnica sofisticata. Ecco lo scheletro:
# copialo in un file di testo e tienilo in ordine cronologico.
#
# ---
#
# > **EN** — *5. The hypothesis log.* All of this chapter's defences boil
# > down to a single practice, which costs ten minutes and is worth more than
# > any sophisticated technique. Here's the skeleton: copy it into a text
# > file and keep it in chronological order.

# %%
MODELLO = """\
data:                2026-08-16
ipotesi:             la rottura del massimo a N giorni produce un vantaggio su BTC
successo se:         supera il 95esimo percentile del metro del caso, con costi 0,25%
fallimento se:       resta sotto, oppure il risultato dipende da N in modo instabile
varianti previste:   24 valori di N, un solo mercato
--- esito ---
risultato:
tentativi effettivi:
note:
"""
print(MODELLO)
print("Dopo sei mesi quel file ti dira' una cosa che nessun backtest puo' dirti: "
      "QUANTE idee hai provato in tutto. E quel numero e' il moltiplicatore da "
      "applicare a ogni tuo risultato positivo.")

# %% [markdown]
# ### Esercizi
#
# 1. Nella terza cella aggiungi una regola e una data d'inizio. Il numero di
#    combinazioni cresce come il prodotto, non come la somma — ed è quello il
#    numero che conta.
# 2. Nella prima cella porta `IDEE` a 500 e conta quante passano. Circa il 5%,
#    come previsto. Ognuna di esse, mostrata da sola, sembrerebbe una scoperta.
# 3. Prendi un tuo risultato passato, stima quanti tentativi ci sono stati dietro
#    (contando anche quelli informali) e passalo al correttore. È l'esercizio più
#    scomodo del libro.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. In the third cell add a rule and a start date. The number of
# >    combinations grows as a product, not a sum — and that's the number
# >    that matters.
# > 2. In the first cell raise `IDEE` to 500 and count how many pass. About
# >    5%, as predicted. Each one, shown on its own, would look like a
# >    discovery.
# > 3. Take one of your own past results, estimate how many attempts were
# >    behind it (counting informal ones too), and run it through the
# >    corrector. It's the most uncomfortable exercise in the book.
