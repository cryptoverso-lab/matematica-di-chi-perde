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
# # Lab 10 — Più parametri, meno sapere
#
# *Quaderno del capitolo «Più parametri, meno sapere» di **La matematica di chi perde**.*
#
# Costruiamo una regola nel modo in cui si costruisce davvero: **un ingrediente
# alla volta**, tenendo ogni volta quello che migliora di più il risultato sui
# dati che stiamo guardando.
#
# Le condizioni fra cui scegliere sono **numeri casuali**: non contengono la
# minima informazione, né sul prezzo né su niente. La seconda metà della storia
# non la guardiamo mai durante la costruzione.
#
# La curva sui dati usati per costruire sale a ogni passo. È garantito — e ha lo
# stesso identico aspetto che avrebbe se il metodo funzionasse davvero.
#
# ---
#
# > **EN** — *Lab 10 — More parameters, less knowledge.* Notebook for the
# > chapter "More parameters, less knowledge". We build a rule the way one
# > really builds it: **one ingredient at a time**, each time keeping
# > whatever improves the result the most on the data we're looking at. The
# > conditions to choose among are **random numbers**: they contain zero
# > information, about price or anything else. We never look at the second
# > half of the history while building. The curve on the data used to build
# > rises at every step. It's guaranteed — and it looks exactly like it
# > would if the method actually worked.

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

from cvbook import seed_for
from cvbook.dati import carica
from cvbook.metriche import rendimenti

r = rendimenti(carica("btcusdt").sort("data")["chiusura"].to_numpy())
meta = len(r) // 2
dentro_campione, fuori_campione = r[:meta], r[meta:]
print(f"{len(r)} giorni: {len(dentro_campione)} per costruire, "
      f"{len(fuori_campione)} mai visti")

# %% [markdown]
# ## 1. L'esperimento
#
# Si riproduce quello che si fa davvero: **si aggiunge un ingrediente alla volta**.
# A ogni passo si prova ogni condizione disponibile e si tiene quella che migliora
# di più il risultato sulla prima metà della storia. La seconda metà non si guarda
# mai durante la costruzione.
#
# ---
#
# > **EN** — *1. The experiment.* We reproduce what actually happens: **one
# > ingredient is added at a time**. At each step every available condition
# > is tried, and whichever improves the result the most on the first half
# > of the history is kept. The second half is never looked at during
# > construction.

# %%
CONDIZIONI_MAX = 25   # <- quante aggiunte al massimo
DISPONIBILI = 400     # <- quante condizioni ci sono nel cassetto
                      # PROVA / TRY: 2000 (vedi esercizio 1)

# In QUESTO esperimento i costi si tengono a zero, e va detto perche'.
# Aumentando le condizioni il segnale cambia stato piu' spesso, quindi opera di
# piu': con i costi dentro, la curva mescolerebbe due effetti diversi — i gradi
# di liberta' e la frequenza. Qui vogliamo isolare il primo. Il secondo lo
# guardiamo a parte, nella cella 2, che e' altrettanto istruttiva.
# In THIS experiment costs are held at zero, and here's why: more conditions
# means the signal flips more often, so it trades more — with costs in, the
# curve would blend two different effects (degrees of freedom and frequency).
# Here we want to isolate the first. We look at the second separately in
# cell 2, which is just as instructive.
COSTO = 0.0
# NON TOCCARE / DO NOT CHANGE: deve restare zero qui — è la cella 2 che
# rimette i costi per isolare il secondo effetto, non questa.
# It must stay zero here — it's cell 2 that puts costs back in to isolate
# the second effect, not this one.


def risultato(rend: np.ndarray, posizione: np.ndarray, costo: float = COSTO) -> float:
    movimenti = np.abs(np.diff(np.concatenate([[0.0], posizione])))
    return float(np.prod(1 + posizione * rend - movimenti * costo))


def ricerca_per_aggiunte(rumore: np.ndarray, passi: int) -> tuple[list[float], list[float]]:
    """Costruzione per aggiunte successive, come si fa davvero.

    A ogni passo si prova ad aggiungere ciascuna delle condizioni disponibili e
    si tiene quella che migliora di piu' il risultato **sui dati che si stanno
    guardando**. Ci si ferma quando nessuna aggiunta migliora — cioe' quando una
    persona reale smetterebbe.

    La regola sta dentro al mercato quando la somma delle condizioni scelte e'
    positiva: cosi' l'esposizione resta attorno alla meta' del tempo e l'unica
    cosa che cambia e' il numero di gradi di liberta'.
    """
    scelte: set[int] = set()
    somma = np.zeros(rumore.shape[1])
    corrente = 0.0
    curva_dentro, curva_fuori = [], []

    for _ in range(passi):
        migliore_indice, migliore_valore = None, -np.inf
        for k in range(len(rumore)):
            if k in scelte:
                continue
            posizione = ((somma + rumore[k]) > 0).astype(float)
            valore = risultato(dentro_campione, posizione[:meta])
            if valore > migliore_valore:
                migliore_indice, migliore_valore = k, valore

        if migliore_valore <= corrente:
            break  # nessuna aggiunta migliora: ci si ferma

        scelte.add(migliore_indice)
        somma = somma + rumore[migliore_indice]
        corrente = migliore_valore
        posizione = (somma > 0).astype(float)
        curva_dentro.append(migliore_valore)
        curva_fuori.append(risultato(fuori_campione, posizione[meta:]))

    return curva_dentro, curva_fuori


rng = np.random.default_rng(seed_for("lab-dimensionalita"))
# Le condizioni sono rumore puro allineato ai giorni: nessuna informazione dentro.
rumore = rng.normal(size=(DISPONIBILI, len(r)))
dentro, fuori = ricerca_per_aggiunte(rumore, CONDIZIONI_MAX)
CONDIZIONI = list(range(1, len(dentro) + 1))

for n, d, f in zip(CONDIZIONI, dentro, fuori):
    print(f"{n:2d} condizioni →  dentro campione {d:10.2f}x   fuori campione {f:8.2f}x")
print(f"\nla ricerca si e' fermata dopo {len(dentro)} aggiunte: nessuna condizione "
      f"rimasta migliorava piu' il risultato che si stava guardando.")

# %%
with avvio.figura("schermo"):
    fig, ax = plt.subplots()
    ax.plot(CONDIZIONI, dentro, marker="o", linewidth=2,
            label="sulla parte usata per costruire")
    ax.plot(CONDIZIONI, fuori, marker="s", linewidth=2, linestyle="--",
            label="sulla parte mai vista")
    ax.axhline(1.0, linestyle=":", linewidth=1)
    ax.set_yscale("log")
    ax.set_xlabel("Condizioni aggiunte alla regola (tutte generate a caso)")
    ax.set_ylabel("Capitale finale (volte, scala log)")
    ax.legend()
    plt.show()

# %% [markdown]
# La curva continua sale a **ogni singolo passo**, e non perché il metodo stia
# imparando qualcosa: sale per costruzione, perché nessuno aggiunge un ingrediente
# che peggiora il numero che sta guardando.
#
# **Quella curva è identica a quella che vedresti se il metodo funzionasse davvero.**
# Guardando solo il risultato della costruzione non puoi distinguere una scoperta
# da rumore memorizzato.
#
# La curva tratteggiata è la risposta, e va letta con attenzione: migliora per le
# prime aggiunte, tocca un massimo, e da lì peggiora. Il guaio è che il passo in
# cui bisognava fermarsi **non è visibile sulla curva continua**.
#
# ---
#
# > **EN** — The solid curve rises at **every single step**, and not because
# > the method is learning anything: it rises by construction, because
# > nobody adds an ingredient that worsens the number they're looking at.
# > **That curve is identical to the one you'd see if the method actually
# > worked.** Looking only at the construction result, you cannot tell a
# > discovery apart from memorized noise. The dashed curve is the answer, and
# > must be read carefully: it improves for the first few additions, peaks,
# > then worsens from there. The trouble is that the step where you should
# > have stopped **is not visible on the solid curve**.

# %% [markdown]
# ## 2. E se i costi li rimettiamo dentro?
#
# La cella precedente li teneva a zero per isolare i gradi di libertà. Rimettendoli,
# succede una cosa che il capitolo sui costi aveva già annunciato: più condizioni
# significa cambiare posizione più spesso, e ogni cambio si paga. Il risultato
# **dentro campione** smette perfino di crescere.
#
# ---
#
# > **EN** — *2. What if we put the costs back in?* The previous cell kept
# > them at zero to isolate degrees of freedom. Putting them back, something
# > the costs chapter had already warned about happens: more conditions means
# > changing position more often, and every change is paid for. The
# > **in-sample** result even stops growing.

# %%
rng2 = np.random.default_rng(seed_for("lab-dimensionalita-costi"))
print(f"{'condizioni':>11s} {'operazioni':>11s} {'senza costi':>13s} {'con 0,12%':>12s}")
for n in CONDIZIONI:
    indici = rng2.integers(0, DISPONIBILI, size=n)
    posizione = (rumore[indici].sum(axis=0) > 0).astype(float)
    movimenti = float(np.abs(np.diff(np.concatenate([[0.0], posizione]))).sum())
    senza = risultato(r, posizione, costo=0.0)
    con = risultato(r, posizione, costo=0.0012)
    print(f"{n:11d} {movimenti:11.0f} {senza:12.2f}x {con:11.2f}x")

print("\nDue effetti diversi che spesso vengono confusi: i gradi di liberta' "
      "gonfiano il risultato apparente, la frequenza lo erode. Nella pratica "
      "agiscono insieme, ed e' per questo che vanno misurati separatamente.")

# %% [markdown]
# ## 3. I parametri che non sai di avere
#
# Prendiamo la regola più semplice immaginabile — «resto investito quando il
# prezzo sta sopra la sua media a N giorni» — e contiamo le scelte che quella
# frase nasconde.
#
# ---
#
# > **EN** — *3. The parameters you don't know you have.* Take the simplest
# > rule imaginable — "stay invested when price is above its N-day average"
# > — and count the choices that sentence hides.

# %%
scelte = {
    "quale asset": 3,
    "quale intervallo (giorn./orario/settim.)": 3,
    "da quando parte la serie": 4,
    "quale prezzo (chiusura, apertura, medio)": 3,
    "media semplice o pesata": 2,
    "cosa fare quando si e' fuori": 2,
    "quale costo per operazione": 3,
    "quando si esegue": 3,
    "ogni quanto si controlla il segnale": 3,
}

totale = 1
for nome, quante in scelte.items():
    totale *= quante
    print(f"  {nome:>42s}: {quante} valori plausibili")
print(f"\ncombinazioni nascoste dietro «un solo parametro»: {totale:,}")
print("Non le hai provate tutte. Ne hai provata UNA, per abitudine, e non l'hai "
      "contata. Se il risultato fosse venuto brutto ne avresti cambiata qualcuna.")

# %% [markdown]
# ## 4. La dispersione: l'informazione più utile di un backtest
#
# Invece di un numero, un intervallo. Riesegui la stessa regola cambiando una a
# una le scelte e guarda quanto si sparpagliano i risultati.
#
# ---
#
# > **EN** — *4. Dispersion: the most useful information in a backtest.*
# > Instead of a number, a range. Rerun the same rule changing the choices
# > one at a time and watch how much the results spread.

# %%
prezzi = carica("btcusdt").sort("data")["chiusura"].to_numpy()


def sopra_media(p: np.ndarray, finestra: int, ritardo: int = 1) -> np.ndarray:
    cumulata = np.concatenate([[0.0], np.cumsum(p)])
    media = np.full(len(p), np.nan)
    media[finestra - 1:] = (cumulata[finestra:] - cumulata[:-finestra]) / finestra
    segnale = np.nan_to_num(np.where(p > media, 1.0, 0.0))
    posizione = np.zeros(len(p))
    posizione[ritardo:] = segnale[:-ritardo]
    return posizione


varianti = []
for finestra in (20, 50, 100, 200):
    for partenza in (0, 200, 400, 600):  # PROVA / TRY: aggiungi altre date (esercizio 3)
        p = prezzi[partenza:]
        rend = rendimenti(p)
        varianti.append(risultato(rend, sopra_media(p, finestra)[1:], costo=0.0012))

varianti = np.array(varianti)
print(f"{len(varianti)} varianti della STESSA idea (4 finestre × 4 date d'inizio)\n")
print(f"  peggiore  {varianti.min():8.2f}x")
print(f"  mediana   {np.median(varianti):8.2f}x")
print(f"  migliore  {varianti.max():8.2f}x")
print(f"  rapporto migliore/peggiore: {varianti.max() / varianti.min():.1f} volte")
print("\nQuesto intervallo e' l'informazione onesta. Il numero singolo che di "
      "solito si pubblica e' un punto scelto dentro di esso.")

# %% [markdown]
# ### Esercizi
#
# 1. Nella prima cella porta `DISPONIBILI` a 2000. Con più condizioni fra cui
#    scegliere la curva continua sale ancora di più e la ricerca si ferma più
#    tardi: il numero di alternative esplorate è esattamente ciò che determina
#    quanto bene si memorizza il rumore.
# 2. Fai l'esperimento della prima cella con i **tuoi** indicatori al posto dei
#    numeri casuali. Se le due curve si separano come qui, hai appena scoperto
#    qualcosa di importante sul tuo metodo.
# 3. Nell'ultima cella aggiungi altre due date d'inizio. La dispersione cresce, e
#    con essa l'onestà del risultato.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. In the first cell raise `DISPONIBILI` to 2000. With more conditions to
# >    choose among, the solid curve rises even more and the search stops
# >    later: the number of alternatives explored is exactly what determines
# >    how well noise gets memorized.
# > 2. Run the first cell's experiment with **your own** indicators instead
# >    of random numbers. If the two curves separate like here, you've just
# >    discovered something important about your method.
# > 3. In the last cell add two more start dates. The dispersion grows, and
# >    with it the honesty of the result.
