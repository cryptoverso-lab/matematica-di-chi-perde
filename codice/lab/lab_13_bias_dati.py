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
# # Lab 13 — Come mente un backtest: i dati
#
# *Quaderno del capitolo «Come mente un backtest — i dati» di
# **La matematica di chi perde**.*
#
# Lo stesso backtest scritto in due versioni, una causale e una con un lookahead
# di **una riga**. Poi il test di invarianza, che scova quell'errore in modo
# meccanico: puoi incollarci dentro il tuo codice.
#
# E infine i cinque controlli da fare sui dati prima di qualunque calcolo. Dieci
# minuti, e sono quelli con il miglior rapporto fra tempo speso ed errori
# trovati.
#
# ---
#
# > **EN** — *Lab 13 — How a backtest lies: the data.* Notebook for the
# > chapter "How a backtest lies — the data". The same backtest written in
# > two versions, one causal and one with a **one-line** lookahead. Then the
# > invariance test, which catches that error mechanically: you can paste
# > your own code into it. And finally the five checks to run on the data
# > before any calculation. Ten minutes, and they have the best ratio of
# > time spent to errors found.

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

avvio.prepara(["btcusdt", "lunausdt"])

# %%
import matplotlib.pyplot as plt
import numpy as np

from cvbook.dati import carica
from cvbook.regole import esegui

df = carica("btcusdt").sort("data")
prezzi = df["chiusura"].to_numpy()
FINESTRA = 20  # PROVA / TRY: qualunque valore (vedi esercizio 1) — il rapporto resta enorme
COSTO = 0.0012  # PROVA / TRY: 0,0006 · 0,0012 · 0,0025


def media_mobile(p: np.ndarray, finestra: int) -> np.ndarray:
    cumulata = np.concatenate([[0.0], np.cumsum(p)])
    m = np.full(len(p), np.nan)
    m[finestra - 1:] = (cumulata[finestra:] - cumulata[:-finestra]) / finestra
    return m


# %% [markdown]
# ## 1. Una riga di differenza
#
# Le due versioni della stessa regola. Guarda **solo** l'ultima riga di ciascuna.
#
# ---
#
# > **EN** — *1. One line of difference.* The two versions of the same rule.
# > Look **only** at the last line of each.

# %%
media = media_mobile(prezzi, FINESTRA)
segnale = np.nan_to_num(np.where(prezzi > media, 1.0, 0.0))

# Versione CAUSALE: la posizione di oggi usa il segnale di ieri.
causale = np.zeros(len(prezzi))
causale[1:] = segnale[:-1]

# Versione CON LOOKAHEAD: la posizione di oggi usa il segnale di oggi, cioe'
# un'informazione che al momento di decidere non esisteva ancora.
# NON TOCCARE / DO NOT CHANGE: è sbagliata apposta, per il confronto — non è
# un bug da sistemare.
con_lookahead = segnale.copy()

a = esegui(prezzi, causale, costo=COSTO)
b = esegui(prezzi, con_lookahead, costo=COSTO)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.semilogy(b["curva"], linewidth=2, label=f"con lookahead — {b['finale']:,.0f}x")
    ax.semilogy(a["curva"], linewidth=2, linestyle="--",
                label=f"causale — {a['finale']:,.1f}x")
    ax.set_ylabel("Capitale (scala log)")
    ax.set_xlabel("Giorni")
    ax.legend()
    plt.show()

print(f"versione causale:      {a['finale']:12,.2f}x")
print(f"versione con lookahead:{b['finale']:12,.2f}x")
print(f"rapporto:              {b['finale'] / a['finale']:12,.0f} volte")
print("\nUna riga. Il risultato non e' un po' piu' ottimista: e' impossibile, "
      "ottenuto da una macchina che sapeva in anticipo come sarebbe finita la "
      "giornata.")

# %% [markdown]
# ## 2. Il test di invarianza
#
# Prendi il calcolo, eseguilo su tutta la serie, poi su una serie troncata, e
# confronta la parte comune. **Devono essere identici.** Se cambiano, il calcolo
# sta usando dati successivi.
#
# Puoi incollarci dentro il tuo codice: se il test fallisce, hai trovato il tuo
# lookahead prima che ti costasse dei soldi.
#
# ---
#
# > **EN** — *2. The invariance test.* Take the calculation, run it on the
# > whole series, then on a truncated one, and compare the common part.
# > **They must be identical.** If they change, the calculation is using
# > future data. You can paste your own code into it: if the test fails,
# > you've found your lookahead before it cost you money.

# %%
def test_invarianza(funzione, p: np.ndarray, tagli=(400, 1200, 2400)) -> bool:
    """True se `funzione(p)` non cambia il passato quando arrivano dati nuovi."""
    completa = funzione(p)
    tutto_bene = True
    for taglio in tagli:
        parziale = funzione(p[:taglio])
        uguali = np.allclose(parziale, completa[:taglio], equal_nan=True)
        if not uguali:
            primo = int(np.argmax(~np.isclose(parziale, completa[:taglio],
                                              equal_nan=True)))
            print(f"  troncando a {taglio}: DIVERSO, prima differenza al giorno {primo}")
            tutto_bene = False
        else:
            print(f"  troncando a {taglio}: identico")
    return tutto_bene


def regola_causale(p: np.ndarray) -> np.ndarray:
    s = np.nan_to_num(np.where(p > media_mobile(p, FINESTRA), 1.0, 0.0))
    pos = np.zeros(len(p))
    pos[1:] = s[:-1]
    return pos


def regola_con_lookahead(p: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.where(p > media_mobile(p, FINESTRA), 1.0, 0.0))


def regola_normalizzata_male(p: np.ndarray) -> np.ndarray:
    """Errore diffusissimo: normalizzare usando media e deviazione di TUTTO."""
    z = (p - p.mean()) / p.std()
    return (z > 0).astype(float)


print("regola causale:")
print("  esito:", "PASSA" if test_invarianza(regola_causale, prezzi) else "FALLISCE")
print("\nregola con lookahead:")
print("  esito:", "PASSA" if test_invarianza(regola_con_lookahead, prezzi) else "FALLISCE")
print("\nregola normalizzata sull'intero periodo:")
print("  esito:", "PASSA" if test_invarianza(regola_normalizzata_male, prezzi) else "FALLISCE")

# %% [markdown]
# Nota il terzo caso: non c'è nessuno sfasamento sbagliato, il codice sembra
# innocuo. Ma normalizzare con la media dell'intero periodo infila nel **primo**
# giorno del test un'informazione sull'**ultimo**.
#
# ---
#
# > **EN** — Note the third case: there's no wrong lag, the code looks
# > innocent. But normalizing with the mean of the entire period sneaks
# > information about the **last** day into the **first** day of the test.

# %% [markdown]
# ## 3. I cinque controlli sui dati
#
# Prima di qualunque calcolo. Costano dieci minuti; saltarli costa giorni di
# lavoro costruito su una base che non regge.
#
# ---
#
# > **EN** — *3. The five checks on the data.* Before any calculation. They
# > cost ten minutes; skipping them costs days of work built on a foundation
# > that doesn't hold.

# %%
def controlla(nome: str) -> None:
    d = carica(nome).sort("data")
    date = d["data"].to_list()
    chiusura = d["chiusura"].to_numpy()
    r = chiusura[1:] / chiusura[:-1] - 1.0

    print(f"\n=== {nome} ===")

    # 1. righe contro calendario
    attesi = (date[-1] - date[0]).days + 1
    print(f"1. righe: {len(date)} su {attesi} giorni di calendario "
          f"({len(date) / attesi:.1%} di copertura)")

    # 2. i venti movimenti piu' grandi
    estremi = np.argsort(np.abs(r))[-5:][::-1]
    print("2. i cinque movimenti piu' grandi:")
    for i in estremi:
        print(f"     {date[i + 1]}  {r[i]:+7.1%}")

    # 3. giorni a variazione esattamente zero
    zeri = int(np.sum(r == 0.0))
    print(f"3. giorni a variazione esattamente zero: {zeri} "
          f"({'sospetti: probabile riempimento' if zeri > 3 else 'ok'})")

    # 4. coerenza fra massimo, minimo, apertura e chiusura
    m, mi = d["massimo"].to_numpy(), d["minimo"].to_numpy()
    ap, ch = d["apertura"].to_numpy(), d["chiusura"].to_numpy()
    incoerenti = int(np.sum((m < ch) | (m < ap) | (mi > ch) | (mi > ap) | (m < mi)))
    print(f"4. barre incoerenti (max sotto la chiusura, ecc.): {incoerenti}")

    # 5. volume all'inizio e alla fine
    v = d["volume"].to_numpy()
    print(f"5. volume mediano dei primi 30 giorni: {np.median(v[:30]):,.0f}")
    print(f"   volume mediano degli ultimi 30:     {np.median(v[-30:]):,.0f}")
    if np.median(v[:30]) < np.median(v[-30:]) / 10:
        print("   → l'inizio della serie e' molto sottile: quei prezzi esistono, "
              "ma non erano ottenibili in quantita'.")


controlla("btcusdt")
controlla("lunausdt")

# %% [markdown]
# Guarda il secondo controllo sul token morto: compare un movimento di **oltre
# diciassette milioni di punti percentuali**. Non è un errore del file: è quello
# che succede quando un prezzo scende a cinque centomillesimi e poi si muove di
# qualche cifra decimale. In percentuale sono numeri assurdi; in denaro sono
# briciole.
#
# È il motivo per cui il controllo numero due va fatto **guardando**, non
# automatizzando una soglia: qualunque filtro che scartasse quel giorno
# scarterebbe un dato vero, e qualunque calcolo che lo tratti come un rendimento
# normale produce statistiche prive di senso. Su serie che arrivano vicino allo
# zero, i rendimenti percentuali smettono di essere la rappresentazione giusta.
#
# ---
#
# > **EN** — Look at the second check on the dead token: a movement of
# > **over seventeen million percentage points** shows up. It's not a file
# > error: it's what happens when a price falls to five hundred-thousandths
# > and then moves by a few decimal digits. In percentage terms these are
# > absurd numbers; in money they're crumbs. That's why check number two
# > should be done **by looking**, not by automating a threshold: any filter
# > that discarded that day would discard real data, and any calculation
# > that treats it as a normal return produces meaningless statistics. On
# > series that get close to zero, percentage returns stop being the right
# > representation.

# %% [markdown]
# ### Esercizi
#
# 1. Nella prima cella cambia `FINESTRA`. Il rapporto fra le due curve resta
#    enorme per qualunque valore: il lookahead non è un errore di taratura, è un
#    errore di tipo.
# 2. Incolla nella seconda cella una **tua** funzione che calcoli una posizione e
#    passala a `test_invarianza`. È il controllo che consiglio di automatizzare.
# 3. Scrivi una quarta regola sbagliata: usa il **massimo dell'intera serie** come
#    soglia. Poi passala al test e guardalo fallire.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. In the first cell change `FINESTRA`. The ratio between the two curves
# >    stays huge for any value: the lookahead isn't a calibration error, it's
# >    a type error.
# > 2. Paste into the second cell **your own** function that computes a
# >    position and pass it to `test_invarianza`. It's the check I recommend
# >    automating.
# > 3. Write a fourth, wrong rule: use the **maximum of the entire series**
# >    as a threshold. Then pass it to the test and watch it fail.
