"""Ingest delle serie cripto dai dump pubblici di Binance.

Perché questa fonte e non le API dei siti di dati: `data.binance.vision`
conserva i dump anche dei simboli **delistati**. Le API gratuite dei portali
espongono in prevalenza le monete ancora vive — e ricostruire da lì la storia
dei token morti significherebbe dimostrare il survivorship bias con un dataset
che ne è affetto.

Si esegue a mano, una volta. Il libro legge solo lo snapshot che produce.

Uso:  uv run --extra ingest python codice/ingest/binance_dump.py
"""

from __future__ import annotations

import io
import sys
import time
import zipfile
from datetime import date
from pathlib import Path

import polars as pl
import requests

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE / "codice" / "src"))

from cvbook.dati import congela  # noqa: E402

CACHE = RADICE / "codice" / "dati" / "cache" / "binance"
BASE = "https://data.binance.vision/data/spot/monthly/klines"

COLONNE = [
    "apertura_ms", "apertura", "massimo", "minimo", "chiusura", "volume",
    "chiusura_ms", "volume_quote", "scambi", "taker_base", "taker_quote", "ignora",
]

# (simbolo, dal, al, descrizione) — il periodo copre la vita del simbolo.
SERIE = [
    ("BTCUSDT", (2017, 8), (2026, 6), "Bitcoin, asset primario del libro"),
    ("ETHUSDT", (2017, 8), (2026, 6), "Ethereum, validazione cross-asset"),
    ("SOLUSDT", (2020, 8), (2026, 6), "Solana, validazione cross-asset"),
    ("LUNAUSDT", (2020, 8), (2022, 12), "Terra/LUNA: collasso di maggio 2022"),
    ("FTTUSDT", (2019, 12), (2022, 12), "FTX Token: collasso di novembre 2022"),
]


def _mesi(dal: tuple[int, int], al: tuple[int, int]):
    anno, mese = dal
    while (anno, mese) <= al:
        yield anno, mese
        mese += 1
        if mese == 13:
            anno, mese = anno + 1, 1


def _scarica_mese(simbolo: str, anno: int, mese: int) -> bytes | None:
    """Scarica un mese, con cache su disco. None se il mese non esiste."""
    nome = f"{simbolo}-1d-{anno:04d}-{mese:02d}.zip"
    locale = CACHE / simbolo / nome
    if locale.exists():
        return locale.read_bytes()

    url = f"{BASE}/{simbolo}/1d/{nome}"
    risposta = requests.get(url, timeout=30)
    if risposta.status_code == 404:
        return None
    risposta.raise_for_status()

    locale.parent.mkdir(parents=True, exist_ok=True)
    locale.write_bytes(risposta.content)
    time.sleep(0.15)  # cortesia verso una fonte pubblica e gratuita
    return risposta.content


def _leggi_zip(grezzo: bytes) -> pl.DataFrame:
    with zipfile.ZipFile(io.BytesIO(grezzo)) as z:
        with z.open(z.namelist()[0]) as f:
            testo = f.read().decode("utf-8")

    # Dal 2025 alcuni dump hanno l'intestazione: si riconosce e si salta.
    if testo.lstrip().startswith("open_time"):
        testo = testo.split("\n", 1)[1]

    return pl.read_csv(
        io.StringIO(testo),
        has_header=False,
        new_columns=COLONNE,
        schema_overrides={c: pl.Float64 for c in COLONNE[1:6]},
    )


def scarica_serie(simbolo: str, dal, al) -> pl.DataFrame:
    parti = []
    mancanti = 0
    for anno, mese in _mesi(dal, al):
        grezzo = _scarica_mese(simbolo, anno, mese)
        if grezzo is None:
            mancanti += 1
            continue
        parti.append(_leggi_zip(grezzo))

    if not parti:
        raise RuntimeError(f"nessun dato per {simbolo}")

    df = pl.concat(parti, how="vertical_relaxed")

    # Binance è passato dai millisecondi ai microsecondi: si riconosce
    # dall'ordine di grandezza invece di assumere l'uno o l'altro.
    df = df.with_columns(
        pl.when(pl.col("apertura_ms") > 1e15)
        .then(pl.col("apertura_ms") // 1000)
        .otherwise(pl.col("apertura_ms"))
        .alias("apertura_ms")
    )

    df = (
        df.with_columns(
            pl.from_epoch("apertura_ms", time_unit="ms").dt.date().alias("data")
        )
        .select(["data", "apertura", "massimo", "minimo", "chiusura", "volume", "scambi"])
        .unique(subset=["data"], keep="first")
        .sort("data")
    )
    if mancanti:
        print(f"    {mancanti} mesi assenti (simbolo non ancora quotato o gia' delistato)")
    return df


def main() -> None:
    oggi = date.today().isoformat()
    for simbolo, dal, al, descrizione in SERIE:
        print(f"{simbolo}: {descrizione}")
        df = scarica_serie(simbolo, dal, al)
        voce = congela(
            simbolo.lower(),
            df,
            origine=f"{BASE}/{simbolo}/1d/ (dump mensili)",
            fonte="Binance Data Vision",
            note=descrizione,
        )
        print(
            f"    {voce.righe} barre giornaliere · {voce.dal} → {voce.al}"
            f" · sha256 {voce.sha256[:12]}…"
        )
    print(f"\nsnapshot congelati il {oggi} in codice/dati/snapshot/")


if __name__ == "__main__":
    main()
