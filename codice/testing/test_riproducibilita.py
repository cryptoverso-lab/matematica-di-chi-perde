"""I due lab non riproducibili restano DUE, e restano dichiarati.

Il piano 04-08 ha misurato che 27 bundle su 29 escono byte per byte identici a
due esecuzioni di fila, e il piano 04-12 ha deciso come trattare i due che
restano: si escludono dal confronto della Action **per nome, con la ragione
accanto** (voce 10 delle voci rinviate del repo del sito).

Questi test presidiano cio' che puo' marcire di quella decisione:

1. l'elenco non si allunga in silenzio — un terzo lab non riproducibile e' un
   fatto nuovo sulla catena, e va guardato prima di essere aggiunto;
2. ogni voce porta una ragione scritta, non un codice nudo — un'esclusione senza
   motivo e' esattamente il filtro anonimo che questa decisione rifiuta;
3. i codici esistono davvero nel registro delle rotte, cosi' un refuso non
   esclude una cartella che non esiste lasciando fuori confronto quella vera.

Uso:  uv run python -m pytest codice/testing/test_riproducibilita.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE / "codice" / "src"))
sys.path.insert(0, str(RADICE / "codice" / "lab"))

from cvbook.link import ROTTE  # noqa: E402
from estrazione.riproducibilita import (  # noqa: E402
    NON_RIPRODUCIBILI,
    righe_di_dichiarazione,
)


def test_i_lab_non_riproducibili_sono_due() -> None:
    """Il numero e' pinnato come gli altri conteggi della catena: se diventasse
    tre, e' la catena ad aver fatto qualcosa di nuovo, non l'elenco a doversi
    allungare."""
    assert sorted(NON_RIPRODUCIBILI) == ["l19", "l20"]


def test_ogni_esclusione_porta_la_sua_ragione() -> None:
    """Una soglia bassa ma non zero: la ragione deve essere una frase, non una
    parola. E' cio' che distingue una dichiarazione da un filtro."""
    for codice, motivo in NON_RIPRODUCIBILI.items():
        assert len(motivo) > 80, f"{codice}: la ragione non e' scritta, e' accennata"
        assert motivo.strip() == motivo


def test_i_codici_esclusi_esistono_nel_registro() -> None:
    """Un refuso escluderebbe una cartella che non esiste, e lascerebbe nel
    confronto proprio il lab che non si riproduce."""
    codici = {codice.lower() for codice in ROTTE}
    assert set(NON_RIPRODUCIBILI) <= codici


def test_la_dichiarazione_nomina_il_lab_e_il_motivo() -> None:
    righe = righe_di_dichiarazione()
    assert len(righe) == len(NON_RIPRODUCIBILI)
    assert righe[0].startswith("l19: ") and "tempo" in righe[0]
    assert righe[1].startswith("l20: ") and "seme" in righe[1]
