"""Controlla che nell'interno del libro non ci sia un solo pixel a colori.

La stampa dell'interno e' quotata in scala di grigi: basta un pixel colorato,
anche invisibile, perche' una tipografia quoti l'intero volume a colori. Il
controllo non si fa a occhio e non si fa sui sorgenti — si fa sul PDF finito,
pagina per pagina, perche' il colore puo' entrare da dove non lo si aspetta:
un riquadro con la tinta di serie di Quarto, un logo, un tratto di una figura.

Ogni pagina viene rasterizzata a bassa risoluzione con poppler e si guarda la
distanza fra i canali RGB: se tre canali coincidono, quel pixel e' grigio.

Uso:  .venv/Scripts/python.exe codice/figure/verifica_grigi.py [pdf] [--dpi 50]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

#: Tolleranza per canale. Zero sarebbe la definizione esatta di grigio, ma la
#: rasterizzazione introduce un punto di scarto sui bordi antialiasati.
TOLLERANZA = 6


def _poppler(nome: str) -> str:
    for cartella in (Path(p) for p in (shutil.os.environ.get("PATH") or "").split(";")):
        for candidato in (cartella / f"{nome}.exe", cartella / nome):
            if not candidato.exists():
                continue
            try:
                v = subprocess.run([str(candidato), "-v"], capture_output=True,
                                   text=True, timeout=20)
            except OSError:
                continue
            if "poppler" in (v.stdout + v.stderr).lower():
                return str(candidato)
    raise FileNotFoundError(f"{nome} di poppler non trovato nel PATH")


def pagine_colorate(pdf: Path, dpi: int = 50) -> list[tuple[int, int]]:
    """(pagina, pixel colorati) per ogni pagina che non e' in scala di grigi."""
    from PIL import Image, ImageChops

    colpite: list[tuple[int, int]] = []
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [_poppler("pdftoppm"), "-png", "-r", str(dpi), str(pdf),
             str(Path(tmp) / "p")],
            check=True, capture_output=True,
        )
        for immagine in sorted(Path(tmp).glob("p-*.png")):
            numero = int(immagine.stem.split("-")[-1])
            with Image.open(immagine) as img:
                canali = img.convert("RGB").split()
                # Distanza fra il canale piu' alto e il piu' basso, pixel per
                # pixel: se e' zero il pixel e' grigio per definizione.
                massimo = ImageChops.lighter(ImageChops.lighter(*canali[:2]), canali[2])
                minimo = ImageChops.darker(ImageChops.darker(*canali[:2]), canali[2])
                scarto = ImageChops.difference(massimo, minimo)
                quanti = sum(
                    conteggio for livello, conteggio in enumerate(scarto.histogram())
                    if livello > TOLLERANZA
                )
            if quanti:
                colpite.append((numero, quanti))
    return colpite


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", nargs="?", default="build/La-matematica-di-chi-perde.pdf")
    ap.add_argument("--dpi", type=int, default=50)
    args = ap.parse_args()

    pdf = Path(args.pdf)
    if not pdf.exists():
        print(f"PDF non trovato: {pdf}")
        return 2

    colpite = pagine_colorate(pdf, args.dpi)
    if colpite:
        print(f"COLORE TROVATO in {len(colpite)} pagine di {pdf.name}:")
        for numero, quanti in colpite[:20]:
            print(f"  p.{numero}: {quanti} pixel")
        return 1

    print(f"{pdf.name}: nessun pixel a colori, l'interno e' interamente in grigi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
