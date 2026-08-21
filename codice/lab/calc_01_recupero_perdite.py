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
# **Non Fidarti di Me**.*
#
# La perdita e il recupero non sono simmetrici, e la differenza cresce in fretta.
# Questo calcolatore mette i tuoi numeri dentro quell'asimmetria: quanto serve
# per tornare in pari, quanto costa la volatilità al capitale composto, e cosa
# succede aggiungendo la leva.

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

from cvbook.dati import carica
from cvbook.metriche import drawdown_massimo, equity, recupero_necessario, rendimenti

# %% [markdown]
# ## 1. Il tuo numero
#
# Cambia `PERDITA` e riesegui. È l'unica cella che devi toccare.

# %%
PERDITA = 0.50  # ← la perdita subita, in frazione: 0,50 vuol dire meno 50%

recupero = recupero_necessario(PERDITA)
print(f"perdita subita:        {PERDITA:6.1%}")
print(f"ti resta:              {1 - PERDITA:6.1%} del capitale")
print(f"serve un guadagno del: {recupero:6.1%} per tornare al punto di partenza")

# %% [markdown]
# ## 2. La curva intera
#
# La forma è la cosa da guardare: fino al 30% è una salita, dal 70% in poi è un
# muro. Non c'è nessuna soglia dichiarata da qualche parte — è aritmetica.

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
    ax.set_xlabel("Perdita subita (%)")
    ax.set_ylabel("Guadagno necessario per tornare in pari (%)")
    ax.set_ylim(0, 1000)
    plt.show()

# %% [markdown]
# ## 3. Il freno della volatilità, sui tuoi parametri
#
# Due strategie con lo **stesso rendimento medio** non lasciano gli stessi soldi:
# la più volatile ne lascia meno. Il freno vale circa metà della varianza, e il
# calcolo qui sotto lo verifica invece di affermarlo.

# %%
MEDIA_GIORNALIERA = 0.0010  # ← rendimento medio per giorno
GIORNI = 1000

rng = np.random.default_rng(20260816)

print(f"{'volatilita/giorno':>18s} {'media aritm.':>14s} {'composto':>12s} {'capitale finale':>16s}")
for vol in (0.005, 0.01, 0.02, 0.035, 0.05):
    r = rng.normal(MEDIA_GIORNALIERA, vol, GIORNI)
    curva = equity(r)
    composto = curva[-1] ** (1 / GIORNI) - 1
    print(f"{vol:18.3%} {r.mean():14.4%} {composto:12.4%} {curva[-1]:16.2f}x")

# %% [markdown]
# La colonna della media aritmetica resta ferma; quella del composto scende. È
# lo stesso rendimento medio che produce risultati diversi, e la differenza è
# **solo** la volatilità.

# %% [markdown]
# ## 4. La leva, che moltiplica il freno per il suo quadrato
#
# Con leva `k` il rendimento atteso si moltiplica per `k`, ma il freno per `k²`.
# Ecco perché esiste un punto oltre il quale aumentare la leva peggiora tutto —
# e su un asset già volatile quel punto arriva prestissimo.

# %%
df = carica("btcusdt").sort("data")
r_reali = rendimenti(df["chiusura"].to_numpy())


def curva_con_leva(rend: np.ndarray, k: float) -> np.ndarray:
    """Capitale con leva `k`, con l'azzeramento che e' definitivo.

    Un giorno in cui la posizione perde piu' del capitale non produce un numero
    negativo: produce la fine. Senza questo taglio il calcolo restituirebbe cali
    superiori al 100%, che non significano niente.
    """
    passi = np.maximum(1.0 + k * rend, 0.0)
    return np.concatenate([[1.0], np.cumprod(passi)])


print(f"{'leva':>5s} {'capitale finale':>16s} {'calo massimo':>14s} {'azzerato il':>14s}")
for k in (1, 2, 3, 5, 10):
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
