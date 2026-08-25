"""Dati dell'edizione — unica fonte di verità per il colophon e per il freeze.

Il colophon stampato non si scrive a mano: nasce da qui, come l'indice dei lab
nasce da `cvbook.link`. I valori che alla chiusura del manoscritto non esistono
ancora restano `None`, e diventano veri cambiando una riga qui.

Su cosa succede quando un valore è `None` il modulo tiene due comportamenti
diversi, ed è voluto. **Editore e ISBN spariscono dalla pagina**: sono dati
anagrafici, e una riga che dichiara di non sapere ancora chi pubblica mette in
pagina un dubbio di lavorazione, che non riguarda chi legge. **L'archivio
permanente resta e si dichiara**: lì il lettore ha bisogno di sapere dove
trovare il codice fra dieci anni, e «in corso di assegnazione, per ora vive
nella repository» è un'informazione, non una lacuna.

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

#: Editore, e ISBN che ne dipende. Si compilano insieme, alla decisione:
#: `EDITORE = "..."`, `ISBN = "978-..."`, poi si rigenera il libro e si
#: ricongela.
#:
#: Finché sono `None` il libro **non ne parla**: la riga non viene stampata,
#: né in seconda pagina né nel colophon. È la scelta del 2026-08-25, e cambia
#: quella di prima: non si stampa più un ripiego («da definire», «assegnato
#: alla pubblicazione»), perché una pagina dei diritti che dichiara ciò che non
#: sa ancora invecchia male e mette in pagina un dubbio che è di lavorazione,
#: non del lettore. Il presidio non sparisce, si sposta dove serve davvero:
#: `pacchetto_amazon.py` rifiuta di considerare caricabile un pacchetto con
#: l'ISBN mancante, quindi il libro non può uscire senza.
EDITORE: str | None = None

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
