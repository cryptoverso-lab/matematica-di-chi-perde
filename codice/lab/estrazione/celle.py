"""Dal sorgente percent alle celle, e da una cella al suo identificativo.

Qui non si esegue e non si valuta nulla: si legge. Tutto cio' che questo modulo
produce si puo' ottenere aprendo il file con un editore — ed e' la ragione per
cui i test che lo coprono girano anche con `-m "not lento"`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import jupytext

from cvbook.link import RAW_BASE

from .comune import ProblemaDiIngest, normalizza

#: Un magic IPython gia' decommentato da jupytext, in testa a una riga.
MAGIC = re.compile(r"^[ \t]*[%!]", re.M)

#: Le tre forme che `scripts/assert-no-hardcoded-config.mjs:70-77` vieta dentro
#: `content/` del repo del sito. Sono ricopiate qui nella stessa forma — il
#: punto e' una CLASSE (`[.]`) e mai un escape — perche' un bundle che le
#: contenesse renderebbe rosso `pnpm verify:config` DOPO il commit, cioe' nel
#: repository sbagliato. Meglio fermarsi qui.
_SEGMENTO = r"[A-Za-z0-9._-]+"
RIFERIMENTI_REPO_VIETATI = re.compile(
    "|".join(
        [
            rf"github[.]com/{_SEGMENTO}/{_SEGMENTO}",
            rf"raw[.]githubusercontent[.]com/{_SEGMENTO}",
            rf"colab[.]research[.]google[.]com/github/{_SEGMENTO}",
        ]
    ),
    re.I,
)


@dataclass(frozen=True)
class Cella:
    """Una cella del sorgente, gia' normalizzata.

    `dove` e' la posizione leggibile (`lab_05_misurare.py, cella 4`): esiste
    perche' ogni fallimento di questo script deve nominare file e cella, e la
    posizione va calcolata dove si conosce, non ricostruita dove serve.
    """

    tipo: str  # "markdown" | "code"
    sorgente: str
    indice: int
    dove: str


def celle_del_sorgente(percorso: Path) -> list[Cella]:
    """Le celle di un sorgente percent, normalizzate a LF.

    `jupytext.read` restituisce anche le celle vuote di coda che il formato
    percent puo' produrre: si scartano qui, perche' un blocco vuoto nel bundle
    sarebbe un `testo` di lunghezza zero, che il contratto rifiuta — con un
    messaggio che parla di forma invece che di contenuto.
    """
    quaderno = jupytext.read(percorso, fmt="py:percent")
    celle: list[Cella] = []
    for indice, cella in enumerate(quaderno.cells):
        sorgente = normalizza(cella.source).strip("\n")
        if sorgente == "":
            continue
        if cella.cell_type not in {"markdown", "code"}:
            raise ProblemaDiIngest(
                f"{percorso.name}, cella {indice}: tipo di cella `{cella.cell_type}` "
                "non previsto. Il corpus ne ha due sole forme, `# %%` e "
                "`# %% [markdown]`: una terza va guardata prima di renderla."
            )
        celle.append(
            Cella(
                tipo=cella.cell_type,
                sorgente=sorgente,
                indice=indice,
                dove=f"{percorso.name}, cella {indice}",
            )
        )
    return celle


def identificativo(tipo: str, ordinale: int) -> str:
    """`p03` / `c04` — tipo piu' ordinale a due cifre.

    L'IDENTIFICATIVO E L'IMPRONTA SONO DUE CAMPI, e la ragione e' misurata
    (04-RESEARCH.md §1.4). Con una stringa sola (`b07-a3f19c2d`) il cambio di
    una virgola in un capoverso cambierebbe la chiave della traduzione, la
    chiave della deroga di perimetro e il nome del file di figura. Con due
    campi:

    1. la traduzione OBSOLETA si distingue da quella MANCANTE — `en.json`
       registra l'impronta da cui e' stata tradotta, e il gate dice «tradotto
       da X, la sorgente ora e' Y» invece di «blocco assente»;
    2. un blocco SPOSTATO si riconosce — la stessa impronta a un `id` diverso
       e' uno spostamento, non una cancellazione piu' un'aggiunta;
    3. le deroghe del gate di perimetro NON si autodistruggono — una deroga su
       `l05/p03` sopravvive a un refuso corretto.

    `id` cambia quando il blocco si sposta, `impronta` quando il contenuto
    cambia: sono due domande diverse e hanno due risposte.
    """
    return f"{'p' if tipo == 'markdown' else 'c'}{ordinale:02d}"


def sostituisci_raw_base(sorgente: str, dove: str) -> tuple[str, int]:
    """`{{RAW_BASE}}` al posto della radice dei file grezzi (D-40).

    IL PUNTO IN CUI LA FASE SI BLOCCHEREBBE SE NON LO SI VEDESSE PRIMA. Tutte e
    29 le celle di setup contengono per esteso
    `https://raw.githubusercontent.com/<org>/<repo>/<ref>/codice/lab/avvio.py`,
    e il controllo 4 di `scripts/assert-no-hardcoded-config.mjs` vieta esatta-
    mente quella forma dentro `content/`, che e' una delle sue radici. Senza
    questa sostituzione, alla PRIMA esecuzione dell'ingest `pnpm verify:config`
    diventerebbe rosso su 29 file.

    La stringa da sostituire si RICOMPONE dalla fonte unica `cvbook.link`, mai
    battuta a mano: al primo cambio di nome del repository una copia locale
    divergerebbe in silenzio e il segnaposto smetterebbe di comparire.

    Le tre uscite possibili sono state pesate in 04-RESEARCH.md §4.2 e due sono
    state scartate: derogare `content/labs/**` toglie il gate proprio dai file
    che lo giustificano; insegnare al gate lo schema del bundle trasforma un
    controllo generico in uno che si rompe al primo cambio di schema. Resta la
    templatizzazione, che fa di D-14 una regola APPLICATA dal gate che esiste
    gia'.
    """
    if RAW_BASE not in sorgente:
        return sorgente, 0
    return sorgente.replace(RAW_BASE, "{{RAW_BASE}}"), sorgente.count(RAW_BASE)


def vieta_riferimenti_al_repository(testo: str, dove: str, cosa: str) -> None:
    """Nessuna sostituzione PARZIALE arriva al repo del sito.

    Se dopo il passaggio resta nel bundle una qualunque delle forme vietate,
    l'ingest si ferma nominando file e cella. E' la differenza fra un rosso qui
    — dove sta chi ha cambiato qualcosa — e un rosso nel repo del sito dopo il
    commit, che e' il difetto che D-08 esiste per evitare.
    """
    trovato = RIFERIMENTI_REPO_VIETATI.search(testo)
    if trovato is None:
        return
    raise ProblemaDiIngest(
        f"{dove}: {cosa} contiene ancora un riferimento al repository "
        f"(`{trovato.group(0)}`).\n"
        "  Nel bundle stanno percorsi relativi e segnaposto, mai indirizzi "
        "scritti per esteso (D-14/D-40).\n"
        "  Con questa stringa dentro, `pnpm verify:config` del repo del sito "
        "diventerebbe rosso DOPO il commit."
    )


def cella_di_setup(celle: list[Cella], percorso: Path) -> Cella:
    """La PRIMA cella di codice, che deve essere la cella di setup.

    «Prima cella di codice» e non «prima cella che contiene `avvio.prepara`»: in
    otto sorgenti su 29 la stringa compare due volte, la seconda dentro un
    commento che invita ad aggiungere una serie (`lab_05` riga 86). Cercare la
    prima occorrenza qualsiasi significherebbe, il giorno in cui la cella di
    setup sparisse, leggere i dataset da un commento — cioe' pubblicare un
    elenco plausibile e sbagliato invece di fermarsi.

    La sua assenza e' un fallimento che nomina il file: senza cella di setup non
    si sa quali serie il lab usa (D-21), e un `Dataset` JSON-LD incompleto
    dichiara il falso.
    """
    for cella in celle:
        if cella.tipo != "code":
            continue
        if "avvio.prepara(" in cella.sorgente:
            return cella
        break
    raise ProblemaDiIngest(
        f"{percorso.name}: la prima cella di codice non e' una cella di setup "
        "— non contiene `avvio.prepara([...])`.\n"
        "  Ogni lab comincia con la cella che scarica il motore e prepara i "
        "dati: senza, non si sa quali serie il lab usa\n"
        "  e la pagina pubblicherebbe una provenienza inventata (D-21)."
    )
