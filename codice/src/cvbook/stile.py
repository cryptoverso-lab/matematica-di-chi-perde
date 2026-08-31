"""Stile delle figure — un solo posto, due destinazioni.

`stampa`  → scala di grigi, vettoriale, conforme ai minimi KDP
`schermo` → colori del brand Cryptoverso, per Colab, repo e social

Le due versioni nascono dallo stesso codice figura: cambia solo il contesto
attivo. Nessuna informazione va mai affidata al solo colore, perche' la
versione stampata non ce l'ha.
"""

from __future__ import annotations

import contextlib
import locale

import matplotlib as mpl
import matplotlib.pyplot as plt

from .layout import (
    CORPO_ETICHETTE_PT,
    KDP_MIN_FONTSIZE_PT,
    KDP_MIN_LINEWIDTH_PT,
    figsize,
)
from .lingua import t

#: Palette brand Cryptoverso (solo per la versione a schermo).
BRAND = {
    "notte": "#0E0830",
    "blu_scuro": "#151B4D",
    "blu": "#3654B5",
    "arancio": "#E4572E",
    "bianco": "#FFFFFF",
}

#: Ciclo di grigi per la stampa. Distanziati in luminanza, non solo di nome.
GRIGI = ["#000000", "#595959", "#8C8C8C", "#BFBFBF"]

#: Stili di linea abbinati ai grigi: la serie resta distinguibile in fotocopia.
TRATTI = ["-", "--", "-.", ":"]

# Il corpo con cui si compone non puo' scendere sotto il minimo di stampa:
# se qualcuno abbassa CORPO_ETICHETTE_PT, la build si ferma qui invece di
# produrre 43 figure fuori specifica.
assert CORPO_ETICHETTE_PT >= KDP_MIN_FONTSIZE_PT

#: Retini per aree e barre. Mai `alpha`: KDP chiede trasparenze appiattite.
RETINI = ["///", "\\\\\\", "xxx", "...", "+++"]

#: Carattere delle figure: lo stesso disegno del testo del libro.
#: Linux Libertine G e' il progenitore di Libertinus Serif, il font del corpo:
#: una figura composta con lo stesso carattere della pagina smette di sembrare
#: incollata da un altro documento. Se non e' installato si ripiega su un serif
#: qualunque, senza rompere la build.
SERIF = ["Linux Libertine G", "Libertinus Serif", "Linux Libertine O", "DejaVu Serif"]

_COMUNE = {
    # Type 42 = TrueType. Il default di matplotlib e' Type 3, causa classica
    # di contestazione nei flussi print-on-demand.
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.04,
    "figure.figsize": figsize("media"),
    "font.family": "serif",
    "font.serif": SERIF,
    "mathtext.fontset": "dejavuserif",
    "font.size": 8.0,
    "axes.titlesize": 8.0,
    "axes.titlelocation": "left",
    "axes.titlepad": 5.0,
    "axes.labelsize": 7.5,
    "axes.labelpad": 3.0,
    "xtick.labelsize": CORPO_ETICHETTE_PT,
    "ytick.labelsize": CORPO_ETICHETTE_PT,
    "legend.fontsize": CORPO_ETICHETTE_PT,
    "axes.spines.top": False,
    "axes.spines.right": False,
    # La griglia sta dietro ai dati e serve a leggere i valori, non a decorare:
    # solo orizzontale, e solo dove aiuta.
    "axes.axisbelow": True,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.alpha": 1.0,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "xtick.major.width": KDP_MIN_LINEWIDTH_PT,
    "ytick.major.width": KDP_MIN_LINEWIDTH_PT,
    "xtick.major.pad": 2.5,
    "ytick.major.pad": 2.5,
    "legend.frameon": False,
    "legend.handlelength": 1.9,
    "legend.handletextpad": 0.6,
    "legend.labelspacing": 0.35,
    "legend.columnspacing": 1.1,
    "legend.borderaxespad": 0.2,
    "figure.constrained_layout.use": True,
    "figure.constrained_layout.h_pad": 0.03,
    "figure.constrained_layout.w_pad": 0.03,
    "figure.constrained_layout.hspace": 0.06,
    "figure.constrained_layout.wspace": 0.06,
}

_STAMPA = _COMUNE | {
    "lines.linewidth": 1.1,
    "lines.solid_capstyle": "round",
    "axes.linewidth": KDP_MIN_LINEWIDTH_PT,
    # Assi e tacche in grigio scuro invece che in nero pieno: restano
    # perfettamente visibili in stampa, ma smettono di competere con i dati.
    "axes.edgecolor": "#4D4D4D",
    # La griglia e' un aiuto alla lettura, non un elemento del disegno: sta
    # sotto il minimo KDP di 0,75 pt per scelta, perche' a 600 DPI una linea
    # di 0,5 pt in grigio chiarissimo si stampa e non compete con i dati.
    # I tratti che portano informazione restano tutti sopra la soglia.
    "grid.linewidth": 0.5,
    "grid.color": "#E9E9E9",
    "axes.prop_cycle": mpl.cycler(color=GRIGI) + mpl.cycler(linestyle=TRATTI),
    "text.color": "black",
    "axes.labelcolor": "#262626",
    "axes.titlecolor": "black",
    "xtick.color": "#4D4D4D",
    "ytick.color": "#4D4D4D",
    "xtick.labelcolor": "#262626",
    "ytick.labelcolor": "#262626",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
}

_SCHERMO = _COMUNE | {
    "lines.linewidth": 1.7,
    "lines.solid_capstyle": "round",
    "axes.linewidth": 0.8,
    "axes.edgecolor": "#B9BDD4",
    "grid.linewidth": 0.6,
    "grid.color": "#EFEFF5",
    # Stesso ordine di lettura della versione stampata: la prima serie e' la
    # protagonista, le altre la accompagnano. Il tratto cicla insieme al colore
    # anche qui: queste figure finiscono nell'ebook, e un lettore a inchiostro
    # elettronico le vede in grigio. Nessuna informazione al solo colore, mai.
    "axes.prop_cycle": (
        mpl.cycler(color=[BRAND["blu"], BRAND["arancio"], BRAND["notte"], "#7A8CC7"])
        + mpl.cycler(linestyle=TRATTI)
    ),
    "text.color": BRAND["notte"],
    "axes.labelcolor": BRAND["blu_scuro"],
    "axes.titlecolor": BRAND["notte"],
    "xtick.color": "#B9BDD4",
    "ytick.color": "#B9BDD4",
    "xtick.labelcolor": BRAND["blu_scuro"],
    "ytick.labelcolor": BRAND["blu_scuro"],
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
}

CONTESTI = {"stampa": _STAMPA, "schermo": _SCHERMO}


def _numeri_italiani() -> bool:
    """Virgola decimale sulle tacche degli assi: e' un libro italiano.

    Vale solo per l'edizione italiana. Con `CVBOOK_LANG=en` la virgola decimale
    non e' uno stile diverso, e' un numero sbagliato: le tacche di un asse
    inglese vogliono il punto. In quel caso la locale numerica torna a "C" —
    punto decimale, nessun separatore di migliaia — e matplotlib formatta come
    farebbe di suo.

    Restituisce False se la locale italiana non e' disponibile sulla macchina,
    cosi' la build non si rompe: le figure escono col punto decimale invece che
    con la virgola, che e' un difetto estetico, non un errore.
    """
    if t("it", "en") == "en":
        # Esplicito e non per omissione: nello stesso processo qualcun altro
        # puo' aver gia' impostato la locale italiana.
        locale.setlocale(locale.LC_NUMERIC, "C")
        return False
    for nome in ("it_IT.UTF-8", "it_IT", "Italian_Italy.1252", "Italian"):
        try:
            locale.setlocale(locale.LC_NUMERIC, nome)
            return True
        except locale.Error:
            continue
    return False


_LOCALE_OK = _numeri_italiani()
for _stile in CONTESTI.values():
    _stile["axes.formatter.use_locale"] = _LOCALE_OK
    # Tacche minori (assi logaritmici): presenti ma discrete, altrimenti
    # diventano un pettine che compete con i dati.
    _stile["xtick.minor.size"] = 1.4
    _stile["ytick.minor.size"] = 1.4
    _stile["xtick.minor.width"] = 0.5
    _stile["ytick.minor.width"] = 0.5


@contextlib.contextmanager
def contesto(destinazione: str = "stampa"):
    """Applica lo stile per la destinazione richiesta, e poi lo rimuove."""
    if destinazione not in CONTESTI:
        raise ValueError(
            f"destinazione sconosciuta: {destinazione!r} — usa {sorted(CONTESTI)}"
        )
    with mpl.rc_context(CONTESTI[destinazione]):
        yield


def num(
    valore: float,
    decimali: int = 0,
    *,
    segno: bool = False,
    percento: bool = False,
    migliaia: bool = True,
) -> str:
    """Numero scritto nella lingua attiva: all'italiana o all'inglese.

    In italiano virgola decimale e punto per le migliaia; con `CVBOOK_LANG=en`
    la convenzione si rovescia, e non e' una scelta di stile: un'etichetta come
    «0,062 points a day» per un lettore anglofono non e' un altro modo di
    scrivere sei centesimi, e' sessantadue.

    Le tacche degli assi le formatta matplotlib con la locale; questo serve per
    i numeri che finiscono dentro un'etichetta scritta a mano, dove altrimenti
    resterebbe la punteggiatura dell'altra lingua in mezzo alla frase.
    """
    grezzo = valore * 100 if percento else valore
    formato = f"{{:{'+' if segno else ''}{',' if migliaia else ''}.{decimali}f}}"
    testo = formato.format(grezzo)
    if t("it", "en") == "it":
        testo = testo.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    # Meno tipografico (U+2212) invece del trattino della tastiera: e' lo stesso
    # segno che matplotlib usa sulle tacche, e in stampa la differenza si vede.
    testo = testo.replace("-", "−")
    return f"{testo}%" if percento else testo


def tacca(valore: float, suffisso: str = "") -> str:
    """Etichetta di tacca scritta a mano, nella punteggiatura della lingua attiva.

    Su un asse logaritmico stretto matplotlib scrive le tacche in notazione
    scientifica, e «10⁻³» e' una barriera gratuita per il lettore a cui questo
    libro parla: in una dozzina di figure le tacche si scrivono a mano. Scritte
    a mano, pero', erano scritte anche in una lingua — e restavano «0,5×» anche
    con `CVBOOK_LANG=en`, cioe' mezzo capitale scritto come cinque. Da qui il
    numero di decimali si ricava dal valore e la punteggiatura da `num`.
    """
    decimali = 0
    while decimali < 6 and round(valore, decimali) != valore:
        decimali += 1
    return f"{num(valore, decimali)}{suffisso}"


MESI_BREVI = ("gen", "feb", "mar", "apr", "mag", "giu",
              "lug", "ago", "set", "ott", "nov", "dic")

#: Stessa cosa in inglese, per `CVBOOK_LANG=en`. Le tacche di data sono
#: un'etichetta d'asse a tutti gli effetti: seguono la lingua attiva come tutto
#: il resto.
_MESI_BREVI_EN = ("jan", "feb", "mar", "apr", "may", "jun",
                   "jul", "aug", "sep", "oct", "nov", "dec")


def _mesi_brevi() -> tuple[str, ...]:
    return _MESI_BREVI_EN if t("it", "en") == "en" else MESI_BREVI


def date_italiane(ax, ogni_giorni: int = 7) -> None:
    """Etichette di data — «8 nov» invece di «2022-11-08» (in inglese «nov 8»).

    Il formato ISO va benissimo in un file di dati e malissimo su una pagina
    stampata: e' lungo, ripete l'anno a ogni tacca e costringe a ruotare le
    etichette. Da usare sulle figure che coprono poche settimane.
    """
    import matplotlib.dates as mdates

    mesi = _mesi_brevi()
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=ogni_giorni))
    ax.xaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(
            lambda x, pos=None: (
                f"{mdates.num2date(x).day} {mesi[mdates.num2date(x).month - 1]}"
                if t("it", "en") == "it"
                else f"{mesi[mdates.num2date(x).month - 1]} {mdates.num2date(x).day}"
            )
        )
    )


def mesi_italiani(ax, ogni_mesi: int = 3) -> None:
    """Etichette di mese — «apr 2021» invece di «2021-04» (in inglese identiche)."""
    import matplotlib.dates as mdates

    mesi = _mesi_brevi()
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=ogni_mesi))
    ax.xaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(
            lambda x, pos=None: (
                f"{mesi[mdates.num2date(x).month - 1]} {mdates.num2date(x).year}"
            )
        )
    )


def firma(fig, fonte: str, estratto: str) -> None:
    """Imprime fonte e data del dato DENTRO la figura.

    Non nella didascalia: cosi' l'informazione viaggia con l'immagine anche
    quando finisce in un notebook, in una slide o su un social.

    Riserva prima la fascia inferiore, altrimenti il layout automatico
    ci sovrappone l'etichetta dell'asse x.
    """
    # Un calcolo diretto non ha una data di estrazione: dirlo con un trattino
    # sospeso ("estratto il —") sembra un dato mancante. Meglio tacere.
    # A direct calculation has no extraction date: a dangling dash ("extracted
    # on —") would look like missing data. Better to say nothing at all.
    testo = f"{t('Fonte', 'Source')}: {fonte}"
    if estratto and estratto.strip() not in {"—", "-", "–"}:
        testo += f" · {t('estratto il', 'extracted on')} {estratto}"

    fig.set_layout_engine("constrained", rect=(0, 0.055, 1, 0.945))
    fig.text(
        0.0,
        0.008,
        testo,
        fontsize=5.5,
        color="#595959",
        ha="left",
        va="bottom",
    )


def _appiattisci(percorso, destinazione: str) -> None:
    """Toglie il canale alpha dal PNG appena salvato.

    matplotlib scrive PNG in RGBA anche quando nessun colore e' trasparente, e
    LuaLaTeX li porta nel PDF come immagine RGB piu' una *soft mask*: erano 43
    trasparenze su 43 figure. KDP chiede esplicitamente di appiattire le
    trasparenze prima del caricamento, e il vincolo di progetto dice la stessa
    cosa; il controllo sui grigi non se ne accorgeva perche' guarda il colore,
    non l'alpha.

    La stampa diventa a un canale (`L`): e' gia' tutto grigio, il file dimezza
    e nel PDF non entra piu' nessuna maschera. Lo schermo resta a colori ma
    perde l'alpha, composto su bianco.
    """
    from PIL import Image

    with Image.open(percorso) as img:
        if img.mode not in ("RGBA", "LA", "P"):
            return
        img = img.convert("RGBA")
        fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
        piatta = Image.alpha_composite(fondo, img)
        piatta = piatta.convert("L" if destinazione == "stampa" else "RGB")
        dpi = 600 if destinazione == "stampa" else 300
        piatta.save(percorso, dpi=(dpi, dpi))


def salva(fig, percorso, destinazione: str = "stampa") -> None:
    """Salva la figura.

    Stampa: PNG a 600 DPI — il doppio del minimo KDP. Si e' scelto il raster
    invece del PDF vettoriale per un motivo pratico: lo stesso file serve sia
    il PDF di stampa sia l'EPUB, evitando due catene di inclusione parallele
    che prima o poi divergono. A 600 DPI su 4,25 pollici sono 2.550 pixel:
    in stampa print-on-demand la differenza col vettoriale non e' percepibile.

    Schermo: PNG a 300 DPI — 1.275 pixel su 4,25 pollici. E' la versione che
    finisce nell'ebook oltre che nei notebook: sotto i 300 le etichette piccole
    si sgranano sui lettori ad alta densita', sopra si paga peso a ogni copia
    consegnata senza che nessuno veda la differenza.
    """
    fig.savefig(percorso, format="png", dpi=600 if destinazione == "stampa" else 300)
    plt.close(fig)
    _appiattisci(percorso, destinazione)
