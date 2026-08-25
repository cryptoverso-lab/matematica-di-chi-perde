"""Dati dell'edizione — unica fonte di verità per il colophon e per il freeze.

Il colophon stampato non si scrive a mano: nasce da qui, come l'indice dei lab
nasce da `cvbook.link`. I valori che alla chiusura del manoscritto non esistono
ancora — editore, ISBN, archivio permanente — restano `None` e vengono stampati
come dichiarazione di ciò che manca, non come un numero inventato. Diventano
veri cambiando una riga qui.

Regola: nessun dato di edizione va scritto dentro un `.qmd`.
"""

from __future__ import annotations

#: Titolo e paratesto: identici a quelli dichiarati in `_quarto.yml`.
TITOLO = "La matematica di chi perde"
SOTTOTITOLO = "Il trading spiegato con dati, statistica e codice che puoi rieseguire tu"
AUTORE = "Luigi Garone"

#: Opera nuova e a sé stante: questa è la sua prima edizione.
EDIZIONE = "Prima edizione"

#: Data in cui il manoscritto è stato congelato: da qui il testo non cambia più
#: senza rieseguire `codice/manoscritto/congela.py` e dichiararne il motivo.
DATA_FREEZE = "2026-08-25"

#: Editore. Deciso il 2026-08-25 da Luigi, e ribalta la scelta del 2026-08-16:
#: il libro **si autopubblica**, non passa da una casa editrice. Esce sotto il
#: marchio che porta già in quarta di copertina e negli indirizzi dei quaderni.
#: Nota sul canale: con l'ISBN gratuito di KDP, Amazon elenca comunque l'opera
#: come «Independently published» nella scheda prodotto e non lascia scegliere
#: un nome di editore. Il colophon del libro può nominare il marchio lo stesso —
#: Cryptoverso esiste ed è dell'autore — ma le due diciture non coincidono.
#: Con un ISBN proprio, invece, il nome dell'editore è quello dichiarato qui.
EDITORE: str | None = "Cryptoverso"

#: ISBN. **Ancora aperto al 2026-08-25**: Luigi sta valutando se prendere quello
#: gratuito di KDP (zero costi, legato ad Amazon, non riutilizzabile altrove)
#: oppure un ISBN proprio dall'agenzia italiana (a pagamento, riutilizzabile su
#: altri canali, e permette di dichiarare l'editore anche nella scheda prodotto).
#: Finché è `None` il colophon dichiara apertamente che manca, invece di
#: stampare un codice inventato.
ISBN: str | None = None

#: Identificativo permanente dell'archivio di codice e dati (dopo la repository
#: pubblica). È ciò che rende verificabile il libro fra dieci anni.
ARCHIVIO_PERMANENTE: str | None = None

#: Diritti: il testo è riservato, il codice è aperto. Vedi `LICENSE`.
#: Senza contratto di edizione i diritti restano interi all'autore, quindi
#: questa è già la formula definitiva.
DIRITTI_TESTO = "© 2026 Luigi Garone. Tutti i diritti riservati."
LICENZA_CODICE = "MIT"

#: Toolchain con cui il libro è materialmente prodotto: dichiararla è parte
#: della tesi del libro, non un vezzo tecnico.
TOOLCHAIN = "Quarto e LuaLaTeX; figure e calcoli in Python (polars, numpy, matplotlib)"
FONT_TESTO = "Libertinus Serif e Libertinus Sans"
FONT_CODICE = "Inconsolata"


def valore_o_riserva(valore: str | None, riserva: str) -> str:
    """Stampa il valore se esiste, altrimenti dichiara apertamente che manca."""
    return valore if valore else riserva
