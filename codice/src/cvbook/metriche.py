"""Metriche — l'unico posto in cui nascono i numeri del libro.

Testo, figure e notebook chiamano queste funzioni: nessuna cifra viene
calcolata due volte in due modi. Tutte le funzioni sono **causali**: il valore
al tempo t usa solo dati fino a t. Verificato dai test in `codice/testing/`.

Convenzione: i rendimenti sono semplici (non logaritmici) salvo dove indicato,
perche' e' cio' che il lettore vede sull'estratto conto.
"""

from __future__ import annotations

import numpy as np

GIORNI_ANNO = 365  # le cripto non chiudono nel weekend


def rendimenti(prezzi: np.ndarray) -> np.ndarray:
    """Rendimenti semplici periodo su periodo. Lunghezza n-1."""
    prezzi = np.asarray(prezzi, dtype=float)
    return prezzi[1:] / prezzi[:-1] - 1.0


def equity(rend: np.ndarray, capitale: float = 1.0) -> np.ndarray:
    """Capitale nel tempo, partendo da `capitale`. Include il punto iniziale."""
    rend = np.asarray(rend, dtype=float)
    return capitale * np.concatenate([[1.0], np.cumprod(1.0 + rend)])


def drawdown(curva: np.ndarray) -> np.ndarray:
    """Distanza percentuale dal massimo precedente, punto per punto.

    Usa `np.maximum.accumulate`: il massimo e' quello **fino a t**, mai il
    massimo dell'intera serie. E' la differenza fra una metrica onesta e una
    che guarda nel futuro.
    """
    curva = np.asarray(curva, dtype=float)
    return curva / np.maximum.accumulate(curva) - 1.0


def drawdown_massimo(curva: np.ndarray) -> float:
    """Il peggior drawdown subito (numero negativo)."""
    return float(drawdown(curva).min())


def recupero_necessario(perdita: float) -> float:
    """Guadagno che serve per tornare in pari dopo una perdita.

    `recupero_necessario(0.5) == 1.0`: perso il 50%, serve il +100%.
    """
    if not 0 <= perdita < 1:
        raise ValueError("la perdita va espressa come frazione in [0, 1)")
    return perdita / (1.0 - perdita)


def cagr(curva: np.ndarray, periodi_anno: int = GIORNI_ANNO) -> float:
    """Rendimento composto annuo. Restituisce NaN se il capitale si azzera."""
    curva = np.asarray(curva, dtype=float)
    if curva[0] <= 0 or curva[-1] <= 0:
        return float("nan")
    anni = (len(curva) - 1) / periodi_anno
    return float((curva[-1] / curva[0]) ** (1 / anni) - 1) if anni > 0 else float("nan")


def volatilita(rend: np.ndarray, periodi_anno: int = GIORNI_ANNO) -> float:
    """Deviazione standard annualizzata dei rendimenti."""
    return float(np.std(np.asarray(rend, dtype=float), ddof=1) * np.sqrt(periodi_anno))


def sharpe(rend: np.ndarray, risk_free: float = 0.0, periodi_anno: int = GIORNI_ANNO) -> float:
    """Sharpe annualizzato. Attenzione: su rendimenti a code grasse dice poco."""
    rend = np.asarray(rend, dtype=float)
    eccesso = rend - risk_free / periodi_anno
    sigma = np.std(eccesso, ddof=1)
    if sigma == 0:
        return float("nan")
    return float(np.mean(eccesso) / sigma * np.sqrt(periodi_anno))


def costi_applicati(rend: np.ndarray, costo_per_operazione: float, operazioni: np.ndarray) -> np.ndarray:
    """Sottrae il costo di transazione dove c'e' stata un'operazione.

    Nessuna simulazione del libro gira senza costi: un backtest a costo zero
    non e' una semplificazione, e' un risultato falso.
    """
    rend = np.asarray(rend, dtype=float)
    operazioni = np.asarray(operazioni, dtype=float)
    if operazioni.shape != rend.shape:
        raise ValueError("operazioni e rendimenti devono avere la stessa lunghezza")
    return rend - operazioni * costo_per_operazione


def rischio_di_rovina(vincite: float, rapporto: float, frazione: float, operazioni: int = 1000,
                      soglia: float = 0.2, campioni: int = 10_000, rng=None) -> float:
    """Probabilita' di scendere sotto `soglia` del capitale iniziale.

    Simulazione, non formula chiusa: cosi' il lettore puo' cambiarne i parametri
    nel notebook e vedere la superficie muoversi.
    """
    rng = rng if rng is not None else np.random.default_rng(0)
    esiti = rng.random((campioni, operazioni)) < vincite
    passi = np.where(esiti, 1 + frazione * rapporto, 1 - frazione)
    curve = np.cumprod(passi, axis=1)
    return float((curve.min(axis=1) < soglia).mean())
