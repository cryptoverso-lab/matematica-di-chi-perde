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
# **Non Fidarti di Me**.*
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
from cvbook.regole import esegui, rottura

ALIQUOTA = 0.26        # ← l'aliquota che ti riguarda (0.33 sulle cripto dal 2026)
ANNI_RIPORTO = 4       # ← per quanti anni si possono riportare le perdite
CAPITALE = 100_000.0   # ← il capitale di partenza

# %% [markdown]
# ## 1. Non è l'aliquota, è il momento
#
# Due persone identiche, stesso rendimento, stessa aliquota. L'unica differenza:
# la prima realizza e paga ogni anno, la seconda lascia correre e paga alla fine.

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
    sx.plot(anni, differita, linewidth=2, label="imposta alla fine")
    sx.plot(anni, annuale, linewidth=2, linestyle="--", label="imposta ogni anno")
    sx.fill_between(anni, annuale, differita, alpha=0.2)
    sx.set_xlabel("Anni")
    sx.set_ylabel("Capitale netto (euro, da 1.000)")
    sx.legend()

    for r in (0.05, 0.10, 0.20):
        divario = [(confronto(r, int(a))[1] / confronto(r, int(a))[0] - 1) * 100
                   for a in anni[1:]]
        dx.plot(anni[1:], divario, linewidth=2, label=f"{r:.0%} lordo annuo")
    dx.set_xlabel("Orizzonte (anni)")
    dx.set_ylabel("Capitale in piu' differendo (%)")
    dx.legend()
    plt.show()

print(f"aliquota usata: {ALIQUOTA:.0%}\n")
print(f"{'orizzonte':>10s} " + "".join(f"{r:>16.0%} lordo" for r in (0.05, 0.10, 0.20)))
for a in (5, 10, 20, 30):
    valori = "".join(f"{confronto(r, a)[1] / confronto(r, a)[0] - 1:21.1%}"
                     for r in (0.05, 0.10, 0.20))
    print(f"{a:9d}a {valori}")

print("\nIl divario cresce con l'orizzonte e soprattutto con il RENDIMENTO. Chi "
      "ha rendimenti alti e orizzonti lunghi — cioe' esattamente la situazione "
      "che ogni strategia attiva promette — e' chi paga di piu' questo attrito.")

# %% [markdown]
# ## 2. Il guadagno tassabile non è il guadagno
#
# Anno per anno, con le perdite riportabili e la loro scadenza.

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
    ax.bar(x - 0.2, [r["lordo"] / 1000 for r in righe], width=0.4, label="risultato lordo")
    ax.bar(x + 0.2, [-r["imposta"] / 1000 for r in righe], width=0.4, label="imposta versata")
    ax.axhline(0, linewidth=1, color="black")
    ax.set_xticks(x)
    ax.set_xticklabels([str(r["anno"]) for r in righe], rotation=45)
    ax.set_ylabel(f"Migliaia di euro (da {CAPITALE / 1000:.0f}.000 iniziali)")
    ax.legend()
    plt.show()

print(f"{'anno':>6s} {'lordo':>14s} {'imponibile':>14s} {'imposta':>12s} {'capitale':>14s}")
for r in righe:
    print(f"{r['anno']:6d} {r['lordo']:14,.0f} {r['imponibile']:14,.0f} "
          f"{r['imposta']:12,.0f} {r['capitale']:14,.0f}")

print(f"\ncapitale finale pagando ogni anno:  {righe[-1]['capitale']:14,.0f}")
print(f"capitale finale pagando alla fine:  {differito:14,.0f}")
print(f"differenza:                         {differito / righe[-1]['capitale'] - 1:14.1%}")
print(f"\nimposte versate:                    {imposte:14,.0f}")
print(f"guadagno lordo complessivo:         {lordo_composto - CAPITALE:14,.0f}")
print(f"aliquota EFFETTIVA sul guadagno:    {imposte / (lordo_composto - CAPITALE):14.1%}")
print(f"perdite mai usate (scadute):        {mai_usate:14,.0f}")

print("\nNota il penultimo numero: l'aliquota effettiva puo' essere PIU' BASSA di "
      "quella nominale, e il danno al capitale finale essere comunque enorme. "
      "Perche' il danno non viene dall'aliquota. Viene dal momento.")

# %% [markdown]
# ## 3. L'esercizio più utile: mescola l'ordine
#
# Stessa sequenza di risultati annuali, ordine diverso. Il risultato lordo
# complessivo non cambia — la moltiplicazione è commutativa — ma l'imposta sì.

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
    ax.set_xlabel("Imposte versate (migliaia di euro)")
    ax.set_ylabel("Su 2.000 ordini diversi")
    plt.show()

print(f"imposte versate nell'ordine reale: {imposte:12,.0f}")
print(f"mescolando l'ordine — minimo:      {imposte_mescolate.min():12,.0f}")
print(f"                      mediana:     {np.median(imposte_mescolate):12,.0f}")
print(f"                      massimo:     {imposte_mescolate.max():12,.0f}")
print(f"\ncapitale finale: da {finali_mescolati.min():,.0f} a {finali_mescolati.max():,.0f}")
print("\nStesso guadagno lordo. Il fisco non tassa il tuo guadagno: tassa il modo "
      "in cui e' arrivato.")

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
