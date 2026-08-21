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
# # Lab 21 — Trova il lookahead
#
# *Quaderno del capitolo «L'AI come acceleratore» di **Non Fidarti di Me**.*
#
# Qui sotto ci sono **due implementazioni della stessa strategia**, entrambe
# scritte come le scriverebbe un assistente automatico su richiesta. Una è
# corretta, l'altra ha un lookahead sottile.
#
# Il tuo compito è trovare quale, **prima** di eseguirle. Poi le esegui e vedi la
# differenza.
#
# È l'esercizio che consiglio di fare prima di far scrivere a una macchina
# qualunque cosa che poi userai con soldi veri.

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
from cvbook.metriche import rendimenti
from cvbook.regole import esegui

prezzi = carica("btcusdt").sort("data")["chiusura"].to_numpy()
COSTO = 0.0012

# %% [markdown]
# ## Le due versioni
#
# La strategia dichiarata è la stessa per entrambe:
#
# > *Resta investito quando il prezzo di chiusura supera la banda superiore,
# > calcolata come media a venti giorni più una deviazione standard a venti
# > giorni. Esci quando scende sotto la media.*
#
# Leggile con calma. Non eseguire ancora la cella dopo.

# %%
def versione_a(p: np.ndarray, finestra: int = 20) -> np.ndarray:
    """Versione A."""
    posizione = np.zeros(len(p))
    stato = 0.0
    for t in range(finestra, len(p)):
        blocco = p[t - finestra:t]
        media = blocco.mean()
        banda = media + blocco.std(ddof=1)
        if p[t - 1] > banda:
            stato = 1.0
        elif p[t - 1] < media:
            stato = 0.0
        posizione[t] = stato
    return posizione


def versione_b(p: np.ndarray, finestra: int = 20) -> np.ndarray:
    """Versione B."""
    posizione = np.zeros(len(p))
    stato = 0.0
    for t in range(finestra, len(p)):
        blocco = p[t - finestra + 1:t + 1]
        media = blocco.mean()
        banda = media + blocco.std(ddof=1)
        if p[t] > banda:
            stato = 1.0
        elif p[t] < media:
            stato = 0.0
        posizione[t] = stato
    return posizione


# %% [markdown]
# ### Prima di continuare
#
# Scrivi qui la tua risposta. Quale delle due usa un'informazione che, al momento
# di decidere, non esisteva ancora?
#
# *(La differenza è di due caratteri.)*

# %%
a = esegui(prezzi, versione_a(prezzi), costo=COSTO)
b = esegui(prezzi, versione_b(prezzi), costo=COSTO)

with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.semilogy(b["curva"], linewidth=2, label=f"versione B — {b['finale']:,.1f}x")
    ax.semilogy(a["curva"], linewidth=2, linestyle="--", label=f"versione A — {a['finale']:,.1f}x")
    ax.set_ylabel("Capitale (scala log)")
    ax.set_xlabel("Giorni")
    ax.legend()
    plt.show()

print(f"versione A: {a['finale']:10.2f}x   operazioni {a['operazioni']:.0f}")
print(f"versione B: {b['finale']:10.2f}x   operazioni {b['operazioni']:.0f}")
print(f"rapporto:   {b['finale'] / a['finale']:10.2f}")

# %% [markdown]
# ## I due test, e perché ne servono due
#
# Il primo è il test di **invarianza per prefisso**: il valore calcolato per un
# dato giorno non deve cambiare quando arrivano dati successivi. Scova gli errori
# in cui una statistica è calcolata sull'intero periodo.
#
# Eseguilo e guarda cosa succede.

# %%
def test_invarianza(funzione, p: np.ndarray, tagli=(600, 1600, 2600)) -> bool:
    """Il passato non deve cambiare quando arriva il futuro."""
    completa = funzione(p)
    passa = True
    for taglio in tagli:
        parziale = funzione(p[:taglio])
        uguali = np.allclose(parziale[:taglio - 1], completa[:taglio - 1])
        print(f"  troncando a {taglio}: {'identico' if uguali else 'DIVERSO'}")
        passa = passa and uguali
    return passa


for nome, funzione in (("versione A", versione_a), ("versione B", versione_b)):
    print(f"{nome}:")
    esito = test_invarianza(funzione, prezzi)
    print(f"  → {'PASSA' if esito else 'FALLISCE'}\n")

# %% [markdown]
# **Passano entrambe.** E questa è la lezione più utile del quaderno.
#
# Il test di invarianza non intercetta questo tipo di errore, perché la versione B
# non usa il *futuro*: usa **il presente**, cioè un dato che al momento della
# decisione non è ancora disponibile ma che appartiene comunque al passato di
# qualunque troncamento. Serve un secondo test, di natura diversa.
#
# Il secondo test è più diretto: **si cambia il prezzo di un giorno e si guarda se
# la posizione di quello stesso giorno cambia.** Se cambia, la decisione stava
# usando un dato che al momento di decidere non esisteva.

# %%
def test_esecuzione_sfasata(funzione, p: np.ndarray, giorni=(700, 1500, 2400)) -> bool:
    """La posizione di oggi non deve dipendere dal prezzo di oggi."""
    base = funzione(p)
    passa = True
    for t in giorni:
        alterata = p.copy()
        alterata[t] *= 1.5   # un movimento enorme, quel giorno
        nuova = funzione(alterata)
        cambia = not np.isclose(nuova[t], base[t])
        print(f"  alterando il giorno {t}: la posizione di quel giorno "
              f"{'CAMBIA' if cambia else 'resta uguale'}")
        passa = passa and not cambia
    return passa


for nome, funzione in (("versione A", versione_a), ("versione B", versione_b)):
    print(f"{nome}:")
    esito = test_esecuzione_sfasata(funzione, prezzi)
    print(f"  → {'PASSA' if esito else 'FALLISCE: decide con il prezzo di oggi'}\n")

# %% [markdown]
# ## La soluzione
#
# La **versione B** usa `p[t]` per decidere la posizione del giorno `t`, e calcola
# media e deviazione su una finestra che **include** il giorno `t`. Al momento in
# cui quella decisione andrebbe presa, la chiusura di oggi non esiste ancora.
#
# La differenza nel codice è `t - finestra + 1:t + 1` contro `t - finestra:t`, e
# `p[t]` contro `p[t - 1]`. Due caratteri. Il risultato cambia di ordini di
# grandezza.
#
# È esattamente l'errore che questi strumenti producono più spesso, e non per
# distrazione: **usare l'indice corrente è la formulazione più naturale in
# linguaggio umano.** «Compro quando il prezzo supera la banda» diventa, senza
# pensarci, `if p[t] > banda`.

# %% [markdown]
# ## Le quattro richieste, scritte al contrario
#
# Il capitolo elenca le formulazioni che uso davvero. Le riporto qui perché siano
# copiabili.

# %%
RICHIESTE = {
    "sul codice":
        "Elenca tutti i punti in cui questo calcolo potrebbe usare "
        "un'informazione non disponibile al momento della decisione, anche i "
        "piu' improbabili, e per ciascuno indica quale riga.",
    "sul risultato":
        "Elenca dieci ragioni per cui questo risultato potrebbe essere un "
        "artefatto e non un fenomeno, ordinate dalla piu' probabile alla meno "
        "probabile.",
    "sul metodo":
        "Assumi che io mi stia ingannando. Descrivi il modo piu' plausibile in "
        "cui questo procedimento produce un risultato positivo anche in assenza "
        "di qualunque vantaggio reale.",
    "sui dati":
        "Scrivi i controlli che rivelerebbero valori riempiti, giunzioni fra "
        "fonti diverse, giorni mancanti trattati come zero e incoerenze fra "
        "massimo, minimo e chiusura; poi eseguili e riporta i conteggi.",
}

for ambito, testo in RICHIESTE.items():
    print(f"\n--- {ambito} ---\n{testo}")

print("\n\nLo schema comune: chiedere un ELENCO invece di un giudizio. Un giudizio "
      "puo' essere assecondante; un elenco e' verificabile voce per voce. E se "
      "l'elenco e' vuoto o generico, quella e' a sua volta un'informazione.")

# %% [markdown]
# ## Il conto che chiude il capitolo
#
# Quante idee riesci a provare in un pomeriggio con uno strumento che scrive il
# codice al posto tuo? E cosa succede al significato del tuo risultato migliore?

# %%
rng = np.random.default_rng(seed_for("lab-ai"))
r = rendimenti(prezzi)
meta = len(r) // 2

print(f"{'idee provate':>13s} {'migliore dentro':>17s} {'la stessa fuori':>17s}")
for tentativi in (10, 50, 200, 1000):
    migliore, fuori = -np.inf, np.nan
    for _ in range(tentativi):
        rumore = rng.normal(size=len(r))
        posizione = (rumore > 0).astype(float)
        dentro = float(np.prod(1 + posizione[:meta] * r[:meta]))
        if dentro > migliore:
            migliore = dentro
            fuori = float(np.prod(1 + posizione[meta:] * r[meta:]))
    print(f"{tentativi:13d} {migliore:16.2f}x {fuori:16.2f}x")

print("\nPiu' cerchi, piu' trovi. E quello che trovi in piu' NON sopravvive al "
      "contatto con dati che non hai usato per cercare.")
print("\nL'intelligenza artificiale non accelera la scoperta: accelera la "
      "RICERCA. Se hai il metodo, accelera anche la scoperta. Se non ce l'hai, "
      "accelera solo la produzione di illusioni — a un ritmo che prima era "
      "fisicamente impossibile.")
