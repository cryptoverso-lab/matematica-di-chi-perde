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
# **La matematica di chi perde**.*
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
#
# ---
#
# > **EN** — *Calculator 5 — The risk of keeping it all in one place.*
# > Notebook for the chapter "Where your money really lives". Three numbers:
# > the probability of suffering at least one custody event within your
# > horizon, how much you'd need to earn to break even, and how the
# > distribution of final capital changes as the share held at the fullest
# > venue varies. **The annual probability you plug in here is your own
# > assumption, not a measurement** — there is no reliable statistic on
# > platform failures, for the same reason there is no complete list of dead
# > tokens: whatever disappears also stops showing up in the counts. This
# > notebook is for understanding the **shape** of the problem, not for
# > estimating its level.

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
from cvbook.metriche import recupero_necessario, rendimenti
from cvbook.simulazioni import bootstrap_traiettorie

# %% [markdown]
# ## 1. I tuoi tre numeri
#
# ---
#
# > **EN** — *1. Your three numbers.*

# %%
RISCHIO_ANNUO = 0.02   # ← la TUA ipotesi: probabilita' che la sede sparisca in un anno
ORIZZONTE = 10         # ← per quanti anni ci tieni i soldi
QUOTA = 0.60           # ← quanta parte del capitale sta nel posto piu' pieno

almeno_uno = 1 - (1 - RISCHIO_ANNUO) ** ORIZZONTE

print(t(f"ipotesi di rischio annuo: {RISCHIO_ANNUO:.1%}", f"assumed annual risk: {RISCHIO_ANNUO:.1%}"))
print(t(f"orizzonte:                {ORIZZONTE} anni", f"horizon:                  {ORIZZONTE} years"))
print(t(f"quota nel posto piu' pieno: {QUOTA:.0%}\n", f"share at the fullest venue: {QUOTA:.0%}\n"))
print(t(f"probabilita' di almeno un evento in {ORIZZONTE} anni: {almeno_uno:.1%}",
        f"probability of at least one event in {ORIZZONTE} years: {almeno_uno:.1%}"))
print(t(f"se accade, ti resta:                     {1 - QUOTA:.0%} del capitale",
        f"if it happens, you're left with:         {1 - QUOTA:.0%} of capital"))
print(t(f"per tornare in pari devi guadagnare:     +{recupero_necessario(QUOTA):.0%}",
        f"to break even you need to gain:          +{recupero_necessario(QUOTA):.0%}"))

# %% [markdown]
# ## 2. Una piccola probabilità, ripetuta, non resta piccola
#
# ---
#
# > **EN** — *2. A small probability, repeated, does not stay small.*

# %%
anni = np.arange(0, 26)

with avvio.figura("schermo"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=(12, 4.5))
    for p in (0.005, 0.01, 0.02, 0.05):
        sx.plot(anni, (1 - (1 - p) ** anni) * 100, linewidth=2,
                label=t(f"{p:.1%} l'anno", f"{p:.1%} a year"))
    sx.axvline(ORIZZONTE, linestyle=":", linewidth=1.2)
    sx.set_xlabel(t("Anni di permanenza", "Years held"))
    sx.set_ylabel(t("Probabilita' di almeno un evento (%)", "Probability of at least one event (%)"))
    sx.legend()

    quote = np.linspace(0.02, 0.95, 300)
    dx.plot(quote * 100, [recupero_necessario(q) * 100 for q in quote], linewidth=2)
    for q in (0.25, 0.50, 0.75):
        dx.plot([q * 100], [recupero_necessario(q) * 100], marker="o")
        dx.annotate(f"{q:.0%} → +{recupero_necessario(q):.0%}",
                    xy=(q * 100, recupero_necessario(q) * 100),
                    xytext=(-6, 8), textcoords="offset points", ha="right")
    dx.set_ylim(0, 500)
    dx.set_xlabel(t("Quota del capitale nella sede (%)", "Share of capital at the venue (%)"))
    dx.set_ylabel(t("Guadagno necessario per tornare in pari (%)", "Gain needed to break even (%)"))
    plt.show()

print(f"{t('rischio annuo', 'annual risk'):>14s} "
      + "".join(f"{a:>10d}" + t(" anni", " years") for a in (5, 10, 20)))
for p in (0.005, 0.01, 0.02, 0.05):
    print(f"{p:14.1%} " + "".join(f"{1 - (1 - p) ** a:14.1%}" for a in (5, 10, 20)))

# %% [markdown]
# ## 3. Dieci anni di mercato vero, con e senza il rischio di sede
#
# I rendimenti sono quelli realmente accaduti, ricampionati a blocchi. L'unica
# cosa aggiunta è l'evento raro. Le tre curve differiscono **solo** per quanta
# parte del capitale sta in una sede sola.
#
# ---
#
# > **EN** — *3. Ten years of real market, with and without custody risk.*
# > The returns are the ones that actually happened, block-resampled. The
# > only thing added is the rare event. The three curves differ **only** in
# > how much capital sits at a single venue.

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
        ax.plot(ordinati, probabilita, linewidth=2,
                label=t(f"{quota:.0%} in una sede", f"{quota:.0%} at one venue"))
    ax.axvline(1.0, linewidth=1.2, linestyle=":")
    ax.set_xscale("log")
    ax.set_xlabel(t(f"Capitale dopo {ORIZZONTE} anni (volte quello iniziale, scala log)",
                     f"Capital after {ORIZZONTE} years (× starting, log scale)"))
    ax.set_ylabel(t("Percorsi con esito peggiore o uguale (%)", "Paths with equal or worse outcome (%)"))
    ax.legend()
    plt.show()

print(t(f"probabilita' di almeno un evento nei {ORIZZONTE} anni: {colpito.mean():.1%}\n",
        f"probability of at least one event in {ORIZZONTE} years: {colpito.mean():.1%}\n"))
print(f"{t('quota in una sede', 'share at one venue'):>18s} {t('mediana', 'median'):>10s} "
      f"{t('5% peggiore', 'worst 5%'):>13s} {t('sotto il capitale', 'below capital'):>19s}")
for quota in QUOTE:
    finali = np.where(colpito, mercato * (1 - quota), mercato)
    print(f"{quota:18.0%} {np.median(finali):9.2f}x {np.percentile(finali, 5):12.2f}x "
          f"{float((finali < 1).mean()):19.1%}")

print(t("\nLa mediana si sposta poco: nel caso tipico non succede niente, ed e' per "
        "questo che il problema non si vede. Cambia la coda sinistra, cioe' "
        "esattamente la parte che decide se sei ancora nel gioco.",
        "\nThe median barely moves: in the typical case nothing happens, and "
        "that's exactly why the problem is invisible. What changes is the left "
        "tail — exactly the part that decides whether you're still in the "
        "game."))

# %% [markdown]
# ## 4. L'esercizio che consiglio
#
# Fallo due volte: la prima con la tua situazione **attuale**, così com'è; la
# seconda con la quota che avresti *deciso* di avere se ci avessi pensato. La
# differenza fra i due numeri è il costo di non aver mai preso quella decisione.
#
# ---
#
# > **EN** — *4. The exercise I recommend.* Do it twice: first with your
# > **current** situation, as it is; then with the share you would have
# > *decided* to hold, had you thought about it. The gap between the two
# > numbers is the cost of never having made that decision.

# %%
QUOTA_ATTUALE = 0.85    # ← quanto hai davvero nel posto piu' pieno, oggi
QUOTA_DECISA = 0.20     # ← il limite che vorresti darti


def coda(quota: float) -> tuple[float, float]:
    finali = np.where(colpito, mercato * (1 - quota), mercato)
    return float(np.percentile(finali, 5)), float((finali < 1).mean())


for nome, quota in (
    (t("cosi' com'e' oggi", "as it is today"), QUOTA_ATTUALE),
    (t("con il limite", "with the limit"), QUOTA_DECISA),
):
    peggiore, sotto = coda(quota)
    print(t(f"{nome:>20s} (quota {quota:.0%}): 5% peggiore {peggiore:6.2f}x   "
            f"percorsi sotto il capitale {sotto:.1%}",
            f"{nome:>20s} (share {quota:.0%}): worst 5% {peggiore:6.2f}x   "
            f"paths below capital {sotto:.1%}"))

print(t("\nDistribuire su piu' sedi NON riduce a zero il rischio: lo trasforma da un "
        "interruttore in una perdita parziale, e in cambio aggiunge piu' cose da "
        "gestire, piu' credenziali, piu' punti in cui sbagliare. E' un compromesso, "
        "non una soluzione.",
        "\nSpreading across several venues does NOT reduce risk to zero: it turns "
        "it from an on/off switch into a partial loss, and in exchange adds more "
        "things to manage, more credentials, more points of failure. It's a "
        "trade-off, not a solution."))

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
#
# ---
#
# > **EN** — *The four questions no calculation replaces.*
# > 1. **Whose key is it?** If the credentials that move the funds are only
# >    yours, the risk is yours and reducible with procedures under your
# >    control. If they belong to someone else, you're running that someone
# >    else's risk.
# > 2. **What happens if that venue shuts down tomorrow morning?** Not what
# >    it *says* would happen — what actually, materially happens.
# > 3. **How much do I have there, as a percentage?** As a percentage, not in
# >    absolute value: absolute value grows on its own with the market, and
# >    that's how almost everyone ends up concentrated without having decided
# >    to.
# > 4. **Who else can move these assets?** Authorizations granted years ago
# >    and never revoked, decommissioned devices, copies of credentials left
# >    in places that seemed convenient at the time.
