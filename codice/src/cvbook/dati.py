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

#: Ultimo giorno in cui un identificativo quota ancora lo strumento che il libro
#: sta misurando. Oltre quella data il ticker c'e' ancora e il prezzo pure, ma
#: dietro c'e' un'altra cosa.
#:
#: `LUNAUSDT` e' il caso da manuale: nei dump di Binance il simbolo ha un buco
#: dal 14 al 30 maggio 2022 e poi riprende a 8,87 dollari. Non e' una risalita,
#: e' LUNA 2.0 — un progetto nuovo listato sotto lo stesso simbolo. Chi disegna
#: la serie per intero ottiene un grafico che scende a 0,00005 e poi risale di
#: centomila volte, cioe' l'esatto contrario di quello che e' successo.
#:
#: Sta qui e non dentro una figura perche' e' una proprieta' del **dato**, non
#: di un disegno: la sanno le figure, i quaderni e i test insieme, e nessuno
#: puo' dimenticarsene per conto proprio. Il gate e' in `test_dominio.py`.
DISCONTINUITA: dict[str, date] = {
    "lunausdt": date(2022, 5, 13),
}


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


def carica_strumento(nome: str, *, verifica: bool = True) -> pl.DataFrame:
    """Come `carica`, ma si ferma dove l'identificativo cambia strumento.

    E' la funzione da usare ogni volta che si misura **quel** token: prezzo,
    rendimenti, paniere, sopravvivenza. `carica` resta grezza apposta, perche'
    il capitolo sui dati che mentono ha bisogno di far vedere la serie intera —
    con dentro la discontinuita' — per insegnare a riconoscerla.
    """
    df = carica(nome, verifica=verifica)
    fine = DISCONTINUITA.get(nome)
    return df.filter(pl.col("data") <= fine) if fine else df


def citazione(nome: str) -> tuple[str, str]:
    """(fonte, data di estrazione) — da imprimere dentro ogni figura."""
    voce = leggi_registro()[nome]
    return voce.fonte, voce.estratto
