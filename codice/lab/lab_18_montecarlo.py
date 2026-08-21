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
# # Lab 18 — Mille futuri invece di uno
#
# *Quaderno del capitolo «Mille futuri invece di uno» di **La matematica di chi perde**.*
#
# Ogni curva di capitale che hai visto in vita tua è **una realizzazione**. Qui
# generi le altre storie possibili, fatte della stessa identica materia prima, e
# guardi dove cade quella che è capitata davvero.
#
# L'output più utile è una frase sola: *«nel 5% dei casi peggiori avresti chiuso a
# X e attraversato un calo del Y%»*. Quella frase, guardata prima di aprire una
# posizione, cambia il dimensionamento più di qualunque ragionamento.
#
# ---
#
# > **EN** — *Lab 18 — A thousand futures instead of one.* Notebook for the
# > chapter "A thousand futures instead of one". Every capital curve you've
# > ever seen is **one realization**. Here you generate the other possible
# > histories, made of the exact same raw material, and look at where the one
# > that actually happened falls. The most useful output is a single
# > sentence: *"in the worst 5% of cases you would have closed at X and gone
# > through a drawdown of Y%."* That sentence, read before opening a
# > position, changes sizing more than any reasoning.

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

avvio.prepara(["btcusdt", "ethusdt", "solusdt"])

# %%
import matplotlib.pyplot as plt
import numpy as np

from cvbook import seed_for
from cvbook.dati import carica
from cvbook.metriche import drawdown_massimo, rendimenti
from cvbook.simulazioni import bootstrap_traiettorie, distribuzione_esiti

SERIE = "btcusdt"  # ← PROVA / TRY: "ethusdt" · "solusdt" (vedi esercizio 3)
PERCORSI = 5000     # ← mille bastano per la mediana, per le CODE servono di piu'
                    # PROVA / TRY: 1000 · 5000 · 20000 (vedi sezione 4 qui sotto)
BLOCCHI = 20        # ← lunghezza dei blocchi ricampionati
                    # PROVA / TRY: 5 · 20 · 60 (vedi esercizio 2)

r = rendimenti(carica(SERIE).sort("data")["chiusura"].to_numpy())
reale = np.cumprod(1 + r)

# %% [markdown]
# ## 1. Le altre storie possibili
#
# I rendimenti non vengono modificati né modellati: sono esattamente quelli, con
# tutte le loro code grasse. Vengono **rimescolati a blocchi**, non giorno per
# giorno — rimescolare i singoli giorni distruggerebbe il raggruppamento della
# volatilità che il Lab 9 ha misurato, e produrrebbe percorsi troppo docili.
#
# ---
#
# > **EN** — *1. The other possible histories.* Returns are neither modified
# > nor modeled: they are exactly those, fat tails and all. They get
# > **block-shuffled**, not day by day — shuffling individual days would
# > destroy the volatility clustering Lab 9 measured, producing paths that
# > are too tame.

# %%
rng = np.random.default_rng(seed_for("lab-montecarlo"))
percorsi = bootstrap_traiettorie(r, n_traiettorie=PERCORSI, rng=rng, a_blocchi=BLOCCHI)

with avvio.figura("schermo"):
    fig, (sx, dx) = plt.subplots(1, 2, figsize=(12, 4.5))
    for k in range(120):
        sx.semilogy(percorsi[k], linewidth=0.5, alpha=0.4, color="#7A8CC7")
    sx.semilogy(reale, linewidth=2.5, color="black", label="la storia capitata")
    sx.set_ylabel("Capitale (scala log)")
    sx.set_xlabel("Giorni")
    sx.legend()

    cali = np.array([drawdown_massimo(p) for p in percorsi])
    dx.hist(cali * 100, bins=60)
    dx.axvline(drawdown_massimo(reale) * 100, linewidth=2.5, color="black")
    dx.set_xlabel("Calo massimo del percorso (%)")
    dx.set_ylabel(f"Su {PERCORSI} percorsi")
    plt.show()

esiti = distribuzione_esiti(percorsi)
print(f"{SERIE}: {len(r)} giorni ricampionati a blocchi di {BLOCCHI}\n")
print(f"la storia capitata:      {reale[-1]:8.2f}x   calo massimo {drawdown_massimo(reale):7.1%}")
print(f"mediana dei percorsi:    {esiti['mediana_finale']:8.2f}x   calo mediano "
      f"{esiti['drawdown_mediano']:7.1%}")
print(f"il 5% peggiore chiude a: {esiti['peggiore_5pct']:8.2f}x   con cali fino a "
      f"{esiti['drawdown_peggiore_5pct']:7.1%}")
print(f"il 5% migliore chiude a: {esiti['migliore_5pct']:8.2f}x")
print(f"percorsi che finiscono sotto il capitale iniziale: {esiti['prob_perdita']:.1%}")

# %% [markdown]
# Rileggi l'ultima riga. **Con gli stessi identici rendimenti**, una quota non
# trascurabile dei percorsi finisce in perdita. Non per una decisione sbagliata:
# per la combinazione in cui sono arrivate le cose.
#
# E nota il calo massimo: quello già visto **non è** il peggio possibile. È solo
# il peggio di una realizzazione, cioè di un campione di dimensione uno.
#
# ---
#
# > **EN** — Reread the last line. **With the exact same returns**, a
# > non-negligible share of paths ends at a loss. Not from a bad decision:
# > from the combination in which things arrived. And note the max drawdown:
# > the one already seen **is not** the worst possible. It's only the worst
# > of one realization, i.e. of a sample of size one.

# %% [markdown]
# ## 2. Dal grafico alla decisione: tre numeri e una soglia
#
# Metti la tua soglia e guarda se la posizione è troppo grande.
#
# ---
#
# > **EN** — *2. From the chart to the decision: three numbers and a
# > threshold.* Enter your threshold and see whether the position is too
# > big.

# %%
CAPITALE = 20_000.0     # PROVA / TRY: il tuo capitale reale
SOGLIA_PERDITA = 0.30   # ← oltre questo calo cambieresti comportamento
                        # PROVA / TRY: la tua soglia vera
QUOTA = 0.50            # ← quanta parte del capitale metti in questa posizione
                        # PROVA / TRY: la quota che stai davvero valutando

calo_5pct = float(np.percentile([drawdown_massimo(p) for p in percorsi], 5))
calo_atteso_sul_totale = abs(calo_5pct) * QUOTA

print(f"calo al 5esimo percentile dei percorsi possibili: {calo_5pct:.1%}")
print(f"mettendoci il {QUOTA:.0%} del capitale, sul totale fa: {calo_atteso_sul_totale:.1%}")
print(f"la tua soglia:                                     {SOGLIA_PERDITA:.1%}\n")
if calo_atteso_sul_totale > SOGLIA_PERDITA:
    quota_compatibile = SOGLIA_PERDITA / abs(calo_5pct)
    print(f"→ la posizione e' TROPPO GRANDE. Compatibile con la tua soglia: "
          f"{quota_compatibile:.1%} del capitale, cioe' "
          f"{quota_compatibile * CAPITALE:,.0f} euro.")
else:
    print("→ la posizione e' compatibile con la soglia che hai dichiarato.")

print("\nRegola: riduci la posizione finche' il calo al quinto percentile non sta "
      "sotto la tua soglia. Non serve altro, e questo unico passaggio fa piu' "
      "lavoro di qualunque affinamento della strategia.")

# %% [markdown]
# ## 3. Perché a blocchi e non giorno per giorno
#
# Il confronto che giustifica l'avvertenza tecnica.
#
# ---
#
# > **EN** — *3. Why in blocks and not day by day.* The comparison that
# > justifies the technical caveat.

# %%
def memoria_della_volatilita(percorso: np.ndarray) -> float:
    """Autocorrelazione a un giorno dell'ampiezza dei movimenti.

    E' la misura diretta del raggruppamento: se i giorni agitati arrivano in
    gruppo, l'ampiezza di oggi somiglia a quella di ieri.
    """
    variazioni = np.abs(percorso[1:] / percorso[:-1] - 1.0)
    return float(np.corrcoef(variazioni[:-1], variazioni[1:])[0, 1])


rng2 = np.random.default_rng(seed_for("lab-montecarlo-confronto"))
puntuale = bootstrap_traiettorie(r, n_traiettorie=400, rng=rng2, a_blocchi=None)
a_blocchi = bootstrap_traiettorie(r, n_traiettorie=400, rng=rng2, a_blocchi=BLOCCHI)

print(f"{'':>22s} {'memoria della vol.':>20s} {'calo mediano':>14s} {'5% peggiore':>13s}")
for nome, insieme in (("giorno per giorno", puntuale), (f"a blocchi di {BLOCCHI}", a_blocchi)):
    memoria = np.median([memoria_della_volatilita(p) for p in insieme])
    cali = np.array([drawdown_massimo(p) for p in insieme])
    print(f"{nome:>22s} {memoria:20.3f} {np.median(cali):14.1%} "
          f"{np.percentile(cali, 5):13.1%}")
print(f"{'la storia vera':>22s} {memoria_della_volatilita(reale):20.3f} "
      f"{drawdown_massimo(reale):14.1%} {'—':>13s}")

print("\nLa prima colonna e' quella che decide. Rimescolare giorno per giorno "
      "azzera la memoria della volatilita': si ottengono percorsi in cui i giorni "
      "agitati sono sparsi, che non e' come si comporta nessun mercato. I blocchi "
      "la conservano quasi tutta.")
print("\nSulle altre due colonne, invece, la differenza qui e' piccola — e va "
      "detto invece di nasconderlo. Su un orizzonte di nove anni il calo massimo "
      "e' dominato dall'accumulo, non dal raggruppamento. Il metodo a blocchi "
      "resta quello giusto, ma su QUESTE due misure non e' li' che si vede.")

# %% [markdown]
# ## 4. Quanti percorsi servono davvero
#
# Mille bastano per la mediana e sono al limite per il quinto percentile. Se il
# numero che ti serve è una coda — e in questo quaderno è sempre una coda —
# diecimila costano qualche secondo in più e danno un valore su cui appoggiare
# una decisione.
#
# ---
#
# > **EN** — *4. How many paths you really need.* A thousand are enough for
# > the median and are borderline for the fifth percentile. If the number
# > you need is a tail — and in this notebook it always is — ten thousand
# > cost a few extra seconds and give you a value to actually base a decision
# > on.

# %%
print(f"{'percorsi':>10s} {'mediana':>10s} {'5% peggiore':>14s}")
for n in (100, 500, 1000, 5000, 20000):
    rng3 = np.random.default_rng(seed_for(f"stabilita-{n}"))
    campione = bootstrap_traiettorie(r, n_traiettorie=n, rng=rng3, a_blocchi=BLOCCHI)
    finali = campione[:, -1]
    print(f"{n:10d} {np.median(finali):9.2f}x {np.percentile(finali, 5):13.2f}x")

print("\nLa colonna di sinistra si stabilizza subito, quella di destra molto piu' "
      "tardi. E' uno dei rari casi, in questo libro, in cui il problema si "
      "risolve semplicemente calcolando di piu'.")

# %% [markdown]
# ### Esercizi
#
# 1. Incolla i **tuoi** rendimenti al posto di `r` (una lista di variazioni
#    percentuali per operazione va benissimo) e leggi la frase del quinto
#    percentile. È la cosa più utile che questo quaderno possa darti.
# 2. Cambia `BLOCCHI` da 5 a 60. Il calo mediano cresce con la lunghezza dei
#    blocchi: la scelta è un parametro, non una verità, e va dichiarata.
# 3. Cambia `SERIE`. Su un asset più volatile la distanza fra mediana e quinto
#    percentile si allarga: è la misura di quanto poco la mediana descriva quel
#    mercato.
#
# ---
#
# > **EN** — *Exercises.*
# > 1. Paste **your own** returns in place of `r` (a list of percentage
# >    changes per trade works fine) and read the fifth-percentile sentence.
# >    It's the most useful thing this notebook can give you.
# > 2. Change `BLOCCHI` from 5 to 60. The median drawdown grows with block
# >    length: the choice is a parameter, not a truth, and must be stated.
# > 3. Change `SERIE`. On a more volatile asset the gap between the median
# >    and the fifth percentile widens: it's the measure of how little the
# >    median describes that market.
