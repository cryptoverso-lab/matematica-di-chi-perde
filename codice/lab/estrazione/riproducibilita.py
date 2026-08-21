"""I due lab che NON si riproducono, dichiarati per nome e con la ragione.

IL FATTO, MISURATO (piano 04-08): eseguendo il corpus due volte di fila e
confrontando i bundle, 27 lab su 29 escono byte per byte identici. I due che
restano diversi lo sono per il contenuto che STAMPANO, non per come l'ingest lo
cattura — e le due cause sono diverse fra loro.

PERCHE' QUESTO FILE ESISTE. Dal piano 04-16 una GitHub Action rigenera il bundle
e confronta. Senza una dichiarazione, quel confronto sarebbe rosso a ogni
esecuzione con dentro sempre e solo `l19` e `l20`, e un presidio che e' rosso
sempre e' un presidio che si impara a saltare. Le uscite possibili erano tre
(voce 10 delle voci rinviate del repo del sito): escludere i due lab **per nome
e con la ragione accanto**, portare nel contratto del bundle un flag
`riproducibile: false` per blocco, oppure accettare una segnalazione al giorno.
E' stata scelta la prima.

PERCHE' NON LA SECONDA. Un campo di contratto costa una migrazione di versione,
un ramo nel gate del sito e un ramo nella pagina, e andrebbe scritto guardando
DUE casi: si valuta quando l'elenco cresce, non prima. Il presidio contro la
crescita e' il conteggio pinnato piu' il test che pretende una ragione scritta.

PERCHE' NON LA TERZA. Una segnalazione quotidiana che nessuno legge e' peggio di
nessuna segnalazione: toglie il presidio E lascia credere che ci sia.

L'ESCLUSIONE E' UNA DICHIARAZIONE, NON UN FILTRO. La differenza sta tutta qui:
un filtro anonimo — `if codice in SALTA` — nasconde due lab dietro una riga di
codice, e fra un anno nessuno sa piu' se quei due sono un'eccezione capita o un
difetto rimasto. Qui ogni codice porta la propria ragione per esteso, l'ingest
la STAMPA a ogni esecuzione del corpus intero, e un test pretende che la ragione
esista e che l'elenco non si allunghi in silenzio.

E DUE COSE CHE NON VANNO «RIPARATE», perche' non sono rotte:

  `l20` — la non riproducibilita' E' LA LEZIONE DEL CAPITOLO. La cella si
  intitola «senza fissare il seme, tre esecuzioni» e insegna che un numero che
  cambia a ogni giro non si puo' ricontrollare. Fissare il seme cancellerebbe
  l'esercizio: sarebbe il sito a riscrivere il libro (D-01).

  `l19` — e' una misura di TEMPO, e il tempo cambia. Arrotondarla vorrebbe dire
  cambiare il testo del quaderno per far contenta una Action, cioe' far decidere
  al presidio che cosa il libro deve dire.
"""

from __future__ import annotations

#: I lab che due esecuzioni di fila non producono uguali, col motivo per esteso.
#: La chiave e' il codice della rotta in minuscolo, cioe' il nome della cartella
#: del bundle nel repo del sito: e' la forma con cui una Action confronta.
NON_RIPRODUCIBILI: dict[str, str] = {
    "l19": (
        "stampa quanto tempo impiega — «tempo impiegato: 0.02 secondi» nel blocco "
        "c03 e «24 varianti complete, con costi, calcolate in 0.19 secondi» nel c07 "
        "— e il tempo cambia da un'esecuzione all'altra. Cambia INTERMITTENTE: su "
        "quattro esecuzioni di fila misurate, tre hanno dato lo stesso byte e una "
        "no, ed e' la ragione per cui l'esclusione serve piu' che se cambiasse "
        "sempre — un presidio rosso a caso e' quello che si impara a ignorare per "
        "primo. Arrotondare il numero significherebbe cambiare il testo del "
        "quaderno per far tornare un confronto."
    ),
    "l20": (
        "genera numeri casuali SENZA seme, di proposito: la cella si intitola "
        "«senza fissare il seme, tre esecuzioni» e il capitolo insegna che un "
        "numero che cambia a ogni giro non si puo' ricontrollare. Fissare il seme "
        "cancellerebbe l'esercizio del capitolo. Misurato: cambiano 3 blocchi su "
        "15 — c04 e c07, i numeri casuali, e c05, che confronta due tempi in "
        "millisecondi."
    ),
}


def righe_di_dichiarazione() -> list[str]:
    """Le righe che l'ingest stampa, una per lab escluso dal confronto.

    Stampate e non commentate: un'esclusione che si legge solo aprendo un
    sorgente e' un'esclusione che nessuno rilegge.
    """
    return [f"{codice}: {motivo}" for codice, motivo in sorted(NON_RIPRODUCIBILI.items())]
