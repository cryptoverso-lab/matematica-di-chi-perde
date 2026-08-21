"""Accesso ai dati del libro — solo snapshot congelati, mai la rete.

Regola d'oro del progetto: gli script di ingest scaricano una volta e salvano
uno snapshot versionato; il libro, le figure e i notebook leggono **solo** lo
snapshot. Una build che chiama un'API è una build che un giorno non compila —
e una figura che non si può riprodurre fra cinque anni non e' una prova.

Ogni snapshot ha una voce nel registro con origine, data di estrazione e
impronta SHA-256: e' cio' che rende citabile ogni cifra stampata nel libro.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path

import polars as pl

RADICE = Path(__file__).resolve().parents[3]
SNAPSHOT = RADICE / "codice" / "dati" / "snapshot"
REGISTRO = RADICE / "codice" / "dati" / "registro.json"


@dataclass(frozen=True)
class Voce:
    """Una serie congelata, con tutto ciò che serve per citarla."""

    nome: str
    file: str
    origine: str          # URL o descrizione della fonte
    fonte: str            # come va citata nel libro e dentro la figura
    estratto: str         # data di estrazione, ISO
    righe: int
    dal: str
    al: str
    sha256: str
    note: str = ""


def _impronta(percorso: Path) -> str:
    h = hashlib.sha256()
    with percorso.open("rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


def leggi_registro() -> dict[str, Voce]:
    if not REGISTRO.exists():
        return {}
    grezzo = json.loads(REGISTRO.read_text(encoding="utf-8"))
    return {k: Voce(**v) for k, v in grezzo.items()}


def _scrivi_registro(voci: dict[str, Voce]) -> None:
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    REGISTRO.write_text(
        json.dumps(
            {k: asdict(v) for k, v in sorted(voci.items())},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def congela(
    nome: str,
    df: pl.DataFrame,
    *,
    origine: str,
    fonte: str,
    colonna_data: str = "data",
    note: str = "",
) -> Voce:
    """Salva una serie come snapshot Parquet e la registra.

    Da chiamare **solo** dagli script di ingest, mai in fase di render.
    """
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    percorso = SNAPSHOT / f"{nome}.parquet"
    df.write_parquet(percorso, compression="zstd")

    date_col = df.get_column(colonna_data)
    voce = Voce(
        nome=nome,
        file=f"codice/dati/snapshot/{nome}.parquet",
        origine=origine,
        fonte=fonte,
        estratto=date.today().isoformat(),
        righe=df.height,
        dal=str(date_col.min()),
        al=str(date_col.max()),
        sha256=_impronta(percorso),
        note=note,
    )

    voci = leggi_registro()
    voci[nome] = voce
    _scrivi_registro(voci)
    return voce


def carica(nome: str, *, verifica: bool = True) -> pl.DataFrame:
    """Carica uno snapshot, verificando che non sia cambiato sotto i piedi."""
    voci = leggi_registro()
    if nome not in voci:
        disponibili = ", ".join(sorted(voci)) or "(nessuno)"
        raise KeyError(f"snapshot sconosciuto: {nome!r}. Disponibili: {disponibili}")

    voce = voci[nome]
    percorso = RADICE / voce.file
    if not percorso.exists():
        raise FileNotFoundError(
            f"snapshot mancante: {voce.file} — rieseguire lo script di ingest"
        )
    if verifica and _impronta(percorso) != voce.sha256:
        raise ValueError(
            f"lo snapshot {nome!r} non corrisponde alla sua impronta nel registro: "
            "il file e' stato modificato dopo il congelamento"
        )
    return pl.read_parquet(percorso)


def citazione(nome: str) -> tuple[str, str]:
    """(fonte, data di estrazione) — da imprimere dentro ogni figura."""
    voce = leggi_registro()[nome]
    return voce.fonte, voce.estratto
