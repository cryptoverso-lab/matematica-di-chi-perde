"""Esecuzione condivisa dei quaderni: ognuno gira una volta sola per sessione.

Due gate diversi guardano gli stessi ventinove quaderni. `test_quaderni`
verifica che girino; `test_quaderni_numeri` verifica **cosa stampano**. Far
partire due volte lo stesso processo raddoppierebbe il tempo della suite senza
aggiungere una sola verifica: l'esito di ogni quaderno viene quindi calcolato
al primo che lo chiede e riusato da tutti gli altri.

I quaderni si eseguono dalla loro cartella, cosi' `avvio.prepara()` trova la
repository locale e non scarica niente dalla rete, e su un backend non
interattivo: qui interessa quello che scrivono, non quello che disegnano.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[2]
LAB = RADICE / "codice" / "lab"


@pytest.fixture(scope="session")
def esito_quaderno():
    """Restituisce una funzione `nome -> CompletedProcess`, con memoria."""
    memoria: dict[str, subprocess.CompletedProcess] = {}

    def esegui(nome: str) -> subprocess.CompletedProcess:
        if nome not in memoria:
            ambiente = os.environ | {"MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"}
            memoria[nome] = subprocess.run(
                [sys.executable, nome],
                cwd=LAB,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=ambiente,
                timeout=900,
            )
        return memoria[nome]

    return esegui
