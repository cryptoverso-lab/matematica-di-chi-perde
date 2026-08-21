"""L'ingest dei lab, diviso in pezzi che si possono aprire uno per volta.

`estrai_bundle.py` era arrivato a 830 righe, sopra la soglia di progetto, e il
piano 04-08 gli aggiunge l'esecuzione dei quaderni e il trattamento delle
figure. La divisione viene PRIMA di quell'aggiunta, non dopo: dividere un file
che nel frattempo e' cresciuto significa dividere anche il codice nuovo, cioe'
mescolare in un solo commit una riorganizzazione e una funzione. Il gate della
divisione sono i 18 test di 04-07, che passano invariati nelle asserzioni.

I pezzi, e la domanda a cui ciascuno risponde:

| Modulo         | Domanda                                                     |
|----------------|-------------------------------------------------------------|
| `comune`       | come si nomina un fallimento, come si normalizza un testo   |
| `celle`        | come si legge un sorgente percent e come si chiamano i suoi blocchi |
| `prosa`        | come il markdown del libro diventa HTML del sito            |
| `dataset`      | quali serie usa un lab, e da dove vengono                   |
| `esecuzione`   | come si esegue un quaderno e si catturano i suoi output     |
| `figure`       | come una figura diventa un file SVG pesato e senza `<style>` |
| `sorgente`     | come le celle diventano blocchi, con i conteggi pinnati     |
| `sito`         | dove si scrive, e con quale contratto                       |
| `bundle`       | come una rotta diventa `lab.json` piu' `it.json`            |

QUESTO `__init__` NON E' UN BARREL. Non ri-esporta nulla: chi usa l'ingest
importa dal modulo che contiene la cosa che gli serve, e un `import *` da qui
avrebbe conservato intatti gli import di prima rendendo la divisione invisibile
— cioe' inutile (e' la lezione di 04-05, dove la stessa divisione fu fatta sul
gate del sito). Qui stanno solo i due percorsi e il ponte verso `cvbook`, che
ogni modulo ha bisogno di trovare gia' pronto.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: La radice del repository. Stessa forma di `costruisci.py`: mai un percorso
#: assoluto scritto nel sorgente, ne' della macchina di build ne' di altro
#: (ASVS V7 — un percorso assoluto finito in un artefatto pubblicato racconta
#: come e' fatta la macchina che l'ha prodotto).
#:
#: `parents[3]` e non `parents[2]`: questo file sta un livello piu' in basso
#: dell'entry point, dentro il pacchetto.
ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "codice" / "lab"

#: `cvbook` vive in `codice/src/` e non e' installato in modo importabile da
#: uno script lanciato a mano; `codice/lab/` serve perche' il pacchetto sia
#: raggiungibile anche quando l'ingest viene importato da un test che parte da
#: un'altra cartella. Sta QUI e in nessun altro modulo: `import estrazione.x`
#: passa sempre di qui prima, quindi due bootstrap sarebbero due copie della
#: stessa riga che un giorno divergono.
for _cartella in (ROOT / "codice" / "src", LAB):
    if str(_cartella) not in sys.path:
        sys.path.insert(0, str(_cartella))
