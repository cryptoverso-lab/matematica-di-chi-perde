"""Regole tecniche classiche, scritte una volta sola e sempre causali.

Ogni funzione restituisce un vettore di **posizioni** lungo quanto i prezzi:
`posizione[t]` e' quanto capitale e' investito durante il giorno t, ed e'
decisa con le informazioni disponibili **fino alla chiusura di t-1**. Questo
sfasamento di un giorno e' l'unica cosa che separa un risultato onesto da un
risultato che guarda nel futuro, ed e' verificato dai test di causalita'.

Le regole implementate qui sono quelle che qualunque manuale di analisi
tecnica presenta come fondamentali. Vivono in `cvbook` e non dentro una
figura perche' le usano anche i quaderni di calcolo: se un numero cambia
qui, cambia nel libro e nel notebook insieme.
"""

from __future__ import annotations

import numpy as np


def _media_mobile(x: np.ndarray, finestra: int) -> np.ndarray:
    """Media mobile semplice, NaN finche' la finestra non e' piena."""
    x = np.asarray(x, dtype=float)
    fuori = np.full(len(x), np.nan)
    if finestra <= len(x):
        cumulata = np.concatenate([[0.0], np.cumsum(x)])
        fuori[finestra - 1:] = (cumulata[finestra:] - cumulata[:-finestra]) / finestra
    return fuori


def _ritarda(segnale: np.ndarray) -> np.ndarray:
    """Sposta il segnale di un giorno: si opera sulla base di ieri, non di oggi."""
    posizione = np.zeros(len(segnale))
    posizione[1:] = segnale[:-1]
    return np.nan_to_num(posizione)


def sopra_media(prezzi: np.ndarray, finestra: int = 200) -> np.ndarray:
    """Investito quando il prezzo chiude sopra la sua media mobile."""
    p = np.asarray(prezzi, dtype=float)
    return _ritarda(np.where(p > _media_mobile(p, finestra), 1.0, 0.0))


def sopra_media_con_lookahead(prezzi: np.ndarray, finestra: int = 200) -> np.ndarray:
    """LA STESSA REGOLA, SBAGLIATA APPOSTA. Non usarla per misurare niente.

    E' identica a `sopra_media` meno una chiamata: manca `_ritarda`. La
    posizione di oggi viene decisa con la chiusura di oggi, che al momento della
    decisione non esiste ancora — e il capitolo sui dati che mentono esiste per
    far vedere quanto e' facile scriverla e quanto vale il risultato.

    Vive qui e non dentro una figura per due ragioni. La prima e' che il libro
    stampa la differenza fra le due curve: se la versione sbagliata fosse
    reimplementata a mano nella figura, «la differenza e' una riga di codice»
    sarebbe un'affermazione e non un fatto verificabile. La seconda e' che i
    test di causalita' la usano come contro-esempio: e' la regola che **deve**
    far fallire il test del prezzo alterato, altrimenti quel test non sarebbe
    sensibile a niente.
    """
    p = np.asarray(prezzi, dtype=float)
    return np.nan_to_num(np.where(p > _media_mobile(p, finestra), 1.0, 0.0))


def incrocio_medie(prezzi: np.ndarray, veloce: int = 50, lenta: int = 200) -> np.ndarray:
    """Investito quando la media breve sta sopra la media lunga."""
    p = np.asarray(prezzi, dtype=float)
    return _ritarda(np.where(_media_mobile(p, veloce) > _media_mobile(p, lenta), 1.0, 0.0))


def rottura(prezzi: np.ndarray, finestra: int = 20) -> np.ndarray:
    """Investito dopo un nuovo massimo a N giorni, fuori dopo un nuovo minimo."""
    p = np.asarray(prezzi, dtype=float)
    segnale = np.full(len(p), np.nan)
    stato = 0.0
    for t in range(finestra, len(p)):
        passato = p[t - finestra:t]
        if p[t] >= passato.max():
            stato = 1.0
        elif p[t] <= passato.min():
            stato = 0.0
        segnale[t] = stato
    return _ritarda(segnale)


def forza_relativa(prezzi: np.ndarray, finestra: int = 14) -> np.ndarray:
    """Indice di forza relativa (RSI), media semplice dei guadagni e delle perdite."""
    p = np.asarray(prezzi, dtype=float)
    delta = np.diff(p, prepend=p[0])
    su = _media_mobile(np.clip(delta, 0, None), finestra)
    giu = _media_mobile(-np.clip(delta, None, 0), finestra)
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = np.where(giu > 0, su / giu, np.inf)
    return 100.0 - 100.0 / (1.0 + rs)


def ipervenduto(prezzi: np.ndarray, finestra: int = 14,
                entra: float = 30.0, esci: float = 70.0) -> np.ndarray:
    """Compra quando la forza relativa scende sotto `entra`, esce sopra `esci`."""
    rsi = forza_relativa(prezzi, finestra)
    segnale = np.full(len(prezzi), np.nan)
    stato = 0.0
    for t in range(finestra, len(prezzi)):
        if rsi[t] < entra:
            stato = 1.0
        elif rsi[t] > esci:
            stato = 0.0
        segnale[t] = stato
    return _ritarda(segnale)


def momento(prezzi: np.ndarray, finestra: int = 365) -> np.ndarray:
    """Investito quando il prezzo e' sopra quello di N giorni fa."""
    p = np.asarray(prezzi, dtype=float)
    segnale = np.full(len(p), np.nan)
    segnale[finestra:] = np.where(p[finestra:] > p[:-finestra], 1.0, 0.0)
    return _ritarda(segnale)


def compra_e_tieni(prezzi: np.ndarray) -> np.ndarray:
    """Il metro di confronto: sempre dentro, una sola operazione."""
    return np.ones(len(prezzi))


def esegui(prezzi: np.ndarray, posizione: np.ndarray, *,
           costo: float = 0.0012) -> dict[str, float | np.ndarray]:
    """Applica una posizione a una serie di prezzi, costi inclusi.

    `costo` e' il costo tutto compreso di una singola operazione (commissione +
    spread + slittamento), espresso in frazione del capitale movimentato. Il
    valore di default e' quello usato in tutto il libro.
    """
    p = np.asarray(prezzi, dtype=float)
    pos = np.asarray(posizione, dtype=float)
    if len(pos) != len(p):
        raise ValueError("posizione e prezzi devono avere la stessa lunghezza")

    rend_mercato = p[1:] / p[:-1] - 1.0
    rend_lordo = pos[1:] * rend_mercato
    movimenti = np.abs(np.diff(pos))
    rend_netto = rend_lordo - movimenti * costo

    # L'INGRESSO DEL PRIMO GIORNO SI PAGA. `np.diff` non lo vede — non c'e' un
    # giorno prima da cui differire — e per le regole non cambiava niente,
    # perche' partono tutte fuori dal mercato e la loro prima entrata cade
    # dentro il vettore. Ma il compra-e-tieni parte gia' dentro: il suo unico
    # ingresso non veniva addebitato, e il metro di confronto di tutto il libro
    # viaggiava gratis mentre ogni regola pagava. Un'asimmetria contabile da
    # dodici centesimi per mille euro, tutta a favore della tesi del libro:
    # esattamente il genere di cosa che questo libro contesta agli altri.
    ingresso = abs(float(pos[0])) * costo
    curva = (1.0 - ingresso) * np.concatenate([[1.0], np.cumprod(1.0 + rend_netto)])
    curva_lorda = np.concatenate([[1.0], np.cumprod(1.0 + rend_lordo)])
    return {
        "curva": curva,
        "curva_lorda": curva_lorda,
        "finale": float(curva[-1]),
        "finale_lordo": float(curva_lorda[-1]),
        "operazioni": float(movimenti.sum() + abs(float(pos[0]))),
        "esposizione": float((pos[1:] > 0).mean()),
    }


#: Barre in un anno di contrattazioni. Le cripto non chiudono mai; una borsa
#: azionaria apre circa 252 giorni l'anno.
BARRE_ANNO_CRIPTO = 365
BARRE_ANNO_BORSA = 252


def catalogo(barre_anno: int = BARRE_ANNO_CRIPTO) -> dict:
    """Le sei regole da manuale, con le finestre nell'unita' del mercato.

    Medie mobili, rotture e forza relativa i manuali le dichiarano in **barre**
    ("media a 200 giorni" significa 200 chiusure), e restano quelle su qualunque
    mercato. Il momento no: e' dichiarato in **mesi**, e dodici mesi sono 365
    barre su un mercato che non chiude mai e circa 252 su una borsa che chiude
    nel fine settimana. Applicare 365 a un titolo azionario significherebbe
    misurare il momento a diciassette mesi e chiamarlo dodici.
    """
    return {
        "Incrocio 50/200": lambda p: incrocio_medie(p, 50, 200),
        "Incrocio 20/50": lambda p: incrocio_medie(p, 20, 50),
        "Sopra la media 200": lambda p: sopra_media(p, 200),
        "Rottura a 20 giorni": lambda p: rottura(p, 20),
        "Forza relativa 30/70": lambda p: ipervenduto(p, 14, 30, 70),
        "Momento a 12 mesi": lambda p: momento(p, barre_anno),
    }


#: Le regole del capitolo nella loro forma cripto, che e' quella storica del
#: libro. Resta il nome importato da figure, quaderni e test.
CATALOGO = catalogo(BARRE_ANNO_CRIPTO)
