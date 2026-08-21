"""Avvio dei quaderni — il pezzo di codice che sta in cima a ogni lab.

Scopo: fare in modo che la prima cella di un quaderno funzioni sempre, sia su
Colab sia sul computer di chi ha clonato la repository, senza che il lettore
debba installare o configurare niente.

Cosa fa, in questo ordine:

1. capisce se sta girando dentro la repository del libro (allora non scarica
   nulla, usa i file locali) oppure altrove (allora prepara una copia);
2. scarica il motore di calcolo `cvbook` e gli snapshot dati richiesti da
   `raw.githubusercontent.com`, ricostruendo la stessa struttura di cartelle
   che il motore si aspetta;
3. mette `cvbook` nel percorso di importazione.

Nessuna chiamata a un'API di mercato, qui o altrove nei quaderni: i dati sono
file fissi, gli stessi identici usati per stampare le figure del libro. E' la
condizione perche' la figura che ottieni sia la figura che stai leggendo.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

#: Radice dei file grezzi. Questo file viene scaricato per primo, quando
#: `cvbook` non c'e' ancora: l'indirizzo va scritto per esteso. Lo tiene
#: allineato a `cvbook.link` il comando `costruisci.py --sincronizza`.
BASE = "https://raw.githubusercontent.com/cryptoverso-lab/matematica-di-chi-perde/main"

#: I moduli del motore. L'ordine non conta: si scaricano tutti.
MODULI = [
    "__init__.py",
    "layout.py",
    "stile.py",
    "dati.py",
    "metriche.py",
    "simulazioni.py",
    "regole.py",
    "ciclica.py",
    "link.py",
]

#: Le serie disponibili. Ogni quaderno chiede solo quelle che gli servono.
#: Le sei non cripto servono ai quaderni che rifanno fuori dalle criptovalute
#: cio' che il libro dimostra dentro.
SERIE = [
    "btcusdt", "ethusdt", "solusdt", "lunausdt", "fttusdt",
    "ftsemib", "eni", "enel", "intesa", "generali", "eurusd",
]


def _radice_locale() -> Path | None:
    """La radice della repository, se il quaderno gira dentro di essa."""
    for cartella in [Path.cwd(), *Path.cwd().parents]:
        if (cartella / "codice" / "src" / "cvbook" / "dati.py").exists():
            return cartella
    return None


def _scarica(percorso_remoto: str, destinazione: Path) -> None:
    if destinazione.exists():
        return
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(f"{BASE}/{percorso_remoto}", destinazione)


def prepara(serie: list[str] | None = None, *, radice: str = ".") -> Path:
    """Prepara l'ambiente e restituisce la radice usata.

    `serie` elenca gli snapshot da scaricare. Ometterlo li scarica tutti:
    sono pochi megabyte, ma su una connessione lenta conviene chiedere solo
    quelli che servono.
    """
    locale = _radice_locale()
    if locale is not None:
        sys.path.insert(0, str(locale / "codice" / "src"))
        print(f"motore locale: {locale}")
        return locale

    base = Path(radice).resolve()
    for modulo in MODULI:
        _scarica(f"codice/src/cvbook/{modulo}", base / "codice" / "src" / "cvbook" / modulo)
    _scarica("codice/dati/registro.json", base / "codice" / "dati" / "registro.json")

    for nome in serie if serie is not None else SERIE:
        if nome not in SERIE:
            raise ValueError(f"serie sconosciuta: {nome!r} — disponibili {SERIE}")
        _scarica(
            f"codice/dati/snapshot/{nome}.parquet",
            base / "codice" / "dati" / "snapshot" / f"{nome}.parquet",
        )

    sys.path.insert(0, str(base / "codice" / "src"))
    quante = len(serie) if serie is not None else len(SERIE)
    print(f"motore e {quante} serie pronti in {base}")
    return base


def figura(destinazione: str = "schermo"):
    """Contesto grafico del libro. `stampa` per i grigi, `schermo` per i colori."""
    from cvbook.stile import contesto

    return contesto(destinazione)
