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

import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[2]
LAB = RADICE / "codice" / "lab"
sys.path.insert(0, str(RADICE / "codice" / "src"))
sys.path.insert(0, str(LAB))

from estrazione.comune import ProblemaDiIngest  # noqa: E402
from estrazione.esecuzione import esegui  # noqa: E402


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
def test_il_pilota_produce_sei_output_testuali_e_due_figure() -> None:
    """I numeri del pilota, misurati e pinnati.

    Sono OTTO output in tutto, che e' il numero che la ricerca dichiara: sei
    testuali e due figure. Il piano li leggeva come «otto testuali piu' due
    figure» — sono dieci, e non e' cio' che il quaderno emette.
    """
    uscite = esegui(LAB / "lab_05_misurare.py")
    tutte = [u for lista in uscite.values() for u in lista]
    testi = [u for u in tutte if u.tipo == "testo"]
    figure = [u for u in tutte if u.tipo == "figura"]

    assert len(testi) == 6, [u.testo[:40] for u in testi]
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
