"""I quaderni devono girare. Tutti, dall'inizio alla fine, senza errori.

E' il gate che rende vera la promessa del libro: *premi Esegui e ottieni la
stessa figura stampata nella pagina che stai leggendo.* Un quaderno che non gira
non e' un quaderno incompleto: e' una promessa non mantenuta.

I quaderni si eseguono dalla loro cartella, in modo che `avvio.prepara()` trovi
la repository locale e non scarichi nulla dalla rete. Le figure vanno su un
backend non interattivo: qui interessa che il codice giri, non vederlo.

Uso:  uv run python -m pytest codice/testing/test_quaderni.py -q
      uv run python -m pytest codice/testing -q -m "not lento"   (per saltarli)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[2]
LAB = RADICE / "codice" / "lab"
ESCLUSI = {"avvio.py", "costruisci.py", "genera_indice.py"}

QUADERNI = sorted(p.name for p in LAB.glob("*.py") if p.name not in ESCLUSI)


@pytest.mark.lento
@pytest.mark.parametrize("quaderno", QUADERNI)
def test_il_quaderno_gira(quaderno: str) -> None:
    ambiente = os.environ | {"MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"}
    esito = subprocess.run(
        [sys.executable, quaderno],
        cwd=LAB,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=ambiente,
        timeout=900,
    )
    assert esito.returncode == 0, (
        f"{quaderno} non gira:\n{esito.stderr[-2500:]}"
    )


def test_ogni_quaderno_ha_la_sua_rotta() -> None:
    sys.path.insert(0, str(RADICE / "codice" / "src"))
    from cvbook.link import ROTTE

    attesi = {r.file for r in ROTTE.values()}
    assert set(QUADERNI) == attesi, (
        f"sorgenti senza rotta: {sorted(set(QUADERNI) - attesi)}; "
        f"rotte senza sorgente: {sorted(attesi - set(QUADERNI))}"
    )
