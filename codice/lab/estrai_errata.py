"""Ingest: dalla tabella di `ERRATA.md` al dato che il sito ordina per data.

`ERRATA.md` e' scritto a mano, in italiano, e vive qui: e' la sede delle
correzioni del libro, e resta tale (D-26). Il sito non lo rende al volo e non
tiene le correzioni in una tabella di Postgres — le riceve GENERATE, come i
bundle dei lab, e le valida col contratto versionato di
`content/labs/schema/lab-bundle.schema.json`.

SI INGERISCE SOLO LA TABELLA `## Correzioni`, e non e' una semplificazione.
Il preambolo di `ERRATA.md` contiene l'indirizzo stampato nel colophon, cioe'
un dominio che il gate `verify:config` del sito VIETA dentro `content/`; e
l'apparato — la spiegazione e le istruzioni per segnalare — vive nei cataloghi
`messages/` del sito perche' deve esistere in due lingue (D-27), mentre le
correzioni restano in italiano perche' si riferiscono al testo italiano del
libro. Un parser che prendesse il documento intero porterebbe di la' un
indirizzo che li' e' rosso, e un apparato in una lingua sola.

ZERO CORREZIONI E' L'ESITO ATTESO, OGGI. La tabella porta una riga segnaposto —
tutte le celle em dash tranne una in corsivo — perche' il libro non e' ancora
pubblicato. Questo script la RICONOSCE e produce un elenco vuoto, non una
correzione con cinque campi vuoti: lo stato vuoto e' uno stato che la pagina
dichiara, e per dichiararlo deve poterlo distinguere da una riga di trattini.

LA DATA SI PRETENDE `AAAA-MM-GG`, E OGNI ALTRA FORMA E' UN ARRESTO CHE NOMINA
LA RIGA. La colonna e' testo libero in un markdown scritto a mano: «12
settembre», «set 2026» e «2026/09/12» si ordinano alfabeticamente, cioe' non si
ordinano. Una tabella di correzioni datate che non si ordina per data e' LAB-08
non soddisfatto, e il difetto non si vedrebbe — la pagina renderebbe le
correzioni nell'ordine sbagliato senza che nulla sia rosso.

Uso:
    uv run python codice/lab/estrai_errata.py --sito <repo del sito>
    uv run python codice/lab/estrai_errata.py --errata <file .md>   # prova, non scrive
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from estrazione import ROOT
from estrazione.comune import ProblemaDiIngest
from estrazione.sito import checkout_del_sito, scrivi_json, versione_del_contratto

#: Il file delle correzioni, nella radice del repository del libro. Il percorso
#: e' relativo e finisce nel dato prodotto (campo `fonte`): e' cio' che dice a
#: chi apre il JSON generato dove si ripara una correzione sbagliata.
ERRATA = "ERRATA.md"

#: Il titolo della sezione da ingerire. Le altre tre — preambolo, «Come
#: segnalare», «Da dove nasce ogni numero del libro» — restano dove sono.
SEZIONE = "## Correzioni"

#: Le cinque colonne, nell'ordine in cui la tabella le scrive.
#:
#: PINNATE, e non dedotte dall'intestazione trovata. E' la stessa disciplina di
#: `ATTESI` in `estrazione/sorgente.py`: un parser che si adatta alla tabella
#: che ha davanti accetta anche il giorno in cui qualcuno aggiunge una colonna
#: in mezzo, e da quel giorno scrive nel campo `dove` il contenuto di un'altra.
COLONNE = ("Data", "Segnalato da", "Dove", "Correzione", "Entrata in stampa")

#: I nomi dei campi prodotti, nello stesso ordine delle colonne. Sono quelli
#: che `content/labs/schema/schema.ts` dichiara in `schemaErrata`.
CAMPI = ("data", "segnalatoDa", "dove", "correzione", "inStampa")

#: La forma della data, pretesa: quella che si ordina.
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: Una cella in corsivo: `*nessuna correzione registrata: ...*`.
CORSIVO = re.compile(r"^\*.+\*$")

#: L'em dash con cui si scrive una cella senza contenuto.
EM_DASH = "—"

#: Le barre verticali che separano le celle, escluse quelle protette da un
#: backslash: `\|` dentro una correzione e' un carattere del testo, non un
#: separatore. Senza questa distinzione una correzione che cita del codice
#: spezzerebbe la riga in sei celle e il messaggio parlerebbe di una colonna
#: in piu' invece che del `\|`.
SEPARATORE = re.compile(r"(?<!\\)\|")


def sezione_delle_correzioni(testo: str, fonte: str) -> list[str]:
    """Le righe della sola sezione `## Correzioni`, senza il resto del file.

    `fonte` e' il nome del file LETTO e non la costante `ERRATA`: le prove in
    negativo si rieseguono su una fixture con `--errata`, e un messaggio che
    nomina sempre `ERRATA.md` manderebbe chi ripara ad aprire il file sbagliato.
    """
    righe = testo.replace("\r\n", "\n").split("\n")

    inizio = None
    for indice, riga in enumerate(righe):
        if riga.strip() == SEZIONE:
            inizio = indice + 1
            break

    if inizio is None:
        raise ProblemaDiIngest(
            f"`{fonte}` non ha una sezione `{SEZIONE}`.\n"
            "  E' la sola sezione che si ingerisce: il resto del documento — il "
            "preambolo con\n"
            "  l'indirizzo del colophon, le istruzioni per segnalare — vive nei "
            "cataloghi del\n"
            "  sito, in due lingue (D-27), e qui non deve entrare."
        )

    fine = len(righe)
    for indice in range(inizio, len(righe)):
        if righe[indice].startswith("## "):
            fine = indice
            break

    return righe[inizio:fine]


def celle(riga: str) -> list[str]:
    """Le celle di una riga di tabella markdown, ripulite dei bordi."""
    nuda = riga.strip()
    if nuda.startswith("|"):
        nuda = nuda[1:]
    if nuda.endswith("|"):
        nuda = nuda[:-1]
    return [pezzo.replace("\\|", "|").strip() for pezzo in SEPARATORE.split(nuda)]


def e_separatore(pezzi: list[str]) -> bool:
    """Vero per la riga `|---|---|…` che divide intestazione e corpo."""
    return all(re.fullmatch(r":?-{3,}:?", pezzo) is not None for pezzo in pezzi)


def e_segnaposto(pezzi: list[str]) -> bool:
    """Vero per la riga che dichiara che non ci sono correzioni.

    La forma e' misurata sul file vero: tutte le celle em dash tranne UNA in
    corsivo. Si pretendono entrambe le cose — un elenco di sole celle em dash
    sarebbe una riga dimenticata a meta', e va vista; una riga con due celle in
    corsivo e' gia' un'altra cosa e non si scarta in silenzio.
    """
    corsive = [pezzo for pezzo in pezzi if CORSIVO.match(pezzo)]
    trattini = [pezzo for pezzo in pezzi if pezzo == EM_DASH]
    return len(corsive) == 1 and len(trattini) == len(pezzi) - 1


def righe_di_tabella(sezione: list[str], fonte: str) -> list[tuple[int, list[str]]]:
    """Le righe di corpo della tabella, con il loro numero nella tabella.

    Verifica l'intestazione contro `COLONNE` prima di guardare il corpo: una
    colonna aggiunta, tolta o rinominata cambia il significato di ogni cella
    che segue, e proseguire significherebbe scrivere nel campo sbagliato un
    dato che sembra a posto.
    """
    tabella = [riga for riga in sezione if riga.strip().startswith("|")]

    if len(tabella) < 2:
        raise ProblemaDiIngest(
            f"`{fonte}` -> `{SEZIONE}`: non c'e' una tabella markdown.\n"
            "  Servono almeno l'intestazione e la riga di separazione."
        )

    intestazione = celle(tabella[0])
    if tuple(intestazione) != COLONNE:
        raise ProblemaDiIngest(
            f"`{fonte}` -> `{SEZIONE}`: l'intestazione della tabella non e' "
            "quella attesa.\n"
            f"  attesa:  {' | '.join(COLONNE)}\n"
            f"  trovata: {' | '.join(intestazione)}\n"
            "  Le colonne sono pinnate in `COLONNE`: una colonna aggiunta o "
            "rinominata sposta\n"
            "  il contenuto di tutte quelle che seguono, e l'ingest scriverebbe "
            "nel campo\n"
            "  sbagliato un dato che sembra a posto. Se la tabella cambia "
            "davvero, si cambia\n"
            "  qui, nello schema del sito e nella pagina, insieme."
        )

    if not e_separatore(celle(tabella[1])):
        raise ProblemaDiIngest(
            f"`{fonte}` -> `{SEZIONE}`: manca la riga di separazione "
            "`|---|---|…` sotto l'intestazione."
        )

    return list(enumerate(map(celle, tabella[2:]), start=1))


def correzione_da_riga(numero: int, pezzi: list[str], fonte: str) -> dict[str, str]:
    """Una riga di tabella diventa una correzione, o un arresto che la nomina.

    Il numero e' quello della riga NELLA TABELLA e non nel file: chi ripara
    apre `ERRATA.md` alla sezione `## Correzioni` e conta le righe da li', ed e'
    l'unico riferimento che resta valido quando il preambolo cambia lunghezza.
    """
    dove = f"`{fonte}` -> `{SEZIONE}`, riga {numero}"

    if len(pezzi) != len(COLONNE):
        raise ProblemaDiIngest(
            f"{dove}: ha {len(pezzi)} celle invece di {len(COLONNE)}.\n"
            f"  {' | '.join(pezzi)}\n"
            "  Una barra verticale dentro il testo di una correzione si scrive "
            "`\\|`."
        )

    for nome, valore in zip(COLONNE, pezzi, strict=True):
        if not valore:
            raise ProblemaDiIngest(
                f"{dove}: la colonna `{nome}` e' vuota.\n"
                "  In una tabella di correzioni una cella vuota non e' «non lo "
                "so»: e' una riga\n"
                "  che il lettore non puo' usare. L'assenza si dichiara con "
                f"l'em dash PIU' la\n"
                f"  parola che dice che cosa manca, mai con il nulla."
            )

    data = pezzi[0]
    if not DATA_ISO.match(data):
        raise ProblemaDiIngest(
            f"{dove}: la data e' `{data}`, e non e' nella forma `AAAA-MM-GG`.\n"
            "  La pagina ordina le correzioni per data DECRESCENTE (LAB-08), "
            "perche' chi torna\n"
            "  sull'errata torna per vedere le nuove. Una data in testo libero "
            "si ordina\n"
            "  alfabeticamente, cioe' non si ordina — e il difetto non si "
            "vedrebbe: si\n"
            "  vedrebbe come una correzione che compare nel posto sbagliato."
        )

    try:
        date.fromisoformat(data)
    except ValueError as errore:
        raise ProblemaDiIngest(
            f"{dove}: la data `{data}` ha la forma giusta ma non e' un giorno "
            "del calendario.\n"
            f"  {errore}"
        ) from errore

    return dict(zip(CAMPI, pezzi, strict=True))


def estrai(testo: str, fonte: str) -> tuple[list[dict[str, str]], int]:
    """Le correzioni e il numero di righe segnaposto scartate."""
    correzioni: list[dict[str, str]] = []
    segnaposto = 0

    for numero, pezzi in righe_di_tabella(sezione_delle_correzioni(testo, fonte), fonte):
        if e_segnaposto(pezzi):
            segnaposto += 1
            continue
        correzioni.append(correzione_da_riga(numero, pezzi, fonte))

    return correzioni, segnaposto


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sito",
        help="percorso del checkout del repo del sito, dove scrivere l'errata",
    )
    parser.add_argument(
        "--errata",
        help="legge un markdown diverso da `ERRATA.md` SENZA scrivere nulla: e' "
        "il modo di rieseguire a mano una prova in negativo su una fixture",
    )
    argomenti = parser.parse_args()

    # I DUE ARGOMENTI SI ESCLUDONO, e non e' pignoleria da riga di comando.
    # `--errata` serve a rieseguire una prova in negativo su una FIXTURE, e il
    # campo `fonte` del dato prodotto dice `ERRATA.md`: accettare i due insieme
    # significherebbe scrivere nel repo del sito le correzioni di un file
    # inventato, dichiarando che vengono dall'errata vera. Un dato falso che si
    # descrive come vero e' peggio di un dato assente.
    if argomenti.errata is not None and argomenti.sito is not None:
        parser.error(
            "`--errata` e `--sito` non stanno insieme: il primo legge una "
            "fixture e non scrive, il secondo scrive cio' che ha letto da "
            f"`{ERRATA}`"
        )

    sorgente = Path(argomenti.errata) if argomenti.errata else ROOT / ERRATA

    try:
        if not sorgente.is_file():
            raise ProblemaDiIngest(f"`{sorgente}` non e' un file.")

        correzioni, segnaposto = estrai(sorgente.read_text(encoding="utf-8"), sorgente.name)

        if argomenti.errata is not None:
            print(
                f"{sorgente.name}: {len(correzioni)} correzioni, "
                f"{segnaposto} righe segnaposto scartate"
            )
            # I CINQUE CAMPI, uno per riga. La prova in negativo che conta non e'
            # «ne ha trovata una»: e' che i cinque campi siano quelli giusti,
            # cioe' che nessuna colonna sia scivolata di uno.
            for numero, correzione in enumerate(correzioni, start=1):
                print(f"  correzione {numero}:")
                for campo, valore in correzione.items():
                    print(f"    {campo:12} {valore}")
            sys.exit(0)

        if argomenti.sito is None:
            parser.error("serve --sito (dove scrivere l'errata) oppure --errata")

        sito = checkout_del_sito(argomenti.sito)
        versione = versione_del_contratto(sito)

        destinazione = sito / "content" / "labs" / "errata.json"
        byte = scrivi_json(
            destinazione,
            {"versione": versione, "fonte": ERRATA, "correzioni": correzioni},
        )

    except ProblemaDiIngest as fallimento:
        print(f"PROBLEMA  {fallimento}")
        sys.exit(1)

    print(
        f"content/labs/errata.json scritto nel repo del sito ({byte} byte, "
        f"contratto versione {versione}): {len(correzioni)} correzioni da "
        f"`{ERRATA}`, {segnaposto} righe segnaposto scartate"
    )
    # Zero e' un fatto da dichiarare, non un motivo per tacere: chi legge questa
    # riga deve poter distinguere «il libro non ha ancora correzioni» da «il
    # parser non ne ha trovate», e la seconda meta' della frase e' cio' che le
    # distingue.
    if not correzioni:
        print(
            "  nessuna correzione: e' lo stato reale finche' il libro non e' in "
            "stampa,\n"
            "  e la pagina lo DICHIARA invece di rendere una tabella di trattini"
        )


if __name__ == "__main__":
    main()
