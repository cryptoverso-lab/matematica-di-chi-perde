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
# # Calcolatore 6 — L'attrito fiscale
#
# *Quaderno del capitolo «L'attrito che nessun backtest include» di
# **La matematica di chi perde**.*
#
# Tre numeri sui tuoi risultati annuali: il capitale finale pagando ogni anno,
# quello pagando alla fine, e le perdite che scadono senza essere state usate.
#
# **Questo quaderno non è consulenza fiscale.** L'aliquota e gli anni di riporto
# sono due caselle da riempire: mettici quelle che ti riguardano, verificate alla
# fonte. Il meccanismo che il quaderno mostra — l'imposta versata presto smette
# di comporre — non dipende da quei numeri.
#
# Per orientarti, il quadro italiano verificato ad agosto 2026 — da ricontrollare,
# perché cambia:
#
# | Su che cosa | Aliquota |
# |---|---|
# | Azioni, obbligazioni societarie, ETF, fondi, derivati | 26% |
# | Titoli di Stato italiani e di Paesi in white list | 12,5% |
# | Investimenti in un PIR mantenuti almeno 5 anni | 0% |
# | Cripto-attività, plusvalenze realizzate dal 1° gennaio 2026 | 33% |
#
# Attenzione all'asimmetria degli ETF armonizzati: i guadagni sono redditi di
# capitale, le perdite redditi diversi, e le due categorie non si compensano
# fra loro.
#
# ---
#
# > **EN** — *Calculator 6 — Tax friction.* Notebook for the chapter "The
# > friction no backtest includes". Three numbers on your annual results:
# > final capital paying every year, paying at the end, and losses that
# > expire unused. **This notebook is not tax advice.** The tax rate and the
# > carry-forward years are two fields to fill in with the ones that apply to
# > you, verified at the source — the mechanism the notebook shows (tax paid
# > early stops compounding) doesn't depend on those numbers. For reference,
# > the Italian framework verified in August 2026 (recheck it, it changes):
# > shares/bonds/ETFs/funds/derivatives 26%, Italian and white-list government
# > bonds 12.5%, PIR investments held ≥5 years 0%, crypto-assets (gains
# > realized from January 1, 2026) 33%. Watch the asymmetry of UCITS ETFs:
# > gains are capital income, losses are "other income", and the two
# > categories don't offset each other.

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
from cvbook.regole import esegui, rottura

ALIQUOTA = 0.26        # ← l'aliquota che ti riguarda (0.33 sulle cripto dal 2026)
ANNI_RIPORTO = 4       # ← per quanti anni si possono riportare le perdite
CAPITALE = 100_000.0   # ← il capitale di partenza

# %% [markdown]
# ## 1. Non è l'aliquota, è il momento
#
# Due persone identiche, stesso rendimento, stessa aliquota. L'unica differenza:
# la prima realizza e paga ogni anno, la seconda lascia correre e paga alla fine.
#
# ---
#
# > **EN** — *1. It's not the rate, it's the timing.* Two identical people,
# > same return, same tax rate. The only difference: the first realizes and
# > pays every year, the second lets it run and pays at the end.

# %%
def confronto(rendimento: float, anni: int, aliquota: float = ALIQUOTA):
    annuale = (1 + rendimento * (1 - aliquota)) ** anni
    lordo = (1 + rendimento) ** anni
    differita = 1 + (lordo - 1) * (1 - aliquota)
    return annuale, differita


anni = np.arange(0, 31)
annuale = np.array([confronto(0.10, int(a))[0] for a in anni]) * 1000
differita = np.array([confronto(0.10, int(a))[1] for a in anni]) * 1000

with avvio.figura("schermo"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=(12, 4.5))
    sx.plot(anni, differita, linewidth=2, label=t("imposta alla fine", "tax at the end"))
    sx.plot(anni, annuale, linewidth=2, linestyle="--", label=t("imposta ogni anno", "tax every year"))
    sx.fill_between(anni, annuale, differita, alpha=0.2)
    sx.set_xlabel(t("Anni", "Years"))
    sx.set_ylabel(t("Capitale netto (euro, da 1.000)", "Net capital (euros, starting from 1,000)"))
    sx.legend()

    for r in (0.05, 0.10, 0.20):
        divario = [(confronto(r, int(a))[1] / confronto(r, int(a))[0] - 1) * 100
                   for a in anni[1:]]
        dx.plot(anni[1:], divario, linewidth=2, label=t(f"{r:.0%} lordo annuo", f"{r:.0%} gross a year"))
    dx.set_xlabel(t("Orizzonte (anni)", "Horizon (years)"))
    dx.set_ylabel(t("Capitale in piu' differendo (%)", "Extra capital by deferring (%)"))
    dx.legend()
    plt.show()

print(t(f"aliquota usata: {ALIQUOTA:.0%}\n", f"tax rate used: {ALIQUOTA:.0%}\n"))
print(f"{t('orizzonte', 'horizon'):>10s} " + "".join(
    f"{r:>16.0%}" + t(" lordo", " gross") for r in (0.05, 0.10, 0.20)))
for a in (5, 10, 20, 30):
    valori = "".join(f"{confronto(r, a)[1] / confronto(r, a)[0] - 1:21.1%}"
                     for r in (0.05, 0.10, 0.20))
    print(f"{a:9d}" + t("a", "y") + f" {valori}")

print(t("\nIl divario cresce con l'orizzonte e soprattutto con il RENDIMENTO. Chi "
        "ha rendimenti alti e orizzonti lunghi — cioe' esattamente la situazione "
        "che ogni strategia attiva promette — e' chi paga di piu' questo attrito.",
        "\nThe gap grows with the horizon and above all with the RETURN. Whoever "
        "has high returns and long horizons — exactly the situation every active "
        "strategy promises — pays the most for this friction."))

# %% [markdown]
# ## 2. Il guadagno tassabile non è il guadagno
#
# Anno per anno, con le perdite riportabili e la loro scadenza.
#
# ---
#
# > **EN** — *2. Taxable gain is not gain.* Year by year, with carry-forward
# > losses and their expiry.

# %%
def simula_imposta(rendimenti_annui, capitale=CAPITALE, aliquota=ALIQUOTA,
                   anni_riporto=ANNI_RIPORTO):
    """Imposta anno per anno, con riporto delle perdite e loro scadenza."""
    crediti: list[list[float]] = []
    righe, imposte_totali = [], 0.0

    for anno, r in rendimenti_annui:
        lordo = capitale * r
        if lordo >= 0:
            usato = 0.0
            for c in crediti:
                if anno - c[0] <= anni_riporto:
                    quota = min(c[1], lordo - usato)
                    c[1] -= quota
                    usato += quota
                    if usato >= lordo:
                        break
            imponibile = max(lordo - usato, 0.0)
            imposta = imponibile * aliquota
        else:
            crediti.append([anno, -lordo])
            imponibile, imposta = 0.0, 0.0

        crediti = [c for c in crediti if c[1] > 1e-9 and anno - c[0] < anni_riporto]
        imposte_totali += imposta
        capitale += lordo - imposta
        righe.append({"anno": anno, "lordo": lordo, "imponibile": imponibile,
                      "imposta": imposta, "capitale": capitale})

    return righe, imposte_totali, sum(c[1] for c in crediti)


# I risultati annuali di una regola meccanica su Bitcoin. Sostituiscili con i TUOI.
# Annual results of a mechanical rule on Bitcoin. Replace them with YOUR OWN.
df = carica("btcusdt").sort("data")
prezzi = df["chiusura"].to_numpy()
anni_serie = np.array([d.year for d in df["data"].to_list()])
curva = esegui(prezzi, rottura(prezzi, 20))["curva"]

RENDIMENTI_ANNUI = []
for a in sorted(set(anni_serie.tolist())):
    indici = np.where(anni_serie == a)[0]
    RENDIMENTI_ANNUI.append((int(a), float(curva[indici[-1]] / curva[indici[0]] - 1.0)))

righe, imposte, mai_usate = simula_imposta(RENDIMENTI_ANNUI)

lordo_composto = CAPITALE
for _, r in RENDIMENTI_ANNUI:
    lordo_composto *= 1 + r
differito = CAPITALE + (lordo_composto - CAPITALE) * (1 - ALIQUOTA)

with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(righe))
    ax.bar(x - 0.2, [r["lordo"] / 1000 for r in righe], width=0.4,
           label=t("risultato lordo", "gross result"))
    ax.bar(x + 0.2, [-r["imposta"] / 1000 for r in righe], width=0.4,
           label=t("imposta versata", "tax paid"))
    ax.axhline(0, linewidth=1, color="black")
    ax.set_xticks(x)
    ax.set_xticklabels([str(r["anno"]) for r in righe], rotation=45)
    ax.set_ylabel(t(f"Migliaia di euro (da {CAPITALE / 1000:.0f}.000 iniziali)",
                     f"Thousands of euros (starting from {CAPITALE / 1000:.0f},000)"))
    ax.legend()
    plt.show()

print(f"{t('anno', 'year'):>6s} {t('lordo', 'gross'):>14s} {t('imponibile', 'taxable'):>14s} "
      f"{t('imposta', 'tax'):>12s} {t('capitale', 'capital'):>14s}")
for r in righe:
    print(f"{r['anno']:6d} {r['lordo']:14,.0f} {r['imponibile']:14,.0f} "
          f"{r['imposta']:12,.0f} {r['capitale']:14,.0f}")

print(t(f"\ncapitale finale pagando ogni anno:  {righe[-1]['capitale']:14,.0f}",
        f"\nfinal capital paying every year:    {righe[-1]['capitale']:14,.0f}"))
print(t(f"capitale finale pagando alla fine:  {differito:14,.0f}",
        f"final capital paying at the end:    {differito:14,.0f}"))
print(t(f"differenza:                         {differito / righe[-1]['capitale'] - 1:14.1%}",
        f"difference:                         {differito / righe[-1]['capitale'] - 1:14.1%}"))
print(t(f"\nimposte versate:                    {imposte:14,.0f}",
        f"\ntax paid:                           {imposte:14,.0f}"))
print(t(f"guadagno lordo complessivo:         {lordo_composto - CAPITALE:14,.0f}",
        f"total gross gain:                   {lordo_composto - CAPITALE:14,.0f}"))
print(t(f"aliquota EFFETTIVA sul guadagno:    {imposte / (lordo_composto - CAPITALE):14.1%}",
        f"EFFECTIVE rate on the gain:         {imposte / (lordo_composto - CAPITALE):14.1%}"))
print(t(f"perdite mai usate (scadute):        {mai_usate:14,.0f}",
        f"losses never used (expired):        {mai_usate:14,.0f}"))

print(t("\nNota il penultimo numero: l'aliquota effettiva puo' essere PIU' BASSA di "
        "quella nominale, e il danno al capitale finale essere comunque enorme. "
        "Perche' il danno non viene dall'aliquota. Viene dal momento.",
        "\nNote the second-to-last number: the effective rate can be LOWER than "
        "the nominal one, and the damage to final capital still be enormous. "
        "Because the damage doesn't come from the rate. It comes from the "
        "timing."))

# %% [markdown]
# ## 3. L'esercizio più utile: mescola l'ordine
#
# Stessa sequenza di risultati annuali, ordine diverso. Il risultato lordo
# complessivo non cambia — la moltiplicazione è commutativa — ma l'imposta sì.
#
# ---
#
# > **EN** — *3. The most useful exercise: shuffle the order.* Same sequence
# > of annual results, different order. The overall gross result doesn't
# > change — multiplication is commutative — but the tax does.

# %%
rng = np.random.default_rng(20260816)
valori = [r for _, r in RENDIMENTI_ANNUI]
anni_etichette = [a for a, _ in RENDIMENTI_ANNUI]

imposte_mescolate, finali_mescolati = [], []
for _ in range(2000):
    ordine = rng.permutation(len(valori))
    sequenza = [(anni_etichette[k], valori[ordine[k]]) for k in range(len(valori))]
    rr, ii, _ = simula_imposta(sequenza)
    imposte_mescolate.append(ii)
    finali_mescolati.append(rr[-1]["capitale"])

imposte_mescolate = np.array(imposte_mescolate)
finali_mescolati = np.array(finali_mescolati)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.hist(imposte_mescolate / 1000, bins=60)
    ax.axvline(imposte / 1000, linewidth=2.5, color="black")
    ax.set_xlabel(t("Imposte versate (migliaia di euro)", "Tax paid (thousands of euros)"))
    ax.set_ylabel(t("Su 2.000 ordini diversi", "Out of 2,000 different orderings"))
    plt.show()

print(t(f"imposte versate nell'ordine reale: {imposte:12,.0f}",
        f"tax paid in the real order:        {imposte:12,.0f}"))
print(t(f"mescolando l'ordine — minimo:      {imposte_mescolate.min():12,.0f}",
        f"shuffling the order — minimum:     {imposte_mescolate.min():12,.0f}"))
print(t(f"                      mediana:     {np.median(imposte_mescolate):12,.0f}",
        f"                      median:      {np.median(imposte_mescolate):12,.0f}"))
print(t(f"                      massimo:     {imposte_mescolate.max():12,.0f}",
        f"                      maximum:     {imposte_mescolate.max():12,.0f}"))
print(t(f"\ncapitale finale: da {finali_mescolati.min():,.0f} a {finali_mescolati.max():,.0f}",
        f"\nfinal capital: from {finali_mescolati.min():,.0f} to {finali_mescolati.max():,.0f}"))
print(t("\nStesso guadagno lordo. Il fisco non tassa il tuo guadagno: tassa il modo "
        "in cui e' arrivato.",
        "\nSame gross gain. The taxman doesn't tax your gain: it taxes how it "
        "arrived."))

# %% [markdown]
# ### Esercizi
#
# 1. Sostituisci `RENDIMENTI_ANNUI` con i **tuoi** risultati annuali — bastano
#    coppie `(anno, rendimento)`. È il conto che nessun software di backtest fa.
# 2. Cambia `ALIQUOTA` e `ANNI_RIPORTO` con quelli in vigore quando leggi. Le
#    conclusioni cambiano di grado, non di segno.
# 3. Metti `ANNI_RIPORTO = 0` — cioè nessun riporto — e guarda quanto peggiora il
#    caso di una strategia molto oscillante. È il costo fiscale della volatilità
#    del **risultato annuale**, che è una cosa diversa dalla volatilità del
#    mercato e non compare in nessuna metrica standard.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. Replace `RENDIMENTI_ANNUI` with **your own** annual results — pairs of
# >    `(year, return)` suffice. It's the calculation no backtesting software
# >    does.
# > 2. Change `ALIQUOTA` and `ANNI_RIPORTO` to whatever is in force when you
# >    read this. The conclusions change in degree, not in sign.
# > 3. Set `ANNI_RIPORTO = 0` — i.e. no carry-forward — and see how much worse
# >    it gets for a highly oscillating strategy. It's the tax cost of the
# >    volatility of the **annual result**, which is a different thing from
# >    market volatility and doesn't appear in any standard metric.
