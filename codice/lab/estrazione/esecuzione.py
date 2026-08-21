"""Il quaderno si esegue davvero, e i suoi output si catturano nell'ordine.

E' il punto in cui LAB-03 smette di essere una promessa: la figura che il
lettore vedra' e' quella che il quaderno produce, e l'ha prodotta una macchina
eseguendolo.

L'ESECUZIONE E' OFFLINE, e non per fiducia. `avvio.prepara()` risale l'albero
delle cartelle cercando `codice/src/cvbook/dati.py`; se lo trova — e lo trova,
perche' la directory di lavoro del kernel e' `codice/lab/` — legge gli snapshot
Parquet tracciati in git e non scarica nulla. E' la condizione perche' la catena
giri in una Action senza segreti e senza rete, ed e' anche la ragione per cui
`resources.metadata.path` non e' un dettaglio di comodo: sbagliarlo trasforma
l'ingest in un client HTTP.

LA CELLA DI RESA SI INIETTA IN MEMORIA (P-5). I sorgenti non si toccano: sono
la sorgente autorevole del libro (D-01/D-03). La cella viene inserita in testa
al quaderno letto, e il bundle riparte dalla cella 1 — l'invariante «il bundle
non contiene mai `InlineBackend`» e' gia' un controllo del gate del sito
(04-05), e qui sta la sorgente che deve rispettarlo.

I QUATTRO MODI DI FALLIRE hanno quattro messaggi diversi, ed e' voluto
(04-RESEARCH §2.2): una cella che lancia, una che non termina, un kernel che
non parte e una figura attesa che non arriva sono quattro riparazioni diverse.
Un `except Exception` unico avrebbe detto quattro volte la stessa cosa inutile.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import jupytext
import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError, CellTimeoutError, DeadKernelError

from . import LAB
from .comune import ProblemaDiIngest, normalizza

#: La configurazione della resa, iniettata come PRIMA cella e mai scritta nei
#: sorgenti. Le quattro righe non sono equivalenti fra loro:
#:
#: - `figure_formats = ['svg']` e' cio' che cambia il formato: nessun lab lo
#:   dichiara, e il default dell'inline backend e' PNG;
#: - `dpi: 72` e `bbox_inches: 'tight'` decidono la scala e il ritaglio;
#: - `svg.fonttype = 'none'` e' la riga che decide se la figura e' LEGGIBILE.
#:   Misurato su tre figure (04-RESEARCH §2.3): col default `'path'` gli
#:   elementi `<text>` sono ZERO — ogni etichetta d'asse, ogni legenda e ogni
#:   numero diventa un tracciato vettoriale, e il grafico torna opaco
#:   esattamente come un PNG. Su un sito il cui core value e' essere
#:   verificabile e citabile e' la differenza fra pubblicare i numeri e
#:   pubblicarne l'immagine.
CELLA_DI_RESA = (
    "%config InlineBackend.figure_formats = ['svg']\n"
    "%config InlineBackend.print_figure_kwargs = {'dpi': 72, 'bbox_inches': 'tight'}\n"
    "import matplotlib\n"
    "matplotlib.rcParams['svg.fonttype'] = 'none'\n"
)

#: Secondi concessi a una cella. Il lab piu' lento del corpus impiega 15,5 s IN
#: TOTALE (04-RESEARCH §2.4): 300 s per cella e' due ordini di grandezza sopra
#: il caso reale, cioe' un limite che non tocca nulla di legittimo e ferma un
#: giro appeso prima che consumi sei ore di runner.
TIMEOUT_PER_CELLA = 300

#: Il nome del kernel. Esplicito e non dedotto: `NoSuchKernel` con un nome
#: scritto e' un messaggio riparabile, un kernel scelto in automatico che
#: sparisce e' un giro che fallisce dicendo che manca qualcosa che nessuno ha
#: chiesto.
KERNEL = "python3"

#: Il budget degli output testuali (04-RESEARCH §3.5, misurato su 262 output).
#: 30 righe tronca oggi UN output vero e uno solo (`calc_08_piano`, 38 righe):
#: la resa «output troncato a 30 righe di 38» di D-33 si vede in pagina dal
#: primo giorno invece di essere codice mai eseguito. Il tetto in caratteri
#: copre il caso che il conteggio di righe non vede: un `print` di un array
#: senza a capo.
RIGHE_MASSIME = 30
CARATTERI_MASSIMI = 4000


@dataclass(frozen=True)
class Uscita:
    """Un output di una cella, prima di diventare bundle.

    Neutrale di proposito: qui non si sa dove finiranno le figure — quello lo
    sa `figure.py`, che ha in mano il checkout del sito. Un modulo che
    eseguisse E scrivesse file sarebbe un modulo che non si puo' provare senza
    un disco.
    """

    tipo: str  # "testo" | "figura"
    testo: str = ""
    righe_totali: int = 0
    troncato: bool = False
    svg: str = ""


def _tronca(testo: str) -> Uscita:
    """Il taglio, che DICHIARA quanto ha tagliato (D-33).

    `righeTotali` e' il totale PRIMA del taglio, e viaggia sempre — anche
    quando non si e' tagliato nulla. Il gate del sito rifiuta un troncamento
    senza totale, e ha ragione: «output troncato a 30 righe di 38» non si
    scrive senza il 38, e un taglio che non dice quanto ha tagliato e' un
    output che afferma il falso in silenzio.

    La frase visibile in pagina la compone il sito (04-UI-SPEC §2): il bundle
    porta i numeri, mai la frase. Una frase nel bundle sarebbe una frase non
    traducibile.
    """
    righe = testo.split("\n")
    totali = len(righe)

    tagliato = False
    if totali > RIGHE_MASSIME:
        righe = righe[:RIGHE_MASSIME]
        tagliato = True

    valore = "\n".join(righe)
    if len(valore) > CARATTERI_MASSIMI:
        valore = valore[:CARATTERI_MASSIMI]
        tagliato = True

    return Uscita(tipo="testo", testo=valore, righe_totali=totali, troncato=tagliato)


def _uscite_di_cella(cella, dove: str) -> list[Uscita]:
    """Gli output di una cella eseguita, nell'ordine in cui il kernel li ha emessi.

    L'ordine non e' un dettaglio estetico: un `print` che precede una figura la
    spiega, uno che la segue la commenta. Rimescolarli cambia il discorso del
    lab.

    Un `image/png` qui dentro NON e' un output valido ed e' il quarto modo di
    fallire: significa che la cella di resa non ha fatto effetto, e senza
    accorgersene si pubblicherebbe una figura opaca al posto di una leggibile.
    """
    uscite: list[Uscita] = []

    for output in cella.get("outputs", []):
        tipo = output.get("output_type")

        if tipo == "stream":
            testo = normalizza(output.get("text", "")).strip("\n")
            if testo:
                uscite.append(_tronca(testo))
            continue

        if tipo in {"execute_result", "display_data"}:
            dati = output.get("data", {})
            if "image/svg+xml" in dati:
                svg = dati["image/svg+xml"]
                if isinstance(svg, list):
                    svg = "".join(svg)
                uscite.append(Uscita(tipo="figura", svg=normalizza(svg)))
                continue
            if "image/png" in dati:
                raise ProblemaDiIngest(
                    f"{dove}: la cella ha prodotto una figura in PNG.\n"
                    "  La cella di resa iniettata dall'ingest chiede SVG "
                    "(`InlineBackend.figure_formats = ['svg']`):\n"
                    "  un PNG significa che non ha fatto effetto, e una figura "
                    "raster non ha etichette leggibili\n"
                    "  ne' per un crawler ne' per una sintesi vocale (P-7)."
                )
            testo = dati.get("text/plain", "")
            if isinstance(testo, list):
                testo = "".join(testo)
            testo = normalizza(testo).strip("\n")
            if testo:
                uscite.append(_tronca(testo))
            continue

        if tipo == "error":
            # Non dovrebbe arrivare qui: `allow_errors` resta al default falso,
            # quindi l'esecuzione si e' gia' fermata. Se ci arriva, si ferma
            # comunque invece di pubblicare un traceback come se fosse un
            # risultato.
            raise ProblemaDiIngest(
                f"{dove}: la cella ha prodotto un errore "
                f"(`{output.get('ename', 'errore')}`), e un traceback non e' un output."
            )

    return uscite


def _indice_della_cella_rotta(quaderno) -> int | None:
    """La prima cella con un output di errore, in indici del SORGENTE.

    L'eccezione di `nbclient` porta il traceback ma non la posizione, e un
    traceback senza «quale cella» manda a cercare. Il quaderno in memoria
    invece la porta: la cella che ha lanciato ha un output `error`. Si sottrae
    1 perche' la cella 0 e' quella di resa, che nel sorgente non esiste.
    """
    for indice, cella in enumerate(quaderno.cells):
        for output in cella.get("outputs", []):
            if output.get("output_type") == "error":
                return indice - 1
    return None


def esegui(percorso: Path) -> dict[int, list[Uscita]]:
    """Esegue un sorgente percent e restituisce gli output per indice di cella.

    La chiave e' l'indice della cella NEL SORGENTE, lo stesso che
    `celle_del_sorgente` registra in `Cella.indice`: e' cio' che permette a
    `sorgente.py` di appendere gli output al blocco giusto senza contare due
    volte, e senza che la cella iniettata sposti di uno tutto il resto.
    """
    quaderno = jupytext.read(percorso, fmt="py:percent")
    quaderno.cells.insert(0, nbformat.v4.new_code_cell(CELLA_DI_RESA))

    cliente = NotebookClient(
        quaderno,
        timeout=TIMEOUT_PER_CELLA,
        kernel_name=KERNEL,
        resources={"metadata": {"path": str(LAB)}},
    )

    try:
        cliente.execute()
    except CellTimeoutError as fallimento:
        raise ProblemaDiIngest(
            f"{percorso.name}: una cella non ha terminato entro "
            f"{TIMEOUT_PER_CELLA} secondi.\n"
            "  Il lab piu' lento del corpus impiega 15,5 secondi IN TOTALE "
            "(04-RESEARCH §2.4):\n"
            "  un timeout qui non e' una macchina lenta, e' una cella che "
            "aspetta qualcosa che non arriva.\n"
            f"  {fallimento}"
        ) from fallimento
    except DeadKernelError as fallimento:
        raise ProblemaDiIngest(
            f"{percorso.name}: il kernel e' morto durante l'esecuzione.\n"
            "  Non e' un difetto del lab: e' la macchina che ha finito la "
            "memoria o il processo che e' stato ucciso.\n"
            f"  {fallimento}"
        ) from fallimento
    except CellExecutionError as fallimento:
        indice = _indice_della_cella_rotta(quaderno)
        dove = (
            f"{percorso.name}, cella {indice}"
            if indice is not None
            else f"{percorso.name}, cella ignota"
        )
        raise ProblemaDiIngest(
            f"{dove}: la cella ha lanciato un'eccezione, e il giro si ferma qui.\n"
            "  Un lab che non gira non si pubblica con un output vuoto: la "
            "pagina direbbe al lettore\n"
            "  che il quaderno funziona, e il lettore lo aprirebbe in Colab per "
            "scoprire che no.\n"
            f"  {fallimento}"
        ) from fallimento
    except Exception as fallimento:
        # Il kernel che non parte arriva come `NoSuchKernel` di
        # `jupyter_client`, che non e' un'eccezione di `nbclient`: si riconosce
        # per nome invece di importare un modulo in piu' solo per un `except`.
        if type(fallimento).__name__ != "NoSuchKernel":
            raise
        raise ProblemaDiIngest(
            f"{percorso.name}: il kernel `{KERNEL}` non esiste su questa macchina.\n"
            "  Si installa con `uv run python -m ipykernel install --user "
            f"--name {KERNEL}`.\n"
            "  `ipykernel` e' gia' in `pyproject.toml`: manca la registrazione "
            "del kernel, non il pacchetto."
        ) from fallimento

    uscite: dict[int, list[Uscita]] = {}
    for indice, cella in enumerate(quaderno.cells):
        if indice == 0:
            continue  # la cella di resa non e' contenuto (P-5)
        if cella.cell_type != "code":
            continue
        trovate = _uscite_di_cella(cella, f"{percorso.name}, cella {indice - 1}")
        if trovate:
            uscite[indice - 1] = trovate

    return uscite
