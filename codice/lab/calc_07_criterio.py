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
# *Quaderno del capitolo «Il Criterio» di **Non Fidarti di Me**.*
#
# Una lista di controllo che gira. Inserisci quello che sai di una proposta —
# periodo, numero di operazioni, percentuale di vincite, costi dichiarati — e ti
# restituisce due cose: **le domande che restano senza risposta**, e **quale
# percentuale di tentativi casuali avrebbe prodotto un risultato altrettanto
# buono**.
#
# È la versione automatica del capitolo, e sta in una pagina.

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

avvio.prepara([])

# %%
from math import ceil, erf, sqrt

import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for

# %% [markdown]
# ## 1. Cosa sai della proposta
#
# Compila quello che sai. Lascia `None` dove **non ti è stato detto**: è proprio
# quello il dato più informativo del quaderno.

# %%
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

# %%
def valuta(p: dict) -> tuple[float, list[str]]:
    punteggio, mancanti = 0.0, []

    # 1. I dati
    dati = [p["fonte_dichiarata"], p["data_di_estrazione"], p["periodo_dal"], p["periodo_al"]]
    presenti = sum(x is not None for x in dati)
    punteggio += presenti / len(dati)
    if presenti < len(dati):
        mancanti.append("1. i dati: manca " + ", ".join(
            n for n, x in zip(("la fonte", "la data di estrazione", "l'inizio del periodo",
                               "la fine del periodo"), dati) if x is None))

    # 2. Il metodo
    metodo = [p["regole_descritte"], p["soglie_dichiarate"], p["costi_dichiarati"] is not None]
    punteggio += sum(bool(x) for x in metodo) / len(metodo)
    if not all(metodo):
        mancanti.append("2. il metodo: non si potrebbe rieseguire cosi' com'e' descritto")

    # 3. I limiti
    limiti = [p["peggior_periodo_dichiarato"], p["durata_peggior_periodo"]]
    punteggio += sum(bool(x) for x in limiti) / len(limiti)
    if not all(limiti):
        mancanti.append("3. i limiti: non dice dove smette di funzionare")

    # 4. I fallimenti
    fallimenti = [p["varianti_provate_dichiarate"] is not None,
                  bool(p["operazioni_in_perdita_mostrate"])]
    punteggio += sum(fallimenti) / len(fallimenti)
    if not all(fallimenti):
        mancanti.append("4. i fallimenti: non si sa quante idee sono state scartate")

    # 5. La forza dell'evidenza
    evidenza = [p["numero_operazioni"] is not None, p.get("confronto_col_caso", False)]
    punteggio += sum(bool(x) for x in evidenza) / len(evidenza)
    if not evidenza[1]:
        mancanti.append("5. l'evidenza: nessun confronto con il caso")

    return punteggio, mancanti


punteggio, mancanti = valuta(PROPOSTA)
print(f"punteggio: {punteggio:.1f} su 5\n")
for m in mancanti:
    print(f"  senza risposta → {m}")

if punteggio < 3:
    print("\nSotto le tre risposte su cinque non stai guardando conoscenza: "
          "stai guardando un'inserzione.")
elif punteggio < 4.5:
    print("\nProbabilmente in buona fede, ma non ha verificato quanto crede.")
else:
    print("\nHa fatto il lavoro. Adesso puoi cominciare a valutare il merito.")

print(f"\nE la domanda che non e' fra le cinque: come guadagna? "
      f"→ {PROPOSTA['come_guadagna']}")

# %% [markdown]
# ## 3. Quale percentuale di tentativi casuali avrebbe fatto altrettanto
#
# La domanda decisiva, e quella che quasi nessuno pone.

# %%
N_PROVE = 20_000
rng = np.random.default_rng(seed_for("calc-criterio"))

n = PROPOSTA["numero_operazioni"]
vinte = int(round(PROPOSTA["quota_vincenti"] * n))
esiti = rng.binomial(n, 0.5, N_PROVE)
quota_caso = float((esiti >= vinte).mean())

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.hist(esiti / n * 100, bins=50)
    ax.axvline(PROPOSTA["quota_vincenti"] * 100, linewidth=2.5, color="black")
    ax.set_xlabel("Quota di operazioni vincenti (%)")
    ax.set_ylabel(f"Su {N_PROVE:,} sequenze prive di vantaggio")
    plt.show()

print(f"dichiarate {vinte} vittorie su {n} operazioni ({PROPOSTA['quota_vincenti']:.0%})")
print(f"con una moneta equa capita nel {quota_caso:.2%} dei casi")
if PROPOSTA["varianti_provate_dichiarate"]:
    tentativi = PROPOSTA["varianti_provate_dichiarate"]
    print(f"con {tentativi} varianti provate, almeno una ci arriva nel "
          f"{1 - (1 - quota_caso) ** tentativi:.1%} dei casi")
else:
    print("\nNon sappiamo quante varianti siano state provate. Assumi che siano "
          "state parecchie: e' l'ipotesi realistica.")
    for tentativi in (5, 20, 100):
        print(f"  con {tentativi:3d} varianti: almeno una ci arriva nel "
              f"{1 - (1 - quota_caso) ** tentativi:5.1%} dei casi")

# %% [markdown]
# ## 4. Il campione basta?

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

print(f"vantaggio medio implicito per operazione: {vantaggio_implicito:.3%}")
print(f"operazioni necessarie per dimostrarlo:    {servono:,}")
print(f"operazioni dichiarate:                    {n:,}")
print(f"→ il campione e' {'sufficiente' if n >= servono else 'INSUFFICIENTE'}: "
      f"servirebbero {servono / max(n, 1):.1f} volte le operazioni dichiarate")

costi = PROPOSTA["costi_dichiarati"]
if costi is not None:
    print(f"\ncosti dichiarati: {costi:.2%} per operazione")
    print(f"vantaggio al netto di costi realistici (0,12%): "
          f"{vantaggio_implicito - (0.0012 - costi):.3%} per operazione")

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
