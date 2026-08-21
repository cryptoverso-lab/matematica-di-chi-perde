"""Da cella markdown a prosa del bundle: i costrutti misurati, e nient'altro.

QUESTO NON E' UN PARSER MARKDOWN, ED E' UNA SCELTA. La superficie da convertire
e' stata contata cella per cella (04-RESEARCH.md §1.1) e rimisurata al momento
di scrivere questo file: sono poche forme, tre delle quali compaiono una volta
sola in tutto il corpus. Portarsi dentro `unified`/`remark`/`rehype` — o il loro
equivalente Python — per riconoscerle significherebbe aggiungere dipendenze,
cioe' superficie da mantenere e da aggiornare, a un contenuto che cambia con le
errata del libro.

Il presidio che rende sicura quella rinuncia e' il FALLIMENTO SULL'OTTAVA
FORMA: qualunque costrutto non previsto ferma l'ingest nominando file e cella,
invece di essere reso male in silenzio. Un convertitore parziale che tace e' il
modo in cui una pagina finisce per mostrare un asterisco al posto di un corsivo,
e nessuno se ne accorge finche' non lo vede un lettore.

I COSTRUTTI RICONOSCIUTI (misurati sul corpus, non ipotizzati):

  di blocco   titolo `##`/`###`, capoverso, riga di separazione `---`,
              citazione `>`, elenco numerato, elenco puntato, tabella
  in linea    grassetto `**`, corsivo `*`, codice `` ` ``
  in attesa   formula `$…$` e `$$…$$` — vedi sotto

LE FORMULE ESISTONO COME CAPACITA', NON COME CONTENUTO (D-48). Nei sorgenti
odierni ci sono ZERO caratteri `$`: le formule del libro stanno nel manoscritto
LaTeX, i lab calcolano e il capitolo spiega. La regola si scrive lo stesso,
perche' e' la capacita' che LAB-02 chiede; e finche' non arrivano celle di
formula dal repo del libro **LAB-02 resta consegnato parzialmente**. Il sito
non scrive formule proprie: sarebbe contenuto inventato su materiale del libro,
cioe' il difetto che D-01 esiste per impedire.

IL TITOLO DEL LIBRO DIVENTA UN SEGNAPOSTO (D-64). Compare una volta in ognuno
dei 29 sorgenti, nella prima cella markdown, in grassetto markdown. Senza
sostituzione `pnpm verify:libro` del repo del sito diventerebbe rosso su 58
file alla prima esecuzione dell'ingest. La PUNTEGGIATURA RESTA QUELLA
DELL'AUTORE: D-60 («le virgolette le mette la frase») vale per i cataloghi del
sito, non per la prosa del bundle, dove il grassetto e' una scelta di chi
scrive.

IL CODICE NON PASSA DI QUI, e non si traduce (D-12).
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

from cvbook.edizione import TITOLO


class ProsaSconosciuta(Exception):
    """Un costrutto markdown che questo convertitore non sa rendere."""


@dataclass
class Resa:
    """L'HTML di una cella, con i conteggi che il chiamante pinna."""

    html: str
    sostituzioni_titolo: int = 0
    formule: int = 0
    testi_formula: list[str] = field(default_factory=list)


#: Le forme che fanno fermare l'ingest, con la ragione gia' scritta accanto:
#: il messaggio deve dire che cosa fare, non solo che qualcosa non va.
FORME_NON_PREVISTE = [
    (re.compile(r"^\s*(```|~~~)"), "un blocco di codice recintato"),
    (re.compile(r"!\["), "un'immagine"),
    (re.compile(r"\]\("), "un link markdown"),
    (re.compile(r"<[a-zA-Z/!]"), "HTML grezzo"),
    (re.compile(r"~~"), "un testo barrato"),
    (re.compile(r"\[\^"), "una nota a pie' di pagina"),
    (re.compile(r"(?<![\w_])_[^_\n]+_(?![\w_])"), "un corsivo con il trattino basso"),
]

TITOLO_RE = re.compile(r"^(#{1,6})[ ]+(.*)$")
SEPARAZIONE_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
NUMERATO_RE = re.compile(r"^([0-9]+)[.)][ ]+(.*)$")
PUNTATO_RE = re.compile(r"^[-*+][ ]+(.*)$")
SEPARATORE_TABELLA_RE = re.compile(r"^\|[ :|-]+\|$")

CODICE_IN_LINEA_RE = re.compile(r"`([^`\n]+)`")
FORMULA_BLOCCO_RE = re.compile(r"\$\$(.+?)\$\$", re.S)
FORMULA_LINEA_RE = re.compile(r"\$([^$\n]+)\$")
GRASSETTO_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
CORSIVO_RE = re.compile(r"\*(.+?)\*", re.S)


def _fallisci(dove: str, cosa: str) -> None:
    raise ProsaSconosciuta(
        f"{dove}: {cosa} — costrutto che il convertitore della prosa non "
        "riconosce.\n"
        "  Il convertitore copre le forme MISURATE sul corpus e si ferma su "
        "una nuova invece di renderla male in silenzio\n"
        "  (D-02). O il costrutto si aggiunge a `codice/lab/prosa.py`, con il "
        "suo caso di prova, o non entra nella cella."
    )


# ------------------------------------------------------------------ #
# In linea: codice, formule, grassetto, corsivo                       #
# ------------------------------------------------------------------ #


def _in_linea(testo: str, dove: str, resa: Resa) -> str:
    """Converte il contenuto di un capoverso, di una voce o di una cella.

    L'ORDINE NON E' ARBITRARIO. Prima si mettono da parte codice in linea e
    formule, perche' dentro un `` `…` `` un asterisco e' un asterisco e non un
    corsivo; poi si sfugge l'HTML, cosi' un `<` del testo diventa `&lt;` e non
    un tag; poi il grassetto e infine il corsivo, perche' `**` contiene `*` e
    l'ordine inverso spezzerebbe ogni grassetto in due corsivi vuoti.

    Alla fine si guarda che cosa e' rimasto: un asterisco, un apice inverso o un
    dollaro spaiati sono la firma di un costrutto che non abbiamo riconosciuto,
    e valgono un fallimento — non un carattere stampato in pagina.
    """
    segnaposti: list[str] = []

    def _metti_da_parte(html_prodotto: str) -> str:
        segnaposti.append(html_prodotto)
        return f"\x00{len(segnaposti) - 1}\x00"

    def _codice(trovato: re.Match[str]) -> str:
        return _metti_da_parte(f"<code>{html.escape(trovato.group(1), quote=False)}</code>")

    def _formula(display: bool):
        def _resa(trovato: re.Match[str]) -> str:
            tex = trovato.group(1).strip()
            resa.formule += 1
            resa.testi_formula.append(tex)
            marcatore = "blocco" if display else "in-linea"
            elemento = "div" if display else "span"
            # Il TeX viaggia in un attributo e non come testo: il componente
            # `Formula` del sito lo rende con KaTeX a build time. Finche' quel
            # collegamento non esiste, il marcatore e' cio' che lo rende
            # cercabile con un grep invece che deducibile.
            return _metti_da_parte(
                f'<{elemento} data-formula="{marcatore}" '
                f'data-tex="{html.escape(tex, quote=True)}"></{elemento}>'
            )

        return _resa

    lavorato = CODICE_IN_LINEA_RE.sub(_codice, testo)
    lavorato = FORMULA_BLOCCO_RE.sub(_formula(True), lavorato)
    lavorato = FORMULA_LINEA_RE.sub(_formula(False), lavorato)

    for schema, cosa in FORME_NON_PREVISTE:
        if schema.search(lavorato):
            _fallisci(dove, cosa)

    lavorato = html.escape(lavorato, quote=False)
    lavorato = GRASSETTO_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", lavorato)
    lavorato = CORSIVO_RE.sub(lambda m: f"<em>{m.group(1)}</em>", lavorato)

    for carattere, cosa in (("*", "un asterisco spaiato"), ("`", "un apice inverso spaiato"), ("$", "un dollaro spaiato")):
        if carattere in lavorato:
            _fallisci(dove, cosa)

    for indice, prodotto in enumerate(segnaposti):
        lavorato = lavorato.replace(f"\x00{indice}\x00", prodotto)

    return lavorato.replace("\n", " ").strip()


# ------------------------------------------------------------------ #
# Di blocco                                                           #
# ------------------------------------------------------------------ #


def _voci_di_elenco(righe: list[str], indice: int, schema: re.Pattern[str], dove: str):
    """Le voci di un elenco, comprese quelle che continuano sulla riga dopo.

    La continuazione esiste nel corpus (misurata: 133 righe rientrate), ed e' la
    ragione per cui questa funzione non e' un `for` sulle righe: una voce che
    va a capo letta come voce nuova produrrebbe un elenco con il doppio delle
    voci, meta' delle quali monche.
    """
    voci: list[str] = []
    while indice < len(righe):
        riga = righe[indice]
        trovato = schema.match(riga)
        if trovato is None:
            break
        voci.append(trovato.group(schema.groups))
        indice += 1
        while indice < len(righe) and righe[indice].startswith(" ") and righe[indice].strip():
            voci[-1] += "\n" + righe[indice].strip()
            indice += 1
    return voci, indice


def _tabella(righe: list[str], indice: int, dove: str):
    """Una tabella con intestazione, separatore e corpo.

    Il separatore e' obbligatorio: senza, quelle righe sono un capoverso che
    comincia con una barra verticale, non una tabella. Pretenderlo qui evita di
    produrre una `<table>` senza `<thead>` da un testo che tabella non e'.
    """
    if indice + 1 >= len(righe) or SEPARATORE_TABELLA_RE.match(righe[indice + 1]) is None:
        _fallisci(dove, "una tabella senza la riga di separazione")

    def _celle(riga: str) -> list[str]:
        return [c.strip() for c in riga.strip().strip("|").split("|")]

    intestazione = _celle(righe[indice])
    indice += 2
    corpo: list[list[str]] = []
    while indice < len(righe) and righe[indice].startswith("|"):
        corpo.append(_celle(righe[indice]))
        indice += 1
    return intestazione, corpo, indice


def _blocchi(righe: list[str], dove: str, resa: Resa, dentro_citazione: bool = False) -> list[str]:
    """L'HTML dei blocchi di una cella, o del contenuto di una citazione."""
    pezzi: list[str] = []
    indice = 0

    while indice < len(righe):
        riga = righe[indice]
        nuda = riga.strip()

        if nuda == "":
            indice += 1
            continue

        for schema, cosa in FORME_NON_PREVISTE[:1]:  # il recinto si vede sulla riga
            if schema.search(riga):
                _fallisci(dove, cosa)

        if SEPARAZIONE_RE.match(nuda):
            pezzi.append("<hr />")
            indice += 1
            continue

        titolo = TITOLO_RE.match(nuda)
        if titolo is not None:
            livello = len(titolo.group(1))
            if livello == 1:
                _fallisci(
                    dove,
                    "un titolo di primo livello fuori dalla prima cella (il titolo "
                    "del lab e' uno solo, e diventa `titolo` del bundle)",
                )
            pezzi.append(f"<h{livello}>{_in_linea(titolo.group(2), dove, resa)}</h{livello}>")
            indice += 1
            continue

        if nuda.startswith(">"):
            if dentro_citazione:
                _fallisci(dove, "una citazione dentro una citazione")
            interne: list[str] = []
            while indice < len(righe) and righe[indice].strip().startswith(">"):
                interne.append(re.sub(r"^\s*>[ ]?", "", righe[indice]))
                indice += 1
            dentro = "".join(_blocchi(interne, dove, resa, dentro_citazione=True))
            pezzi.append(f"<blockquote>{dentro}</blockquote>")
            continue

        if nuda.startswith("|"):
            intestazione, corpo, indice = _tabella(righe, indice, dove)
            teste = "".join(f"<th>{_in_linea(c, dove, resa)}</th>" for c in intestazione)
            righe_corpo = "".join(
                "<tr>" + "".join(f"<td>{_in_linea(c, dove, resa)}</td>" for c in voce) + "</tr>"
                for voce in corpo
            )
            pezzi.append(
                f"<table><thead><tr>{teste}</tr></thead><tbody>{righe_corpo}</tbody></table>"
            )
            continue

        if NUMERATO_RE.match(riga):
            voci, indice = _voci_di_elenco(righe, indice, NUMERATO_RE, dove)
            dentro = "".join(f"<li>{_in_linea(v, dove, resa)}</li>" for v in voci)
            pezzi.append(f"<ol>{dentro}</ol>")
            continue

        if PUNTATO_RE.match(riga) and not SEPARAZIONE_RE.match(nuda):
            voci, indice = _voci_di_elenco(righe, indice, PUNTATO_RE, dove)
            dentro = "".join(f"<li>{_in_linea(v, dove, resa)}</li>" for v in voci)
            pezzi.append(f"<ul>{dentro}</ul>")
            continue

        capoverso: list[str] = []
        while indice < len(righe):
            corrente = righe[indice]
            spoglia = corrente.strip()
            if spoglia == "" or SEPARAZIONE_RE.match(spoglia) or spoglia.startswith((">", "|")):
                break
            if TITOLO_RE.match(spoglia) or NUMERATO_RE.match(corrente) or PUNTATO_RE.match(corrente):
                break
            capoverso.append(spoglia)
            indice += 1
        pezzi.append(f"<p>{_in_linea(chr(10).join(capoverso), dove, resa)}</p>")

    return pezzi


def titolo_e_corpo(sorgente: str, dove: str) -> tuple[str | None, str]:
    """Stacca il titolo di primo livello dalla prima cella markdown.

    Il titolo del lab e' un campo del bundle (`titolo` di `{it,en}.json`), non
    un capoverso della prosa: la pagina lo rende come titolo del documento, e
    lasciarlo anche dentro la prosa lo farebbe comparire due volte. Compare
    esattamente una volta per file, ed e' misurato.
    """
    righe = sorgente.split("\n")
    for posizione, riga in enumerate(righe):
        if riga.strip() == "":
            continue
        trovato = TITOLO_RE.match(riga.strip())
        if trovato is None or len(trovato.group(1)) != 1:
            return None, sorgente
        testo = trovato.group(2).strip()
        if any(c in testo for c in "*`$"):
            _fallisci(dove, "un titolo di lab con markup dentro")
        return testo, "\n".join(righe[posizione + 1 :])
    return None, sorgente


def converti(sorgente: str, dove: str) -> Resa:
    """L'HTML di una cella markdown, con i conteggi che il chiamante pinna."""
    resa = Resa(html="")
    conteggio = sorgente.count(TITOLO)
    testo = sorgente.replace(TITOLO, "{{TITOLO_LIBRO}}") if conteggio else sorgente
    resa.sostituzioni_titolo = conteggio
    resa.html = "".join(_blocchi(testo.split("\n"), dove, resa))
    if resa.html == "":
        _fallisci(dove, "una cella markdown che non produce prosa")
    return resa
