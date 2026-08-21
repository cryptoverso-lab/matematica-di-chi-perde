"""Il repo del sito: si verifica prima di aprire, e prima di scrivere.

Il percorso arriva da fuori — riga di comando oggi, variabile della Action
domani — e questo modulo ci scrive dentro. Le tre funzioni sono in ordine di
fiducia crescente: prima si pretende che la cartella dichiari di essere quel
checkout, poi si legge da li' la versione del contratto, e solo allora si
scrive.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .comune import ProblemaDiIngest

#: Il file che dichiara che una cartella e' il checkout del repo del sito.
#: Il percorso arriva da fuori (argomento della riga di comando), quindi prima
#: di aprire o scrivere alcunche' si verifica che sia un checkout DICHIARATO e
#: non una cartella qualsiasi (ASVS V12, T-4-05). Non e' prudenza teorica:
#: `--sito` finisce in una `Action` che lo compone da variabili.
MARCATORE_SITO = Path("content") / "labs" / "schema" / "lab-bundle.schema.json"

#: Il registro delle 32 rotte stampate sui QR, nel repo del sito. Porta per ogni
#: codice l'intestazione nelle DUE lingue — `heading` e `headingEn` — ed e' da
#: dove `content/redirects/legacy-routes.ts` nasce.
REGISTRO_ROTTE = Path("content") / "redirects" / "legacy-routes.source.json"

#: `L05 — `, `C01 – `: il codice in testa all'intestazione. Sta nel titolo della
#: rotta, non nella descrizione, e va tolto da entrambe le lingue perche' il
#: campo `domanda` del bundle e' la sola descrizione.
PREFISSO_CODICE_RE = re.compile(r"^[A-Za-z]\d{2}\s*[—–-]\s*")


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


def descrizione_inglese(sito: Path, codice: str, descrizione_it: str) -> str:
    """La descrizione inglese della rotta, LETTA dal registro del sito.

    PERCHE' NON SI TRADUCE QUI, E PERCHE' NON STA NEL REPO DEL LIBRO. La
    descrizione inglese di ogni lab esiste gia', pubblicata dalla Fase 1: e'
    l'intestazione con cui `/lab` elenca i 29 lab in inglese, quella che
    `llms.txt` dichiara ai crawler di retrieval e quella che i `<title>` delle
    pagine EN portano da mesi. Scriverne una seconda — qui o in `cvbook.link` —
    significherebbe pubblicare due frasi diverse per la stessa cosa sulla stessa
    pagina, e la seconda divergerebbe dalla prima al primo ritocco.

    LA GARANZIA CHE SIA LA DESCRIZIONE GIUSTA E' UN CONFRONTO, non una fiducia.
    Lo stesso registro porta l'intestazione ITALIANA, e quella deve coincidere
    parola per parola con la `descrizione` che `cvbook.link` dichiara per quel
    codice: misurato, coincide su tutti e 29. Se un giorno i due registri
    divergessero, la coppia (italiano dal libro, inglese dal sito) non sarebbe
    piu' la stessa frase in due lingue — e l'ingest si ferma qui invece di
    scrivere in `en.json` la traduzione di un'altra rotta.
    """
    percorso = sito / REGISTRO_ROTTE
    if not percorso.is_file():
        raise ProblemaDiIngest(
            f"manca `{REGISTRO_ROTTE.as_posix()}` nel checkout del sito.\n"
            "  E' il registro da cui si legge la descrizione INGLESE della rotta, "
            "cioe' il campo\n"
            "  `domanda` di `en.json`: senza, la pagina inglese avrebbe la "
            "descrizione italiana."
        )
    registro = json.loads(percorso.read_text(encoding="utf-8"))
    voce = next(
        (r for r in registro.get("routes", []) if r.get("route") == codice.lower()),
        None,
    )
    if voce is None:
        raise ProblemaDiIngest(
            f"il registro delle rotte del sito non dichiara `{codice.lower()}`.\n"
            "  I 29 lab e i 32 redirect nascono dallo stesso elenco: un codice "
            "che manca di la'\n"
            "  e' un QR stampato che nessuna pagina serve."
        )
    italiano = PREFISSO_CODICE_RE.sub("", voce.get("heading", "")).strip()
    inglese = PREFISSO_CODICE_RE.sub("", voce.get("headingEn", "")).strip()
    if italiano != descrizione_it:
        raise ProblemaDiIngest(
            f"{codice.lower()}: i due registri non descrivono la stessa rotta.\n"
            f"  libro: «{descrizione_it}»\n"
            f"  sito:  «{italiano}»\n"
            "  La descrizione inglese si prende dal registro del sito, e la si "
            "puo' prendere solo\n"
            "  finche' quella italiana coincide: altrimenti si starebbe "
            "pubblicando in inglese\n"
            "  la descrizione di un'altra rotta."
        )
    if not inglese:
        raise ProblemaDiIngest(
            f"{codice.lower()}: il registro del sito non porta l'intestazione "
            "inglese (`headingEn`).\n"
            "  E' il campo `domanda` di `en.json`, ed e' obbligatorio nel "
            "contratto del bundle."
        )
    return inglese

