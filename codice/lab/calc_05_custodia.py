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
# # Calcolatore 5 — Il rischio di stare in un posto solo
#
# *Quaderno del capitolo «Dove stanno davvero i tuoi soldi» di
# **Non Fidarti di Me**.*
#
# Tre numeri: la probabilità di subire almeno un evento di custodia nel tuo
# orizzonte, quanto servirebbe guadagnare per tornare in pari, e come cambia la
# distribuzione del capitale finale al variare della quota che tieni nel posto
# più pieno.
#
# **La probabilità annua che metti qui dentro è un'ipotesi tua, non una misura.**
# Non esiste una statistica affidabile dei fallimenti di piattaforma, per la
# stessa ragione per cui non esiste un elenco completo dei token morti: chi
# sparisce smette anche di comparire nei conteggi. Questo quaderno serve a capire
# la **forma** del problema, non a stimarne il livello.

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
from cvbook.metriche import recupero_necessario, rendimenti
from cvbook.simulazioni import bootstrap_traiettorie

# %% [markdown]
# ## 1. I tuoi tre numeri

# %%
RISCHIO_ANNUO = 0.02   # ← la TUA ipotesi: probabilita' che la sede sparisca in un anno
ORIZZONTE = 10         # ← per quanti anni ci tieni i soldi
QUOTA = 0.60           # ← quanta parte del capitale sta nel posto piu' pieno

almeno_uno = 1 - (1 - RISCHIO_ANNUO) ** ORIZZONTE

print(f"ipotesi di rischio annuo: {RISCHIO_ANNUO:.1%}")
print(f"orizzonte:                {ORIZZONTE} anni")
print(f"quota nel posto piu' pieno: {QUOTA:.0%}\n")
print(f"probabilita' di almeno un evento in {ORIZZONTE} anni: {almeno_uno:.1%}")
print(f"se accade, ti resta:                     {1 - QUOTA:.0%} del capitale")
print(f"per tornare in pari devi guadagnare:     +{recupero_necessario(QUOTA):.0%}")

# %% [markdown]
# ## 2. Una piccola probabilità, ripetuta, non resta piccola

# %%
anni = np.arange(0, 26)

with avvio.figura("schermo"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=(12, 4.5))
    for p in (0.005, 0.01, 0.02, 0.05):
        sx.plot(anni, (1 - (1 - p) ** anni) * 100, linewidth=2, label=f"{p:.1%} l'anno")
    sx.axvline(ORIZZONTE, linestyle=":", linewidth=1.2)
    sx.set_xlabel("Anni di permanenza")
    sx.set_ylabel("Probabilita' di almeno un evento (%)")
    sx.legend()

    quote = np.linspace(0.02, 0.95, 300)
    dx.plot(quote * 100, [recupero_necessario(q) * 100 for q in quote], linewidth=2)
    for q in (0.25, 0.50, 0.75):
        dx.plot([q * 100], [recupero_necessario(q) * 100], marker="o")
        dx.annotate(f"{q:.0%} → +{recupero_necessario(q):.0%}",
                    xy=(q * 100, recupero_necessario(q) * 100),
                    xytext=(-6, 8), textcoords="offset points", ha="right")
    dx.set_ylim(0, 500)
    dx.set_xlabel("Quota del capitale nella sede (%)")
    dx.set_ylabel("Guadagno necessario per tornare in pari (%)")
    plt.show()

print(f"{'rischio annuo':>14s} " + "".join(f"{a:>10d} anni" for a in (5, 10, 20)))
for p in (0.005, 0.01, 0.02, 0.05):
    print(f"{p:14.1%} " + "".join(f"{1 - (1 - p) ** a:14.1%}" for a in (5, 10, 20)))

# %% [markdown]
# ## 3. Dieci anni di mercato vero, con e senza il rischio di sede
#
# I rendimenti sono quelli realmente accaduti, ricampionati a blocchi. L'unica
# cosa aggiunta è l'evento raro. Le tre curve differiscono **solo** per quanta
# parte del capitale sta in una sede sola.

# %%
PERCORSI = 5000
QUOTE = [1.00, 0.50, 0.20]

r = rendimenti(carica("btcusdt").sort("data")["chiusura"].to_numpy())
rng = np.random.default_rng(seed_for("calc-custodia"))
giorni = min(365 * ORIZZONTE, len(r))
mercato = bootstrap_traiettorie(r[:giorni], n_traiettorie=PERCORSI, rng=rng,
                                a_blocchi=20)[:, -1]
colpito = (rng.random((PERCORSI, ORIZZONTE)) < RISCHIO_ANNUO).any(axis=1)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    for quota in QUOTE:
        finali = np.maximum(np.where(colpito, mercato * (1 - quota), mercato), 1e-4)
        ordinati = np.sort(finali)
        probabilita = np.arange(1, len(ordinati) + 1) / len(ordinati) * 100
        ax.plot(ordinati, probabilita, linewidth=2, label=f"{quota:.0%} in una sede")
    ax.axvline(1.0, linewidth=1.2, linestyle=":")
    ax.set_xscale("log")
    ax.set_xlabel(f"Capitale dopo {ORIZZONTE} anni (volte quello iniziale, scala log)")
    ax.set_ylabel("Percorsi con esito peggiore o uguale (%)")
    ax.legend()
    plt.show()

print(f"probabilita' di almeno un evento nei {ORIZZONTE} anni: {colpito.mean():.1%}\n")
print(f"{'quota in una sede':>18s} {'mediana':>10s} {'5% peggiore':>13s} "
      f"{'sotto il capitale':>19s}")
for quota in QUOTE:
    finali = np.where(colpito, mercato * (1 - quota), mercato)
    print(f"{quota:18.0%} {np.median(finali):9.2f}x {np.percentile(finali, 5):12.2f}x "
          f"{float((finali < 1).mean()):19.1%}")

print("\nLa mediana si sposta poco: nel caso tipico non succede niente, ed e' per "
      "questo che il problema non si vede. Cambia la coda sinistra, cioe' "
      "esattamente la parte che decide se sei ancora nel gioco.")

# %% [markdown]
# ## 4. L'esercizio che consiglio
#
# Fallo due volte: la prima con la tua situazione **attuale**, così com'è; la
# seconda con la quota che avresti *deciso* di avere se ci avessi pensato. La
# differenza fra i due numeri è il costo di non aver mai preso quella decisione.

# %%
QUOTA_ATTUALE = 0.85    # ← quanto hai davvero nel posto piu' pieno, oggi
QUOTA_DECISA = 0.20     # ← il limite che vorresti darti


def coda(quota: float) -> tuple[float, float]:
    finali = np.where(colpito, mercato * (1 - quota), mercato)
    return float(np.percentile(finali, 5)), float((finali < 1).mean())


for nome, quota in (("cosi' com'e' oggi", QUOTA_ATTUALE), ("con il limite", QUOTA_DECISA)):
    peggiore, sotto = coda(quota)
    print(f"{nome:>20s} (quota {quota:.0%}): 5% peggiore {peggiore:6.2f}x   "
          f"percorsi sotto il capitale {sotto:.1%}")

print("\nDistribuire su piu' sedi NON riduce a zero il rischio: lo trasforma da un "
      "interruttore in una perdita parziale, e in cambio aggiunge piu' cose da "
      "gestire, piu' credenziali, piu' punti in cui sbagliare. E' un compromesso, "
      "non una soluzione.")

# %% [markdown]
# ### Le quattro domande, che nessun calcolo sostituisce
#
# 1. **Di chi è la chiave?** Se le credenziali che muovono i fondi sono solo tue,
#    il rischio è tuo e riducibile con procedure che dipendono da te. Se sono di
#    qualcun altro, stai correndo il rischio di quel qualcuno.
# 2. **Cosa succede se quella sede chiude domani mattina?** Non cosa *dice* che
#    succederebbe: cosa succede materialmente.
# 3. **Quanto ne ho lì, in percentuale?** In percentuale, non in valore assoluto:
#    il valore assoluto cresce da solo con il mercato, ed è così che quasi tutti
#    finiscono concentrati senza averlo deciso.
# 4. **Chi altro può muovere queste cose?** Autorizzazioni concesse anni fa e mai
#    revocate, dispositivi dismessi, copie delle credenziali in posti che al
#    momento sembravano comodi.
