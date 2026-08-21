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
# # Lab 11 — Quante osservazioni servono davvero
#
# *Quaderno del capitolo «Quanto serve per sapere se sei bravo» di
# **La matematica di chi perde**.*
#
# Il conto con i tuoi numeri: quante operazioni servirebbero per stabilire che il
# vantaggio che pensi di avere non è rumore. E poi la simulazione che consiglio a
# tutti: venti strategie **prive di qualunque vantaggio**, testate tutte. In media
# una supera il test standard. Vederla passare, sapendo che dentro non c'è nulla,
# vale più di dieci pagine di spiegazioni.
#
# ---
#
# > **EN** — *Lab 11 — How many observations you really need.* Notebook for
# > the chapter "How much it takes to know if you're good". The calculation
# > with your own numbers: how many trades it would take to establish that
# > the edge you think you have isn't noise. Then the simulation I recommend
# > to everyone: twenty strategies **with absolutely no edge**, all tested.
# > On average one passes the standard test. Watching it pass, knowing
# > there's nothing inside, is worth more than ten pages of explanation.

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

avvio.prepara(["btcusdt"])

# %%
from math import ceil, erf, sqrt

import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for
from cvbook.dati import carica
from cvbook.metriche import rendimenti

# %% [markdown]
# ## 1. Il conto, con i tuoi numeri
#
# Due soli ingredienti: **quanto è grande il vantaggio** che vuoi dimostrare e
# **quanto oscillano** i risultati attorno a esso. Il rapporto fra i due decide
# tutto. È lo stesso motivo per cui in una stanza silenziosa senti un sussurro e
# in discoteca devi urlare.
#
# ---
#
# > **EN** — *1. The calculation, with your own numbers.* Just two
# > ingredients: **how big the edge is** you want to prove, and **how much
# > the results swing** around it. Their ratio decides everything. It's the
# > same reason you hear a whisper in a silent room and have to shout in a
# > nightclub.

# %%
VANTAGGIO = 0.001        # ← guadagno medio per operazione, al netto dei costi
                         # PROVA / TRY: il TUO vantaggio stimato (esercizio 1)
OSCILLAZIONE = 0.035     # ← deviazione standard del risultato per operazione
                         # PROVA / TRY: la TUA oscillazione (esercizio 1)
OPERAZIONI_ANNO = 250    # ← quante ne fai in un anno
POTENZA = 0.80           # ← probabilita' di accorgersene, se il vantaggio esiste
ALFA = 0.05              # ← rischio accettato di scambiare rumore per segnale


def quantile_normale(p: float) -> float:
    """Inversa della normale standard, per bisezione: nessuna dipendenza esterna."""
    basso, alto = -10.0, 10.0
    for _ in range(200):
        mezzo = (basso + alto) / 2
        if 0.5 * (1 + erf(mezzo / sqrt(2))) < p:
            basso = mezzo
        else:
            alto = mezzo
    return (basso + alto) / 2


def quante_servono(vantaggio: float, oscillazione: float,
                   potenza: float = POTENZA, alfa: float = ALFA) -> int:
    if vantaggio <= 0:
        raise ValueError("il vantaggio deve essere positivo")
    z_alfa = quantile_normale(1 - alfa)
    z_potenza = quantile_normale(potenza)
    return int(ceil(((z_alfa + z_potenza) * oscillazione / vantaggio) ** 2))


n = quante_servono(VANTAGGIO, OSCILLAZIONE)
print(f"vantaggio da dimostrare: {VANTAGGIO:.3%} per operazione")
print(f"oscillazione per operazione: {OSCILLAZIONE:.1%}\n")
print(f"operazioni necessarie: {n:,}")
print(f"a {OPERAZIONI_ANNO} operazioni l'anno: {n / OPERAZIONI_ANNO:,.1f} anni")

# %% [markdown]
# ## 2. La tabella, e la riga che fa male
#
# ---
#
# > **EN** — *2. The table, and the row that hurts.*

# %%
oscillazione_btc = float(np.std(rendimenti(
    carica("btcusdt").sort("data")["chiusura"].to_numpy()), ddof=1))
print(f"oscillazione giornaliera misurata su Bitcoin: {oscillazione_btc:.1%}\n")

vantaggi = [0.0005, 0.001, 0.002, 0.005, 0.010]
print(f"{'vantaggio':>10s} {'operazioni':>12s} {'a 250/anno':>14s}")
for v in vantaggi:
    q = quante_servono(v, oscillazione_btc)
    print(f"{v:10.2%} {q:12,d} {q / 250:13.1f} anni")

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    griglia = np.linspace(0.0003, 0.012, 200)
    ax.plot(griglia * 100, [quante_servono(v, oscillazione_btc) for v in griglia], linewidth=2)
    for v in vantaggi:
        ax.plot([v * 100], [quante_servono(v, oscillazione_btc)], marker="o")
    ax.set_yscale("log")
    ax.set_xlabel("Vantaggio medio per operazione (%)")
    ax.set_ylabel("Operazioni necessarie (scala log)")
    plt.show()

print("\nUn vantaggio dello 0,1% per operazione sarebbe un risultato eccellente — "
      "e i costi si mangiano gia' lo 0,12% a giro. Per dimostrarlo servono "
      "decenni di operativita' quotidiana.")

# %% [markdown]
# ## 3. Quaranta operazioni non distinguono nulla da nulla
#
# Con una moneta perfettamente equa, quante volte capita di ottenere 26 teste o
# più su 40 lanci? Il capitolo dice il 4%. Verifichiamolo invece di crederci.
#
# ---
#
# > **EN** — *3. Forty trades don't tell anything apart from nothing.* With
# > a perfectly fair coin, how often do you get 26 heads or more out of 40
# > flips? The chapter says 4%. Let's verify it instead of taking it on
# > faith.

# %%
LANCI = 40
VITTORIE = 26
PROVE = 200_000  # PROVA / TRY: 20000 (veloce) · 200000 (percentuale più precisa)

rng = np.random.default_rng(seed_for("lab-potere-moneta"))
esiti = rng.binomial(LANCI, 0.5, PROVE)
quota = float((esiti >= VITTORIE).mean())

print(f"su {PROVE:,} sequenze di {LANCI} lanci di una moneta EQUA:")
print(f"  {VITTORIE} vittorie o piu': {quota:.2%} delle volte")
print(f"\nE se hai provato piu' di una manciata di strategie prima di trovare "
      f"questa, quel {quota:.0%} te lo sei praticamente garantito.")

# %% [markdown]
# ## 4. Venti strategie senza alcun vantaggio, testate tutte
#
# ---
#
# > **EN** — *4. Twenty strategies with no edge at all, all tested.*

# %%
STRATEGIE = 20        # PROVA / TRY: 200 (vedi esercizio 2)
OSSERVAZIONI = 500    # PROVA / TRY: 5000 (vedi esercizio 3)

rng = np.random.default_rng(seed_for("lab-potere-multipli"))
soglia = quantile_normale(1 - ALFA)

print(f"{'strategia':>10s} {'risultato medio':>17s} {'statistica t':>14s} {'supera il test?':>17s}")
passate = 0
for k in range(STRATEGIE):
    campione = rng.normal(0.0, OSCILLAZIONE, OSSERVAZIONI)  # vantaggio ESATTAMENTE zero
    t = campione.mean() / (campione.std(ddof=1) / np.sqrt(OSSERVAZIONI))
    supera = t > soglia
    passate += supera
    print(f"{k + 1:10d} {campione.mean():17.4%} {t:14.2f} {'SI' if supera else 'no':>17s}")

print(f"\n{passate} strategie su {STRATEGIE} hanno superato il test standard.")
print("Dentro non c'era niente. Nessuna di esse aveva un vantaggio: era zero, "
      "messo li' da noi.")

# %% [markdown]
# ## 5. Il correttore per test multipli
#
# Gli dici quanti tentativi hai fatto e ti restituisce la soglia che avresti
# dovuto usare. Applicalo ai tuoi risultati passati — con una certa cautela
# emotiva.
#
# ---
#
# > **EN** — *5. The multiple-testing corrector.* Tell it how many attempts
# > you made and it gives back the threshold you should have used. Apply it
# > to your past results — with some emotional caution.

# %%
def soglia_corretta(tentativi: int, alfa: float = ALFA) -> float:
    """Correzione conservativa: si divide il rischio accettato per i tentativi."""
    return quantile_normale(1 - alfa / tentativi)


print(f"{'tentativi':>10s} {'soglia sulla statistica t':>27s} "
      f"{'prob. che almeno uno passi':>28s}")
for tentativi in (1, 5, 20, 50, 100, 500):
    print(f"{tentativi:10d} {soglia_corretta(tentativi):27.2f} "
          f"{1 - (1 - ALFA) ** tentativi:27.1%}")

print("\nCon cento tentativi, trovare qualcosa che supera il test non corretto e' "
      "praticamente certo. Non e' un difetto del test: e' la sua definizione.")

# %% [markdown]
# ### Esercizi
#
# 1. Nella prima cella metti il **tuo** vantaggio stimato e la **tua**
#    oscillazione, calcolati sul tuo registro. Il numero che esce è il tuo
#    orizzonte di verifica reale.
# 2. Nella quarta cella porta `STRATEGIE` a 200. Quante passano? Circa il 5%,
#    come previsto — e ognuna di esse, mostrata da sola, sembrerebbe una scoperta.
# 3. Cambia `OSSERVAZIONI` da 500 a 5000 nella quarta cella. La quota di
#    strategie che passa **non cambia**: più dati non proteggono dai test
#    multipli. Solo il conteggio dei tentativi protegge.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. In the first cell, enter **your own** estimated edge and **your own**
# >    swing, computed from your log. The resulting number is your real
# >    verification horizon.
# > 2. In the fourth cell raise `STRATEGIE` to 200. How many pass? About 5%,
# >    as predicted — and each one, shown on its own, would look like a
# >    discovery.
# > 3. Change `OSSERVAZIONI` from 500 to 5000 in the fourth cell. The share
# >    of strategies that pass **doesn't change**: more data doesn't protect
# >    against multiple testing. Only counting the attempts does.
