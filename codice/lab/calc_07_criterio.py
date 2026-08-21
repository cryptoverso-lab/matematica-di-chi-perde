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
# # Calcolatore 7 — Il Criterio, eseguibile
#
# *Quaderno del capitolo «Il Criterio» di **La matematica di chi perde**.*
#
# Una lista di controllo che gira. Inserisci quello che sai di una proposta —
# periodo, numero di operazioni, percentuale di vincite, costi dichiarati — e ti
# restituisce due cose: **le domande che restano senza risposta**, e **quale
# percentuale di tentativi casuali avrebbe prodotto un risultato altrettanto
# buono**.
#
# È la versione automatica del capitolo, e sta in una pagina.
#
# ---
#
# > **EN** — *Calculator 7 — The Criterion, executable.* Notebook for the
# > chapter "The Criterion". A checklist that actually runs. Enter what you
# > know about a proposal — period, number of trades, win rate, stated costs —
# > and it gives back two things: **the questions left unanswered**, and
# > **what percentage of random attempts would have produced an equally good
# > result**. It's the automatic version of the chapter, and it fits on one
# > page.

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

avvio.prepara([])

# %%
from math import ceil, erf, sqrt

import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for
from cvbook.lingua import t

# %% [markdown]
# ## 1. Cosa sai della proposta
#
# Compila quello che sai. Lascia `None` dove **non ti è stato detto**: è proprio
# quello il dato più informativo del quaderno.
#
# ---
#
# > **EN** — *1. What you know about the proposal.* Fill in what you know.
# > Leave `None` where **you weren't told**: that's exactly the most
# > informative data point in this notebook.

# %%
# PROVA / TRY: l'intero dizionario qui sotto è da riscrivere con la proposta
# che vuoi valutare — è il punto del quaderno, non un'eccezione alla regola.
PROPOSTA = {
    # 1. I dati
    "fonte_dichiarata": None,        # es. "Binance, dump giornalieri" oppure None
    "data_di_estrazione": None,      # es. "2026-03-01" oppure None
    "periodo_dal": "2015-01-01",     # oppure None
    "periodo_al": "2026-01-01",      # oppure None
    # 2. Il metodo
    "regole_descritte": True,        # si potrebbe ricostruire la procedura?
    "soglie_dichiarate": True,
    "costi_dichiarati": 0.0005,      # frazione per operazione, oppure None
    # 3. I limiti
    "peggior_periodo_dichiarato": True,
    "durata_peggior_periodo": True,
    # 4. I fallimenti
    "varianti_provate_dichiarate": None,   # quante ne ha provate? None = non lo dice
    "operazioni_in_perdita_mostrate": False,
    # 5. La forza dell'evidenza
    "numero_operazioni": 400,
    "quota_vincenti": 0.58,
    "risultato_finale": 6.0,         # capitale finale, in volte
    "durata_anni": 11,
    # e la domanda che non e' nelle cinque
    "come_guadagna": "vendita di un corso",
}

# %% [markdown]
# ## 2. Le cinque domande, contate
#
# ---
#
# > **EN** — *2. The five questions, counted.*

# %%
def valuta(p: dict) -> tuple[float, list[str]]:
    punteggio, mancanti = 0.0, []

    # 1. I dati
    dati = [p["fonte_dichiarata"], p["data_di_estrazione"], p["periodo_dal"], p["periodo_al"]]
    presenti = sum(x is not None for x in dati)
    punteggio += presenti / len(dati)
    if presenti < len(dati):
        mancanti.append(t("1. i dati: manca ", "1. the data: missing ") + ", ".join(
            n for n, x in zip(
                t(("la fonte", "la data di estrazione", "l'inizio del periodo", "la fine del periodo"),
                  ("the source", "the extraction date", "the start of the period", "the end of the period")),
                dati) if x is None))

    # 2. Il metodo
    metodo = [p["regole_descritte"], p["soglie_dichiarate"], p["costi_dichiarati"] is not None]
    punteggio += sum(bool(x) for x in metodo) / len(metodo)
    if not all(metodo):
        mancanti.append(t("2. il metodo: non si potrebbe rieseguire cosi' com'e' descritto",
                           "2. the method: it couldn't be rerun as described"))

    # 3. I limiti
    limiti = [p["peggior_periodo_dichiarato"], p["durata_peggior_periodo"]]
    punteggio += sum(bool(x) for x in limiti) / len(limiti)
    if not all(limiti):
        mancanti.append(t("3. i limiti: non dice dove smette di funzionare",
                           "3. the limits: it doesn't say where it stops working"))

    # 4. I fallimenti
    fallimenti = [p["varianti_provate_dichiarate"] is not None,
                  bool(p["operazioni_in_perdita_mostrate"])]
    punteggio += sum(fallimenti) / len(fallimenti)
    if not all(fallimenti):
        mancanti.append(t("4. i fallimenti: non si sa quante idee sono state scartate",
                           "4. the failures: unknown how many ideas were discarded"))

    # 5. La forza dell'evidenza
    evidenza = [p["numero_operazioni"] is not None, p.get("confronto_col_caso", False)]
    punteggio += sum(bool(x) for x in evidenza) / len(evidenza)
    if not evidenza[1]:
        mancanti.append(t("5. l'evidenza: nessun confronto con il caso",
                           "5. the evidence: no comparison against chance"))

    return punteggio, mancanti


punteggio, mancanti = valuta(PROPOSTA)
print(t(f"punteggio: {punteggio:.1f} su 5\n", f"score: {punteggio:.1f} out of 5\n"))
for m in mancanti:
    print(t("  senza risposta → ", "  unanswered → ") + m)

if punteggio < 3:
    print(t("\nSotto le tre risposte su cinque non stai guardando conoscenza: "
            "stai guardando un'inserzione.",
            "\nBelow three answers out of five you're not looking at knowledge: "
            "you're looking at an advertisement."))
elif punteggio < 4.5:
    print(t("\nProbabilmente in buona fede, ma non ha verificato quanto crede.",
            "\nProbably in good faith, but hasn't verified as much as it believes."))
else:
    print(t("\nHa fatto il lavoro. Adesso puoi cominciare a valutare il merito.",
            "\nIt did the work. Now you can start evaluating the merit."))

print(t(f"\nE la domanda che non e' fra le cinque: come guadagna? "
        f"→ {PROPOSTA['come_guadagna']}",
        f"\nAnd the question that isn't among the five: how does it make money? "
        f"→ {PROPOSTA['come_guadagna']}"))

# %% [markdown]
# ## 3. Quale percentuale di tentativi casuali avrebbe fatto altrettanto
#
# La domanda decisiva, e quella che quasi nessuno pone.
#
# ---
#
# > **EN** — *3. What percentage of random attempts would have done as well.*
# > The decisive question, and the one almost nobody asks.

# %%
N_PROVE = 20_000  # PROVA / TRY: 2000 (veloce) · 20000 · 100000 (coda più precisa)
rng = np.random.default_rng(seed_for("calc-criterio"))
# NON TOCCARE / DO NOT CHANGE: il seme fissa l'istogramma e la percentuale
# citati nel testo; con N_PROVE già a 20.000 il seme conta pochissimo, ma la
# regola resta la stessa di tutto il libro: non si cambia dopo aver visto il numero.

n = PROPOSTA["numero_operazioni"]
vinte = int(round(PROPOSTA["quota_vincenti"] * n))
esiti = rng.binomial(n, 0.5, N_PROVE)
quota_caso = float((esiti >= vinte).mean())

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.hist(esiti / n * 100, bins=50)
    ax.axvline(PROPOSTA["quota_vincenti"] * 100, linewidth=2.5, color="black")
    ax.set_xlabel(t("Quota di operazioni vincenti (%)", "Share of winning trades (%)"))
    ax.set_ylabel(t(f"Su {N_PROVE:,} sequenze prive di vantaggio",
                     f"Out of {N_PROVE:,} sequences with no edge"))
    plt.show()

print(t(f"dichiarate {vinte} vittorie su {n} operazioni ({PROPOSTA['quota_vincenti']:.0%})",
        f"claimed {vinte} wins out of {n} trades ({PROPOSTA['quota_vincenti']:.0%})"))
print(t(f"con una moneta equa capita nel {quota_caso:.2%} dei casi",
        f"with a fair coin this happens in {quota_caso:.2%} of cases"))
if PROPOSTA["varianti_provate_dichiarate"]:
    tentativi = PROPOSTA["varianti_provate_dichiarate"]
    print(t(f"con {tentativi} varianti provate, almeno una ci arriva nel "
            f"{1 - (1 - quota_caso) ** tentativi:.1%} dei casi",
            f"with {tentativi} variants tried, at least one gets there in "
            f"{1 - (1 - quota_caso) ** tentativi:.1%} of cases"))
else:
    print(t("\nNon sappiamo quante varianti siano state provate. Assumi che siano "
            "state parecchie: e' l'ipotesi realistica.",
            "\nWe don't know how many variants were tried. Assume there were "
            "quite a few: it's the realistic assumption."))
    for tentativi in (5, 20, 100):
        print(t(f"  con {tentativi:3d} varianti: almeno una ci arriva nel "
                f"{1 - (1 - quota_caso) ** tentativi:5.1%} dei casi",
                f"  with {tentativi:3d} variants: at least one gets there in "
                f"{1 - (1 - quota_caso) ** tentativi:5.1%} of cases"))

# %% [markdown]
# ## 4. Il campione basta?
#
# ---
#
# > **EN** — *4. Is the sample big enough?*

# %%
def quantile_normale(p: float) -> float:
    basso, alto = -10.0, 10.0
    for _ in range(200):
        mezzo = (basso + alto) / 2
        if 0.5 * (1 + erf(mezzo / sqrt(2))) < p:
            basso = mezzo
        else:
            alto = mezzo
    return (basso + alto) / 2


vantaggio_implicito = (PROPOSTA["risultato_finale"] ** (1 / n)) - 1
oscillazione = 0.03   # ipotesi prudente sull'oscillazione per operazione
servono = int(ceil(((quantile_normale(0.95) + quantile_normale(0.80))
                    * oscillazione / max(vantaggio_implicito, 1e-9)) ** 2))

print(t(f"vantaggio medio implicito per operazione: {vantaggio_implicito:.3%}",
        f"implied average edge per trade:           {vantaggio_implicito:.3%}"))
print(t(f"operazioni necessarie per dimostrarlo:    {servono:,}",
        f"trades needed to prove it:                {servono:,}"))
print(t(f"operazioni dichiarate:                    {n:,}",
        f"trades claimed:                           {n:,}"))
print(t(f"→ il campione e' {'sufficiente' if n >= servono else 'INSUFFICIENTE'}: "
        f"servirebbero {servono / max(n, 1):.1f} volte le operazioni dichiarate",
        f"→ the sample is {'sufficient' if n >= servono else 'INSUFFICIENT'}: "
        f"it would take {servono / max(n, 1):.1f} times the claimed trades"))

costi = PROPOSTA["costi_dichiarati"]
if costi is not None:
    print(t(f"\ncosti dichiarati: {costi:.2%} per operazione",
            f"\nstated costs: {costi:.2%} per trade"))
    print(t(f"vantaggio al netto di costi realistici (0,12%): "
            f"{vantaggio_implicito - (0.0012 - costi):.3%} per operazione",
            f"edge net of realistic costs (0.12%): "
            f"{vantaggio_implicito - (0.0012 - costi):.3%} per trade"))

# %% [markdown]
# ### Cosa fare da domani
#
# Prendi tre cose che ti sono passate davanti nell'ultimo mese: un video, un
# post, la pubblicità di un corso. Compila `PROPOSTA` per ciascuna e segna il
# punteggio.
#
# Non aspettarti di scoprire dei truffatori. Scoprirai qualcosa di più utile e
# più scomodo: che nella maggior parte dei casi **non c'è materiale sufficiente
# nemmeno per compilare la tabella**. E quando non c'è materiale per le domande,
# non stai valutando una proposta debole: stai valutando una proposta vuota, e il
# tuo lavoro è finito in trenta secondi.
#
# ---
#
# > **EN** — *What to do starting tomorrow.* Take three things that crossed
# > your path in the last month: a video, a post, an ad for a course. Fill in
# > `PROPOSTA` for each and note the score. Don't expect to uncover scammers.
# > You'll discover something more useful and more uncomfortable: that in most
# > cases **there isn't even enough material to fill in the table**. And when
# > there's no material for the questions, you're not evaluating a weak
# > proposal — you're evaluating an empty one, and your work is done in
# > thirty seconds.
