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
# **La matematica di chi perde**.*
#
# Tre conti sui tuoi numeri: quanto rischiare per operazione dato il capitale e
# la perdita massima che accetti; qual è la frazione ottimale teorica dato il
# vantaggio che pensi di avere; e quanto vale il rischio **complessivo** delle
# tue posizioni aperte tenendo conto di quanto sono correlate.
#
# Poi il grafico della rovina. È il conto da fare **prima** di aumentare la
# dimensione, non dopo.
#
# ---
#
# > **EN** — *Calculator 4 — How much to risk.* Notebook for the chapter
# > "Sizing is the strategy". Three calculations on your own numbers: how much
# > to risk per trade given your capital and the maximum loss you accept; what
# > the theoretical optimal fraction is given the edge you believe you have;
# > and what the **overall** risk of your open positions is once correlation
# > is taken into account. Then the ruin curve — the calculation to make
# > **before** increasing size, not after.

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
from cvbook.lingua import t
from cvbook.metriche import GIORNI_ANNO, rendimenti, rischio_di_rovina

# %% [markdown]
# ## 1. La curva che sale, tocca la vetta e crolla
#
# Un gioco con un vantaggio **reale e noto**: si vince una certa percentuale
# delle volte, guadagnando quanto si rischia. È un vantaggio che sui mercati veri
# non si trova. La domanda è: quanto rischiare, ogni volta?
#
# ---
#
# > **EN** — *1. The curve that rises, peaks and crashes.* A game with a
# > **real and known** edge: you win a certain percentage of the time,
# > earning as much as you risk — an edge you don't find in real markets. The
# > question is: how much to risk, every time?

# %%
VINCITE = 0.55        # ← quota di operazioni vincenti
                      # PROVA / TRY: 0,52 (vedi esercizio 1) · 0,55 · 0,60
RAPPORTO = 1.0        # ← quanto si guadagna rispetto a quanto si rischia
                      # PROVA / TRY: 0,5 · 1,0 · 2,0
OPERAZIONI = 500      # PROVA / TRY: 100 (veloce) · 500 · 2000 (curva più liscia)
PERCORSI = 4000       # PROVA / TRY: 500 (veloce, mediana rumorosa) · 4000 · 20000

frazioni = np.arange(0.01, 0.51, 0.01)
rng = np.random.default_rng(seed_for("calc-dimensionamento"))
# NON TOCCARE / DO NOT CHANGE: il seme fissa i numeri citati nel testo qui
# sotto (la frazione ottimale simulata, le probabilità di rovina) — cambiarlo
# dopo aver visto il risultato è il p-hacking che il libro smonta altrove.
# The seed fixes the numbers quoted in the text below (the simulated optimal
# fraction, the ruin probabilities) — changing it after seeing the result is
# the p-hacking the book takes apart elsewhere.
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
    sx.set_xlabel(t("Frazione di capitale rischiata per operazione (%)",
                     "Fraction of capital risked per trade (%)"))
    sx.set_ylabel(t(f"Capitale mediano dopo {OPERAZIONI} operazioni (scala log)",
                     f"Median capital after {OPERAZIONI} trades (log scale)"))

    dx.plot(frazioni * 100, rovine * 100, linewidth=2)
    dx.set_xlabel(t("Frazione rischiata per operazione (%)", "Fraction risked per trade (%)"))
    dx.set_ylabel(t("Percorsi sotto un quinto del capitale (%)", "Paths below a fifth of capital (%)"))
    plt.show()

kelly = VINCITE - (1 - VINCITE) / RAPPORTO
print(t(f"vantaggio: si vince il {VINCITE:.0%} delle volte, rapporto {RAPPORTO:g}\n",
        f"edge: wins {VINCITE:.0%} of the time, ratio {RAPPORTO:g}\n"))
print(t(f"frazione con la crescita mediana migliore (simulata): {ottimale:.0%}",
        f"fraction with the best median growth (simulated):     {ottimale:.0%}"))
print(t(f"frazione ottimale teorica:                            {kelly:.0%}",
        f"theoretical optimal fraction:                         {kelly:.0%}"))
print(t(f"\ncapitale mediano rischiando il {ottimale:.0%}: {mediane[int(np.argmax(mediane))]:,.1f}x",
        f"\nmedian capital risking {ottimale:.0%}: {mediane[int(np.argmax(mediane))]:,.1f}x"))
for f in (0.02, 0.20, 0.30, 0.40):
    k = int(round(f * 100)) - 1
    if 0 <= k < len(frazioni):
        print(t(f"  rischiando il {f:>4.0%}: {mediane[k]:12,.2f}x   "
                f"probabilita' di rovina {rovine[k]:6.1%}",
                f"  risking {f:>4.0%}: {mediane[k]:12,.2f}x   "
                f"probability of ruin {rovine[k]:6.1%}"))

print(t("\nAvere ragione non basta. Bisogna anche rischiare la quantita' giusta: "
        "oltre un certo punto, aumentare il rischio RIDUCE il risultato — non lo "
        "aumenta con piu' varianza, lo riduce e basta.",
        "\nBeing right isn't enough. You also have to risk the right amount: "
        "past a certain point, increasing risk REDUCES the outcome — it doesn't "
        "boost it with more variance, it just reduces it."))

# %% [markdown]
# ## 2. La curva è piatta a sinistra e ripida a destra
#
# Il motivo per cui, quando sei incerto sul vantaggio — e lo sei sempre — devi
# sbagliare **per difetto**.
#
# ---
#
# > **EN** — *2. The curve is flat on the left and steep on the right.* The
# > reason why, when you're uncertain about your edge — and you always are —
# > you must err **on the low side**.

# %%
i_ott = int(np.argmax(mediane))
print(f"{t('frazione', 'fraction'):>10s} {t('capitale mediano', 'median capital'):>18s} "
      f"{t('perdita rispetto al massimo', 'loss relative to peak'):>30s}")
for delta in (-8, -6, -4, -2, 0, 2, 4, 6, 8):
    k = i_ott + delta
    if 0 <= k < len(frazioni):
        perdita = mediane[k] / mediane[i_ott] - 1
        print(f"{frazioni[k]:10.0%} {mediane[k]:17,.1f}x {perdita:29.1%}")

print(t("\nStare sotto costa poco, stare sopra costa moltissimo. E' l'asimmetria "
        "che perdona il difetto e punisce l'eccesso.",
        "\nBeing under costs little, being over costs a lot. It's the asymmetry "
        "that forgives shortfall and punishes excess."))

# %% [markdown]
# ## 3. Il tuo rischio per operazione
#
# Nota la distinzione che quasi tutti confondono: la **dimensione** è quanto
# capitale impegni, il **rischio** è quanto perdi se va male. È il secondo che va
# tenuto costante.
#
# ---
#
# > **EN** — *3. Your risk per trade.* Note the distinction almost everyone
# > confuses: **size** is how much capital you commit, **risk** is how much
# > you lose if it goes wrong. It's the second one that must be kept constant.

# %%
CAPITALE = 20_000.0              # PROVA / TRY: il tuo capitale reale
RISCHIO_PER_OPERAZIONE = 0.01   # ← percentuale del capitale, fra 0,5% e 2%
                                 # PROVA / TRY: 0,005 · 0,01 · 0,02
DISTANZA_USCITA = 0.08          # ← a che distanza esci in perdita
                                 # PROVA / TRY: 0,04 (stop stretto) · 0,08 · 0,15

rischio_euro = CAPITALE * RISCHIO_PER_OPERAZIONE
dimensione = rischio_euro / DISTANZA_USCITA

print(t(f"capitale:                {CAPITALE:12,.0f} euro", f"capital:                 {CAPITALE:12,.0f} euros"))
print(t(f"rischio per operazione:  {rischio_euro:12,.0f} euro ({RISCHIO_PER_OPERAZIONE:.1%})",
        f"risk per trade:          {rischio_euro:12,.0f} euros ({RISCHIO_PER_OPERAZIONE:.1%})"))
print(t(f"uscita in perdita a:     {DISTANZA_USCITA:12.1%} dall'ingresso",
        f"stop loss at:            {DISTANZA_USCITA:12.1%} from entry"))
print(t(f"→ dimensione della posizione: {dimensione:,.0f} euro "
        f"({dimensione / CAPITALE:.1%} del capitale)",
        f"→ position size: {dimensione:,.0f} euros "
        f"({dimensione / CAPITALE:.1%} of capital)"))
print(t("\nSe l'uscita fosse a meta' distanza, la dimensione raddoppierebbe a "
        "parita' di rischio. E' esattamente il meccanismo per cui gli stop stretti "
        "spesso AUMENTANO il rischio complessivo invece di ridurlo.",
        "\nIf the stop were at half the distance, size would double for the same "
        "risk. That's exactly the mechanism by which tight stops often INCREASE "
        "overall risk instead of reducing it."))

# %% [markdown]
# ## 4. Il conto della rovina
#
# ---
#
# > **EN** — *4. The ruin calculation.*

# %%
print(f"{t('rischio per op.', 'risk per trade'):>16s} "
      f"{t('10 perdite di fila', '10 losses in a row'):>20s} "
      f"{t('serve per tornare', 'needed to recover'):>19s} "
      f"{t('prob. di rovina', 'ruin prob.'):>17s}")
for rischio in (0.005, 0.01, 0.02, 0.05, 0.10, 0.20):  # PROVA / TRY: aggiungi il tuo rischio per operazione
    resta = (1 - rischio) ** 10
    recupero = 1 / resta - 1
    # NON TOCCARE / DO NOT CHANGE: seme fissato riga per riga (uno per
    # rischio) perché la probabilità di rovina stampata sia sempre la stessa.
    # Seed fixed row by row (one per risk level) so the printed ruin
    # probability is always the same.
    prob = rischio_di_rovina(VINCITE, RAPPORTO, rischio, operazioni=1000,
                             soglia=0.2, campioni=4000,
                             rng=np.random.default_rng(seed_for(f"rovina-{rischio}")))
    print(f"{rischio:16.1%} {resta:19.1%} {recupero:18.0%} {prob:17.1%}")

print(t("\nDieci perdite consecutive, con un metodo che vince il 55% delle volte, "
        "capitano circa una volta ogni tremila operazioni: quasi certamente almeno "
        "una volta nella tua vita operativa.",
        "\nTen consecutive losses, with a method that wins 55% of the time, happen "
        "roughly once every three thousand trades: almost certainly at least once "
        "in your trading lifetime."))

# %% [markdown]
# ## 5. Il rischio complessivo, che non è la somma
#
# Se hai cinque posizioni che rischiano il 2% ciascuna, non stai rischiando il
# 2%. E nemmeno il 10%, se non sono perfettamente correlate.
#
# ---
#
# > **EN** — *5. Overall risk, which is not the sum.* If you have five
# > positions each risking 2%, you're not risking 2%. Nor 10%, unless they're
# > perfectly correlated.

# %%
POSIZIONI = 5           # PROVA / TRY: il numero VERO delle tue posizioni aperte
RISCHIO_CIASCUNA = 0.02  # PROVA / TRY: il rischio che assegni a ciascuna

print(t(f"{POSIZIONI} posizioni al {RISCHIO_CIASCUNA:.0%} ciascuna\n",
        f"{POSIZIONI} positions at {RISCHIO_CIASCUNA:.0%} each\n"))
print(f"{t('correlazione', 'correlation'):>13s} {t('rischio complessivo', 'overall risk'):>21s}")
for rho in (0.0, 0.3, 0.7, 0.9, 1.0):
    varianza = POSIZIONI * RISCHIO_CIASCUNA**2 * (1 + (POSIZIONI - 1) * rho)
    print(f"{rho:13.1f} {np.sqrt(varianza / POSIZIONI) * np.sqrt(POSIZIONI):21.1%}")

print(t("\nNei momenti brutti la correlazione sale — il Lab 7 lo misura — quindi il "
        "numero da usare per il limite complessivo e' quello delle righe in basso, "
        "non quello delle righe in alto.",
        "\nIn bad moments correlation rises — Lab 7 measures it — so the number to "
        "use for the overall limit is the one from the bottom rows, not the top "
        "ones."))

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
#
# ---
#
# > **EN** — *Exercises.*
# > 1. In the first cell set `VINCITE = 0.52`, already a very hard edge to
# >    actually have. The optimal fraction collapses, and with it the margin
# >    for error.
# > 2. Halve the edge you believe you have and redo the calculation: if you
# >    were risking the optimal fraction of the overestimated edge, you're
# >    now on the declining branch of the curve without having done anything.
# > 3. In the fifth cell, enter the **real** number of your open positions and
# >    the correlation measured with Lab 7. Compare it with the limit you had
# >    in mind.
