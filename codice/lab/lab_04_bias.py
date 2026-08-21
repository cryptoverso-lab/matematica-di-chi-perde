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
# # Lab 4 — Il costo misurato dei tuoi automatismi
#
# *Quaderno del capitolo «Perché il tuo cervello non è fatto per questo» di
# **La matematica di chi perde**.*
#
# Il capitolo dice che prendere i piccoli utili e tenere le perdite grandi è
# **misurabile e caro**. Qui lo misuri sui tuoi parametri, e poi provi
# l'esperimento che il capitolo racconta: distinguere a occhio un processo con un
# vantaggio reale da uno senza. Quasi nessuno ci riesce.
#
# ---
#
# > **EN** — *Lab 4 — The measured cost of your reflexes.* Notebook for the
# > chapter "Why your brain isn't built for this". The chapter says that
# > taking small profits and holding large losses is **measurable and
# > expensive**. Here you measure it on your own parameters, then try the
# > experiment the chapter describes: telling apart by eye a process with a
# > real edge from one without. Almost nobody can.

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
import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for
from cvbook.dati import carica
from cvbook.metriche import drawdown_massimo, equity, rendimenti
from cvbook.simulazioni import equity_casuali

prezzi = carica("btcusdt").sort("data")["chiusura"].to_numpy()
r = rendimenti(prezzi)

# %% [markdown]
# ## 1. Il costo del prendere subito l'utile
#
# Due comportamenti, stessa serie di prezzi, stesso capitale, stessi costi.
# Il primo compra e non tocca più niente. Il secondo fa quello che l'esperienza
# dei conti reali documenta: chiude appena è in utile di una certa percentuale,
# e resta dentro finché la perdita non raggiunge una soglia molto più larga.
#
# Nessuna previsione distingue i due. Solo le due soglie.
#
# ---
#
# > **EN** — *1. The cost of taking the profit right away.* Two behaviours,
# > same price series, same capital, same costs. The first buys and never
# > touches anything again. The second does what real-account experience
# > documents: closes as soon as it's up a certain percentage, and stays in
# > until the loss reaches a much wider threshold. No forecast tells the two
# > apart. Only the two thresholds do.

# %%
PRENDI_UTILE = 0.10   # ← chiudi quando sei in utile di questa percentuale
                      # PROVA / TRY: 0,05 · 0,10 · 0,50 (vedi esercizi 1 e 2)
SOPPORTA_PERDITA = 0.50  # ← resti dentro finche' la perdita non arriva a questa
                         # PROVA / TRY: 0,10 · 0,50 · 0,70 (vedi esercizi 1 e 2)
COSTO = 0.0012           # PROVA / TRY: 0,0006 · 0,0012 · 0,0025


def con_soglie(p: np.ndarray, su: float, giu: float, costo: float) -> np.ndarray:
    """Chiude quando la posizione tocca una soglia, e rientra il giorno dopo.

    Sono tre le cose che questo comportamento paga rispetto al non far nulla,
    e vale la pena tenerle distinte perche' pesano in modo molto diverso:

    1. il costo dell'uscita e quello del rientro, cioe' due volte `costo`;
    2. il giorno passato fuori dal mercato ad ogni chiusura — ed e' questa la
       voce piu' cara, perche' il capitolo sulla media che mente ha mostrato
       che pochissimi giorni contengono quasi tutto il risultato;
    3. niente altro: nessuna previsione, nessuna scelta di direzione.
    """
    valore = np.empty(len(p))
    valore[0] = 1.0
    ingresso, quota, liquido, dentro = p[0], 1.0 / p[0], 0.0, True

    for i in range(1, len(p)):
        if dentro:
            corrente = quota * p[i]
            variazione = p[i] / ingresso - 1.0
            if variazione >= su or variazione <= -giu:
                liquido = corrente * (1.0 - costo)   # esce: paga il costo
                dentro, corrente = False, liquido
            valore[i] = corrente
        else:
            ingresso = p[i]                          # rientra il giorno dopo
            quota = liquido * (1.0 - costo) / p[i]   # e ripaga il costo
            dentro = True
            valore[i] = quota * p[i]

    return valore


fermo = equity(r)
nervoso = con_soglie(prezzi, PRENDI_UTILE, SOPPORTA_PERDITA, COSTO)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.semilogy(fermo, linewidth=1.8, label="compra e non tocca niente")
    ax.semilogy(nervoso, linewidth=1.8, linestyle="--",
                label=f"chiude a +{PRENDI_UTILE:.0%}, sopporta -{SOPPORTA_PERDITA:.0%}")
    ax.set_ylabel("Capitale (scala log)")
    ax.set_xlabel("Giorni")
    ax.legend()
    plt.show()

print(f"chi non ha toccato niente:  {fermo[-1]:6.2f}x   calo massimo {drawdown_massimo(fermo):.1%}")
print(f"chi ha preso i piccoli utili: {nervoso[-1]:6.2f}x   calo massimo {drawdown_massimo(nervoso):.1%}")
print(f"differenza: {nervoso[-1] / fermo[-1] - 1:+.1%}")

# %% [markdown]
# Nota le due colonne del calo massimo. Il secondo comportamento ha rinunciato a
# una parte del risultato **senza comprarsi in cambio nemmeno un po' di
# tranquillità**. Ha pagato per l'illusione di controllo.
#
# ---
#
# > **EN** — Note the two maximum-drawdown columns. The second behaviour gave
# > up part of the result **without buying even a bit of peace of mind in
# > return**. It paid for the illusion of control.

# %% [markdown]
# ## 2. L'asimmetria del dolore, e perché appiattisce
#
# I parametri sperimentali della teoria del prospetto: la perdita pesa circa due
# volte e mezzo il guadagno di pari entità, e la curva si appiattisce
# allontanandosi dallo zero.
#
# ---
#
# > **EN** — *2. The asymmetry of pain, and why it flattens.* The
# > experimental parameters of prospect theory: a loss weighs about two and a
# > half times a gain of equal size, and the curve flattens out moving away
# > from zero.

# %%
CURVATURA = 0.88
AVVERSIONE = 2.25
# NON TOCCARE / DO NOT CHANGE: sono i parametri stimati sperimentalmente dalla
# teoria del prospetto (Kahneman e Tversky), non un valore a piacere — cambiarli
# smetterebbe di rappresentare quella ricerca.

importi = np.linspace(-10_000, 10_000, 400)
# np.where valuta entrambi i rami: si eleva a potenza il valore assoluto e si
# rimette il segno dopo, altrimenti numpy si lamenta delle radici di numeri
# negativi (e ha ragione).
grandezza = np.abs(importi) ** CURVATURA
valore = np.where(importi >= 0, grandezza, -AVVERSIONE * grandezza)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.plot(importi, valore, linewidth=2)
    ax.axhline(0, linewidth=0.8, color="#8C8C8C")
    ax.axvline(0, linewidth=0.8, color="#8C8C8C")
    ax.set_xlabel("Guadagno o perdita (euro)")
    ax.set_ylabel("Valore percepito (unità arbitrarie)")
    plt.show()

for x in (2_000, 8_000):
    su = x**CURVATURA
    giu = AVVERSIONE * x**CURVATURA
    print(f"{x:6,d} euro:  piacere {su:9.1f}   dolore {giu:9.1f}   rapporto {giu / su:.2f}")

passo_vicino = AVVERSIONE * (2000**CURVATURA)
passo_lontano = AVVERSIONE * (10000**CURVATURA - 8000**CURVATURA)
print(f"\ndolore nel passare da 0 a -2.000:      {passo_vicino:8.1f}")
print(f"dolore nel passare da -8.000 a -10.000: {passo_lontano:8.1f}")
print("È il motivo per cui, dopo una perdita gia' grande, rischiare ancora "
      "costa pochissimo in termini di sofferenza attesa.")

# %% [markdown]
# ## 3. Riesci a distinguere il vantaggio dal rumore?
#
# Sei serie. Alcune hanno un vantaggio reale, altre no. Scrivi la tua risposta
# prima di eseguire la cella successiva.
#
# ---
#
# > **EN** — *3. Can you tell the edge apart from noise?* Six series. Some
# > have a real edge, others don't. Write down your answer before running the
# > next cell.

# %%
rng = np.random.default_rng(seed_for("lab-bias-indovina"))
# NON TOCCARE / DO NOT CHANGE: scrivi la tua risposta PRIMA di eseguire la
# cella successiva. Cambiare il seme dopo aver sbagliato per ottenere un
# disegno più facile vanificherebbe l'esercizio, non lo migliorerebbe.
VANTAGGI = rng.permutation([0.0, 0.0, 0.0, 0.0005, 0.0005, 0.0])

with avvio.figura("schermo"):
    fig, assi = plt.subplots(2, 3, figsize=(11, 5))
    curve = []
    for k, ax in enumerate(assi.flat):
        c = equity_casuali(1, 400, rendimento_atteso=VANTAGGI[k],
                           volatilita_periodo=0.02, rng=rng)[0]
        curve.append(c)
        ax.plot(c * 100, linewidth=1.4)
        ax.axhline(100, linestyle=":", linewidth=0.8)
        ax.set_title(f"serie {k + 1}", fontsize=10)
        ax.set_xticks([])
    plt.show()

# %%
print("vantaggio reale per operazione:")
for k, v in enumerate(VANTAGGI):
    print(f"  serie {k + 1}: {v:.4%}  →  capitale finale {curve[k][-1]:.2f}x")
print("\nSe le due con vantaggio non sono quelle che avevi indicato, non e' un "
      "tuo limite: 400 osservazioni non bastano a distinguerle, e il capitolo "
      "sulla potenza statistica dice quante ne servirebbero.")

# %% [markdown]
# ### Esercizi
#
# 1. Nella prima cella metti `PRENDI_UTILE = 0.05` e `SOPPORTA_PERDITA = 0.70`:
#    è il comportamento estremo, e il costo cresce di conseguenza.
# 2. Prova `PRENDI_UTILE = 0.50` e `SOPPORTA_PERDITA = 0.10` — cioè il contrario
#    di quello che fa quasi tutti. Guarda cosa succede al risultato **e** al calo
#    massimo: non è gratis nemmeno quello.
# 3. Rifai l'esperimento della terza cella cambiando `400` in `4000`. Con dieci
#    volte le osservazioni la distinzione diventa possibile. È esattamente il
#    punto del capitolo sul potere statistico.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. In the first cell set `PRENDI_UTILE = 0.05` and `SOPPORTA_PERDITA = 0.70`:
# >    it's the extreme behaviour, and the cost grows accordingly.
# > 2. Try `PRENDI_UTILE = 0.50` and `SOPPORTA_PERDITA = 0.10` — the opposite
# >    of what almost everyone does. Watch what happens to the result **and**
# >    to the maximum drawdown: that isn't free either.
# > 3. Redo the third cell's experiment changing `400` to `4000`. With ten
# >    times the observations the distinction becomes possible. It's exactly
# >    the point of the chapter on statistical power.
