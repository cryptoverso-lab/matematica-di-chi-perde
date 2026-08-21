"""Le celle diventano blocchi, e i conteggi sono pinnati sul corpus intero.

E' il modulo che tiene insieme gli altri: legge le celle, converte la prosa,
sostituisce i segnaposto, calcola le impronte, e restituisce un'`Estrazione` —
tutto cio' che si puo' sapere di un lab SENZA eseguirlo. Gli output e le figure
li aggiunge `bundle.py` chiamando `esecuzione` e `figure`, perche' quelli
richiedono un kernel.
"""

from __future__ import annotations

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
    prosa: dict[str, dict] = {}
    ordinali = {"markdown": 0, "code": 0}
    magic = 0
    sostituzioni_raw = 0
    sostituzioni_titolo = 0
    formule = 0
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
        prosa=prosa,
        titolo=titolo,
        setup=setup,
        dataset=serie_dichiarate(setup, percorso),
        magic=magic,
        sostituzioni_raw=sostituzioni_raw,
        sostituzioni_titolo=sostituzioni_titolo,
        formule=formule,
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

