"""Simulazioni — il caso come ipotesi nulla.

Serve a rispondere alla domanda che il libro pone di continuo: *questo
risultato è distinguibile da qualcosa ottenuto per puro caso?* Se non lo è,
non è una prova di bravura, per quanto la curva sia bella.

Tutte le funzioni prendono un generatore esplicito: nessuna casualità globale,
nessun risultato che cambia da un'esecuzione all'altra.
"""

from __future__ import annotations

import numpy as np

from .metriche import drawdown_massimo, equity


def equity_casuali(
    n_curve: int,
    n_periodi: int,
    *,
    rendimento_atteso: float = 0.0,
    volatilita_periodo: float = 0.02,
    rng: np.random.Generator,
) -> np.ndarray:
    """Curve di capitale generate da puro rumore.

    Nessuna abilità, nessun segnale: solo caso. Serve a mostrare che fra queste
    ce ne sono sempre alcune bellissime — quelle che si vedono nelle pubblicità.
    """
    rend = rng.normal(rendimento_atteso, volatilita_periodo, size=(n_curve, n_periodi))
    return np.cumprod(1.0 + rend, axis=1)


def migliori_per_caso(curve: np.ndarray, quante: int = 5) -> np.ndarray:
    """Le curve casuali con il risultato finale migliore.

    E' l'operazione che compie, senza dirlo, chi mostra i propri risultati
    migliori: seleziona ex post da un insieme di tentativi.
    """
    ordine = np.argsort(curve[:, -1])[::-1]
    return curve[ordine[:quante]]


def bootstrap_traiettorie(
    rend: np.ndarray,
    *,
    n_traiettorie: int = 1000,
    rng: np.random.Generator,
    a_blocchi: int | None = None,
) -> np.ndarray:
    """Rimescola i rendimenti realizzati per ottenere futuri alternativi.

    Con `a_blocchi` si campionano blocchi contigui invece di singoli giorni:
    conserva l'autocorrelazione e i grappoli di volatilità, che il rimescolamento
    puntuale distrugge. Sui mercati la versione a blocchi è quasi sempre la più
    onesta delle due.
    """
    rend = np.asarray(rend, dtype=float)
    n = len(rend)

    if a_blocchi is None:
        indici = rng.integers(0, n, size=(n_traiettorie, n))
        return np.cumprod(1.0 + rend[indici], axis=1)

    n_blocchi = int(np.ceil(n / a_blocchi))
    partenze = rng.integers(0, max(n - a_blocchi, 1), size=(n_traiettorie, n_blocchi))
    offset = np.arange(a_blocchi)
    indici = (partenze[:, :, None] + offset[None, None, :]).reshape(n_traiettorie, -1)
    indici = np.clip(indici[:, :n], 0, n - 1)
    return np.cumprod(1.0 + rend[indici], axis=1)


def distribuzione_esiti(traiettorie: np.ndarray) -> dict[str, float]:
    """Cosa dicono mille futuri, invece dell'unico che è capitato."""
    finali = traiettorie[:, -1]
    dd = np.array([drawdown_massimo(t) for t in traiettorie])
    return {
        "mediana_finale": float(np.median(finali)),
        "peggiore_5pct": float(np.percentile(finali, 5)),
        "migliore_5pct": float(np.percentile(finali, 95)),
        "prob_perdita": float((finali < 1.0).mean()),
        "drawdown_mediano": float(np.median(dd)),
        "drawdown_peggiore_5pct": float(np.percentile(dd, 5)),
    }


def quanti_servono(
    vantaggio: float,
    volatilita_periodo: float,
    *,
    potenza: float = 0.8,
    alfa: float = 0.05,
) -> int:
    """Quante osservazioni servono per distinguere un vantaggio dal caso.

    Approssimazione normale a una coda. Serve al capitolo sul potere statistico:
    la risposta, per vantaggi realistici, è quasi sempre umiliante.
    """
    from math import ceil

    from scipy.stats import norm  # import locale: non serve altrove

    z_alfa = norm.ppf(1 - alfa)
    z_potenza = norm.ppf(potenza)
    if vantaggio <= 0:
        raise ValueError("il vantaggio deve essere positivo")
    return int(ceil(((z_alfa + z_potenza) * volatilita_periodo / vantaggio) ** 2))


def curva_da_rendimenti(rend: np.ndarray, capitale: float = 1.0) -> np.ndarray:
    """Ponte verso `metriche.equity`, per non duplicare la logica."""
    return equity(rend, capitale)
