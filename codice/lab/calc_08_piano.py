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
# *Quaderno del capitolo «Il tuo piano, scritto» di **La matematica di chi perde**.*
#
# Compila le sette voci e ottieni un documento da salvare, con i numeri già
# calcolati — incluso il rischio complessivo e quanto puoi tenere presso un
# singolo intermediario.
#
# E c'è il registro pronto da compilare, con i cinque campi e le statistiche che
# si aggiornano da sole. Compresa la colonna che nessuno tiene: **quanto tempo
# passa in media fra il momento in cui apri e quello in cui chiudi in utile
# rispetto a quando chiudi in perdita.**
#
# ---
#
# > **EN** — *Calculator 8 — Your plan, written down.* Notebook for the
# > chapter "Your plan, written down". Fill in the seven items and get a
# > document to save, with the numbers already computed — including overall
# > risk and how much you can hold at a single broker. There is also a
# > ready-to-fill trade log, with five fields and statistics that update on
# > their own — including the column nobody keeps: **how long, on average,
# > it takes between opening a position and closing it at a profit versus
# > closing it at a loss.** The example content of the plan and the log stays
# > in Italian: it is a document meant to be rewritten with your own words,
# > not a label to translate.

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
import numpy as np
import polars as pl

from cvbook.lingua import t

# %% [markdown]
# ## 1. Le sette voci
#
# ---
#
# > **EN** — *1. The seven items.*

# %%
# PROVA / TRY: l'intero dizionario qui sotto è da riscrivere con il TUO piano
# — è il punto del quaderno, non un'eccezione alla regola.
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
#
# ---
#
# > **EN** — *2. The numbers the plan must contain, calculated.*

# %%
capitale = PIANO["capitale"]
rischio = PIANO["rischio_per_operazione"]
n = PIANO["posizioni_massime_aperte"]
rho = PIANO["correlazione_attesa_fra_posizioni"]

rischio_euro = capitale * rischio
varianza = n * rischio**2 * (1 + (n - 1) * rho)
rischio_complessivo = float(np.sqrt(varianza))
per_intermediario = capitale * PIANO["quota_massima_per_intermediario"]

print(t(f"capitale:                         {capitale:12,.0f} euro",
        f"capital:                          {capitale:12,.0f} euros"))
print(t(f"rischio per operazione:           {rischio_euro:12,.0f} euro ({rischio:.1%})",
        f"risk per trade:                   {rischio_euro:12,.0f} euros ({rischio:.1%})"))
print(t(f"posizioni massime aperte:         {n:12d}", f"maximum open positions:           {n:12d}"))
print(t(f"correlazione attesa:              {rho:12.2f}", f"expected correlation:             {rho:12.2f}"))
print(t(f"→ rischio complessivo di portafoglio: {rischio_complessivo:8.1%} "
        f"({capitale * rischio_complessivo:,.0f} euro)",
        f"→ overall portfolio risk: {rischio_complessivo:8.1%} "
        f"({capitale * rischio_complessivo:,.0f} euros)"))
print(t(f"→ massimo per intermediario:          {per_intermediario:8,.0f} euro "
        f"({PIANO['quota_massima_per_intermediario']:.0%})",
        f"→ maximum per broker:                 {per_intermediario:8,.0f} euros "
        f"({PIANO['quota_massima_per_intermediario']:.0%})"))

if not PIANO["puo_sparire_senza_conseguenze"]:
    print(t("\n*** ATTENZIONE: hai dichiarato che perdere questo capitale avrebbe "
            "conseguenze sulla tua vita. Questa voce viene PRIMA di ogni altra: il "
            "capitale e' troppo alto. ***",
            "\n*** WARNING: you stated that losing this capital would have "
            "consequences for your life. This item comes BEFORE every other one: "
            "the capital is too high. ***"))

# %% [markdown]
# ## 3. Il documento da salvare
#
# ---
#
# > **EN** — *3. The document to save.* The template below stays in Italian
# > by design: it is the document you rewrite in your own words, not a
# > user-interface label.

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
print(t("(salvato in piano.txt)", "(saved to piano.txt)"))

# %% [markdown]
# ## 4. Il registro delle operazioni
#
# Cinque campi. L'ultimo — *cosa mi aspetto* — è quello che conta, e va scritto
# **prima**.
#
# ---
#
# > **EN** — *4. The trade log.* Five fields. The last one — *what I expect*
# > — is the one that matters, and must be written **before**.

# %%
# PROVA / TRY: sostituisci l'intero REGISTRO d'esempio con le tue ultime
# operazioni reali — vedi l'esercizio 1
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
#
# ---
#
# > **EN** — *5. The statistics that update on their own.*

# %%
righe = REGISTRO.with_columns(
    (pl.col("data_chiusura").str.to_date() - pl.col("data_apertura").str.to_date())
    .dt.total_days().alias("giorni"),
    (pl.col("risultato_pct") > 0).alias("in_utile"),
)

utili = righe.filter(pl.col("in_utile"))
perdite = righe.filter(~pl.col("in_utile"))

print(t(f"operazioni:                 {righe.height}", f"trades:                     {righe.height}"))
print(t(f"chiuse in utile:            {utili.height} ({utili.height / righe.height:.0%})",
        f"closed at a profit:         {utili.height} ({utili.height / righe.height:.0%})"))
print(t(f"rischio medio dichiarato:   {righe['rischio_pct'].mean():.2%}",
        f"average declared risk:      {righe['rischio_pct'].mean():.2%}"))
print(t(f"rischio massimo usato:      {righe['rischio_pct'].max():.2%}"
        f"   (nel piano: {rischio:.2%})",
        f"maximum risk used:          {righe['rischio_pct'].max():.2%}"
        f"   (in the plan: {rischio:.2%})"))

if righe["rischio_pct"].max() > rischio + 1e-9:
    fuori = righe.filter(pl.col("rischio_pct") > rischio)
    print(t(f"\n*** {fuori.height} operazioni hanno superato il rischio dichiarato nel "
            f"piano. Guarda la colonna 'perche': quasi sempre non e' una regola. ***",
            f"\n*** {fuori.height} trades exceeded the risk stated in the plan. "
            f"Look at the 'perche' (why) column: it's almost never a rule. ***"))

if utili.height and perdite.height:
    print(t(f"\ngiorni medi tenendo una posizione in utile:   {utili['giorni'].mean():6.1f}",
            f"\naverage days holding a winning position:      {utili['giorni'].mean():6.1f}"))
    print(t(f"giorni medi tenendo una posizione in perdita: {perdite['giorni'].mean():6.1f}",
            f"average days holding a losing position:       {perdite['giorni'].mean():6.1f}"))
    if perdite["giorni"].mean() > utili["giorni"].mean():
        print(t("\n→ Tieni le perdite piu' a lungo degli utili. E' il capitolo sul "
                "cervello, misurato su di te: chiudere in rosso trasforma una perdita "
                "potenziale in una definitiva, e il tuo sistema di valutazione lo "
                "evita finche' puo'.",
                "\n→ You hold losses longer than profits. It's the chapter on the "
                "brain, measured on yourself: closing in the red turns a potential "
                "loss into a definitive one, and your evaluation system avoids that "
                "as long as it can."))

# %% [markdown]
# ## 6. Il test del piano: fallo girare all'indietro
#
# Prendi il piano appena scritto e applicalo alle tue ultime operazioni reali,
# una per una, come se fosse già in vigore.
#
# ---
#
# > **EN** — *6. Testing the plan: run it backwards.* Take the plan you just
# > wrote and apply it to your last real trades, one by one, as if it were
# > already in force.

# %%
permesse = righe.filter(
    (pl.col("rischio_pct") <= rischio + 1e-9) & (pl.col("perche") == "rottura")
)
print(t(f"operazioni che il piano AVREBBE PERMESSO: {permesse.height} su {righe.height} "
        f"({permesse.height / righe.height:.0%})",
        f"trades the plan WOULD HAVE ALLOWED: {permesse.height} out of {righe.height} "
        f"({permesse.height / righe.height:.0%})"))

non_nel_piano = righe.filter(pl.col("perche") != "rottura")
if non_nel_piano.height:
    print(t(f"\nchiuse o aperte per motivi non previsti dal piano: {non_nel_piano.height}",
            f"\nopened or closed for reasons not covered by the plan: {non_nel_piano.height}"))
    for riga in non_nel_piano.iter_rows(named=True):
        print(f"  {riga['data_apertura']}  «{riga['perche']}»  "
              + t(f"→ risultato {riga['risultato_pct']:+.1%}", f"→ result {riga['risultato_pct']:+.1%}"))
    print(t("\nOgni voce di questa lista e' un pezzo di regola che ti manca. La cosa "
            "da fare non e' vergognarsene: e' AGGIUNGERLA al piano, formulata in "
            "modo che la prossima volta sia una decisione presa prima.",
            "\nEvery entry in this list is a piece of rule you're missing. The thing "
            "to do isn't to feel bad about it: it's to ADD IT to the plan, worded so "
            "that next time it's a decision made in advance."))

print(t("\nLa trappola: l'esercizio serve a misurare il piano, NON a rifarlo finche' "
        "non approva quello che hai gia' fatto. Se lo usi per ammorbidire le regole "
        "fino a giustificare ogni operazione passata, hai appena eseguito su te "
        "stesso il capitolo sui modi in cui mente il metodo.",
        "\nThe trap: the exercise is meant to measure the plan, NOT to rewrite it "
        "until it approves what you already did. If you use it to soften the rules "
        "until every past trade is justified, you've just run on yourself the "
        "chapter on the ways a method lies."))

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
#
# ---
#
# > **EN** — *Exercises.*
# > 1. Replace the sample log with your **own** last fifty trades. Seven
# >    columns are enough.
# > 2. Look first at the maximum-risk-used row. In my experience, the largest
# >    positions aren't the ones with the best expectancy: they're the ones
# >    where you were most convinced.
# > 3. Reread item 6 of the plan — *what would make me change my mind* — and
# >    ask yourself whether it contains a number. If it doesn't, it's not a
# >    plan item: it's a wish.
