"""Quali serie usa un lab, e da dove vengono.

Le serie si leggono dall'ALBERO SINTATTICO della cella di setup — e' Python che
legge Python — e la loro provenienza si COPIA dal registro dei dati, mai
ricalcolata (D-20). Sono due regole diverse per due ragioni diverse: la prima
perche' una regex sbaglierebbe il caso multiriga misurato in `lab_17` (P-10),
la seconda perche' un'impronta ricalcolata qui non sarebbe piu' l'impronta che
il registro dichiara.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from . import ROOT
from .celle import MAGIC, Cella
from .comune import ProblemaDiIngest

#: Le voci del registro che il bundle pubblica, nell'ordine in cui il contratto
#: le dichiara. `byte` non c'e': vedi `provenienza_delle_serie`.
CAMPI_DI_PROVENIENZA = ("fonte", "origine", "estratto", "righe", "dal", "al", "sha256", "file")


def serie_dichiarate(setup: Cella, percorso: Path) -> list[str]:
    """Le serie che il lab prepara, lette dall'ALBERO SINTATTICO della cella.

    NON UNA REGEX, ED E' UN DIFETTO MISURATO (04-RESEARCH.md §12 P-10):
    `lab_17_prezzo_e_tempo.py` scrive la chiamata su DUE righe e dichiara otto
    serie; una regex a riga singola ne leggerebbe sei, e il `Dataset` JSON-LD
    della pagina dichiarerebbe il falso — che e' esattamente cio' che D-21
    vieta. Qui e' Python che legge Python: l'unica lettura che non si rompe
    alla prossima formattazione del sorgente.

    I magic vanno commentati prima di analizzare: jupytext li restituisce
    decommentati (`%pip install ...`), che e' la forma giusta per la pagina e
    non e' Python valido.

    Una lista vuota e' un caso VALIDO e non un errore: tre lab non usano dati.
    Una forma che questa funzione non sa leggere e' invece un fallimento che
    nomina il file (D-21): meglio fermarsi che pubblicare un elenco incompleto.
    """
    pulito = MAGIC.sub("# ", setup.sorgente)
    try:
        albero = ast.parse(pulito)
    except SyntaxError as errore:
        raise ProblemaDiIngest(
            f"{percorso.name}: la cella di setup non e' Python analizzabile "
            f"({errore.msg}, riga {errore.lineno}).\n"
            "  Le serie usate dal lab si leggono da li': senza, l'elenco dei "
            "dataset sarebbe un'ipotesi."
        ) from errore

    for nodo in ast.walk(albero):
        if not isinstance(nodo, ast.Call):
            continue
        funzione = nodo.func
        if not isinstance(funzione, ast.Attribute) or funzione.attr != "prepara":
            continue
        if not isinstance(funzione.value, ast.Name) or funzione.value.id != "avvio":
            continue
        return _serie_dagli_argomenti(nodo, percorso)

    raise ProblemaDiIngest(
        f"{percorso.name}: nella cella di setup non c'e' una chiamata "
        "`avvio.prepara([...])` leggibile.\n"
        "  Quali serie un lab usa NON si indovina (D-21): un elenco incompleto "
        "produrrebbe un `Dataset`\n"
        "  JSON-LD che dichiara il falso."
    )


def _serie_dagli_argomenti(chiamata: ast.Call, percorso: Path) -> list[str]:
    """Gli argomenti di `prepara`, o il rifiuto di indovinare."""
    if not chiamata.args:
        raise ProblemaDiIngest(
            f"{percorso.name}: `avvio.prepara()` e' chiamata senza elenco.\n"
            "  Senza argomento `avvio.py` scarica TUTTE e undici le serie, e il "
            "bundle dichiarerebbe come\n"
            "  usate dal lab anche quelle che non tocca. L'elenco si scrive."
        )

    elenco = chiamata.args[0]
    if not isinstance(elenco, (ast.List, ast.Tuple)):
        raise ProblemaDiIngest(
            f"{percorso.name}: l'argomento di `avvio.prepara` non e' un elenco "
            f"scritto per esteso ma un `{type(elenco).__name__}`.\n"
            "  L'ingest non esegue il quaderno per scoprirlo (D-09): la forma "
            "leggibile e' una lista di stringhe,\n"
            "  e una forma nuova va guardata prima di finire in pagina (D-21)."
        )

    serie: list[str] = []
    for voce in elenco.elts:
        if not isinstance(voce, ast.Constant) or not isinstance(voce.value, str):
            raise ProblemaDiIngest(
                f"{percorso.name}: nell'elenco di `avvio.prepara` c'e' una voce "
                "che non e' una stringa scritta per esteso.\n"
                "  Il nome della serie e' cio' che collega il lab al registro "
                "della provenienza: non si calcola."
            )
        serie.append(voce.value)
    return serie


def provenienza_delle_serie(serie: list[str], percorso: Path) -> dict[str, dict]:
    """La provenienza delle serie usate, COPIATA dal registro (D-20).

    Origine, fonte, data di estrazione, righe, intervallo, impronta e percorso
    si ricopiano come stanno: le impronte non si ricalcolano e non si inventano.
    Una serie dichiarata in `prepara` e assente dal registro e' un fallimento
    che NOMINA LA SERIE — pubblicare una provenienza mancante significherebbe
    rendere un `Dataset` JSON-LD che non sa dire ne' origine ne' impronta di un
    dato che la pagina mostra.

    `byte` E' L'UNICO CAMPO CHE IL REGISTRO NON PORTA, ed e' misurato sul file
    che il registro stesso indica. Non e' una deroga a D-20: la dimensione di un
    file non e' un'impronta, e' una proprieta' del file, e misurarla ha come
    effetto secondario di accorgersi che lo snapshot esista davvero. Se il
    registro un giorno dichiarera' anche i byte, questa riga diventa una copia
    come le altre.
    """
    registro = json.loads(
        (ROOT / "codice" / "dati" / "registro.json").read_text(encoding="utf-8")
    )
    provenienza: dict[str, dict] = {}

    for nome in serie:
        voce = registro.get(nome)
        if voce is None:
            disponibili = ", ".join(sorted(registro))
            raise ProblemaDiIngest(
                f"{percorso.name}: la serie `{nome}` e' dichiarata in "
                "`avvio.prepara([...])` ma non e' nel registro.\n"
                "  La provenienza si COPIA da `codice/dati/registro.json` "
                "(D-20): senza, la pagina pubblicherebbe\n"
                "  un `Dataset` di cui non sa dire ne' origine ne' impronta.\n"
                f"  Serie nel registro: {disponibili}"
            )

        mancanti = [campo for campo in CAMPI_DI_PROVENIENZA if campo not in voce]
        if mancanti:
            raise ProblemaDiIngest(
                f"{percorso.name}: la voce `{nome}` del registro non ha "
                f"{', '.join(mancanti)}.\n"
                "  Sono i campi che il blocco di riproducibilita' mostra IN "
                "PAGINA (D-23), non solo nel JSON-LD."
            )

        snapshot = ROOT / voce["file"]
        if not snapshot.is_file():
            raise ProblemaDiIngest(
                f"{percorso.name}: la serie `{nome}` punta a `{voce['file']}`, "
                "che non esiste.\n"
                "  Il bundle dichiara la dimensione del file che il lettore "
                "scarica, e un percorso che\n"
                "  non apre nulla e' un collegamento morto annunciato con un numero."
            )

        copia = {campo: voce[campo] for campo in CAMPI_DI_PROVENIENZA}
        copia["byte"] = snapshot.stat().st_size
        provenienza[nome] = copia

    return provenienza
