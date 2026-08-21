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

QUESTO FILE E' SOLO LA RIGA DI COMANDO. Il lavoro sta nel pacchetto
`codice/lab/estrazione/`, un modulo per domanda: leggere le celle, convertire la
prosa, leggere i dataset, eseguire il quaderno, trattare le figure, comporre il
bundle. La divisione e' del piano 04-08 ed e' stata fatta PRIMA di aggiungerci
l'esecuzione: dividere dopo avrebbe mescolato in un commit solo una
riorganizzazione e una funzione nuova.

Uso:
    uv run python codice/lab/estrai_bundle.py --sito <repo del sito>
    uv run python codice/lab/estrai_bundle.py --sito <repo del sito> --lab lab_05_misurare
    uv run python codice/lab/estrai_bundle.py --sorgente <file .py>   # prova, non scrive
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

# Il pacchetto `estrazione` sta accanto a questo file: e' `codice/lab/` a
# entrare in `sys.path` quando lo script viene lanciato, e il suo `__init__`
# mette a posto il resto (`cvbook`). Da qui in giu' si importa dal modulo che
# contiene la cosa, mai da un barrel: la divisione dev'essere visibile negli
# import, altrimenti non e' stata fatta.
from estrazione.bundle import bundle_di_rotta, rotte_scelte
from estrazione.comune import ProblemaDiIngest
from estrazione.sorgente import ATTESI, Estrazione, estrai_dal_sorgente, verifica_conteggi
from estrazione.sito import checkout_del_sito, scrivi_json, versione_del_contratto


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
                f"{estrazione.sostituzioni_raw} sostituzioni di {{{{RAW_BASE}}}}, "
                f"{estrazione.sostituzioni_titolo} di {{{{TITOLO_LIBRO}}}}, "
                f"{estrazione.formule} formule"
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
            scrivi_json(cartella / "it.json", prosa)
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
        "{{RAW_BASE}}, "
        f"{sum(e.sostituzioni_titolo for e in estrazioni)} di "
        "{{TITOLO_LIBRO}}, "
        f"{sum(e.formule for e in estrazioni)} formule"
    )
    sys.exit(1 if problemi else 0)


if __name__ == "__main__":
    main()
