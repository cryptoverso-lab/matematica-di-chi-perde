"""cvbook — libreria del libro *Non Fidarti di Me*.

Unico posto in cui nascono i numeri del libro: caricamento degli snapshot,
stile delle figure, metriche e simulazioni. Testo, figure e notebook Colab
usano questa stessa implementazione: se un numero cambia qui, cambia ovunque.
"""

__version__ = "0.1.0"

SEED = 20260816
"""Seed di progetto. Ogni figura ne deriva uno proprio con `seed_for(nome)`."""


def seed_for(nome: str) -> int:
    """Seed deterministico e stabile per una figura o un lab.

    Deriva dal nome invece che da un contatore, così aggiungere una figura
    non cambia i numeri casuali di tutte le altre.
    """
    import hashlib

    h = hashlib.sha256(f"{SEED}:{nome}".encode()).digest()
    return int.from_bytes(h[:4], "big")
