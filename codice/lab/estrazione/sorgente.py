"""Le celle diventano blocchi, e i conteggi sono pinnati sul corpus intero.

E' il modulo che tiene insieme gli altri: legge le celle, converte la prosa,
sostituisce i segnaposto, calcola le impronte, e restituisce un'`Estrazione` —
tutto cio' che si puo' sapere di un lab SENZA eseguirlo. Gli output e le figure
li aggiunge `bundle.py` chiamando `esecuzione` e `figure`, perche' quelli
richiedono un kernel.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .celle import (
    MAGIC,
    Cella,
    cella_di_setup,
    celle_del_sorgente,
    identificativo,
    sostituisci_raw_base,
    vieta_riferimenti_al_repository,
)
from .comune import ProblemaDiIngest, impronta_breve
from .dataset import serie_dichiarate
from .prosa import ProsaSconosciuta, converti, titolo_e_corpo

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


@dataclass
class Estrazione:
    """Il risultato della lettura di un sorgente, prima di diventare bundle."""

    blocchi: list[dict]
    prosa: dict[str, dict]
    titolo: str | None
    setup: Cella
    dataset: list[str]
    magic: int
    sostituzioni_raw: int
    sostituzioni_titolo: int
    formule: int
    figure: int = 0


def estrai_dal_sorgente(
    percorso: Path,
    uscite: dict[int, list] | None = None,
    tratta_figura: Callable[[str, str], tuple[str, int]] | None = None,
) -> Estrazione:
    """Struttura, identificativi, impronte — e, se ci sono, gli output.

    `uscite` arriva da `esecuzione.esegui` ed e' indicizzato per indice di cella
    del SORGENTE: senza, i blocchi di codice escono con `output: []`, che e' il
    modo in cui `--sorgente` legge un file senza avviare un kernel. Con, ogni
    blocco riceve i propri output nell'ordine in cui il kernel li ha emessi.

    `tratta_figura` e' il pezzo che scrive i file SVG, e arriva da fuori perche'
    QUI non si sa dove vanno: la cartella e' quella del lab nel checkout del
    sito, che conosce solo `bundle.py`. L'identificativo della figura invece si
    deriva qui, dove si conosce l'identificativo del blocco — `c01-1` e' la
    prima figura di `c01`, ed e' la stessa chiave con cui `{it,en}.json`
    indicizza `figure`. Derivarla in due posti significherebbe che il controllo
    del peso e quello dell'`alt` cercano due chiavi diverse per la stessa
    figura (04-05).
    """
    if uscite and tratta_figura is None:
        raise ProblemaDiIngest(
            f"{percorso.name}: ci sono output da collocare ma nessun modo di "
            "scrivere le figure.\n"
            "  E' un errore di programmazione dell'ingest, non del lab."
        )
    celle = celle_del_sorgente(percorso)
    setup = cella_di_setup(celle, percorso)

    blocchi: list[dict] = []
    prosa: dict[str, dict] = {}
    ordinali = {"markdown": 0, "code": 0}
    magic = 0
    sostituzioni_raw = 0
    sostituzioni_titolo = 0
    formule = 0
    figure = 0
    ordinali_figura: dict[str, int] = {}
    titolo: str | None = None

    for cella in celle:
        ordinali[cella.tipo] += 1
        chiave = identificativo(cella.tipo, ordinali[cella.tipo])

        if cella.tipo == "markdown":
            # L'impronta si calcola sul sorgente della cella COM'E' NEL FILE, non
            # sull'HTML che ne esce: e' il testo del libro a cambiare, ed e' su
            # quel cambiamento che il gate di parita' deve accendersi. Un'impronta
            # calcolata sull'uscita cambierebbe anche il giorno in cui cambia
            # questo convertitore, rendendo obsolete traduzioni che nessuno ha
            # toccato.
            impronta = impronta_breve(cella.sorgente)
            testo = cella.sorgente
            if ordinali["markdown"] == 1:
                titolo, testo = titolo_e_corpo(testo, cella.dove)
                if titolo is None:
                    raise ProblemaDiIngest(
                        f"{percorso.name}: la prima cella markdown non comincia "
                        "con il titolo del lab (`# ...`).\n"
                        "  Il titolo e' un campo del bundle, non un capoverso: "
                        "senza, la pagina non ha un titolo\n"
                        "  e il campo `titolo` di `it.json` andrebbe inventato."
                    )
            try:
                resa = converti(testo, cella.dove)
            except ProsaSconosciuta as fallimento:
                raise ProblemaDiIngest(str(fallimento)) from fallimento
            vieta_riferimenti_al_repository(resa.html, cella.dove, "la prosa della cella")
            sostituzioni_titolo += resa.sostituzioni_titolo
            formule += resa.formule
            blocchi.append({"id": chiave, "tipo": "prosa", "impronta": impronta})
            prosa[chiave] = {"testo": resa.html, "daImpronta": impronta}
            continue

        magic += len(MAGIC.findall(cella.sorgente))
        sorgente, sostituite = sostituisci_raw_base(cella.sorgente, cella.dove)
        sostituzioni_raw += sostituite
        vieta_riferimenti_al_repository(sorgente, cella.dove, "il sorgente della cella")

        output: list[dict] = []
        for uscita in (uscite or {}).get(cella.indice, []):
            if uscita.tipo == "testo":
                output.append(
                    {
                        "kind": "testo",
                        "valore": uscita.testo,
                        "righeTotali": uscita.righe_totali,
                        "troncato": uscita.troncato,
                    }
                )
                continue
            figure += 1
            ordinali_figura[chiave] = ordinali_figura.get(chiave, 0) + 1
            file, byte = tratta_figura(f"{chiave}-{ordinali_figura[chiave]}", uscita.svg)
            output.append({"kind": "figura", "file": file, "byte": byte})

        blocchi.append(
            {
                "id": chiave,
                "tipo": "codice",
                "impronta": impronta_breve(sorgente),
                "linguaggio": "python",
                "sorgente": sorgente,
                "output": output,
            }
        )

    return Estrazione(
        blocchi=blocchi,
        prosa=prosa,
        titolo=titolo,
        setup=setup,
        dataset=serie_dichiarate(setup, percorso),
        magic=magic,
        sostituzioni_raw=sostituzioni_raw,
        sostituzioni_titolo=sostituzioni_titolo,
        formule=formule,
        figure=figure,
    )


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
        if misurati[nome] != atteso:
            problemi.append(
                f"conteggio `{nome}`: {misurati[nome]} sul corpus, atteso {atteso}.\n"
                "  Il numero e' pinnato di proposito: un'occorrenza in piu' o in "
                "meno significa che il corpus\n"
                "  e' cambiato sotto la regola, e va guardata prima di finire in "
                "pagina."
            )

