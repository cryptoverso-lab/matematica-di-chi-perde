"""Il vocabolario comune dell'ingest: il fallimento che ha un nome, e il LF.

Due cose sole, e stanno insieme perche' le usano tutti gli altri moduli:
l'eccezione da cui passa ogni arresto e la normalizzazione da cui passa ogni
impronta. Un secondo punto di normalizzazione sarebbe una seconda
normalizzazione, e due normalizzazioni prima o poi divergono — con l'effetto
che il gate di parita' del sito diventerebbe rosso su bundle che nessuno ha
toccato.
"""

from __future__ import annotations

import hashlib


class ProblemaDiIngest(Exception):
    """Un fallimento che NOMINA il file, e quando serve anche la cella.

    Tutti i modi in cui questo script si ferma passano di qui, e nessuno di
    essi e' un avviso: un bundle incompleto pubblicato e' peggio di un bundle
    non pubblicato, perche' la pagina lo rende senza sapere che manca qualcosa.
    """


# ------------------------------------------------------------------ #
# Normalizzazione: UN SOLO PUNTO, prima di qualunque impronta         #
# ------------------------------------------------------------------ #


def normalizza(testo: str) -> str:
    """Fine riga a LF e niente spazi in coda (D-46).

    Misurato (04-RESEARCH.md §1.3): i 29 sorgenti stanno su disco in CRLF e in
    git in LF (`core.autocrlf=true`, nessun `.gitattributes` prima di questo
    piano). L'ingest gira in due posti — la macchina di Luigi e il runner Linux
    della Action — quindi una sha256 sui byte del file darebbe DUE impronte per
    lo stesso contenuto: ogni giro della Action riscriverebbe tutti gli
    identificativi di blocco (D-13), disallineerebbe tutte le traduzioni EN e
    il gate di parita' (D-35) sarebbe rosso senza che nulla sia cambiato. Un
    gate sempre rosso viene disattivato.

    Sta in una funzione sola e la chiamano tutti: due punti di normalizzazione
    sono due normalizzazioni che prima o poi divergono. Il `.gitattributes`
    aggiunto da questo piano e' il rimedio alla radice e non la sostituisce: la
    affianca, perche' un checkout gia' esistente resta com'e'.
    """
    piatto = testo.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(riga.rstrip() for riga in piatto.split("\n"))


def impronta_breve(testo: str) -> str:
    """Le prime 12 cifre esadecimali della sha256 del testo normalizzato.

    Dodici e non otto: 04-RESEARCH.md §1.4 e' la sezione che argomenta la forma,
    l'esempio di §4.1 e' abbreviato. Il repo del sito ha gia' scelto le dodici
    (`content/labs/schema/schema.ts`), e il suo controllo 3 ricalcola questa
    stessa impronta sui blocchi di codice: se le due funzioni divergessero, il
    gate del sito sarebbe rosso su ogni bundle.
    """
    return hashlib.sha256(normalizza(testo).encode("utf-8")).hexdigest()[:12]


def impronta_etichettata(testo: str) -> str:
    """`sha256:<64 esadecimali>` del testo normalizzato — la forma del contratto."""
    return "sha256:" + hashlib.sha256(normalizza(testo).encode("utf-8")).hexdigest()


def byte_normalizzati(testo: str) -> int:
    """I byte del testo a LF, cioe' quelli che il lettore SCARICA.

    La dimensione sta accanto al collegamento (D-18), e il collegamento porta al
    blob di `raw.githubusercontent.com`, che e' a LF. Scrivere qui la dimensione
    del file su disco significherebbe annunciare al lettore Windows un numero e
    al lettore Linux un altro, per lo stesso file.
    """
    return len(testo.encode("utf-8"))
