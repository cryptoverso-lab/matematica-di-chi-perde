"""Esegue i quaderni come li esegue un lettore, non come li esegue la repository.

`test_quaderni.py` li fa girare in casa: dentro il repo, con il `.venv` del
libro e le versioni pinnate dal lockfile. E' un test utile e non e' questo.
Un lettore apre Colab, cioe':

- una cartella **vuota**, senza il repo del libro da nessuna parte;
- un ambiente in cui `cvbook` non esiste e va scaricato da
  `raw.githubusercontent.com` insieme agli snapshot dei dati;
- pacchetti **non pinnati**: numpy e matplotlib sono quelli preinstallati
  dall'immagine, polars arriva da `%pip install "polars>=1.0"`, e domani
  saranno versioni diverse da oggi.

E' la differenza fra «i quaderni girano» e «la promessa stampata in quarta di
copertina e' vera». Questo script prova la seconda.

Cosa NON puo' fare: girare dentro Colab davvero. Colab richiede un accesso
Google interattivo e non ha un'esecuzione headless pubblica. Quello che fa e'
riprodurre le tre condizioni che rompono davvero un quaderno — ambiente vuoto,
rete, versioni libere — su un interprete pulito. Il residuo non coperto e'
l'immagine specifica di Colab, e si chiude solo aprendone uno a mano.

Uso:
    .venv/Scripts/python.exe codice/testing/prova_colab.py            # tutti
    .venv/Scripts/python.exe codice/testing/prova_colab.py lab_01     # uno solo
    .venv/Scripts/python.exe codice/testing/prova_colab.py --python 3.13
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "codice" / "lab"

#: Cio' che l'immagine di Colab ha gia' installato e che i quaderni usano. Non
#: si pinna niente di proposito: il punto e' rompersi qui invece che in mano al
#: lettore, il giorno in cui una di queste esce in una versione incompatibile.
#:
#: `pip` e' in questo elenco e non e' un dettaglio: `uv venv` crea un ambiente
#: **senza pip**, e la prima cella di ogni quaderno comincia con
#: `%pip install -q "polars>=1.0"`. Senza pip quella riga non fa niente in
#: silenzio e il quaderno muore due celle dopo con un ModuleNotFoundError che
#: sembra un difetto del libro e invece e' un difetto della prova. Colab pip ce
#: l'ha; l'ambiente della prova deve somigliargli, non al nostro lockfile.
#: **polars non si preinstalla di proposito**: deve arrivare dalla cella di
#: setup, perche' e' quella la riga che deve funzionare in mano al lettore.
PREINSTALLATI = ["pip", "numpy", "matplotlib", "pandas"]

#: Cio' che serve a eseguire un `.ipynb` senza Jupyter completo.
ESECUZIONE = ["nbclient", "nbformat", "ipykernel"]


def quaderni(filtro: str | None) -> list[Path]:
    tutti = sorted(LAB.glob("*.ipynb"))
    if filtro:
        tutti = [p for p in tutti if filtro in p.name]
    return tutti


def prepara_ambiente(dove: Path, versione: str) -> Path:
    """Un interprete pulito, con dentro solo cio' che Colab ha di suo."""
    venv = dove / ".venv-colab"
    subprocess.run(["uv", "venv", "--python", versione, str(venv)],
                   check=True, capture_output=True, text=True)
    python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run(["uv", "pip", "install", "--python", str(python), "--quiet",
                    *PREINSTALLATI, *ESECUZIONE],
                   check=True, capture_output=True, text=True)
    return python


def esegui(quaderno: Path, python: Path, dove: Path, timeout: int) -> tuple[bool, str, float]:
    """Esegue il quaderno in una cartella vuota. Vero se arriva in fondo."""
    lavoro = dove / quaderno.stem
    lavoro.mkdir(parents=True, exist_ok=True)
    copia = lavoro / quaderno.name
    shutil.copy2(quaderno, copia)

    codice = (
        "import sys, nbformat\n"
        "from nbclient import NotebookClient\n"
        "nb = nbformat.read(sys.argv[1], as_version=4)\n"
        "NotebookClient(nb, timeout=int(sys.argv[2]), kernel_name='python3',\n"
        "               resources={'metadata': {'path': sys.argv[3]}}).execute()\n"
    )
    inizio = time.monotonic()
    esito = subprocess.run(
        [str(python), "-c", codice, str(copia), str(timeout), str(lavoro)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    durata = time.monotonic() - inizio
    if esito.returncode == 0:
        return True, "", durata
    # L'errore utile e' l'ultima riga non vuota del traceback.
    righe = [r for r in (esito.stderr or esito.stdout).splitlines() if r.strip()]
    return False, (righe[-1] if righe else "errore senza messaggio")[:200], durata


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("filtro", nargs="?", help="esegue solo i quaderni che contengono questa stringa")
    ap.add_argument("--python", default="3.12", help="versione dell'interprete (default: 3.12)")
    ap.add_argument("--timeout", type=int, default=900, help="secondi per quaderno")
    ap.add_argument("--tieni", action="store_true", help="non cancella la cartella di lavoro")
    args = ap.parse_args()

    elenco = quaderni(args.filtro)
    if not elenco:
        print("nessun quaderno trovato: costruiscili con codice/lab/costruisci.py")
        return 2

    dove = Path(tempfile.mkdtemp(prefix="prova-colab-"))
    print(f"ambiente pulito in {dove}  (python {args.python})")
    try:
        python = prepara_ambiente(dove, args.python)
    except subprocess.CalledProcessError as errore:
        print(f"non riesco a preparare l'ambiente: {errore.stderr[:400]}")
        return 2

    print(f"{len(elenco)} quaderni, come li esegue un lettore\n")
    falliti: list[tuple[str, str]] = []
    for n, quaderno in enumerate(elenco, 1):
        ok, messaggio, durata = esegui(quaderno, python, dove, args.timeout)
        segno = "ok  " if ok else "ROTTO"
        print(f"  [{n:2d}/{len(elenco)}] {segno} {quaderno.name:38s} {durata:6.1f}s")
        if not ok:
            print(f"          {messaggio}")
            falliti.append((quaderno.name, messaggio))

    print()
    if falliti:
        print(f"{len(falliti)} quaderni su {len(elenco)} NON girano in un ambiente pulito:")
        for nome, messaggio in falliti:
            print(f"  - {nome}: {messaggio}")
    else:
        print(f"tutti e {len(elenco)} girano in un ambiente pulito, "
              "scaricando motore e dati dalla repository pubblica")

    rapporto = ROOT / "codice" / "testing" / "prova-colab-esito.json"
    rapporto.write_text(json.dumps({
        "python": args.python,
        "quaderni": len(elenco),
        "falliti": [{"quaderno": n, "errore": m} for n, m in falliti],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nesito in {rapporto.relative_to(ROOT)}")

    if not args.tieni:
        shutil.rmtree(dove, ignore_errors=True)
    return 1 if falliti else 0


if __name__ == "__main__":
    raise SystemExit(main())
