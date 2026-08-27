"""Cap. fisco — Il guadagno tassabile non e' il guadagno.

Anno per anno, sui risultati realmente ottenuti da una regola meccanica su
Bitcoin: quanto ha guadagnato o perso, quanto di quel risultato e' finito nella
base imponibile dopo aver usato le perdite riportabili, e quanta imposta ne e'
uscita. Le perdite non compensate entro il termine scadono: sono soldi persi
due volte.

Le regole di compensazione qui usate — riporto per quattro anni, compensazione
solo contro risultati positivi successivi — sono un parametro dichiarato del
calcolo, non una consulenza: verificare la normativa vigente.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cvbook.dati import carica, citazione  # noqa: E402
from cvbook.lingua import t  # noqa: E402
from cvbook.regole import esegui, rottura  # noqa: E402
from cvbook.stile import firma  # noqa: E402

CAPITOLO = "sec-cap-fisco"
ALIQUOTA = 0.26
ANNI_RIPORTO = 4
CAPITALE = 100_000.0
#: La didascalia stampata in pagina, parola per parola. Non e' una copia
#: libera: `test_conformita` verifica che coincida con quella del `.qmd`.
#: Trentatre' su quarantatre' erano divergenti, e quattro portavano numeri
#: di una versione precedente del calcolo.
DIDASCALIA = (
    "Anno per anno, il risultato di una regola meccanica su Bitcoin e cosa ne "
    "fa il fisco. Le barre chiare sono il risultato lordo dell'anno, quelle "
    "scure l'imposta versata. Da guardare due cose: gli anni in perdita, dove "
    "l'imposta è zero ma il credito che ne nasce può scadere inutilizzato — "
    "succede a quelli in basso a destra — e la distanza fra pagare ogni anno "
    "e pagare la stessa aliquota una volta sola alla fine. Stessa strategia, "
    "stessa aliquota, 46% di capitale finale di differenza."
)


def _annuali():
    df = carica("btcusdt").sort("data")
    p = df["chiusura"].to_numpy()
    anni = np.array([d.year for d in df["data"].to_list()])
    curva = esegui(p, rottura(p, 20))["curva"]

    # Il rendimento di un anno si misura dalla chiusura dell'anno precedente,
    # non dalla sua prima seduta: partendo dalla prima seduta si perde il
    # movimento del passaggio d'anno, e i dieci rendimenti annuali non
    # ricompongono piu' il risultato complessivo della regola. Con questa base
    # il prodotto degli anni coincide con la curva, all'ultimo decimale.
    fuori = []
    base = float(curva[0])
    for a in sorted(set(anni.tolist())):
        ultimo = int(np.where(anni == a)[0][-1])
        fuori.append((int(a), float(curva[ultimo]) / base - 1.0))
        base = float(curva[ultimo])
    return fuori


def simula_imposta(rendimenti_annui, capitale=CAPITALE, aliquota=ALIQUOTA,
                   anni_riporto=ANNI_RIPORTO):
    """Imposta anno per anno con riporto delle perdite a scadenza."""
    crediti: list[list[float]] = []
    righe, imposte_totali = [], 0.0

    for anno, r in rendimenti_annui:
        lordo = capitale * r
        if lordo >= 0:
            usato = 0.0
            for c in crediti:
                if anno - c[0] <= anni_riporto:
                    quota = min(c[1], lordo - usato)
                    c[1] -= quota
                    usato += quota
                    if usato >= lordo:
                        break
            imponibile = max(lordo - usato, 0.0)
            imposta = imponibile * aliquota
        else:
            crediti.append([anno, -lordo])
            imponibile, imposta = 0.0, 0.0

        scaduti = sum(c[1] for c in crediti if anno - c[0] >= anni_riporto)
        crediti = [c for c in crediti if c[1] > 1e-9 and anno - c[0] < anni_riporto]

        imposte_totali += imposta
        capitale += lordo - imposta
        righe.append({"anno": anno, "lordo": lordo, "imponibile": imponibile,
                      "imposta": imposta, "capitale": capitale, "scaduti": scaduti})

    residuo = sum(c[1] for c in crediti)
    return righe, imposte_totali, residuo


def disegna(destinazione: str = "stampa"):
    annuali = _annuali()
    righe, imposte, residuo = simula_imposta(annuali)

    lordo_composto = CAPITALE
    for _, r in annuali:
        lordo_composto *= 1 + r
    differita = CAPITALE + (lordo_composto - CAPITALE) * (1 - ALIQUOTA)

    anni = [r["anno"] for r in righe]
    x = np.arange(len(anni))
    lordi = np.array([r["lordo"] for r in righe]) / 1000
    tasse = np.array([r["imposta"] for r in righe]) / 1000

    fig, ax = plt.subplots()
    ax.bar(x - 0.19, lordi, width=0.36, facecolor="white", edgecolor="black",
           linewidth=0.75, hatch="///", label=t("risultato lordo", "gross result"))
    ax.bar(x + 0.19, -tasse, width=0.36, facecolor="#404040", edgecolor="black",
           linewidth=0.75, label=t("imposta versata", "tax paid"))
    ax.axhline(0, color="black", linewidth=0.8)

    # Una nota sola, invece di un'etichetta per ogni anno in perdita: quattro
    # etichette finivano addosso alle barre vicine e ai nomi degli anni.
    # In basso a destra: sotto le barre degli ultimi due anni, che scendono
    # poco, c'e' l'unica zona del riquadro che nessuna barra attraversa.
    # One note only, instead of a label per loss year: four labels used to
    # collide with neighbouring bars and year names. Bottom right, under the
    # last two years' bars — the only spot no bar ever crosses.
    ax.text(0.995, 0.02,
            t(
                "sotto lo zero: perdite\nche valgono solo se\narriva un anno positivo\n"
                "entro il termine",
                "below zero: losses\nthat only count if\na positive year arrives\n"
                "within the carry-forward window",
            ),
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.2,
            linespacing=1.35)

    ax.set_xticks(x)
    ax.set_xticklabels([str(a) for a in anni], rotation=45, ha="right", fontsize=6.5)
    ax.set_ylabel(t("Migliaia di euro (da 100.000 iniziali)", "Thousands of euros (starting from 100,000)"))
    ax.legend(loc="upper left", fontsize=6.5)
    ax.grid(axis="x", visible=False)

    fonte, estratto = citazione("btcusdt")
    firma(fig, t(f"{fonte}, regola meccanica, aliquota dichiarata {ALIQUOTA:.0%}",
                  f"{fonte}, mechanical rule, stated tax rate {ALIQUOTA:.0%}"), estratto)

    disegna.numeri = {
        "capitale_finale_annuale": righe[-1]["capitale"],
        "capitale_finale_differito": differita,
        "divario": differita / righe[-1]["capitale"] - 1,
        "imposte_pagate": imposte,
        "guadagno_lordo": lordo_composto - CAPITALE,
        # L'ALIQUOTA EFFETTIVA NON SI CALCOLA QUI. La versione che stava in
        # questa riga divideva le imposte del percorso tassato per il guadagno
        # del percorso lordo — due capitali diversi — e usciva 21,5% invece di
        # 30,2%: il numero sbagliato che il capitolo ha portato per settimane.
        # E' stato corretto in `numeri_fisco._scenario`, che e' l'unico posto
        # in cui quel rapporto ha senso, e qui era rimasta la copia vecchia
        # sotto lo stesso nome. Chi la vuole: `numeri_fisco.numeri()`.
        "perdite_mai_usate": residuo,
    }
    return fig


if __name__ == "__main__":
    from cvbook.stile import contesto

    with contesto("stampa"):
        disegna()
    for k, v in disegna.numeri.items():
        print(f"{k:28s} {v:,.2f}")
