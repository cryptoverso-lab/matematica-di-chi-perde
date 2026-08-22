"""L'esecuzione dei quaderni: questi test AVVIANO un kernel, e sono lenti.

Stanno separati da `test_estrazione.py` di proposito. Quello dichiara in testa
di non eseguire niente e di girare in tre secondi, ed e' la suite che si lancia
mentre si lavora; mettergli dentro un giro da minuti avrebbe reso falsa la sua
prima riga e avrebbe insegnato a lanciarla con un filtro — cioe' a non
lanciarla.

Tutti i test di questo file sono marcati `lento`. Il giro completo del corpus
misura ~2,5 minuti su una macchina di sviluppo (04-RESEARCH §2.4), ed e' il
prezzo dell'unica prova che conta per LAB-03: che gli output pubblicati vengano
da un'esecuzione vera.

Uso:  uv run python -m pytest codice/testing/test_esecuzione.py -q
      uv run python -m pytest codice/testing -q -m "not lento"   (per saltarli)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[2]
LAB = RADICE / "codice" / "lab"
sys.path.insert(0, str(RADICE / "codice" / "src"))
sys.path.insert(0, str(LAB))

from costruisci import ESCLUSI  # noqa: E402
from estrazione.comune import ProblemaDiIngest  # noqa: E402
from estrazione.esecuzione import esegui  # noqa: E402
from estrazione.figure import BUDGET_FIGURA_BYTE, Figure  # noqa: E402
from estrazione.sito import MARCATORE_SITO, checkout_del_sito  # noqa: E402
from estrazione.sorgente import estrai_dal_sorgente  # noqa: E402

#: Dove sta il checkout del sito quando i test girano a mano. La variabile
#: d'ambiente esiste perche' il percorso NON si scrive in un file: cambia da
#: macchina a macchina, e in CI e' il passo di checkout a deciderlo.
VARIABILE_SITO = "CV_SITO"


def _checkout_del_sito_o_salta() -> Path:
    """Il checkout del sito, o un `skip` che dice come si fa.

    Serve per il binario di `svgo`, che vive nel `node_modules` del sito: senza,
    le figure non si possono ne' ottimizzare ne' pesare. Un test che fallisse
    per un percorso non configurato direbbe «rotto» dove la verita' e' «non
    misurabile qui», ed e' la differenza fra un gate e un fastidio.
    """
    grezzo = os.environ.get(VARIABILE_SITO)
    if grezzo is None:
        candidato = RADICE.parents[1] / "Logika.studio" / "Cryptoverso" / "cryptoverso-website"
        grezzo = str(candidato)
    try:
        sito = checkout_del_sito(grezzo)
    except ProblemaDiIngest:
        pytest.skip(
            f"nessun checkout del sito: manca `{MARCATORE_SITO.as_posix()}` sotto "
            f"`{grezzo}`. Si indica con la variabile d'ambiente {VARIABILE_SITO}."
        )
    if not (sito / "node_modules" / ".bin" / "svgo").exists():
        pytest.skip(f"`svgo` non installato sotto `{grezzo}`: lanciare `pnpm install`.")
    return sito


def _copia_con(tmp_path: Path, nome_file: str, prima: str, dopo: str) -> Path:
    """Una copia di un sorgente vero con UNA cosa cambiata.

    Stessa disciplina di `test_estrazione.py`: un sorgente inventato dentro il
    test proverebbe che l'ingest rifiuta un file inventato, non che rifiuta il
    sorgente vero con un difetto dentro.
    """
    testo = (LAB / nome_file).read_text(encoding="utf-8")
    assert prima in testo, f"il sorgente {nome_file} non contiene piu' {prima!r}"
    copia = tmp_path / nome_file
    copia.write_text(testo.replace(prima, dopo, 1), encoding="utf-8", newline="\n")
    return copia


@pytest.mark.lento
def test_il_pilota_produce_cinque_output_testuali_e_due_figure() -> None:
    """I numeri del pilota, misurati e pinnati.

    SETTE output in tutto: cinque testuali e due figure.

    Erano SEI testuali fino al 2026-08-22. Il sesto era la riga di rumore di
    `pip` (`…: No module named pip`), che la normalizzazione di
    `estrazione/riservatezza.py` ora scarta: non e' un risultato del quaderno,
    e' un messaggio dell'ambiente che lo esegue, e finiva pubblicato su tutte e
    58 le pagine insieme al percorso assoluto della macchina di build.

    Il nome del test e' stato cambiato con il numero. Un test che si chiama
    «sei output» e ne pretende cinque e' una bugia che si legge nel report
    prima ancora di aprire il file, ed e' il modo in cui un conteggio pinnato
    smette di essere un presidio e diventa un residuo.

    Restano dentro `motore locale: .` e `WindowsPath('.')`: quelli SONO
    risultati del quaderno — dicono al lettore dove il motore e' stato
    caricato — e il punto e' il segnaposto relativo che ha preso il posto della
    radice assoluta.
    """
    uscite = esegui(LAB / "lab_05_misurare.py")
    tutte = [u for lista in uscite.values() for u in lista]
    testi = [u for u in tutte if u.tipo == "testo"]
    figure = [u for u in tutte if u.tipo == "figura"]

    assert len(testi) == 5, [u.testo[:40] for u in testi]
    assert len(figure) == 2
    assert all(u.svg.lstrip().startswith("<?xml") or "<svg" in u.svg for u in figure)


@pytest.mark.lento
def test_l_output_piu_lungo_del_corpus_viene_troncato_dichiarando_il_totale() -> None:
    """`calc_08_piano` e' l'unico output del corpus che il limite tocca.

    Trentotto righe misurate (04-RESEARCH §3.5): con il limite a 30 il
    troncamento di D-33 si vede in pagina dal primo giorno invece di essere
    codice mai eseguito. Il test pretende ENTRAMBE le cose — che sia troncato e
    che dichiari il totale — perche' un taglio senza il totale e' l'unica forma
    che D-33 vieta davvero.
    """
    uscite = esegui(LAB / "calc_08_piano.py")
    troncati = [u for lista in uscite.values() for u in lista if u.troncato]

    assert len(troncati) == 1, [u.righe_totali for lista in uscite.values() for u in lista]
    tagliato = troncati[0]
    assert tagliato.righe_totali == 38
    assert len(tagliato.testo.split("\n")) == 30
    assert tagliato.righe_totali > len(tagliato.testo.split("\n"))


@pytest.mark.lento
def test_una_cella_che_lancia_ferma_il_giro_nominando_file_e_cella(tmp_path: Path) -> None:
    """La prova in negativo del primo modo di fallire.

    Un lab che non gira non si pubblica con un output vuoto: la pagina direbbe
    al lettore che il quaderno funziona, e il lettore lo aprirebbe in Colab per
    scoprire che no. Il messaggio deve portare IL FILE e L'INDICE DELLA CELLA:
    un traceback senza posizione manda a cercare.
    """
    copia = _copia_con(
        tmp_path,
        "lab_05_misurare.py",
        'avvio.prepara(["btcusdt"',
        'questa_funzione_non_esiste(["btcusdt"',
    )

    with pytest.raises(ProblemaDiIngest) as fallimento:
        esegui(copia)

    messaggio = str(fallimento.value)
    assert "lab_05_misurare.py" in messaggio
    assert "cella " in messaggio
    assert "NameError" in messaggio


@pytest.mark.lento
def test_la_cella_di_resa_non_compare_fra_gli_output() -> None:
    """P-5: la cella iniettata e' infrastruttura, non contenuto.

    Gli indici restituiti sono quelli del SORGENTE, dove la cella di resa non
    esiste: il primo indice possibile e' 0 e nessuno di essi porta gli output
    della cella 0 del quaderno eseguito. Senza questa traslazione ogni output
    finirebbe nel blocco sbagliato — quello prima.
    """
    uscite = esegui(LAB / "lab_05_misurare.py")

    assert min(uscite) >= 0
    for lista in uscite.values():
        for uscita in lista:
            assert "InlineBackend" not in uscita.testo


# ------------------------------------------------------------------ #
# Le figure, sul corpus INTERO                                        #
# ------------------------------------------------------------------ #


@pytest.mark.lento
def test_il_corpus_produce_quaranta_figure_tutte_leggibili_e_in_budget(tmp_path: Path) -> None:
    """Il conteggio pinnato, le due invarianti e il budget, in un giro solo.

    UN SOLO TEST e non quattro perche' il costo e' l'esecuzione dei 29 quaderni
    (~2,5 minuti): quattro test che rieseguono lo stesso giro sarebbero dieci
    minuti per quattro asserzioni che si possono fare sulla stessa passata.

    Il conteggio vale SOLO sul corpus intero: su un lab solo i totali non
    significano nulla, e un controllo aggirabile con un filtro non e' un
    controllo.

    Il checkout del sito serve per due cose e nessuna delle due e' scrivere:
    il binario di `svgo` e il contratto che dichiara che quella cartella e' il
    posto giusto. Le figure vengono trattate e pesate, e buttate.
    """
    sito = _checkout_del_sito_o_salta()

    figure = 0
    pesi: list[tuple[str, int]] = []
    for percorso in sorted(LAB.glob("*.py")):
        if percorso.name in ESCLUSI:
            continue
        tavole = Figure(sito, percorso.stem, None)
        estrazione = estrai_dal_sorgente(
            percorso, uscite=esegui(percorso), tratta_figura=tavole.tratta
        )
        tavole.verifica_budget_di_pagina()
        figure += estrazione.figure
        pesi.extend(tavole.pesate)

    assert figure == 40, (
        f"il corpus ha prodotto {figure} figure invece di 40: una figura che sparisce "
        "non produce un errore, produce una pagina con un grafico in meno"
    )
    assert all(byte <= BUDGET_FIGURA_BYTE for _, byte in pesi)
    assert max(byte for _, byte in pesi) <= BUDGET_FIGURA_BYTE


@pytest.mark.lento
def test_ogni_figura_del_pilota_ha_il_testo_nel_dom_e_nessuno_style(tmp_path: Path) -> None:
    """Le due invarianti su artefatti veri, e il `byte` che coincide col file.

    `verify:labs` ri-misura le stesse cose dal lato del sito su cio' che e'
    stato committato (D-08): il gate non CREDE al campo `byte`, pesa il file e
    confronta. Qui e' la sorgente che deve produrre due numeri uguali, e le
    figure si scrivono in una cartella temporanea perche' una prova che sporca
    il repository e' una prova che nessuno rifara'.
    """
    sito = _checkout_del_sito_o_salta()
    tavole = Figure(sito, "l05", tmp_path)

    percorso = LAB / "lab_05_misurare.py"
    estrazione = estrai_dal_sorgente(
        percorso, uscite=esegui(percorso), tratta_figura=tavole.tratta
    )
    tavole.verifica_budget_di_pagina()

    assert estrazione.figure == 2
    assert tavole.riscritture > 0

    for identificativo, byte in tavole.pesate:
        file = tmp_path / "figure" / f"{identificativo}.svg"
        assert file.stat().st_size == byte, (
            "il campo `byte` deve essere il peso ESATTO del file: il gate del "
            "sito lo pesa e confronta"
        )
        svg = file.read_text(encoding="utf-8")
        assert "<text" in svg
        assert "<style" not in svg
        assert "viewBox=" in svg
        assert "Libertine" not in svg
