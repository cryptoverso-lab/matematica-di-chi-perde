"""Il repo del sito: si verifica prima di aprire, e prima di scrivere.

Il percorso arriva da fuori — riga di comando oggi, variabile della Action
domani — e questo modulo ci scrive dentro. Le tre funzioni sono in ordine di
fiducia crescente: prima si pretende che la cartella dichiari di essere quel
checkout, poi si legge da li' la versione del contratto, e solo allora si
scrive.
"""

from __future__ import annotations

import json
from pathlib import Path

from .comune import ProblemaDiIngest

#: Il file che dichiara che una cartella e' il checkout del repo del sito.
#: Il percorso arriva da fuori (argomento della riga di comando), quindi prima
#: di aprire o scrivere alcunche' si verifica che sia un checkout DICHIARATO e
#: non una cartella qualsiasi (ASVS V12, T-4-05). Non e' prudenza teorica:
#: `--sito` finisce in una `Action` che lo compone da variabili.
MARCATORE_SITO = Path("content") / "labs" / "schema" / "lab-bundle.schema.json"


def checkout_del_sito(grezzo: str) -> Path:
    """Il percorso del repo del sito, risolto e VERIFICATO (ASVS V12, T-4-05).

    Il valore arriva da fuori — riga di comando oggi, variabile della Action
    domani — e questo script ci scrive dentro. Prima di aprire o scrivere
    alcunche' si pretende che la cartella dichiari di essere quel checkout,
    portando il contratto del bundle al suo posto. Una cartella qualsiasi non
    e' un checkout: e' una cartella qualsiasi in cui si stanno per scrivere
    file.
    """
    percorso = Path(grezzo).expanduser().resolve()
    if not (percorso / MARCATORE_SITO).is_file():
        raise ProblemaDiIngest(
            f"`{grezzo}` non sembra il checkout del repo del sito: manca "
            f"`{MARCATORE_SITO.as_posix()}`.\n"
            "  E' il contratto del bundle, ed e' anche cio' che dichiara che "
            "quella cartella e' il posto giusto in cui scrivere."
        )
    return percorso


def versione_del_contratto(sito: Path) -> int:
    """La versione del contratto, LETTA dal contratto (D-08).

    Non e' un letterale in questo file, e non e' pignoleria: il numero di
    versione e' cio' che permette al sito di rifiutare un bundle di un altro
    contratto con un messaggio che nomina entrambe le versioni. Se stesse
    scritto in due posti, il giorno del passaggio alla 2 uno dei due resterebbe
    indietro, e il rifiuto arriverebbe come un errore di forma.
    """
    contratto = json.loads((sito / MARCATORE_SITO).read_text(encoding="utf-8"))
    try:
        return contratto["$defs"]["labBundle"]["properties"]["versione"]["const"]
    except (KeyError, TypeError) as errore:
        raise ProblemaDiIngest(
            f"`{MARCATORE_SITO.as_posix()}` non dichiara la versione del "
            "contratto in `$defs.labBundle.properties.versione.const`.\n"
            "  Il file si rigenera nel repo del sito con "
            "`node content/labs/build-schema.mjs`."
        ) from errore


def scrivi_json(percorso: Path, dato: dict) -> int:
    """Scrive un file del bundle a LF, e restituisce i byte scritti.

    `newline=""` perche' su Windows Python tradurrebbe `\n` in `\r\n` in
    scrittura: il bundle uscirebbe in CRLF, il gate del sito lo rifiuterebbe
    (controllo 3, divieto del CR) e la prova «CRLF e LF danno lo stesso file»
    sarebbe falsa proprio nel punto in cui viene scritta.
    """
    percorso.parent.mkdir(parents=True, exist_ok=True)
    testo = json.dumps(dato, ensure_ascii=False, indent=2) + "\n"
    with percorso.open("w", encoding="utf-8", newline="") as file:
        file.write(testo)
    return len(testo.encode("utf-8"))
