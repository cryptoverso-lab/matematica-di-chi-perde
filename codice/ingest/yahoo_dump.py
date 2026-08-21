"""Ingest delle serie azionarie e valutarie da Yahoo Finance.

Perché servono: fino a questo snapshot il libro dimostrava tutto su cinque
serie cripto, e il @sec-cap-12 mostra da solo che quelle cinque valgono poco
più di una scommessa. Un indice, quattro blue chip italiane di settori diversi
e un cambio danno al libro il fuori campione che pretende dagli altri.

`yfinance` non è una fonte ufficiale e va a limite di richieste con facilità:
per questo si esegue **a mano, una volta**, con cache su disco. Il libro legge
solo lo snapshot congelato che questo script produce.

Attenzione ai prezzi: si scaricano **aggiustati** (`auto_adjust=True`), cioè
corretti per dividendi e frazionamenti. È la scelta giusta per tutto ciò che
il libro calcola — che è sempre una variazione percentuale — ed è quella
sbagliata per qualunque regola basata su un livello assoluto di prezzo. Il
@sec-cap-16 lo dice, e le *Fonti e dati* lo ripetono.

Uso:  uv run --extra ingest python codice/ingest/yahoo_dump.py
"""

from __future__ import annotations

import sys
import time
from datetime import date
from pathlib import Path

import polars as pl

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE / "codice" / "src"))

# Il terminale Windows parla ancora cp1252: senza questo, una freccia o una
# lettera accentata nel rapporto dei controlli fa fallire l'ingest.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from cvbook.dati import congela  # noqa: E402

CACHE = RADICE / "codice" / "dati" / "cache" / "yahoo"

#: Estremo destro comune a tutte le serie del libro: le cripto sono congelate
#: al 30 giugno 2026, e due periodi diversi renderebbero i confronti discutibili.
FINE = date(2026, 7, 1)
INIZIO = date(2000, 1, 1)

#: Serie che partono dopo il 2000, e perché. È il controllo numero due del
#: @sec-cap-16 applicato a se stessi: la serie del cambio, fino a tutto il
#: 2008, contiene dieci movimenti oltre il 5% che arrivano **in coppie
#: opposte** — un balzo e il giorno dopo il ritorno esatto. Su un cambio fra
#: due valute principali quei movimenti non sono esistiti: sono quotazioni
#: sbagliate della fonte. Dal 2009 il movimento più grande dell'intera serie
#: vale il 3,5%, che è un valore plausibile. Si taglia, e lo si dichiara.
DAL = {"eurusd": date(2009, 1, 1)}

# (nome, ticker, descrizione della fonte, nota per il registro)
SERIE = [
    ("ftsemib", "FTSEMIB.MI", "indice FTSE MIB, chiusure giornaliere",
     "FTSE MIB: l'indice del mercato italiano, il termine di paragone non cripto"),
    ("eni", "ENI.MI", "azione ENI, chiusure giornaliere aggiustate",
     "ENI, blue chip italiana: energia, storia lunga"),
    ("enel", "ENEL.MI", "azione Enel, chiusure giornaliere aggiustate",
     "Enel, blue chip italiana: utility, bassa volatilità"),
    ("intesa", "ISP.MI", "azione Intesa Sanpaolo, chiusure giornaliere aggiustate",
     "Intesa Sanpaolo, blue chip italiana: il ciclo bancario"),
    ("generali", "G.MI", "azione Assicurazioni Generali, chiusure giornaliere aggiustate",
     "Generali, blue chip italiana: assicurativo"),
    ("eurusd", "EURUSD=X", "cambio euro/dollaro, chiusure giornaliere dal 2009",
     "EUR/USD: una seconda classe di attività, non un secondo titolo"),
]


def _scarica(ticker: str) -> pl.DataFrame:
    """Scarica una serie, con cache su disco. La rete si tocca una volta sola."""
    locale = CACHE / f"{ticker.replace('=', '_')}.csv"
    if locale.exists():
        return pl.read_csv(locale, try_parse_dates=True)

    import yfinance as yf

    grezzo = yf.download(
        ticker, start=INIZIO.isoformat(), end=FINE.isoformat(),
        interval="1d", auto_adjust=True, progress=False, threads=False,
    )
    if grezzo is None or grezzo.empty:
        raise RuntimeError(f"nessun dato per {ticker}")

    # yfinance restituisce colonne a due livelli anche per un ticker solo.
    if hasattr(grezzo.columns, "levels"):
        grezzo.columns = grezzo.columns.get_level_values(0)

    df = pl.DataFrame({
        "data": [d.date() for d in grezzo.index],
        "apertura": grezzo["Open"].to_numpy(dtype=float),
        "massimo": grezzo["High"].to_numpy(dtype=float),
        "minimo": grezzo["Low"].to_numpy(dtype=float),
        "chiusura": grezzo["Close"].to_numpy(dtype=float),
        "volume": grezzo["Volume"].to_numpy(dtype=float),
    })
    df = df.drop_nulls("chiusura").unique(subset=["data"], keep="first").sort("data")

    locale.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(locale)
    time.sleep(2.0)  # cortesia, e Yahoo risponde 429 con pochissimo
    return df


def _sedute_attese(dal: date, al: date) -> int:
    """Giorni feriali nel periodo: il calendario di borsa, meno le festività."""
    giorni = (al - dal).days + 1
    inizio = pl.date_range(dal, al, "1d", eager=True)
    return int((inizio.dt.weekday() <= 5).sum()) if giorni > 0 else 0


def controlli(nome: str, df: pl.DataFrame) -> None:
    """I cinque controlli del @sec-cap-16, eseguiti prima di usare i dati.

    Non correggono niente: mostrano. Se qualcosa non torna, la serie non entra
    nel libro — è il costo di dieci minuti contro giorni di lavoro su una base
    che non regge.
    """
    print(f"\n  cinque controlli su «{nome}»")

    d = df["data"].to_list()
    chiusura = df["chiusura"].to_numpy()
    var = chiusura[1:] / chiusura[:-1] - 1.0

    # 1 — righe contro calendario di borsa.
    attese = _sedute_attese(d[0], d[-1])
    print(f"    1. righe: {df.height} su {attese} giorni feriali "
          f"({df.height / attese:.1%} — le festività di borsa spiegano il resto)")
    buchi = [
        (d[i - 1], d[i], (d[i] - d[i - 1]).days)
        for i in range(1, len(d))
        if (d[i] - d[i - 1]).days > 5
    ]
    if buchi:
        print(f"       {len(buchi)} interruzioni oltre i 5 giorni; la più lunga: "
              f"{max(b[2] for b in buchi)} giorni")
        for da, a, quanti in sorted(buchi, key=lambda b: -b[2])[:3]:
            print(f"         {da} → {a} ({quanti} giorni)")
    else:
        print("       nessuna interruzione oltre i cinque giorni")

    # 2 — i venti movimenti più grandi in valore assoluto.
    ordine = sorted(range(len(var)), key=lambda i: -abs(var[i]))[:20]
    estremi = ", ".join(f"{d[i + 1]} {var[i]:+.1%}" for i in ordine[:6])
    print(f"    2. venti movimenti maggiori, i primi sei: {estremi}")
    print(f"       il ventesimo vale {abs(var[ordine[-1]]):.1%}")

    # 3 — giorni a variazione esattamente zero.
    zeri = int((var == 0).sum())
    print(f"    3. giorni a variazione esattamente zero: {zeri} ({zeri / len(var):.2%})")

    # 4 — coerenza fra massimo, minimo, apertura e chiusura.
    incoerenti = df.filter(
        (pl.col("massimo") < pl.max_horizontal("apertura", "chiusura", "minimo"))
        | (pl.col("minimo") > pl.min_horizontal("apertura", "chiusura", "massimo"))
    ).height
    print(f"    4. barre incoerenti (massimo/minimo/apertura/chiusura): {incoerenti}")

    # 5 — volume all'inizio e alla fine della serie.
    volume = df["volume"].to_numpy()
    testa, coda = volume[:60], volume[-60:]
    if float(coda.mean()) > 0:
        print(f"    5. volume mediano: {testa.mean():,.0f} nei primi 60 giorni, "
              f"{coda.mean():,.0f} negli ultimi 60")
        nulli = int((volume == 0).sum())
        if nulli:
            print(f"       {nulli} giorni a volume zero ({nulli / len(volume):.1%})")
    else:
        print("    5. volume assente: è una serie di cambio, non ha un volume "
              "di borsa (Yahoo lo riporta a zero)")


def main() -> None:
    for nome, ticker, origine, nota in SERIE:
        print(f"\n{ticker}: {nota}")
        df = _scarica(ticker)
        if nome in DAL:
            df = df.filter(pl.col("data") >= DAL[nome])
            print(f"  serie ristretta dal {DAL[nome]} — vedi DAL, in testa al file")
        controlli(nome, df)
        voce = congela(
            nome, df,
            origine=f"Yahoo Finance, ticker {ticker}, {origine}",
            fonte="Yahoo Finance",
            note=nota,
        )
        print(f"    → {voce.righe} sedute · {voce.dal} → {voce.al}"
              f" · sha256 {voce.sha256[:12]}…")
    print(f"\nsnapshot congelati il {date.today().isoformat()} "
          "in codice/dati/snapshot/")


if __name__ == "__main__":
    main()
