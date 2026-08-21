"""Una rotta diventa `lab.json` piu' `it.json`.

E' il punto in cui i pezzi si compongono: le celle, la prosa, i dataset e — dal
piano 04-08 — gli output e le figure di un'esecuzione vera. I percorsi che
finiscono nel bundle sono RELATIVI al repository del codice: Colab, `raw` e la
pagina del repository si compongono a render, in un solo modulo del sito
(D-14).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from cvbook.link import ROTTE

from . import ROOT
from .comune import (
    ProblemaDiIngest,
    byte_normalizzati,
    impronta_etichettata,
    normalizza,
)
from .dataset import provenienza_delle_serie
from .esecuzione import esegui
from .figure import Figure
from .sorgente import Estrazione, estrai_dal_sorgente


def figure_conservate(percorso_it: Path, prodotte: Iterable[str]) -> dict:
    """L'apparato editoriale delle figure gia' scritto a mano, TENUTO.

    E' l'unico campo del bundle che questa catena non sa produrre. `alt`,
    `didascalia` e `metodo` sono lavoro editoriale (UI-SPEC 3.4, LAB-03): li
    scrive una persona nel repo del sito, guardando la figura. Fino al piano
    04-10 `it.json` veniva ricomposto da zero con un `"figure": {}` LETTERALE,
    e la conseguenza era misurata: rieseguendo l'ingest su `lab_05_misurare` i
    due `alt` del pilota sparivano, `pnpm verify:labs` diventava rosso con «la
    figura non ha un `alt` in questa lingua», e il testo perduto non era piu'
    da nessuna parte. Un `alt` scritto a mano aveva la vita di una
    riesecuzione — cioe' di una GitHub Action.

    IL FILTRO SUGLI IDENTIFICATIVI PRODOTTI NON E' UN DETTAGLIO. Senza, l'`alt`
    di una figura che il quaderno non emette piu' sopravvivrebbe per sempre nel
    bundle: e' esattamente il residuo che un ingest esiste per non produrre.
    L'ordine e' quello delle figure prodotte, non quello del file su disco,
    cosi' due esecuzioni di fila scrivono lo stesso byte.

    `en.json` non passa di qui perche' l'ingest non lo scrive affatto: la
    fusione riguarda la sola lingua in cui l'apparato nasce.
    """
    if not percorso_it.is_file():
        return {}
    try:
        esistente = json.loads(percorso_it.read_text(encoding="utf-8"))
    except json.JSONDecodeError as errore:
        raise ProblemaDiIngest(
            f"`{percorso_it.as_posix()}` esiste ma non e' JSON leggibile: "
            f"{errore}.\n"
            "  Va letto PRIMA di riscriverlo, perche' porta l'apparato\n"
            "  editoriale delle figure che questa catena non sa riprodurre:\n"
            "  sovrascriverlo alla cieca lo cancellerebbe."
        ) from errore
    vecchie = esistente.get("figure") if isinstance(esistente, dict) else None
    if not isinstance(vecchie, dict):
        return {}
    return {
        identificativo: vecchie[identificativo]
        for identificativo in prodotte
        if identificativo in vecchie
    }


def bundle_di_rotta(
    rotta, versione: int, eseguito: str, sito: Path
) -> tuple[dict, dict, Estrazione]:
    """`lab.json` (e, dal piano 04-07 Task 2, `it.json`) di una rotta.

    I percorsi che finiscono nel bundle sono RELATIVI al repo del libro: la URL
    di Colab, quella dei file grezzi e quella della pagina del repository si
    compongono a render, in un solo modulo del sito (D-14). Un percorso
    assoluto della macchina di build qui dentro sarebbe, oltre che inutile, un
    dettaglio di infrastruttura pubblicato (ASVS V7).

    L'ORDINE DEI TRE PASSAGGI e' quello che rende falsificabile il budget: si
    esegue, si trattano le figure una per una — e una fuori budget ferma il giro
    qui — e solo alla fine si controlla la somma della pagina. Un lab che sfonda
    non scrive un `lab.json` a meta': l'eccezione risale prima che qualcosa
    venga scritto.
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

    cartella = sito / "content" / "labs" / rotta.codice.lower()
    figure = Figure(sito, rotta.codice.lower(), cartella)
    estrazione = estrai_dal_sorgente(
        percorso_py, uscite=esegui(percorso_py), tratta_figura=figure.tratta
    )
    figure.verifica_budget_di_pagina()

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
        "dataset": estrazione.dataset,
        "provenienza": provenienza_delle_serie(estrazione.dataset, percorso_py),
        "blocchi": estrazione.blocchi,
    }

    prosa = {
        "titolo": estrazione.titolo or rotta.titolo,
        "domanda": rotta.descrizione,
        "blocchi": estrazione.prosa,
        # L'apparato delle figure e' l'UNICO campo editoriale del bundle: lo
        # scrive una persona nel repo del sito, non questa catena. Percio' si
        # FONDE con cio' che sta su disco invece di essere ricomposto — vedi
        # `figure_conservate`, che spiega il difetto misurato.
        "figure": figure_conservate(
            cartella / "it.json", (identificativo for identificativo, _ in figure.pesate)
        ),
    }

    return lab, prosa, estrazione


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
