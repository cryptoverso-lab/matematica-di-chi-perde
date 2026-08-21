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
# # Calcolatore 8 — Il tuo piano, scritto
#
# *Quaderno del capitolo «Il tuo piano, scritto» di **Non Fidarti di Me**.*
#
# Compila le sette voci e ottieni un documento da salvare, con i numeri già
# calcolati — incluso il rischio complessivo e quanto puoi tenere presso un
# singolo intermediario.
#
# E c'è il registro pronto da compilare, con i cinque campi e le statistiche che
# si aggiornano da sole. Compresa la colonna che nessuno tiene: **quanto tempo
# passa in media fra il momento in cui apri e quello in cui chiudi in utile
# rispetto a quando chiudi in perdita.**

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
import numpy as np
import polars as pl

# %% [markdown]
# ## 1. Le sette voci

# %%
PIANO = {
    "perche_sono_qui": "far crescere una parte del patrimonio su un orizzonte di 10 anni",
    "capitale": 20_000.0,
    "puo_sparire_senza_conseguenze": True,   # rispondi onestamente
    "rischio_per_operazione": 0.01,          # fra 0,5% e 2%
    "posizioni_massime_aperte": 5,
    "correlazione_attesa_fra_posizioni": 0.7,
    "quota_massima_per_intermediario": 0.20,
    "regola_ingresso": "rottura del massimo a 20 giorni, verificata sul mercato scelto",
    "regola_uscita": "chiusura sotto il minimo a 20 giorni, oppure allo stop dichiarato",
    "cosa_mi_farebbe_cambiare_idea": (
        "un calo superiore al peggiore osservato in verifica, oppure 200 operazioni "
        "con risultato sotto il metro del caso"
    ),
    "data_revisione": "trimestrale, il primo giorno del trimestre",
}

# %% [markdown]
# ## 2. I numeri che il piano deve contenere, calcolati

# %%
capitale = PIANO["capitale"]
rischio = PIANO["rischio_per_operazione"]
n = PIANO["posizioni_massime_aperte"]
rho = PIANO["correlazione_attesa_fra_posizioni"]

rischio_euro = capitale * rischio
varianza = n * rischio**2 * (1 + (n - 1) * rho)
rischio_complessivo = float(np.sqrt(varianza))
per_intermediario = capitale * PIANO["quota_massima_per_intermediario"]

print(f"capitale:                         {capitale:12,.0f} euro")
print(f"rischio per operazione:           {rischio_euro:12,.0f} euro ({rischio:.1%})")
print(f"posizioni massime aperte:         {n:12d}")
print(f"correlazione attesa:              {rho:12.2f}")
print(f"→ rischio complessivo di portafoglio: {rischio_complessivo:8.1%} "
      f"({capitale * rischio_complessivo:,.0f} euro)")
print(f"→ massimo per intermediario:          {per_intermediario:8,.0f} euro "
      f"({PIANO['quota_massima_per_intermediario']:.0%})")

if not PIANO["puo_sparire_senza_conseguenze"]:
    print("\n*** ATTENZIONE: hai dichiarato che perdere questo capitale avrebbe "
          "conseguenze sulla tua vita. Questa voce viene PRIMA di ogni altra: il "
          "capitale e' troppo alto. ***")

# %% [markdown]
# ## 3. Il documento da salvare

# %%
verdetto_capitale = (
    "NO" if PIANO["puo_sparire_senza_conseguenze"]
    else "SI — allora il capitale e' troppo alto, e questa voce viene prima di tutte"
)

DOCUMENTO = f"""\
PIANO OPERATIVO — versione del 2026-08-16
(non sovrascrivere le versioni precedenti: aggiungerle in coda, con la data)

1. PERCHE' SONO QUI
   {PIANO['perche_sono_qui']}

2. CAPITALE, E QUANTO PUO' SPARIRE
   capitale destinato:  {capitale:,.0f} euro
   se andasse a zero domani, la mia vita cambierebbe? {verdetto_capitale}

3. RISCHIO PER OPERAZIONE
   {rischio:.2%} del capitale, cioe' {rischio_euro:,.0f} euro. Fisso.
   Non dipende dall'occasione: dipendere dall'occasione significa rischiare di
   piu' quando si e' piu' convinti, e la convinzione non e' correlata al risultato.

4. RISCHIO COMPLESSIVO
   massimo {n} posizioni aperte
   rischio complessivo atteso: {rischio_complessivo:.1%} ({capitale * rischio_complessivo:,.0f} euro)
   massimo presso un singolo intermediario: {per_intermediario:,.0f} euro \
({PIANO['quota_massima_per_intermediario']:.0%})

5. REGOLE DI INGRESSO E USCITA
   ingresso: {PIANO['regola_ingresso']}
   uscita:   {PIANO['regola_uscita']}
   test: se do queste due righe a un'altra persona e le applica ai dati di ieri,
   ottiene la mia stessa decisione?

6. COSA MI FAREBBE CAMBIARE IDEA
   {PIANO['cosa_mi_farebbe_cambiare_idea']}

7. QUANDO RIVEDO IL PIANO
   {PIANO['data_revisione']}
   Fuori da quelle date il piano non si tocca.

REGOLA SOPRA TUTTE
   Le modifiche al piano entrano in vigore dalla PROSSIMA operazione, mai da
   quella in corso.
"""

print(DOCUMENTO)

with open("piano.txt", "w", encoding="utf-8") as f:
    f.write(DOCUMENTO)
print("(salvato in piano.txt)")

# %% [markdown]
# ## 4. Il registro delle operazioni
#
# Cinque campi. L'ultimo — *cosa mi aspetto* — è quello che conta, e va scritto
# **prima**.

# %%
REGISTRO = pl.DataFrame({
    "data_apertura": ["2026-01-08", "2026-01-22", "2026-02-11", "2026-03-03", "2026-03-19"],
    "data_chiusura": ["2026-01-12", "2026-02-28", "2026-02-13", "2026-04-30", "2026-03-24"],
    "cosa": ["asset A", "asset A", "asset B", "asset A", "asset B"],
    "rischio_pct": [0.01, 0.01, 0.01, 0.02, 0.01],
    "perche": ["rottura", "rottura", "rottura", "convinzione", "rottura"],
    "cosa_mi_aspetto": ["continuazione", "continuazione", "continuazione",
                        "rimbalzo", "continuazione"],
    "risultato_pct": [0.03, -0.01, 0.05, -0.02, 0.02],
})

print(REGISTRO)

# %% [markdown]
# ## 5. Le statistiche che si aggiornano da sole

# %%
righe = REGISTRO.with_columns(
    (pl.col("data_chiusura").str.to_date() - pl.col("data_apertura").str.to_date())
    .dt.total_days().alias("giorni"),
    (pl.col("risultato_pct") > 0).alias("in_utile"),
)

utili = righe.filter(pl.col("in_utile"))
perdite = righe.filter(~pl.col("in_utile"))

print(f"operazioni:                 {righe.height}")
print(f"chiuse in utile:            {utili.height} ({utili.height / righe.height:.0%})")
print(f"rischio medio dichiarato:   {righe['rischio_pct'].mean():.2%}")
print(f"rischio massimo usato:      {righe['rischio_pct'].max():.2%}"
      f"   (nel piano: {rischio:.2%})")

if righe["rischio_pct"].max() > rischio + 1e-9:
    fuori = righe.filter(pl.col("rischio_pct") > rischio)
    print(f"\n*** {fuori.height} operazioni hanno superato il rischio dichiarato nel "
          f"piano. Guarda la colonna 'perche': quasi sempre non e' una regola. ***")

if utili.height and perdite.height:
    print(f"\ngiorni medi tenendo una posizione in utile:   {utili['giorni'].mean():6.1f}")
    print(f"giorni medi tenendo una posizione in perdita: {perdite['giorni'].mean():6.1f}")
    if perdite["giorni"].mean() > utili["giorni"].mean():
        print("\n→ Tieni le perdite piu' a lungo degli utili. E' il capitolo sul "
              "cervello, misurato su di te: chiudere in rosso trasforma una perdita "
              "potenziale in una definitiva, e il tuo sistema di valutazione lo "
              "evita finche' puo'.")

# %% [markdown]
# ## 6. Il test del piano: fallo girare all'indietro
#
# Prendi il piano appena scritto e applicalo alle tue ultime operazioni reali,
# una per una, come se fosse già in vigore.

# %%
permesse = righe.filter(
    (pl.col("rischio_pct") <= rischio + 1e-9) & (pl.col("perche") == "rottura")
)
print(f"operazioni che il piano AVREBBE PERMESSO: {permesse.height} su {righe.height} "
      f"({permesse.height / righe.height:.0%})")

non_nel_piano = righe.filter(pl.col("perche") != "rottura")
if non_nel_piano.height:
    print(f"\nchiuse o aperte per motivi non previsti dal piano: {non_nel_piano.height}")
    for riga in non_nel_piano.iter_rows(named=True):
        print(f"  {riga['data_apertura']}  «{riga['perche']}»  "
              f"→ risultato {riga['risultato_pct']:+.1%}")
    print("\nOgni voce di questa lista e' un pezzo di regola che ti manca. La cosa "
          "da fare non e' vergognarsene: e' AGGIUNGERLA al piano, formulata in "
          "modo che la prossima volta sia una decisione presa prima.")

print("\nLa trappola: l'esercizio serve a misurare il piano, NON a rifarlo finche' "
      "non approva quello che hai gia' fatto. Se lo usi per ammorbidire le regole "
      "fino a giustificare ogni operazione passata, hai appena eseguito su te "
      "stesso il capitolo sui modi in cui mente il metodo.")

# %% [markdown]
# ### Esercizi
#
# 1. Sostituisci il registro d'esempio con le **tue** ultime cinquanta operazioni.
#    Bastano le sette colonne.
# 2. Guarda per prima la riga del rischio massimo usato. Nella mia esperienza, le
#    posizioni più grandi non sono quelle con l'aspettativa migliore: sono quelle
#    in cui si era più convinti.
# 3. Rileggi la voce 6 del piano — *cosa mi farebbe cambiare idea* — e chiediti se
#    contiene un numero. Se non lo contiene, non è una voce del piano: è un
#    desiderio.
