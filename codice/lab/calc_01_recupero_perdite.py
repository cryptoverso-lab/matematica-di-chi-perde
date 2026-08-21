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
# # Calcolatore 1 — Quanto serve per recuperare una perdita
#
# *Quaderno del capitolo «L'aritmetica che nessuno ti mostra» di
# **La matematica di chi perde**.*
#
# La perdita e il recupero non sono simmetrici, e la differenza cresce in fretta.
# Questo calcolatore mette i tuoi numeri dentro quell'asimmetria: quanto serve
# per tornare in pari, quanto costa la volatilità al capitale composto, e cosa
# succede aggiungendo la leva.
#
# ---
#
# > **EN** — *Calculator 1 — How much it takes to recover from a loss.*
# > Notebook for the chapter "The arithmetic nobody shows you" of **The math of
# > those who lose**. Loss and recovery are not symmetric, and the gap grows
# > fast. This calculator puts your own numbers inside that asymmetry: how much
# > it takes to break even, what volatility costs compounded capital, and what
# > happens once you add leverage.

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

from cvbook.dati import carica
from cvbook.lingua import t
from cvbook.metriche import drawdown_massimo, equity, recupero_necessario, rendimenti

# %% [markdown]
# ## 1. Il tuo numero
#
# Cambia `PERDITA` e riesegui. È l'unica cella che devi toccare.
#
# ---
#
# > **EN** — *1. Your number.* Change `PERDITA` (loss) and rerun. It's the
# > only cell you need to touch.

# %%
PERDITA = 0.50  # ← la perdita subita, in frazione: 0,50 vuol dire meno 50%
                # PROVA / TRY: qualunque valore fra 0,01 e 0,99 · guarda cosa
                # succede vicino a 0,90 (dove la curva diventa quasi verticale)

recupero = recupero_necessario(PERDITA)
print(t("perdita subita:        ", "loss taken:             ") + f"{PERDITA:6.1%}")
print(t("ti resta:              ", "you have left:          ") + f"{1 - PERDITA:6.1%}"
      + t(" del capitale", " of capital"))
print(t("serve un guadagno del: ", "you need a gain of:     ") + f"{recupero:6.1%}"
      + t(" per tornare al punto di partenza", " to get back to break even"))

# %% [markdown]
# ## 2. La curva intera
#
# La forma è la cosa da guardare: fino al 30% è una salita, dal 70% in poi è un
# muro. Non c'è nessuna soglia dichiarata da qualche parte — è aritmetica.
#
# ---
#
# > **EN** — *2. The full curve.* The shape is what matters: up to 30% it's a
# > climb, past 70% it's a wall. No threshold is declared anywhere — it's
# > arithmetic.

# %%
perdite = np.linspace(0.01, 0.95, 200)
recuperi = np.array([recupero_necessario(p) for p in perdite])

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.plot(perdite * 100, recuperi * 100, linewidth=2)
    for p in (0.2, 0.5, 0.8, 0.9):
        r = recupero_necessario(p)
        ax.plot([p * 100], [r * 100], marker="o")
        ax.annotate(
            f"-{p:.0%} → +{r:.0%}",
            xy=(p * 100, r * 100),
            xytext=(-6, 8),
            textcoords="offset points",
            ha="right",
        )
    ax.set_xlabel(t("Perdita subita (%)", "Loss taken (%)"))
    ax.set_ylabel(t("Guadagno necessario per tornare in pari (%)", "Gain needed to break even (%)"))
    ax.set_ylim(0, 1000)
    plt.show()

# %% [markdown]
# ## 3. Il freno della volatilità, sui tuoi parametri
#
# Due strategie con lo **stesso rendimento medio** non lasciano gli stessi soldi:
# la più volatile ne lascia meno. Il freno vale circa metà della varianza, e il
# calcolo qui sotto lo verifica invece di affermarlo.
#
# ---
#
# > **EN** — *3. The volatility drag, on your own parameters.* Two strategies
# > with the **same average return** don't leave you with the same money: the
# > more volatile one leaves less. The drag is worth about half the variance,
# > and the calculation below verifies it instead of just asserting it.

# %%
MEDIA_GIORNALIERA = 0.0010  # ← rendimento medio per giorno
                            # PROVA / TRY: 0,0005 · 0,0010 · 0,0020 — il freno
                            # dipende dalla volatilità, non da questo valore
GIORNI = 1000               # PROVA / TRY: 250 (un anno) · 1000 · 3000

rng = np.random.default_rng(20260816)
# NON TOCCARE / DO NOT CHANGE: il seme è fisso perché la tabella qui sotto è
# commentata nel testo con questi numeri esatti; cambiarlo dopo aver visto il
# risultato è il p-hacking che il libro smonta altrove.

print(f"{t('volatilita/giorno', 'volatility/day'):>18s} "
      f"{t('media aritm.', 'arith. mean'):>14s} "
      f"{t('composto', 'compounded'):>12s} "
      f"{t('capitale finale', 'final capital'):>16s}")
for vol in (0.005, 0.01, 0.02, 0.035, 0.05):
    r = rng.normal(MEDIA_GIORNALIERA, vol, GIORNI)
    curva = equity(r)
    composto = curva[-1] ** (1 / GIORNI) - 1
    print(f"{vol:18.3%} {r.mean():14.4%} {composto:12.4%} {curva[-1]:16.2f}x")

# %% [markdown]
# La colonna della media aritmetica resta ferma; quella del composto scende. È
# lo stesso rendimento medio che produce risultati diversi, e la differenza è
# **solo** la volatilità.
#
# ---
#
# > **EN** — The arithmetic-mean column stays put; the compounded one drops.
# > It's the same average return producing different outcomes, and the
# > difference is **only** volatility.

# %% [markdown]
# ## 4. La leva, che moltiplica il freno per il suo quadrato
#
# Con leva `k` il rendimento atteso si moltiplica per `k`, ma il freno per `k²`.
# Ecco perché esiste un punto oltre il quale aumentare la leva peggiora tutto —
# e su un asset già volatile quel punto arriva prestissimo.
#
# ---
#
# > **EN** — *4. Leverage, which multiplies the drag by its square.* With
# > leverage `k` the expected return is multiplied by `k`, but the drag by
# > `k²`. That's why there's a point past which more leverage makes everything
# > worse — and on an already-volatile asset that point arrives very soon.

# %%
df = carica("btcusdt").sort("data")
# PROVA / TRY: per usare un'altra serie aggiungila anche alla cella di setup
# (avvio.prepara([...])) — le 11 disponibili sono in codice/dati/registro.json:
# btcusdt · ethusdt · solusdt · lunausdt · fttusdt · ftsemib · eni · enel ·
# intesa · generali · eurusd
r_reali = rendimenti(df["chiusura"].to_numpy())


def curva_con_leva(rend: np.ndarray, k: float) -> np.ndarray:
    """Capitale con leva `k`, con l'azzeramento che e' definitivo.

    Un giorno in cui la posizione perde piu' del capitale non produce un numero
    negativo: produce la fine. Senza questo taglio il calcolo restituirebbe cali
    superiori al 100%, che non significano niente.

    Capital with `k`× leverage, where wipeout is permanent: a day in which the
    position loses more than the capital does not produce a negative number —
    it produces the end. Without this floor the calculation would return
    drawdowns above 100%, which mean nothing.
    """
    passi = np.maximum(1.0 + k * rend, 0.0)
    return np.concatenate([[1.0], np.cumprod(passi)])


print(f"{t('leva', 'leverage'):>5s} {t('capitale finale', 'final capital'):>16s} "
      f"{t('calo massimo', 'max drawdown'):>14s} {t('azzerato il', 'wiped out on'):>14s}")
for k in (1, 2, 3, 5, 10):  # PROVA / TRY: aggiungi 4 o 6, come suggerito negli esercizi
    curva = curva_con_leva(r_reali, k)
    azzerata = np.argmax(curva <= 0.0) if np.any(curva <= 0.0) else None
    quando = str(df["data"][int(azzerata)]) if azzerata is not None else "—"
    print(f"{k:5d} {curva[-1]:16.4f}x {drawdown_massimo(curva):14.1%} {quando:>14s}")

# %% [markdown]
# ### Esercizi
#
# 1. Metti `PERDITA = 0.83`, che è il calo massimo realmente attraversato da
#    questo asset nel periodo. Il numero che esce è il motivo per cui il capitolo
#    sul rischio parla di **sopravvivenza** e non di rendimento.
# 2. Nella cella della leva, prova `k = 4` e `k = 6`. Trova il punto in cui il
#    capitale finale smette di crescere. Nessuna previsione è cambiata: solo la
#    dimensione.
# 3. Nella cella del freno, tieni fissa `MEDIA_GIORNALIERA` e chiediti quale
#    volatilità azzera il composto. La risposta è la radice quadrata del doppio
#    della media — provala.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. Set `PERDITA = 0.83`, the actual maximum drawdown this asset went
# >    through in the period. The resulting number is why the risk chapter
# >    talks about **survival**, not return.
# > 2. In the leverage cell, try `k = 4` and `k = 6`. Find the point where
# >    final capital stops growing. No forecast changed — only the size.
# > 3. In the drag cell, keep `MEDIA_GIORNALIERA` fixed and ask yourself which
# >    volatility wipes out the compounded return. The answer is the square
# >    root of twice the mean — try it.
