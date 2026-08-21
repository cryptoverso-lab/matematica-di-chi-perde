"""Pre-render: genera tutte le figure come artefatti, prima che Quarto renderizzi.

Le figure NON si calcolano dentro i .qmd: si producono qui, in due versioni
(stampa e schermo), e il manoscritto le include come immagini. Cosi' il render
del libro non dipende dalla rete e la stessa figura serve carta, EPUB e Colab.

Ogni script `fig_*.py` in questa cartella espone una funzione `disegna(destinazione)`
che restituisce una figura matplotlib.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codice" / "src"))

from cvbook.stile import contesto, salva  # noqa: E402

OUT = {
    "stampa": ROOT / "figure" / "stampa",
    "schermo": ROOT / "figure" / "schermo",
}
MANIFEST = ROOT / "figure" / "manifest.json"


#: Marchi che entrano nelle pagine del libro (colophon ed epilogo). Non sono
#: figure — non nascono da dati — ma seguono la stessa regola: nell'interno del
#: libro non entra un solo pixel a colori, altrimenti la stampa dell'intero
#: volume viene quotata a colori. Qui vengono convertiti in scala di grigi.
MARCHI = {
    "marchio-cryptoverso": ROOT / "copertina" / "asset" / "logo" / "cryptoverso-logo-01.png",
    "firma-autore": ROOT / "copertina" / "asset" / "brand" / "firma-luigi-garone.png",
}


def _carica(percorso: Path):
    spec = importlib.util.spec_from_file_location(percorso.stem, percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _marchi_in_grigi() -> None:
    """Copia i marchi nell'interno del libro, in scala di grigi e su fondo bianco."""
    from PIL import Image

    for nome, sorgente in MARCHI.items():
        if not sorgente.exists():
            print(f"  attenzione: manca {sorgente.name}")
            continue
        img = Image.open(sorgente).convert("RGBA")
        # Trasparenza appiattita su bianco: le specifiche di stampa la chiedono.
        fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
        piatta = Image.alpha_composite(fondo, img).convert("L")
        for cartella in OUT.values():
            piatta.save(cartella / f"{nome}.png", dpi=(600, 600))
        print(f"marchio in grigi: {nome}")


def main() -> None:
    for d in OUT.values():
        d.mkdir(parents=True, exist_ok=True)

    script = sorted((ROOT / "codice" / "figure").glob("fig_*.py"))
    manifest: dict[str, dict] = {}

    for s in script:
        modulo = _carica(s)
        nome = s.stem.removeprefix("fig_")
        for destinazione, cartella in OUT.items():
            with contesto(destinazione):
                fig = modulo.disegna(destinazione)
                salva(fig, cartella / f"{nome}.png", destinazione)
        manifest[nome] = {
            "sorgente": str(s.relative_to(ROOT)).replace("\\", "/"),
            "didascalia": getattr(modulo, "DIDASCALIA", ""),
            "capitolo": getattr(modulo, "CAPITOLO", None),
        }
        print(f"figura generata: {nome}")

    _marchi_in_grigi()

    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"{len(manifest)} figure · manifest in {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
