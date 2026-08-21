"""La tabella dell'errata diventa dato, e i suoi fallimenti nominano la riga.

`ERRATA.md` e' un markdown scritto a mano: e' la sola parte del materiale del
libro che nessuna macchina produce, e quindi la sola in cui un refuso di FORMA
— una data scritta a parole, una cella lasciata vuota, una colonna aggiunta in
mezzo — e' non solo possibile ma probabile. L'ingest deve fermarsi su ognuno di
quei casi nominando la riga, perche' l'alternativa non e' un errore: e' una
pagina pubblica che mostra correzioni nell'ordine sbagliato o campi scivolati
di una colonna, senza che niente sia rosso.

Le cinque cose asserite qui sono le cinque prove in negativo del piano 04-17,
AUTOMATIZZATE invece che rieseguite a mano:

1. la riga segnaposto di oggi produce ZERO correzioni, non una correzione vuota
   — e' lo stato reale finche' il libro non e' in stampa;
2. una correzione vera produce UNA correzione con i cinque campi al posto giusto;
3. una data fuori da `AAAA-MM-GG` ferma l'ingest NOMINANDO la riga (LAB-08);
4. una data conforme ma inesistente (`2026-02-31`) lo ferma anche lei;
5. una cella vuota e una colonna aggiunta lo fermano, perche' la prima e' una
   riga che il lettore non puo' usare e la seconda sposta il contenuto di tutte
   le colonne che seguono.

E una sesta, che non e' un fallimento ma il vincolo di D-27: `estrai` guarda la
SOLA tabella, quindi l'indirizzo del colophon che sta nel preambolo non entra
nel dato — cioe' non arriva in `content/` del sito, dove `verify:config` lo
vieta.

Uso:  uv run python -m pytest codice/testing/test_errata.py -q
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[2]
LAB = RADICE / "codice" / "lab"
sys.path.insert(0, str(RADICE / "codice" / "src"))
sys.path.insert(0, str(LAB))

from estrai_errata import CAMPI, ERRATA, SEZIONE, estrai  # noqa: E402
from estrazione.comune import ProblemaDiIngest  # noqa: E402

#: La riga segnaposto, com'e' scritta oggi in `ERRATA.md`. Copiata dal file e
#: non ricostruita: e' la forma che il parser deve riconoscere, e ricostruirla
#: qui significherebbe provare il parser contro la propria idea della riga.
SEGNAPOSTO = (
    "| — | — | — | *nessuna correzione registrata: il libro non è ancora "
    "pubblicato* | — |"
)

CORREZIONE_VERA = (
    "| 2026-09-12 | Marco Rossi | Capitolo 5, figura 5.2 | L'asse delle ordinate "
    "riportava la scala lineare invece di quella logaritmica | — non ancora "
    "ristampato |"
)


def documento() -> str:
    """Il vero `ERRATA.md` del repository, letto e non ricostruito."""
    return (RADICE / ERRATA).read_text(encoding="utf-8")


def con_riga(riga: str) -> str:
    """Il documento vero con la riga segnaposto sostituita da un'altra."""
    testo = documento()
    assert SEGNAPOSTO in testo, (
        "la riga segnaposto di `ERRATA.md` e cambiata: se e cambiata perche il "
        "libro e in stampa e le correzioni sono arrivate, questo test va "
        "riscritto sul nuovo stato, non aggiustato"
    )
    return testo.replace(SEGNAPOSTO, riga)


def test_la_riga_segnaposto_produce_zero_correzioni() -> None:
    correzioni, segnaposto = estrai(documento(), ERRATA)

    assert correzioni == []
    assert segnaposto == 1


def test_una_correzione_vera_esce_coi_cinque_campi_al_posto_giusto() -> None:
    correzioni, segnaposto = estrai(con_riga(CORREZIONE_VERA), ERRATA)

    assert segnaposto == 0
    assert len(correzioni) == 1
    # I cinque campi in chiaro, e non un `set(correzione) == set(CAMPI)`: il
    # difetto vero non e' un campo mancante — lo vedrebbe lo schema del sito —
    # ma una colonna scivolata di uno, che passa qualunque controllo di forma.
    assert tuple(correzioni[0]) == CAMPI
    assert correzioni[0]["data"] == "2026-09-12"
    assert correzioni[0]["segnalatoDa"] == "Marco Rossi"
    assert correzioni[0]["dove"] == "Capitolo 5, figura 5.2"
    assert correzioni[0]["correzione"].startswith("L'asse delle ordinate")
    assert correzioni[0]["inStampa"] == "— non ancora ristampato"


def test_una_data_non_ordinabile_ferma_l_ingest_nominando_la_riga() -> None:
    testo = con_riga(f"{SEGNAPOSTO}\n| 12 settembre 2026 | Marco Rossi | Cap. 5 | Refuso | — |")

    with pytest.raises(ProblemaDiIngest) as fallimento:
        estrai(testo, ERRATA)

    messaggio = str(fallimento.value)
    assert "riga 2" in messaggio
    assert "12 settembre 2026" in messaggio
    assert "AAAA-MM-GG" in messaggio


def test_una_data_conforme_ma_inesistente_ferma_l_ingest() -> None:
    with pytest.raises(ProblemaDiIngest) as fallimento:
        estrai(con_riga("| 2026-02-31 | Marco Rossi | Cap. 5 | Refuso | — |"), ERRATA)

    assert "2026-02-31" in str(fallimento.value)
    assert "calendario" in str(fallimento.value)


def test_una_cella_vuota_ferma_l_ingest_nominando_la_colonna() -> None:
    with pytest.raises(ProblemaDiIngest) as fallimento:
        estrai(con_riga("| 2026-09-12 | Marco Rossi |  | Refuso | — |"), ERRATA)

    assert "`Dove`" in str(fallimento.value)


def test_una_colonna_aggiunta_ferma_l_ingest_invece_di_scivolare() -> None:
    intestazione = "| Data | Segnalato da | Dove | Correzione | Entrata in stampa |"
    testo = documento().replace(
        intestazione,
        "| Data | Segnalato da | Capitolo | Dove | Correzione | Entrata in stampa |",
    )

    with pytest.raises(ProblemaDiIngest) as fallimento:
        estrai(testo, ERRATA)

    assert "intestazione" in str(fallimento.value)


def test_si_ingerisce_la_sola_tabella_e_il_preambolo_resta_fuori() -> None:
    """D-27 e T-4-12: l'indirizzo del colophon non deve arrivare nel sito.

    Il preambolo di `ERRATA.md` contiene l'indirizzo stampato nel colophon, che
    il gate `verify:config` del sito vieta dentro `content/`. La difesa non e'
    una lista di domini vietati ripetuta qui: e' che si ingerisca SOLO la
    tabella.

    L'INDIRIZZO NON E' SCRITTO IN QUESTO TEST, e non e' una posa: nessun host e
    nessun dominio si scrive in un sorgente, e un test che copiasse quello del
    colophon sarebbe la seconda copia di un valore che cambia. Si RICAVA dal
    documento — i frammenti fra backtick che contengono una barra sono gli
    indirizzi che il preambolo cita — e poi si pretende che nessuno di essi
    compaia nel dato estratto. Se un giorno il preambolo non citasse piu' un
    indirizzo, il test lo direbbe invece di diventare verde per vuoto.
    """
    testo = con_riga(CORREZIONE_VERA)
    preambolo = testo.split(SEZIONE)[0]
    indirizzi = [pezzo for pezzo in re.findall(r"`([^`]+)`", preambolo) if "/" in pezzo]

    assert indirizzi, "il preambolo non cita piu un indirizzo: test da rivedere, non da togliere"

    correzioni, _ = estrai(testo, ERRATA)

    for correzione in correzioni:
        for valore in correzione.values():
            for indirizzo in indirizzi:
                assert indirizzo not in valore
