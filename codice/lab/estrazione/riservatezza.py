"""Che cosa un output NON deve raccontare della macchina che l'ha prodotto.

L'ingest esegue i quaderni su UNA macchina e pubblica il risultato su 58
pagine. Tutto cio' che in quel risultato dipende dalla macchina — la radice del
checkout, il percorso dell'interprete, il rumore di un gestore di pacchetti che
li' dentro e' configurato diversamente — non e' un risultato del lab: e' un
dettaglio di chi ha premuto «esegui», e sopravvive nell'artefatto per anni.

E' la minaccia T-4-23, e fino al piano 04-19 era dichiarata mitigata guardando
i SORGENTI (`__init__.ROOT`: nessun percorso assoluto scritto a mano). La
mitigazione era vera e insufficiente: nessun percorso e' scritto nei sorgenti,
e tutti e 29 i bundle ne pubblicavano tre, perche' li stampa il codice eseguito.

Due difetti, non uno:

1. LA DIVULGAZIONE. La radice del checkout esiste su una macchina sola al
   mondo, e pubblicarla dice come quella macchina e' fatta (ASVS V7). Non e'
   ricopiata qui dentro nemmeno come esempio: un file che vieta i percorsi
   assoluti non ne contiene uno;
2. IL DANNO EDITORIALE, che qui e' il peggiore. Fra quelle righe c'e' un
   ERRORE — «No module named pip» — su una pagina il cui unico scopo e'
   dimostrare che il calcolo si riproduce ovunque. Il lettore non sa che quel
   pip non serve: legge che il quaderno e' partito rotto.

TRE MOSSE, E LA TERZA E' QUELLA CHE TIENE. Si scartano le righe che non sono un
risultato, si sostituisce la radice con un segnaposto RELATIVO, e poi si
PRETENDE che non resti un percorso assoluto: le prime due sanno cio' che e'
gia' successo, la terza ferma la classe intera anche su una macchina diversa
da questa. Un ingest che si limitasse a sostituire la propria radice sarebbe
corretto oggi e muto il giorno in cui gira in una Action, dove la radice e'
`/home/runner/work/...` e nessuno la sta cercando.

PERCHE' QUI E NON NEL QUADERNO. `avvio.prepara()` stampa la radice locale
apposta: chi esegue il lab sulla propria macchina vuole sapere dove il motore
e' stato trovato, e togliere quella riga dal sorgente peggiorerebbe il lab per
riparare l'artefatto (D-01/D-03: i sorgenti sono la fonte autorevole). E' la
PUBBLICAZIONE a dover dimenticare la macchina, non l'esecuzione.
"""

from __future__ import annotations

import re

from . import ROOT
from .comune import ProblemaDiIngest

#: La radice diventa questo: il punto, cioe' «la cartella in cui sei».
#:
#: Relativo e non simbolico (`<radice>`) perche' l'output resti leggibile come
#: cio' che e': `motore locale: .` e' una frase vera in qualunque checkout,
#: `motore locale: <radice>` e' una frase su un file di configurazione.
RADICE_SEGNAPOSTO = "."

#: LE RIGHE CHE NON SONO UN RISULTATO, ciascuna con la ragione per cui non lo e'.
#:
#: Le due forme vengono entrambe dal `%pip install` della cella di setup, che
#: sulla macchina di build parla con un ambiente virtuale senza `pip` — mentre
#: su Colab, dove la cella serve davvero, non dice niente di tutto questo. Sono
#: quindi rumore DELLA MACCHINA, non output del lab, e la loro riparazione non
#: sta nel quaderno: il `%pip install` deve restare, perche' e' cio' che fa
#: funzionare il lab per il lettore.
#:
#: Il riconoscimento non nomina mai un percorso: la seconda forma si ancora
#: alla coda della riga, cosi' vale identica su una macchina con un'altra
#: radice o un altro interprete.
RIGHE_DA_SCARTARE: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^Note: you may need to restart the kernel.*$"),
        "l'avviso del gestore di pacchetti, non un risultato del lab",
    ),
    (
        re.compile(r"^.*: No module named pip$"),
        "l'ambiente di build non ha `pip`, e il lettore leggerebbe un errore",
    ),
]

#: IL CRITERIO STRETTO per «questo e' un percorso assoluto».
#:
#: Il criterio LARGO — `[A-Za-z]:[/\\]|/home/|/Users/` — e' quello con cui
#: T-4-23 fu dichiarata chiusa nel piano 04-07, ed e' inservibile: `[A-Za-z]:/`
#: matcha anche il `s://` di ogni `https://`. Sul corpus di oggi conta 92
#: stringhe, e sono quasi tutte URL di provenienza perfettamente legittime. Un
#: criterio che conta le URL come percorsi assoluti non distingue piu' niente
#: il giorno in cui il difetto vero compare — ed e' esattamente cio' che e'
#: successo.
#:
#: Lo sguardo indietro e' cio' che lo rende stretto: una lettera di unita' e'
#: tale solo se PRIMA di lei non c'e' un carattere alfanumerico, e in
#: `https://` prima della `s` c'e' una `p`. Stessa regola per le radici POSIX,
#: che altrimenti si accenderebbero su `esempio.com/home/pagina`.
#:
#: La stessa espressione, con le stesse due famiglie, e' il controllo 8 di
#: `verify:labs` nel repo del sito: due misure indipendenti dello stesso
#: divieto, una dove il difetto nasce e una dove verrebbe pubblicato (D-08).
PERCORSO_ASSOLUTO = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z]:[\\/](?![\\/])"
    r"|(?<![A-Za-z0-9])/(?:home|Users|root)/[A-Za-z0-9._-]"
)


def _senza_le_righe_di_rumore(testo: str) -> str:
    """Le righe che nessuna macchina diversa da questa avrebbe stampato."""
    tenute = [
        riga
        for riga in testo.split("\n")
        if not any(forma.match(riga) for forma, _ in RIGHE_DA_SCARTARE)
    ]
    return "\n".join(tenute)


def _senza_la_radice(testo: str) -> str:
    """La radice del checkout sostituita dal segnaposto, in ENTRAMBE le forme.

    Due forme e non una perche' lo stesso percorso esce dal kernel scritto in
    due modi: `print(Path)` su Windows usa il backslash, la `repr` di una
    `WindowsPath` usa la barra. Sostituirne una sola avrebbe ripulito due righe
    su tre e lasciato la terza a dire tutto — che e' il modo peggiore di
    fallire, perche' il diff sembra risolto.

    La radice si legge da `ROOT`, che ogni macchina calcola per conto suo: qui
    dentro non c'e' nessun percorso scritto a mano.
    """
    ripulito = testo
    for forma in {str(ROOT), ROOT.as_posix()}:
        ripulito = ripulito.replace(forma, RADICE_SEGNAPOSTO)
    return ripulito


def ripulisci(testo: str, dove: str) -> str:
    """L'output come si puo' pubblicare, o un arresto che dice cosa e' rimasto.

    L'arresto non e' pessimismo: e' l'unica parte di questo modulo che vale
    anche per un percorso che nessuno ha ancora visto. Chi lo incontra aggiunge
    una regola qui — non a mano nel bundle, che il primo giro di ingest
    riscriverebbe senza lasciare traccia (D-01, D-06).
    """
    ripulito = _senza_la_radice(_senza_le_righe_di_rumore(testo))

    trovato = PERCORSO_ASSOLUTO.search(ripulito)
    if trovato is not None:
        riga = next(r for r in ripulito.split("\n") if trovato.group(0) in r)
        raise ProblemaDiIngest(
            f"{dove}: un output contiene ancora un percorso assoluto "
            f"(«{riga.strip()}»).\n"
            "  La radice di QUESTO checkout viene gia' sostituita: se ne resta uno, "
            "e' un percorso\n"
            "  di un'altra origine — un interprete, una cache, una cartella "
            "temporanea — e va\n"
            "  trattato con una regola in `estrazione/riservatezza.py`, non "
            "corretto nel bundle.\n"
            "  Un percorso assoluto pubblicato racconta la macchina che l'ha "
            "prodotto (T-4-23)."
        )

    return ripulito
