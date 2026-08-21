"""Costruisce i quaderni `.ipynb` dai sorgenti `.py` in formato percent.

I sorgenti sono file Python veri: si eseguono, si leggono, si confrontano in
git riga per riga. Il `.ipynb` resta un **artefatto di build**, non un sorgente
da modificare a mano — ma e' TRACCIATO, e la ragione non e' di comodo.

PERCHE' I `.ipynb` STANNO IN GIT (D-15/D-16/D-51). Colab apre soltanto file
presi da GitHub: il bottone «Apri in Colab» di ogni pagina di lab punta al
`.ipynb` di questa cartella. Se non fosse tracciato, tutti e ventinove i
bottoni darebbero 404 a un lettore col libro in mano e il codice QR gia'
stampato. Si committano **puliti, senza output**: e' cio' che questo script
produce, e' tutto cio' che Colab chiede, e committarli eseguiti farebbe
crescere il repository di qualche megabyte a ogni giro. Gli output veri il
lettore li ottiene eseguendo — e li vede in pagina perche' l'ingest
(`estrai_bundle.py`) esegue i quaderni per conto suo.

E PERCHE' GLI IDENTIFICATIVI DI CELLA SONO DERIVATI DAL CONTENUTO. `jupytext`
li assegna casuali (nbformat 4.5): due costruzioni di fila dello stesso
sorgente davano due quaderni diversi, quindi tutti e ventinove comparivano
modificati in `git status` dopo ogni giro, e le impronte che l'ingest pubblica
(`impronteSorgente.ipynb`) cambiavano senza che il contenuto cambiasse. Vedi
`_ferma_gli_identificativi`.

La prima cella di ogni quaderno scarica `avvio.py` da un indirizzo scritto per
esteso: li' `cvbook` non esiste ancora, quindi l'indirizzo non puo' essere
importato. Non per questo va battuto a mano in ventinove file: lo ricopia
`--sincronizza` da `cvbook.link.URL_AVVIO`, e `--verifica` (con il gate in
`test_quaderni.py`) fallisce nominando file e riga se uno se ne allontana.
Se cambia l'organizzazione GitHub e questa riga no, ogni quaderno muore
all'avvio.

Uso:
    uv run python codice/lab/costruisci.py                 # costruisce tutto
    uv run python codice/lab/costruisci.py --verifica      # solo i controlli
    uv run python codice/lab/costruisci.py --sincronizza   # riallinea l'avvio
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "codice" / "lab"
sys.path.insert(0, str(ROOT / "codice" / "src"))

from cvbook.link import RAW_BASE, ROTTE, URL_AVVIO  # noqa: E402

#: File della cartella che non sono quaderni.
#:
#: E' l'UNICA sede dell'elenco: `test_quaderni.py` e l'ingest lo importano da
#: qui. Fino a questo piano era ricopiato nei test, e il primo file nuovo di
#: questa cartella lo ha fatto vedere — un modulo non-quaderno rendeva rosso il
#: gate «ogni quaderno ha la sua rotta» invece di essere semplicemente ignorato.
#: I `.py` di `codice/lab/` che NON sono quaderni. Sede unica: `test_quaderni.py`
#: importa questa costante invece di ricopiarla, perche' due elenchi divergono e
#: il giorno in cui divergono `costruisci.py` prova a costruire
#: `estrai_bundle.ipynb`.
#:
#: I moduli dell'ingest non sono in elenco: dal piano 04-08 vivono nel pacchetto
#: `codice/lab/estrazione/`, e un `glob("*.py")` non entra nelle sottocartelle.
#: E' il modo migliore di essere esclusi — per posizione invece che per nome.
ESCLUSI = {
    "avvio.py",
    "costruisci.py",
    "genera_indice.py",
    "estrai_bundle.py",
    "estrai_errata.py",
}

AVVIO = LAB / "avvio.py"

#: L'indirizzo scaricato dalla cella di setup di ogni quaderno...
SCHEMA_URLRETRIEVE = re.compile(r'(urllib\.request\.urlretrieve\(\s*")([^"]*)(")')
#: ...e la radice dei file grezzi dentro `avvio.py`, che dai quaderni viene
#: scaricato per primo e quindi non puo' importare nulla.
SCHEMA_BASE = re.compile(r'^(BASE = ")([^"]*)(")', re.M)


def sorgenti() -> list[Path]:
    return sorted(p for p in LAB.glob("*.py") if p.name not in ESCLUSI)


def _da_sincronizzare() -> list[tuple[Path, re.Pattern[str], str]]:
    """(file, schema dell'indirizzo, valore atteso) per ogni riga di avvio."""
    voci: list[tuple[Path, re.Pattern[str], str]] = [(AVVIO, SCHEMA_BASE, RAW_BASE)]
    voci += [(p, SCHEMA_URLRETRIEVE, URL_AVVIO) for p in sorgenti()]
    return voci


def _leggi(percorso: Path) -> str:
    """Legge senza tradurre i fine riga: riscrivere un file non deve cambiarli.

    Il freeze del manoscritto misura i byte, non le righe: una conversione
    silenziosa CRLF/LF fa fallire un gate che non c'entra nulla.
    """
    with open(percorso, encoding="utf-8", newline="") as f:
        return f.read()


def _scrivi(percorso: Path, testo: str) -> None:
    with open(percorso, "w", encoding="utf-8", newline="") as f:
        f.write(testo)


def avvii_disallineati() -> list[str]:
    """Quaderni la cui riga di bootstrap non viene piu' da `cvbook.link`."""
    fuori: list[str] = []
    for percorso, schema, atteso in _da_sincronizzare():
        testo = _leggi(percorso)
        trovato = schema.search(testo)
        if trovato is None:
            fuori.append(f"{percorso.relative_to(ROOT).as_posix()}: manca la riga di avvio")
            continue
        if trovato.group(2) != atteso:
            riga = testo[: trovato.start(2)].count("\n") + 1
            fuori.append(
                f"{percorso.relative_to(ROOT).as_posix()}:{riga}: "
                f"avvio da {trovato.group(2)!r}, atteso {atteso!r}"
            )
    return fuori


def sincronizza() -> list[Path]:
    """Riscrive le righe di avvio a partire da `cvbook.link`. Ritorna i toccati."""
    toccati: list[Path] = []
    for percorso, schema, atteso in _da_sincronizzare():
        testo = _leggi(percorso)
        nuovo = schema.sub(lambda m: f"{m.group(1)}{atteso}{m.group(3)}", testo, count=1)
        if nuovo != testo:
            _scrivi(percorso, nuovo)
            toccati.append(percorso)
    return toccati


def verifica() -> list[str]:
    """Controlla la corrispondenza fra rotte dichiarate e sorgenti presenti."""
    problemi: list[str] = []
    attesi = {r.file for r in ROTTE.values()}
    presenti = {p.name for p in sorgenti()}

    for mancante in sorted(attesi - presenti):
        problemi.append(f"rotta senza sorgente: {mancante}")
    for orfano in sorted(presenti - attesi):
        problemi.append(f"sorgente senza rotta in cvbook.link: {orfano}")

    for p in sorgenti():
        testo = p.read_text(encoding="utf-8")
        if "format_name: percent" not in testo:
            problemi.append(f"{p.name}: manca l'intestazione jupytext")
        if "avvio.prepara" not in testo:
            problemi.append(f"{p.name}: manca la cella di setup (avvio.prepara)")
        if "api.binance" in testo or "requests.get" in testo:
            problemi.append(f"{p.name}: chiama la rete fuori dal setup")

    problemi += avvii_disallineati()
    return problemi


def _ferma_gli_identificativi(percorso: Path) -> None:
    """Identificativi di cella DERIVATI dal contenuto, e file scritto a LF.

    Difetto misurato: `jupytext --to ipynb` assegna a ogni cella un `id`
    CASUALE (nbformat 4.5). Due costruzioni di fila dello stesso sorgente
    davano quindi due quaderni diversi — tutti e 29 comparivano modificati in
    `git status` dopo ogni giro, e il `.ipynb` e' tracciato (D-15/D-16).

    Non e' rumore estetico. L'ingest pubblica `impronteSorgente.ipynb` e
    `dimensioni.ipynb`: con gli `id` casuali quei due numeri cambiavano a ogni
    ricostruzione, cioe' il bundle cambiava senza che il contenuto cambiasse, e
    il presidio del diff (D-06) — l'unica cosa che fa vedere una modifica
    inattesa — sarebbe annegato nel proprio rumore.

    L'identificativo diventa le prime otto cifre della sha256 di indice piu'
    sorgente della cella: stabile finche' la cella non cambia, diverso appena
    cambia, e unico dentro un quaderno perche' l'indice ne fa parte.

    Il file si scrive con `newline=""` per la stessa ragione del bundle: su
    Windows Python tradurrebbe ogni fine riga in CRLF, e il quaderno su disco
    starebbe in CRLF mentre in git sta in LF.
    """
    quaderno = nbformat.read(percorso, as_version=4)
    for indice, cella in enumerate(quaderno.cells):
        seme = f"{indice}\n{cella.source}"
        cella["id"] = hashlib.sha256(seme.encode("utf-8")).hexdigest()[:8]
    with percorso.open("w", encoding="utf-8", newline="") as file:
        nbformat.write(quaderno, file)


def costruisci() -> int:
    fatti = 0
    for p in sorgenti():
        quaderno = p.with_suffix(".ipynb")
        subprocess.run(
            [sys.executable, "-m", "jupytext", "--to", "ipynb", "--output",
             str(quaderno), str(p)],
            check=True,
            capture_output=True,
        )
        _ferma_gli_identificativi(quaderno)
        fatti += 1
        print(f"quaderno: {quaderno.name}")
    return fatti


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verifica", action="store_true", help="solo i controlli")
    parser.add_argument(
        "--sincronizza",
        action="store_true",
        help="riscrive la riga di avvio dei quaderni da cvbook.link",
    )
    argomenti = parser.parse_args()

    if argomenti.sincronizza:
        toccati = sincronizza()
        for p in toccati:
            print(f"avvio riallineato: {p.relative_to(ROOT).as_posix()}")
        print(f"{len(toccati)} file riallineati su {URL_AVVIO}")
        return

    problemi = verifica()
    for problema in problemi:
        print(f"PROBLEMA  {problema}")

    if argomenti.verifica:
        print(f"{len(sorgenti())} sorgenti, {len(ROTTE)} rotte, {len(problemi)} problemi")
        sys.exit(1 if problemi else 0)

    if problemi:
        print("costruzione interrotta: risolvere i problemi elencati")
        sys.exit(1)

    print(f"{costruisci()} quaderni costruiti in {LAB.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
