"""Le due coordinate di un movimento — ampiezza e durata — e il ruolo del volume.

Un movimento di mercato si descrive con due numeri: **quanto** si e' spostato il
prezzo e **quanto a lungo** ci ha messo. Il volume e' la terza colonna che ogni
piattaforma mostra, e la domanda del capitolo e' se sia davvero una terza
coordinata o la conseguenza delle prime due e del calendario.

Qui vivono gli attrezzi per rispondere: la segmentazione in movimenti, la
decomposizione di Shapley dell'R quadro fra blocchi di variabili, e le date di
scadenza dei derivati. Nessuna funzione guarda avanti nel tempo tranne la
segmentazione, che per definizione riconosce un estremo solo dopo l'inversione:
serve a **descrivere** movimenti conclusi, mai a produrre un segnale.
"""

from __future__ import annotations

import calendar
import datetime as dt
import itertools
import math
from dataclasses import dataclass

import numpy as np

#: Soglia di inversione di riferimento del libro. Le figure la dichiarano e i
#: quaderni la lasciano cambiare: fra il 3% e il 10% le conclusioni non si
#: muovono, ed e' un controllo che il lettore puo' rifare.
SOGLIA = 0.05

#: Finestra su cui si normalizza il volume, in giorni. Un anno di borsa: cosi'
#: il confronto fra un giorno del 2003 e uno del 2025 non e' falsato dal fatto
#: che negli anni il mercato e' semplicemente diventato piu' grande.
FINESTRA_VOLUME = 250


def movimenti(chiusure: np.ndarray, soglia: float = SOGLIA) -> list[tuple[int, int]]:
    """Segmenta la serie in movimenti alternati fra estremi successivi.

    Un estremo diventa definitivo quando il prezzo si e' allontanato di almeno
    `soglia` (in logaritmo) nella direzione opposta. E' il classico zigzag, con
    una avvertenza che il libro ripete: **l'ultimo estremo non e' mai
    confermato**, e per confermare quelli passati serve il futuro. Una
    segmentazione del genere descrive la storia, non anticipa niente.
    """
    lp = np.log(np.asarray(chiusure, dtype=float))
    estremi = [0]
    direzione = 0
    alto_i = basso_i = 0
    alto = basso = lp[0]

    for i in range(1, len(lp)):
        x = lp[i]
        if x > alto:
            alto, alto_i = x, i
        if x < basso:
            basso, basso_i = x, i
        if direzione >= 0 and alto - x >= soglia:
            estremi.append(alto_i)
            direzione = -1
            k = int(np.argmin(lp[alto_i:i + 1])) + alto_i
            basso, basso_i = lp[k], k
            alto, alto_i = x, i
        elif direzione <= 0 and x - basso >= soglia:
            estremi.append(basso_i)
            direzione = +1
            k = int(np.argmax(lp[basso_i:i + 1])) + basso_i
            alto, alto_i = lp[k], k
            basso, basso_i = x, i

    estremi = sorted(set(estremi))
    return [(estremi[k], estremi[k + 1]) for k in range(len(estremi) - 1)]


def volume_relativo(volume: np.ndarray, finestra: int = FINESTRA_VOLUME) -> np.ndarray:
    """Volume diviso per la sua mediana dei giorni precedenti. Causale."""
    v = np.asarray(volume, dtype=float)
    fuori = np.full(len(v), np.nan)
    for i in range(finestra, len(v)):
        mediana = np.median(v[i - finestra:i])
        if mediana > 0:
            fuori[i] = v[i] / mediana
    return fuori


@dataclass(frozen=True)
class Tavolo:
    """Un movimento per riga, tre colonne: velocita', durata, volume.

    La colonna si chiama **velocita'** e non «prezzo», ed e' una correzione che
    e' costata due giri. Non e' il livello del prezzo: e' quanta strada faceva
    il prezzo in un giorno, cioe' l'oscillazione tipica delle sedute di quel
    movimento. Chiamarla «prezzo» faceva leggere la decomposizione come «il
    livello spiega l'ampiezza», che non e' quello che misura.
    """

    ampiezza: np.ndarray   # |variazione logaritmica| fra i due estremi
    durata: np.ndarray     # barre fra i due estremi
    velocita: np.ndarray   # deviazione standard dei rendimenti giornalieri del tratto
    volume: np.ndarray     # volume relativo medio del tratto

    def __len__(self) -> int:
        return len(self.ampiezza)


def tavolo(chiusure: np.ndarray, volume: np.ndarray, soglia: float = SOGLIA,
           durata_minima: int = 3) -> Tavolo:
    """Costruisce il tavolo dei movimenti conclusi.

    Le tre colonne sono misurate **sulla stessa finestra e con lo stesso
    trattamento**: e' cio' che rende leale il confronto fra loro. Il volume non
    e' penalizzato da nessuna scelta che non sia stata applicata anche al
    prezzo e al tempo.
    """
    c = np.asarray(chiusure, dtype=float)
    r = np.diff(np.log(c), prepend=np.nan)
    vrel = volume_relativo(volume)

    righe = []
    for a, b in movimenti(c, soglia):
        if a < FINESTRA_VOLUME + 10 or b - a < durata_minima:
            continue
        ampiezza = abs(math.log(c[b] / c[a]))
        sigma = float(np.std(r[a + 1:b + 1], ddof=1))
        tratto = vrel[a + 1:b + 1]
        tratto = tratto[np.isfinite(tratto)]
        medio = float(tratto.mean()) if len(tratto) else float("nan")
        if ampiezza > 0 and sigma > 0 and np.isfinite(medio) and medio > 0:
            righe.append((ampiezza, b - a, sigma, medio))

    dati = np.array(righe, dtype=float).reshape(-1, 4)
    return Tavolo(dati[:, 0], dati[:, 1], dati[:, 2], dati[:, 3])


def r_quadro(y: np.ndarray, regressori: list[np.ndarray]) -> float:
    """R quadro di una regressione lineare con intercetta. Zero se non c'e' nulla."""
    y = np.asarray(y, dtype=float)
    if not regressori:
        return 0.0
    X = np.column_stack([np.ones(len(y))] + [np.asarray(c, float) for c in regressori])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residui = y - X @ beta
    scarto = y - y.mean()
    return float(1.0 - residui @ residui / (scarto @ scarto))


def shapley(y: np.ndarray, blocchi: dict[str, list[np.ndarray]]) -> dict[str, float]:
    """Ripartisce l'R quadro fra blocchi di variabili, senza arbitrio.

    Con regressori correlati la domanda «quanto spiega questa variabile» non ha
    una risposta unica: dipende dall'ordine in cui le si inserisce. La quota di
    Shapley e' la media del contributo marginale su **tutti** gli ordini
    possibili — l'unica ripartizione che tratta i blocchi allo stesso modo e la
    cui somma e' esattamente l'R quadro del modello completo.
    """
    nomi = list(blocchi)
    k = len(nomi)
    memoria: dict[tuple[str, ...], float] = {}

    def R(sottoinsieme) -> float:
        chiave = tuple(sorted(sottoinsieme))
        if chiave not in memoria:
            colonne = [c for nome in chiave for c in blocchi[nome]]
            memoria[chiave] = r_quadro(y, colonne)
        return memoria[chiave]

    quote = {nome: 0.0 for nome in nomi}
    for nome in nomi:
        altri = [x for x in nomi if x != nome]
        for r in range(k):
            for combinazione in itertools.combinations(altri, r):
                peso = math.factorial(r) * math.factorial(k - r - 1) / math.factorial(k)
                quote[nome] += peso * (R(list(combinazione) + [nome]) - R(combinazione))
    return quote


def decomposizione(t: Tavolo) -> dict[str, float]:
    """Quanto di un movimento spiegano velocita', tempo e volume — e in che quota.

    Il bersaglio e' l'ampiezza del movimento. I tre blocchi sono le tre colonne
    del tavolo, tutte in logaritmo perche' sono grandezze che vivono su ordini
    di grandezza diversi.
    """
    y = np.log(t.ampiezza)
    velocita, tempo, volume = np.log(t.velocita), np.log(t.durata), np.log(t.volume)
    quote = shapley(y, {"velocita": [velocita], "tempo": [tempo], "volume": [volume]})
    con_volume = r_quadro(y, [velocita, tempo, volume])
    senza_volume = r_quadro(y, [velocita, tempo])
    return {
        "movimenti": len(t),
        "velocita": quote["velocita"],
        "tempo": quote["tempo"],
        "volume": quote["volume"],
        "totale": con_volume,
        "velocita_e_tempo": senza_volume,
        "guadagno_volume": con_volume - senza_volume,
        # La cifra del capitolo: di tutto cio' che le tre colonne spiegano,
        # quanto ne portano le prime due.
        "quota_velocita_e_tempo": senza_volume / con_volume,
    }


# --- Il calendario delle scadenze -------------------------------------------
# I derivati non scadono quando capita. Sull'IDEM di Borsa Italiana indici e
# azioni scadono il **terzo venerdi'** del mese; sui future e sulle opzioni in
# criptovaluta (CME, Deribit) la scadenza mensile e' l'**ultimo venerdi'**.
# Sono fatti di calendario, noti in anticipo, uguali per tutti.

def terzo_venerdi(giorno: dt.date) -> bool:
    """Scadenza dei derivati su indici e azioni italiane."""
    scarto = (4 - giorno.replace(day=1).weekday()) % 7
    return giorno.day == 1 + scarto + 14


def ultimo_venerdi(giorno: dt.date) -> bool:
    """Scadenza mensile dei derivati sulle criptovalute."""
    ultimo = giorno.replace(day=calendar.monthrange(giorno.year, giorno.month)[1])
    return giorno == ultimo - dt.timedelta(days=(ultimo.weekday() - 4) % 7)


def effetto_scadenza(date: list[dt.date], volume: np.ndarray, *,
                     cripto: bool, finestra: int = 60) -> dict[str, float]:
    """Quanto volume in piu' si scambia nel giorno di scadenza.

    Due confronti, e il secondo e' quello che conta. Il primo mette il giorno di
    scadenza contro un giorno qualunque; ma la scadenza cade sempre di venerdi',
    e il venerdi' non e' un giorno qualunque. Il confronto **con gli altri
    venerdi'** toglie di mezzo il giorno della settimana e lascia solo cio' che
    e' attribuibile alla scadenza. Su un mercato dove l'eccesso e' un effetto
    del venerdi' e non della scadenza, il secondo numero crolla — ed e' cio' che
    va stampato, non il primo.

    Mediane e non medie: il volume ha code lunghissime e una media si farebbe
    dettare da tre sedute.
    """
    rel = volume_relativo(np.asarray(volume, dtype=float), finestra)
    scade = np.array([(ultimo_venerdi if cripto else terzo_venerdi)(g) for g in date])
    venerdi = np.array([g.weekday() == 4 for g in date])
    altro = np.array([not terzo_venerdi(g) and not ultimo_venerdi(g) for g in date])
    valido = np.isfinite(rel)

    def mediana(maschera: np.ndarray) -> float:
        # Spostando le date per il test placebo si finisce anche su giorni in
        # cui il mercato e' chiuso: nessuna seduta, nessuna mediana. Meglio un
        # NaN dichiarato di un errore a meta' di un quaderno.
        scelte = rel[maschera]
        return float(np.median(scelte)) if len(scelte) else float("nan")

    dentro = mediana(valido & scade)
    altri_venerdi = mediana(valido & venerdi & ~scade)
    normale = mediana(valido & altro)
    return {
        "scadenze": int(np.sum(valido & scade)),
        "mediana_scadenza": dentro,
        "mediana_altri_venerdi": altri_venerdi,
        "mediana_normale": normale,
        "eccesso": dentro / altri_venerdi - 1.0,
        "eccesso_grezzo": dentro / normale - 1.0,
    }
