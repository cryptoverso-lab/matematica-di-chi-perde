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
# # Calcolatore 2 — I costi, sui tuoi numeri
#
# *Quaderno del capitolo «I costi che ti mangiano vivo» di **Non Fidarti di Me**.*
#
# Tre risposte, con i tuoi parametri: quanto ti costano i costi in un anno, quale
# rendimento lordo ti serve **solo per pareggiarli**, e quanto ti sarebbe rimasto
# operando a quella frequenza su una serie reale.
#
# Il numero che quasi nessuno conosce è il secondo.

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

avvio.prepara(["btcusdt", "ethusdt", "solusdt"])

# %%
import matplotlib.pyplot as plt
import numpy as np

from cvbook.dati import carica
from cvbook.metriche import equity, rendimenti

# %% [markdown]
# ## 1. I tuoi tre numeri
#
# Se non conosci il tuo costo per giro, il capitolo spiega come misurarlo: prendi
# dieci operazioni chiuse, confronta il prezzo che avevi visto con quello
# ottenuto, somma le commissioni. Quasi tutti scoprono di stare più vicini allo
# 0,25% che allo 0,06%.

# %%
CAPITALE = 10_000.0   # ← il capitale impegnato, in euro
COSTO_GIRO = 0.0012   # ← costo tutto compreso di un giro completo (0,12%)
OPERAZIONI_ANNO = 52  # ← quanti giri completi fai in un anno

speso = CAPITALE * COSTO_GIRO * OPERAZIONI_ANNO
pareggio = (1 + COSTO_GIRO) ** OPERAZIONI_ANNO - 1

print(f"in un anno paghi:        {speso:10,.2f} euro")
print(f"cioe' il:                {speso / CAPITALE:10.2%} del capitale")
print(f"rendimento lordo per     ")
print(f"NON perdere nulla:       {pareggio:10.2%}")

# %% [markdown]
# ## 2. La soglia, al variare della frequenza
#
# La riga tratteggiata è, come nel libro, il rendimento medio storico di lungo
# periodo di un indice azionario ampio. Tutto ciò che sta sopra è territorio in
# cui il costo si mangia più di quanto un mercato intero abbia mai reso.

# %%
FREQUENZE = np.array([12, 26, 52, 125, 250, 500])
COSTI = [0.0006, 0.0012, 0.0025]

with avvio.figura("schermo"):
    fig, ax = plt.subplots(figsize=(9, 5))
    for c in COSTI:
        soglia = ((1 + c) ** FREQUENZE - 1) * 100
        ax.plot(FREQUENZE, soglia, marker="o", label=f"costo {c:.2%} a giro")

    # Riferimento in grigio, con l'etichetta in legenda invece che sul grafico:
    # una scritta appoggiata sulle curve e' il modo piu' rapido di rendere
    # illeggibile una figura che dice una cosa semplice.
    ax.axhline(
        10,
        linestyle="--",
        linewidth=1.2,
        color="#8C8C8C",
        zorder=0,
        label="~10% annuo: media storica di un indice azionario",
    )

    ax.set_xscale("log")
    ax.set_xticks(FREQUENZE)
    ax.set_xticklabels([str(f) for f in FREQUENZE])
    ax.set_xlabel("Operazioni complete all'anno")
    ax.set_ylabel("Rendimento lordo necessario per pareggiare (%)")
    ax.set_ylim(0, None)
    ax.legend(loc="upper left")
    plt.show()

for c in COSTI:
    print(f"costo {c:.2%}: " + "  ".join(
        f"{f}op→{((1 + c) ** f - 1):.1%}" for f in FREQUENZE))

# %% [markdown]
# ## 3. Cosa sarebbe rimasto, su dati reali
#
# Stessa esposizione, stesso asset, stesso periodo. L'unica cosa che cambia è
# **quante volte** si chiude e si riapre la stessa posizione. Nessuna previsione
# diversa, nessuna decisione diversa.

# %%
SERIE = "btcusdt"  # ← prova anche "ethusdt" o "solusdt"

r = rendimenti(carica(SERIE).sort("data")["chiusura"].to_numpy())
n = len(r)


def con_frequenza(rend: np.ndarray, ogni_n_giorni: int | None, costo: float) -> float:
    """Capitale finale restando sempre investiti ma rientrando ogni N giorni."""
    operazioni = np.zeros(len(rend))
    if ogni_n_giorni is not None:
        operazioni[::ogni_n_giorni] = 1.0
    return float(equity(rend - operazioni * costo)[-1])


print(f"{SERIE} · {n} giorni\n")
print(f"{'frequenza':>22s} " + " ".join(f"{c:>10.2%}" for c in COSTI))
for ogni, etichetta in [(None, "mai (compra e tieni)"), (365, "una volta l'anno"),
                        (30, "una volta al mese"), (7, "una volta a settimana"),
                        (1, "ogni giorno")]:
    valori = " ".join(f"{con_frequenza(r, ogni, c):10.3f}x" for c in COSTI)
    print(f"{etichetta:>22s} {valori}")

# %% [markdown]
# ### Esercizi
#
# 1. **Metti la tua frequenza reale** in `OPERAZIONI_ANNO`: contale sull'estratto
#    conto dell'ultimo anno, non a memoria. Poi confronta la soglia di pareggio
#    con quello che pensavi di poter ottenere.
# 2. Raddoppia `COSTO_GIRO` e riesegui tutto. Se una strategia sopravvive solo al
#    costo ottimistico, quel vantaggio appartiene a chi ha costi bassi, non a te.
# 3. Nella terza cella cambia serie. La colonna del compra-e-tieni cambia molto;
#    il **rapporto** fra le righe quasi per niente: il costo della frequenza non
#    dipende da quale asset hai scelto.
