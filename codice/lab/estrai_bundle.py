"""Ingest: dai sorgenti percent dei lab al bundle che il sito legge.

I 29 sorgenti di `codice/lab/` sono la fonte; il bundle e' cio' che il sito
pubblica. Questo script fa la traduzione fra le due cose, e la fa **in locale,
senza rete** (D-09): legge un checkout, non `raw.githubusercontent.com`. E' la
precondizione perche' la catena sia riproducibile a mano anche prima che la
GitHub Action esista (D-07).

LA FORMA PRODOTTA NON E' DECISA QUI. E' il contratto versionato nel repo del
sito, `content/labs/schema/lab-bundle.schema.json`, generato dallo zod che il
sito usa per validare (D-08). Da li' si legge anche il numero di versione: se
il contratto passa alla 2, questo script scrive 2 senza che nessuno se ne
ricordi, e il sito rifiuta il bundle vecchio con il messaggio che nomina
entrambe le versioni.

PERCHE' LE CELLE SI LEGGONO CON `jupytext` E NON CON UN PARSER SCRITTO A MANO.
E' misurato (04-RESEARCH.md §1.2): un parser percent di ~40 righe confrontato
con `jupytext.read(fmt='py:percent')` su tutti e 29 i file da 344 celle
identiche su 373, e le 29 differenze hanno **una sola** causa — i magic IPython,
che il formato percent scrive commentati (`# %pip install ...`) e che jupytext
decommenta in lettura. La pagina deve mostrare la forma del `.ipynb`, cioe'
quella decommentata, perche' descrive cio' che il lettore eseguira' su Colab.
Usando jupytext quella differenza sparisce all'origine, e non resta un parser
da mantenere. Il presidio non e' «funziona su lab_01»: e' il CONTEGGIO PINNATO
di `ATTESI`, che il giorno in cui un lab guadagna un secondo magic diventa
rosso invece di far comparire in pagina codice diverso da quello che gira.

ZERO DIPENDENZE NUOVE. `jupytext` e' gia' in `pyproject.toml`; la validazione
del bundle contro il contratto la fa `pnpm verify:labs` del repo del sito, che
e' lo stesso validatore che il sito usa e quindi non puo' divergere.

Uso:
    uv run python codice/lab/estrai_bundle.py --sito <repo del sito>
    uv run python codice/lab/estrai_bundle.py --sito <repo del sito> --lab lab_05_misurare
    uv run python codice/lab/estrai_bundle.py --sorgente <file .py>   # prova, non scrive
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import jupytext

#: La radice del repository. Stessa forma di `costruisci.py`: mai un percorso
#: assoluto scritto nel sorgente, ne' della macchina di build ne' di altro
#: (ASVS V7 — un percorso assoluto finito in un artefatto pubblicato racconta
#: come e' fatta la macchina che l'ha prodotto).
ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "codice" / "lab"
sys.path.insert(0, str(ROOT / "codice" / "src"))
sys.path.insert(0, str(LAB))

from costruisci import sorgenti  # noqa: E402
from cvbook.link import RAW_BASE, ROTTE  # noqa: E402

#: Il file che dichiara che una cartella e' il checkout del repo del sito.
#: Il percorso arriva da fuori (argomento della riga di comando), quindi prima
#: di aprire o scrivere alcunche' si verifica che sia un checkout DICHIARATO e
#: non una cartella qualsiasi (ASVS V12, T-4-05). Non e' prudenza teorica:
#: `--sito` finisce in una `Action` che lo compone da variabili.
MARCATORE_SITO = Path("content") / "labs" / "schema" / "lab-bundle.schema.json"

#: I conteggi che il corpus intero deve dare. Non sono documentazione: sono il
#: presidio. Una regola che «funziona» su un file e' una regola non misurata;
#: una regola con accanto il numero di volte che tocca il corpus diventa rossa
#: il giorno in cui il corpus cambia sotto di lei.
ATTESI = {
    "sorgenti": 29,
    "magic": 29,
    "raw_base": 29,
    "titolo": 29,
}

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


# ------------------------------------------------------------------ #
# Le celle, e gli identificativi in DUE campi                         #
# ------------------------------------------------------------------ #


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


@dataclass
class Estrazione:
    """Il risultato della lettura di un sorgente, prima di diventare bundle."""

    blocchi: list[dict]
    prosa: dict[str, dict]
    titolo: str | None
    setup: Cella
    magic: int
    sostituzioni_raw: int
    sostituzioni_titolo: int
    formule: int


def estrai_dal_sorgente(percorso: Path) -> Estrazione:
    """Struttura, identificativi e impronte di un sorgente.

    Qui non si esegue nulla: gli output e le figure arrivano dal piano
    successivo, che manda i quaderni in esecuzione. Questo passaggio produce
    cio' che si puo' sapere leggendo, ed e' gia' tutto cio' che serve al gate di
    parita' e alle traduzioni.
    """
    celle = celle_del_sorgente(percorso)
    setup = cella_di_setup(celle, percorso)

    blocchi: list[dict] = []
    ordinali = {"markdown": 0, "code": 0}
    magic = 0
    sostituzioni_raw = 0

    for cella in celle:
        ordinali[cella.tipo] += 1
        chiave = identificativo(cella.tipo, ordinali[cella.tipo])

        if cella.tipo == "markdown":
            blocchi.append(
                {"id": chiave, "tipo": "prosa", "impronta": impronta_breve(cella.sorgente)}
            )
            continue

        magic += len(MAGIC.findall(cella.sorgente))
        sorgente, sostituite = sostituisci_raw_base(cella.sorgente, cella.dove)
        sostituzioni_raw += sostituite
        vieta_riferimenti_al_repository(sorgente, cella.dove, "il sorgente della cella")

        blocchi.append(
            {
                "id": chiave,
                "tipo": "codice",
                "impronta": impronta_breve(sorgente),
                "linguaggio": "python",
                "sorgente": sorgente,
                "output": [],
            }
        )

    return Estrazione(
        blocchi=blocchi,
        prosa={},
        titolo=None,
        setup=setup,
        magic=magic,
        sostituzioni_raw=sostituzioni_raw,
        sostituzioni_titolo=0,
        formule=0,
    )


# ------------------------------------------------------------------ #
# Il repo del sito: si verifica prima di aprire, e prima di scrivere  #
# ------------------------------------------------------------------ #


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


# ------------------------------------------------------------------ #
# Il bundle di un lab                                                 #
# ------------------------------------------------------------------ #


def bundle_di_rotta(rotta, versione: int, eseguito: str) -> tuple[dict, dict, Estrazione]:
    """`lab.json` (e, dal piano 04-07 Task 2, `it.json`) di una rotta.

    I percorsi che finiscono nel bundle sono RELATIVI al repo del libro: la URL
    di Colab, quella dei file grezzi e quella della pagina del repository si
    compongono a render, in un solo modulo del sito (D-14). Un percorso
    assoluto della macchina di build qui dentro sarebbe, oltre che inutile, un
    dettaglio di infrastruttura pubblicato (ASVS V7).
    """
    relativo_py = f"codice/lab/{rotta.file}"
    relativo_ipynb = relativo_py.replace(".py", ".ipynb")
    percorso_py = ROOT / relativo_py
    percorso_ipynb = ROOT / relativo_ipynb

    if not percorso_ipynb.is_file():
        raise ProblemaDiIngest(
            f"{rotta.file}: manca il quaderno `{relativo_ipynb}`.\n"
            "  I `.ipynb` sono artefatti di build e non stanno in git (D-15): "
            "si producono con\n"
            "  `uv run python codice/lab/costruisci.py`."
        )

    testo_py = normalizza(percorso_py.read_text(encoding="utf-8"))
    testo_ipynb = normalizza(percorso_ipynb.read_text(encoding="utf-8"))

    estrazione = estrai_dal_sorgente(percorso_py)

    lab = {
        "versione": versione,
        "codice": rotta.codice.lower(),
        "sorgente": relativo_py,
        "quaderno": relativo_ipynb,
        "eseguito": eseguito,
        "impronteSorgente": {
            "py": impronta_etichettata(testo_py),
            "ipynb": impronta_etichettata(testo_ipynb),
        },
        "dimensioni": {
            "py": byte_normalizzati(testo_py),
            "ipynb": byte_normalizzati(testo_ipynb),
        },
        "dataset": [],
        "provenienza": {},
        "blocchi": estrazione.blocchi,
    }

    prosa = {
        "titolo": estrazione.titolo or rotta.titolo,
        "domanda": rotta.descrizione,
        "blocchi": estrazione.prosa,
        "figure": {},
    }

    return lab, prosa, estrazione


# ------------------------------------------------------------------ #
# Riga di comando                                                     #
# ------------------------------------------------------------------ #


def rotte_scelte(filtro: str | None) -> list:
    """Le rotte da lavorare, filtrate per nome del sorgente.

    Il filtro NON entra mai in un percorso di filesystem: si confronta con i
    nomi che `cvbook.link` dichiara, e un nome sconosciuto e' un errore che
    elenca quelli buoni. Un argomento che diventasse un percorso permetterebbe
    a `--lab ../../qualcosa` di decidere che file aprire.
    """
    tutte = list(ROTTE.values())
    if filtro is None:
        return tutte
    voluto = filtro if filtro.endswith(".py") else f"{filtro}.py"
    scelte = [r for r in tutte if r.file == voluto]
    if not scelte:
        disponibili = ", ".join(sorted(r.file.removesuffix(".py") for r in tutte))
        raise ProblemaDiIngest(
            f"lab sconosciuto: `{filtro}`.\n  Disponibili: {disponibili}"
        )
    return scelte


def verifica_conteggi(estrazioni: list[Estrazione], problemi: list[str]) -> None:
    """I conteggi pinnati, controllati SOLO sul corpus intero.

    Su un lab solo i totali non hanno significato, e un controllo che si possa
    aggirare filtrando non e' un controllo. Su tutti e 29 invece questi numeri
    sono l'unica cosa che distingue «la regola funziona» da «la regola tocca
    esattamente cio' che deve toccare».
    """
    misurati = {
        "magic": sum(e.magic for e in estrazioni),
        "raw_base": sum(e.sostituzioni_raw for e in estrazioni),
        "titolo": sum(e.sostituzioni_titolo for e in estrazioni),
    }
    for nome, atteso in ATTESI.items():
        if nome == "sorgenti":
            continue
        if nome == "titolo" and misurati[nome] == 0:
            continue  # la sostituzione del titolo arriva con `prosa.py`
        if misurati[nome] != atteso:
            problemi.append(
                f"conteggio `{nome}`: {misurati[nome]} sul corpus, atteso {atteso}.\n"
                "  Il numero e' pinnato di proposito: un'occorrenza in piu' o in "
                "meno significa che il corpus\n"
                "  e' cambiato sotto la regola, e va guardata prima di finire in "
                "pagina."
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sito",
        help="percorso del checkout del repo del sito, dove scrivere il bundle",
    )
    parser.add_argument(
        "--lab",
        help="lavora un solo lab, per nome del sorgente (es. lab_05_misurare)",
    )
    parser.add_argument(
        "--sorgente",
        help="legge un singolo file percent SENZA scrivere nulla: e' il modo di "
        "rieseguire a mano una prova in negativo su una fixture",
    )
    parser.add_argument(
        "--eseguito",
        default=date.today().isoformat(),
        help="data dell'esecuzione che ha prodotto gli output (ISO). Dal piano "
        "successivo la scrive l'esecuzione dei quaderni",
    )
    argomenti = parser.parse_args()

    problemi: list[str] = []

    try:
        if argomenti.sorgente is not None:
            percorso = Path(argomenti.sorgente).expanduser().resolve()
            if not percorso.is_file():
                raise ProblemaDiIngest(f"`{argomenti.sorgente}` non e' un file.")
            estrazione = estrai_dal_sorgente(percorso)
            prosa = sum(1 for b in estrazione.blocchi if b["tipo"] == "prosa")
            codice = len(estrazione.blocchi) - prosa
            print(
                f"{percorso.name}: {len(estrazione.blocchi)} blocchi "
                f"({prosa} di prosa, {codice} di codice), "
                f"setup alla cella {estrazione.setup.indice}, "
                f"{estrazione.sostituzioni_raw} sostituzioni di {{{{RAW_BASE}}}}"
            )
            sys.exit(0)

        if argomenti.sito is None:
            parser.error("serve --sito (dove scrivere il bundle) oppure --sorgente")

        sito = checkout_del_sito(argomenti.sito)
        versione = versione_del_contratto(sito)
        rotte = rotte_scelte(argomenti.lab)

        estrazioni: list[Estrazione] = []
        scritti = 0
        for rotta in rotte:
            lab, prosa, estrazione = bundle_di_rotta(rotta, versione, argomenti.eseguito)
            estrazioni.append(estrazione)
            cartella = sito / "content" / "labs" / lab["codice"]
            scrivi_json(cartella / "lab.json", lab)
            scritti += 1

        if argomenti.lab is None:
            if len(rotte) != ATTESI["sorgenti"]:
                problemi.append(
                    f"rotte: {len(rotte)}, attese {ATTESI['sorgenti']}."
                )
            verifica_conteggi(estrazioni, problemi)

    except ProblemaDiIngest as fallimento:
        print(f"PROBLEMA  {fallimento}")
        sys.exit(1)

    for problema in problemi:
        print(f"PROBLEMA  {problema}")

    blocchi = sum(len(e.blocchi) for e in estrazioni)
    print(
        f"{scritti} bundle scritti in content/labs/ del repo del sito "
        f"(contratto versione {versione}): {blocchi} blocchi, "
        f"{sum(e.sostituzioni_raw for e in estrazioni)} sostituzioni di "
        "{{RAW_BASE}}"
    )
    sys.exit(1 if problemi else 0)


if __name__ == "__main__":
    main()
