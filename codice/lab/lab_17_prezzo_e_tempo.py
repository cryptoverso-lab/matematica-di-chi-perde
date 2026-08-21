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
# # Lab 17 — Le due coordinate di un movimento
#
# *Quaderno del capitolo «Prezzo e tempo» di **La matematica di chi perde**.*
#
# Un movimento di mercato si descrive con due numeri: **quanto** si è spostato il
# prezzo e **quanto a lungo** ci ha messo. Il volume è la terza colonna che ogni
# piattaforma mostra. La domanda del capitolo è se sia una terza coordinata o la
# conseguenza delle prime due e del calendario.
#
# Qui rifai la misura sull'asset che scegli, e soprattutto puoi provare a farla
# cadere: cambia la soglia, cambia la finestra, cambia il mercato.
#
# Nulla di quello che c'è qui dentro è un'indicazione operativa. La
# segmentazione riconosce un estremo **dopo** l'inversione: descrive movimenti
# finiti, non ne annuncia uno che comincia.
#
# ---
#
# > **EN** — *Lab 17 — The two coordinates of a move.* Notebook for the
# > chapter "Price and time". A market move is described by two numbers:
# > **how much** the price moved and **how long** it took. Volume is the
# > third column every platform shows. The chapter's question is whether
# > it's a third coordinate or a consequence of the first two plus the
# > calendar. Here you redo the measurement on the asset of your choice, and
# > above all you can try to break it: change the threshold, change the
# > window, change the market. Nothing in here is trading advice. The
# > segmentation recognizes an extreme **after** the reversal: it describes
# > finished moves, it does not announce one beginning.

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

avvio.prepara(["btcusdt", "ethusdt", "solusdt", "ftsemib", "eni", "enel",
               "intesa", "generali"])

# %%
import matplotlib.pyplot as plt
import numpy as np

from cvbook.ciclica import (
    decomposizione,
    effetto_scadenza,
    movimenti,
    r_quadro,
    tavolo,
)
from cvbook.dati import carica

SERIE = "btcusdt"   # ← "btcusdt", "ethusdt", "solusdt", "ftsemib", "eni", "enel", "intesa", "generali"
SOGLIA = 0.05       # ← quanto deve rientrare il prezzo perché un estremo sia definitivo
CRIPTO = SERIE.endswith("usdt")

df = carica(SERIE).sort("data")
prezzi = df["chiusura"].to_numpy()
volumi = df["volume"].to_numpy()

# %% [markdown]
# ## 1. Dove sono gli estremi
#
# Una regola sola, dichiarata prima: un estremo diventa definitivo quando il
# prezzo si è allontanato di `SOGLIA` nella direzione opposta.
#
# ---
#
# > **EN** — *1. Where the extremes are.* One single rule, declared upfront:
# > an extreme becomes final when price has moved `SOGLIA` away in the
# > opposite direction.

# %%
tratti = movimenti(prezzi, SOGLIA)
estremi = sorted({i for coppia in tratti for i in coppia})
print(f"{len(tratti)} movimenti su {len(prezzi)} barre")

with avvio.figura():
    fig, ax = plt.subplots(figsize=(9, 4))
    fetta = slice(estremi[-14], len(prezzi))
    ax.plot(df["data"].to_numpy()[fetta], prezzi[fetta], linewidth=0.9)
    dentro = [i for i in estremi if i >= estremi[-14]]
    ax.plot(df["data"].to_numpy()[dentro], prezzi[dentro], marker="o", linewidth=1.4)
    ax.set_title(f"{SERIE}: gli ultimi movimenti riconosciuti a soglia {SOGLIA:.0%}")
    plt.show()

# %% [markdown]
# ## 2. Quanto spiegano prezzo, tempo e volume
#
# Il bersaglio è l'ampiezza del movimento. I tre blocchi sono misurati sulla
# **stessa finestra** e con lo **stesso trattamento**: è ciò che rende leale il
# confronto. La ripartizione è quella di Shapley, cioè la media del contributo
# su tutti gli ordini di inserimento possibili — con variabili correlate,
# «quanto spiega questa» dipende dall'ordine, e la media è l'unica risposta che
# non lo sceglie a piacere.
#
# ---
#
# > **EN** — *2. How much price, time and volume explain.* The target is
# > the size of the move. The three blocks are measured on the **same
# > window** and with the **same treatment**: that's what makes the
# > comparison fair. The split is Shapley's, i.e. the average contribution
# > over every possible insertion order — with correlated variables, "how
# > much this explains" depends on the order, and the average is the only
# > answer that doesn't pick one arbitrarily.

# %%
t = tavolo(prezzi, volumi, SOGLIA)
d = decomposizione(t)

print(f"movimenti misurati       {d['movimenti']:.0f}")
print(f"prezzo (quota Shapley)   {d['prezzo']:.1%}")
print(f"tempo  (quota Shapley)   {d['tempo']:.1%}")
print(f"volume (quota Shapley)   {d['volume']:.1%}")
print(f"tutte e tre insieme      {d['totale']:.1%}")
print(f"solo prezzo e tempo      {d['prezzo_e_tempo']:.1%}")
print(f"il volume aggiunge       {d['guadagno_volume']:+.1%} di R quadro")

# %% [markdown]
# ## 3. Il primo esercizio: prova a far cadere il risultato
#
# La soglia dello zigzag è un parametro, e un parametro è sempre sospetto —
# vedi il capitolo sull'ottimizzare. Fallo variare e guarda se la conclusione
# si muove. Se si muovesse, il capitolo sarebbe da riscrivere.
#
# ---
#
# > **EN** — *3. First exercise: try to break the result.* The zigzag
# > threshold is a parameter, and a parameter is always suspect — see the
# > chapter on optimizing. Vary it and see whether the conclusion moves. If
# > it did, the chapter would need rewriting.

# %%
print(f"{'soglia':>7s} {'movimenti':>10s} {'prezzo':>8s} {'tempo':>8s} {'volume':>8s}")
for s in (0.02, 0.03, 0.05, 0.08, 0.10, 0.15):
    ts = tavolo(prezzi, volumi, s)
    if len(ts) < 40:
        print(f"{s:7.0%} {len(ts):10d}  (troppo pochi movimenti)")
        continue
    ds = decomposizione(ts)
    quota = ds["prezzo"] + ds["tempo"] + ds["volume"]
    print(f"{s:7.0%} {ds['movimenti']:10.0f} {ds['prezzo'] / quota:8.1%} "
          f"{ds['tempo'] / quota:8.1%} {ds['volume'] / quota:8.1%}")

# %% [markdown]
# ## 4. Il secondo esercizio: togli il legame e guardalo sparire
#
# Rimescola la colonna del volume fra i movimenti. Il volume resta lo stesso
# insieme di numeri, ma non appartiene più al movimento accanto a cui sta. Se la
# sua quota fosse rumore, non cambierebbe quasi nulla. Vedere una struttura
# sparire quando la si distrugge di proposito è il modo più diretto di
# convincersi che c'era.
#
# ---
#
# > **EN** — *4. Second exercise: remove the link and watch it vanish.*
# > Shuffle the volume column across moves. Volume stays the same set of
# > numbers, but no longer belongs to the move it sits next to. If its share
# > were noise, almost nothing would change. Watching a structure disappear
# > when you destroy it on purpose is the most direct way to convince
# > yourself it was there.

# %%
rng = np.random.default_rng(0)
y = np.log(t.ampiezza)
prezzo, tempo = np.log(t.prezzo), np.log(t.durata)
volume = np.log(t.volume)

vero = r_quadro(y, [prezzo, tempo, volume]) - r_quadro(y, [prezzo, tempo])
finti = [
    r_quadro(y, [prezzo, tempo, rng.permutation(volume)]) - r_quadro(y, [prezzo, tempo])
    for _ in range(500)
]
print(f"il volume vero aggiunge      {vero:+.2%}")
print(f"un volume rimescolato        {np.mean(finti):+.2%} in media, "
      f"{np.percentile(finti, 95):+.2%} nel 5% dei casi migliori")

# %% [markdown]
# ## 5. Da dove viene il volume: il calendario
#
# I derivati non scadono quando capita. Sull'IDEM di Borsa Italiana indici e
# azioni scadono il **terzo venerdì** del mese; sui future e sulle opzioni in
# criptovaluta la scadenza mensile è l'**ultimo venerdì**. Sono date pubbliche,
# note con anni di anticipo, che non dicono niente su dove andrà il prezzo.
#
# ---
#
# > **EN** — *5. Where volume comes from: the calendar.* Derivatives don't
# > expire whenever. On Borsa Italiana's IDEM, indices and stocks expire the
# > **third Friday** of the month; on crypto futures and options, the
# > monthly expiry is the **last Friday**. These are public dates, known
# > years in advance, that say nothing about where price will go.

# %%
e = effetto_scadenza(df["data"].to_list(), volumi, cripto=CRIPTO)
quale = "ultimo venerdì" if CRIPTO else "terzo venerdì"
print(f"{SERIE}: {e['scadenze']} giorni di scadenza ({quale})")
print(f"volume mediano in scadenza   {e['mediana_scadenza']:.3f}")
print(f"volume mediano negli altri   {e['mediana_normale']:.3f}")
print(f"eccesso                      {e['eccesso']:+.1%}")

# %% [markdown]
# ## 6. Il terzo esercizio: il test placebo sulla scadenza
#
# Sposta la data di scadenza di una o due settimane. Restando di venerdì il
# confronto non cambia natura: cambia solo il fatto che quel venerdì non era
# una scadenza. Se l'eccesso di volume viene davvero dalla scadenza, sulle date
# finte deve sparire. Se restasse, staremmo misurando qualcos'altro.
#
# Su ENI il salto è netto: la data vera sta a +39%, le finte fra il −15% e il
# +3%. Su Bitcoin la data vera sta a +5% e le finte oscillano fra −5% e +3%:
# cioè il +5% è dentro il rumore delle date sbagliate, e la conclusione onesta
# è che lì la scadenza non si vede.
#
# ---
#
# > **EN** — *6. Third exercise: the placebo test on the expiry.* Shift the
# > expiry date by one or two weeks. Staying on a Friday, the comparison
# > doesn't change nature — only the fact that that Friday wasn't an expiry.
# > If the volume excess really comes from the expiry, it must vanish on the
# > fake dates. If it stayed, we'd be measuring something else. On ENI the
# > jump is clear: the real date sits at +39%, the fake ones between −15%
# > and +3%. On Bitcoin the real date sits at +5% and the fake ones swing
# > between −5% and +3%: i.e. the +5% is within the noise of the wrong
# > dates, and the honest conclusion is that there the expiry effect isn't
# > visible.

# %%
import datetime as dt

date = df["data"].to_list()
for spostamento in (-14, -7, 0, 7, 14):
    finte = [g + dt.timedelta(days=spostamento) for g in date]
    e2 = effetto_scadenza(finte, volumi, cripto=CRIPTO)
    etichetta = "vera" if spostamento == 0 else f"{spostamento:+d} giorni"
    print(f"scadenza {etichetta:>10s}: eccesso {e2['eccesso']:+7.1%}")

# %% [markdown]
# ## Cosa portarti via
#
# 1. Un movimento ha due coordinate, e la seconda — il tempo — di solito pesa
#    più della prima.
# 2. Il volume ha avuto le stesse identiche condizioni delle altre due colonne e
#    non è entrato. Non perché sia inutile: perché quello che dice, prezzo e
#    tempo lo dicevano già.
# 3. Buona parte di ciò che resta del volume è calendario. Il calendario è una
#    forma del tempo, non una terza dimensione.
#
# ---
#
# > **EN** — *Takeaways.*
# > 1. A move has two coordinates, and the second — time — usually weighs
# >    more than the first.
# > 2. Volume had the exact same conditions as the other two columns and
# >    didn't make the cut. Not because it's useless: because what it says,
# >    price and time already said.
# > 3. Most of what's left of volume is calendar. The calendar is a form of
# >    time, not a third dimension.
