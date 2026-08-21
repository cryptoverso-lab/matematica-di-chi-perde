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
# # Calcolatore 4 — Quanto rischiare
#
# *Quaderno del capitolo «Il dimensionamento è la strategia» di
# **Non Fidarti di Me**.*
#
# Tre conti sui tuoi numeri: quanto rischiare per operazione dato il capitale e
# la perdita massima che accetti; qual è la frazione ottimale teorica dato il
# vantaggio che pensi di avere; e quanto vale il rischio **complessivo** delle
# tue posizioni aperte tenendo conto di quanto sono correlate.
#
# Poi il grafico della rovina. È il conto da fare **prima** di aumentare la
# dimensione, non dopo.

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

avvio.prepara(["btcusdt"])

# %%
import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for
from cvbook.dati import carica
from cvbook.metriche import GIORNI_ANNO, rendimenti, rischio_di_rovina

# %% [markdown]
# ## 1. La curva che sale, tocca la vetta e crolla
#
# Un gioco con un vantaggio **reale e noto**: si vince una certa percentuale
# delle volte, guadagnando quanto si rischia. È un vantaggio che sui mercati veri
# non si trova. La domanda è: quanto rischiare, ogni volta?

# %%
VINCITE = 0.55        # ← quota di operazioni vincenti
RAPPORTO = 1.0        # ← quanto si guadagna rispetto a quanto si rischia
OPERAZIONI = 500
PERCORSI = 4000

frazioni = np.arange(0.01, 0.51, 0.01)
rng = np.random.default_rng(seed_for("calc-dimensionamento"))
esiti = rng.random((PERCORSI, OPERAZIONI)) < VINCITE

mediane, rovine = [], []
for f in frazioni:
    passi = np.where(esiti, 1 + f * RAPPORTO, 1 - f)
    curve = np.cumprod(passi, axis=1)
    mediane.append(float(np.median(curve[:, -1])))
    rovine.append(float((curve[:, -1] < 0.2).mean()))

mediane, rovine = np.array(mediane), np.array(rovine)
ottimale = float(frazioni[int(np.argmax(mediane))])

with avvio.figura("schermo"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=(12, 4.5))
    sx.plot(frazioni * 100, mediane, linewidth=2)
    sx.axvline(ottimale * 100, linestyle=":", linewidth=1.5)
    sx.set_yscale("log")
    sx.set_xlabel("Frazione di capitale rischiata per operazione (%)")
    sx.set_ylabel(f"Capitale mediano dopo {OPERAZIONI} operazioni (scala log)")

    dx.plot(frazioni * 100, rovine * 100, linewidth=2)
    dx.set_xlabel("Frazione rischiata per operazione (%)")
    dx.set_ylabel("Percorsi sotto un quinto del capitale (%)")
    plt.show()

kelly = VINCITE - (1 - VINCITE) / RAPPORTO
print(f"vantaggio: si vince il {VINCITE:.0%} delle volte, rapporto {RAPPORTO:g}\n")
print(f"frazione con la crescita mediana migliore (simulata): {ottimale:.0%}")
print(f"frazione ottimale teorica:                            {kelly:.0%}")
print(f"\ncapitale mediano rischiando il {ottimale:.0%}: {mediane[int(np.argmax(mediane))]:,.1f}x")
for f in (0.02, 0.20, 0.30, 0.40):
    k = int(round(f * 100)) - 1
    if 0 <= k < len(frazioni):
        print(f"  rischiando il {f:>4.0%}: {mediane[k]:12,.2f}x   "
              f"probabilita' di rovina {rovine[k]:6.1%}")

print("\nAvere ragione non basta. Bisogna anche rischiare la quantita' giusta: "
      "oltre un certo punto, aumentare il rischio RIDUCE il risultato — non lo "
      "aumenta con piu' varianza, lo riduce e basta.")

# %% [markdown]
# ## 2. La curva è piatta a sinistra e ripida a destra
#
# Il motivo per cui, quando sei incerto sul vantaggio — e lo sei sempre — devi
# sbagliare **per difetto**.

# %%
i_ott = int(np.argmax(mediane))
print(f"{'frazione':>10s} {'capitale mediano':>18s} {'perdita rispetto al massimo':>30s}")
for delta in (-8, -6, -4, -2, 0, 2, 4, 6, 8):
    k = i_ott + delta
    if 0 <= k < len(frazioni):
        perdita = mediane[k] / mediane[i_ott] - 1
        print(f"{frazioni[k]:10.0%} {mediane[k]:17,.1f}x {perdita:29.1%}")

print("\nStare sotto costa poco, stare sopra costa moltissimo. E' l'asimmetria "
      "che perdona il difetto e punisce l'eccesso.")

# %% [markdown]
# ## 3. Il tuo rischio per operazione
#
# Nota la distinzione che quasi tutti confondono: la **dimensione** è quanto
# capitale impegni, il **rischio** è quanto perdi se va male. È il secondo che va
# tenuto costante.

# %%
CAPITALE = 20_000.0
RISCHIO_PER_OPERAZIONE = 0.01   # ← percentuale del capitale, fra 0,5% e 2%
DISTANZA_USCITA = 0.08          # ← a che distanza esci in perdita

rischio_euro = CAPITALE * RISCHIO_PER_OPERAZIONE
dimensione = rischio_euro / DISTANZA_USCITA

print(f"capitale:                {CAPITALE:12,.0f} euro")
print(f"rischio per operazione:  {rischio_euro:12,.0f} euro ({RISCHIO_PER_OPERAZIONE:.1%})")
print(f"uscita in perdita a:     {DISTANZA_USCITA:12.1%} dall'ingresso")
print(f"→ dimensione della posizione: {dimensione:,.0f} euro "
      f"({dimensione / CAPITALE:.1%} del capitale)")
print("\nSe l'uscita fosse a meta' distanza, la dimensione raddoppierebbe a "
      "parita' di rischio. E' esattamente il meccanismo per cui gli stop stretti "
      "spesso AUMENTANO il rischio complessivo invece di ridurlo.")

# %% [markdown]
# ## 4. Il conto della rovina

# %%
print(f"{'rischio per op.':>16s} {'10 perdite di fila':>20s} {'serve per tornare':>19s} "
      f"{'prob. di rovina':>17s}")
for rischio in (0.005, 0.01, 0.02, 0.05, 0.10, 0.20):
    resta = (1 - rischio) ** 10
    recupero = 1 / resta - 1
    prob = rischio_di_rovina(VINCITE, RAPPORTO, rischio, operazioni=1000,
                             soglia=0.2, campioni=4000,
                             rng=np.random.default_rng(seed_for(f"rovina-{rischio}")))
    print(f"{rischio:16.1%} {resta:19.1%} {recupero:18.0%} {prob:17.1%}")

print("\nDieci perdite consecutive, con un metodo che vince il 55% delle volte, "
      "capitano circa una volta ogni tremila operazioni: quasi certamente almeno "
      "una volta nella tua vita operativa.")

# %% [markdown]
# ## 5. Il rischio complessivo, che non è la somma
#
# Se hai cinque posizioni che rischiano il 2% ciascuna, non stai rischiando il
# 2%. E nemmeno il 10%, se non sono perfettamente correlate.

# %%
POSIZIONI = 5
RISCHIO_CIASCUNA = 0.02

print(f"{POSIZIONI} posizioni al {RISCHIO_CIASCUNA:.0%} ciascuna\n")
print(f"{'correlazione':>13s} {'rischio complessivo':>21s}")
for rho in (0.0, 0.3, 0.7, 0.9, 1.0):
    varianza = POSIZIONI * RISCHIO_CIASCUNA**2 * (1 + (POSIZIONI - 1) * rho)
    print(f"{rho:13.1f} {np.sqrt(varianza / POSIZIONI) * np.sqrt(POSIZIONI):21.1%}")

print("\nNei momenti brutti la correlazione sale — il Lab 7 lo misura — quindi il "
      "numero da usare per il limite complessivo e' quello delle righe in basso, "
      "non quello delle righe in alto.")

# %% [markdown]
# ### Esercizi
#
# 1. Nella prima cella metti `VINCITE = 0.52`, che è già un vantaggio molto
#    difficile da avere davvero. La frazione ottimale crolla, e con essa il
#    margine d'errore.
# 2. Dimezza il vantaggio che credi di avere e rifai il conto: se stavi
#    rischiando la frazione ottimale del vantaggio sopravvalutato, ora sei nel
#    ramo discendente della curva senza aver fatto niente.
# 3. Nella quinta cella metti il numero **vero** delle tue posizioni aperte e la
#    correlazione misurata con il Lab 7. Confronta con il limite che avevi in
#    mente.
