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
#: `figure` vale 40 ed e' il conteggio misurato eseguendo tutti e 29 i quaderni
#: (04-RESEARCH §2.4). Sta qui per la stessa ragione degli altri tre, ma il
#: difetto che intercetta e' piu' silenzioso: una figura che sparisse — un
#: `plt.show()` tolto, una cella commentata — non produrrebbe nessun errore,
#: produrrebbe una pagina con un grafico in meno. Che nessuno nota, finche' non
#: e' il proprio.
#: `code_inglesi` vale 221 e dice una cosa sola: **ogni** cella markdown del
#: corpus e' bilingue, nessuna esclusa. E' il conteggio che rende sicura la
#: divisione fatta da `prosa.separa_lingue`: se un giorno una cella non venisse
#: riconosciuta, il numero scenderebbe invece di lasciare l'inglese dentro la
#: pagina italiana — che e' precisamente il difetto silenzioso da cui la
#: divisione nasce. `code_inglesi_nude` conta il ramo fragile, quello
#: riconosciuto dall'impronta e non dal marcatore: 29, una per lab, ed e' la
#: sola cella del corpus che non dichiara la propria coda.
#: `prosa_solo_inglese` vale 1: `lab_21_ai.py` cella 17 e' tutta inglese perche'
#: traduce cio' che la cella di codice prima di lei STAMPA. Non produce un
#: blocco italiano, ed e' corretto — ma e' un'eccezione, e un'eccezione contata
#: e' un'eccezione che non puo' diventare due senza che nessuno lo veda.
#: `titoli_specchio` vale 148 ed e' il presidio della STRUTTURA della pagina
#: inglese: tante quante sono le celle il cui ramo italiano apre con un titolo,
#: e in ognuna il corsivo in testa alla coda inglese torna a essere un titolo
#: dello stesso livello (`prosa._inglese_di_cella`). Se domani una coda perdesse
#: il corsivo, l'ingest si fermerebbe; se un titolo italiano sparisse, il numero
#: scenderebbe. In entrambi i casi la differenza si vede qui invece che in una
#: pagina inglese con 148 sezioni in meno.
#: `titolo_en` vale 29: ogni lab dichiara il proprio titolo inglese, e un lab che
#: non lo dichiarasse avrebbe il titolo italiano dentro `en.json`.
ATTESI = {
    "sorgenti": 29,
    "magic": 29,
    "raw_base": 29,
    "titolo": 29,
    "figure": 40,
    "code_inglesi": 221,
    "code_inglesi_nude": 29,
    "prosa_solo_inglese": 1,
    "titoli_specchio": 148,
    "titolo_en": 29,
}


@dataclass
class Estrazione:
    """Il risultato della lettura di un sorgente, prima di diventare bundle."""

    blocchi: list[dict]
    prosa: dict[str, dict]
    #: La stessa prosa in inglese, con gli STESSI identificativi di blocco: e'
    #: la parita' che il gate del sito pretende, e nasce qui invece di essere
    #: ricostruita a mano da chi traduce (D-11, D-35).
    prosa_en: dict[str, dict]
    titolo: str | None
    titolo_en: str | None
    setup: Cella
    dataset: list[str]
    magic: int
    sostituzioni_raw: int
    sostituzioni_titolo: int
    formule: int
    figure: int = 0
    code_inglesi: int = 0
    code_inglesi_nude: int = 0
    prosa_solo_inglese: int = 0
    titoli_specchio: int = 0


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
    prosa_en: dict[str, dict] = {}
    ordinali = {"markdown": 0, "code": 0}
    magic = 0
    sostituzioni_raw = 0
    sostituzioni_titolo = 0
    formule = 0
    figure = 0
    code_inglesi = 0
    code_inglesi_nude = 0
    prosa_solo_inglese = 0
    titoli_specchio = 0
    ordinali_figura: dict[str, int] = {}
    titolo: str | None = None
    titolo_en: str | None = None

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
                resa = converti(testo, cella.dove, prima_cella=ordinali["markdown"] == 1)
            except ProsaSconosciuta as fallimento:
                raise ProblemaDiIngest(str(fallimento)) from fallimento
            vieta_riferimenti_al_repository(resa.html, cella.dove, "la prosa della cella")
            # Il divieto vale sulle DUE lingue: una URL del repository nella
            # coda inglese sarebbe pubblicata su `/en/lab/<codice>` esattamente
            # come lo sarebbe in italiano, e un controllo che guarda una lingua
            # sola e' un controllo che copre meta' delle pagine (D-14).
            vieta_riferimenti_al_repository(
                resa.html_en, cella.dove, "la prosa inglese della cella"
            )
            sostituzioni_titolo += resa.sostituzioni_titolo
            titoli_specchio += resa.titoli_specchio
            if resa.titolo_en:
                titolo_en = resa.titolo_en
            formule += resa.formule
            code_inglesi += 1 if resa.coda_inglese else 0
            code_inglesi_nude += 1 if resa.coda_senza_marcatore else 0
            if resa.html == "":
                # La cella era TUTTA inglese: in italiano non ha niente da
                # dire, e un blocco vuoto in pagina sarebbe peggio della sua
                # assenza. L'ordinale e' gia' stato consumato sopra, quindi
                # gli identificativi delle celle successive NON scorrono: il
                # bundle salta un `p`, e chi confronta due edizioni continua
                # a leggere lo stesso blocco sotto lo stesso nome (D-13).
                prosa_solo_inglese += 1
                continue
            blocchi.append({"id": chiave, "tipo": "prosa", "impronta": impronta})
            prosa[chiave] = {"testo": resa.html, "daImpronta": impronta}
            # `daImpronta` e' la STESSA nelle due lingue, e non e' una
            # semplificazione: le due prose vengono dalla stessa cella, quindi
            # l'impronta da cui sono tradotte e' una sola. E' anche cio' che
            # rende funzionante il presidio di D-13: cambiando la cella cambia
            # l'impronta, e le due traduzioni diventano obsolete insieme —
            # perche' insieme lo sono davvero.
            prosa_en[chiave] = {"testo": resa.html_en, "daImpronta": impronta}
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
        prosa_en=prosa_en,
        titolo=titolo,
        titolo_en=titolo_en,
        setup=setup,
        dataset=serie_dichiarate(setup, percorso),
        magic=magic,
        sostituzioni_raw=sostituzioni_raw,
        sostituzioni_titolo=sostituzioni_titolo,
        formule=formule,
        figure=figure,
        code_inglesi=code_inglesi,
        code_inglesi_nude=code_inglesi_nude,
        prosa_solo_inglese=prosa_solo_inglese,
        titoli_specchio=titoli_specchio,
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
        "figure": sum(e.figure for e in estrazioni),
        "code_inglesi": sum(e.code_inglesi for e in estrazioni),
        "code_inglesi_nude": sum(e.code_inglesi_nude for e in estrazioni),
        "prosa_solo_inglese": sum(e.prosa_solo_inglese for e in estrazioni),
        "titoli_specchio": sum(e.titoli_specchio for e in estrazioni),
        "titolo_en": sum(1 for e in estrazioni if e.titolo_en),
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

