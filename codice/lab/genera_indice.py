"""Pre-render: scrive l'indice dei quaderni a partire da `cvbook.link`.

L'elenco stampato in fondo al libro non si mantiene a mano: nasce dalla stessa
mappa che genera i QR e le pagine di redirect. Cosi' e' impossibile che il
libro citi una rotta che non esiste, o che una rotta esista senza comparire
nell'indice.

Il riferimento al capitolo e' scritto come citazione Quarto soppressa
(`[-@sec-cap-XX]`): stampa il numero del capitolo, e il numero si aggiorna da
solo se in futuro se ne inserisce uno nuovo.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codice" / "src"))

from cvbook.link import DOMINIO, ROTTE  # noqa: E402

DESTINAZIONE = ROOT / "manoscritto" / "99-backmatter" / "_tabella-lab.md"

#: Frammenti inclusi dentro il riquadro «Provalo tu» di ogni capitolo: il QR
#: per la carta, il collegamento per l'ebook. Vivono qui e non nei `.qmd`
#: perche' l'indirizzo del libro deve restare in un posto solo: se cambia il
#: dominio, cambia una riga in `cvbook.link` e si rirenderizza.
CARTELLA_ROTTE = ROOT / "manoscritto" / "_rotte"

#: Il richiamo stampato. Per la carta e' LaTeX grezzo invece che Markdown, e la
#: ragione e' quel `\\mbox`: il riquadro «Provalo tu» e' `breakable`, e nella
#: versione a Markdown si spezzava proprio fra il QR e l'indirizzo — sei volte
#: su ventinove — lasciando l'indirizzo da solo in cima alla pagina dopo,
#: dentro un moncone di riquadro. Un QR senza il suo indirizzo accanto e' un
#: vicolo cieco per chi non puo' inquadrarlo, ed e' esattamente il lettore per
#: cui l'indirizzo e' stampato.
#:
#: Una `minipage` non basta: `tcolorbox` spezza con `\\vsplit`, che scende
#: dentro il vbox e lo divide comunque (provato: stessi sei riquadri rotti).
#: Una scatola *orizzontale* invece `\\vsplit` non la attraversa, e il
#: `tabular` dentro l'`\\mbox` tiene l'impaginazione a due righe di prima. Cosi'
#: QR e indirizzo o stanno insieme in fondo alla pagina, o vanno insieme a
#: quella dopo.
#:
#: Il `\\nobreak` davanti all'`\\mbox` chiude l'altra meta' dello stesso difetto.
#: Tenere insieme QR e indirizzo non basta se poi la rottura del riquadro cade
#: *subito prima* del blocco: il testo resta su una pagina e il QR compare da
#: solo in cima a quella dopo, dentro un moncone di riquadro (visto a p. 69).
#: `\\nobreak` in modo verticale mette una penalita' infinita fra il capoverso e
#: il blocco, e la colla di `\\parskip` che segue non e' piu' un punto di rottura
#: legale perche' viene dopo una penalita': cosi' TeX e' costretto a spezzare
#: piu' su, fra le righe di testo, e il QR scende sempre accompagnato da almeno
#: una riga del capoverso che lo introduce.
#:
#: Il percorso della figura e' relativo alla radice del progetto, che e' da
#: dove Quarto compila il `.tex`: il LaTeX grezzo non passa dalla riscrittura
#: dei percorsi che Quarto fa sulle immagini Markdown.
RICHIAMO = """<!-- File generato da codice/lab/genera_indice.py — non modificare a mano. -->

```{=latex}
\\nobreak
\\noindent\\mbox{\\begin{tabular}{@{}l@{}}
\\includegraphics[width=26mm]{figure/qr/@CODICE@.pdf}\\\\[.4em]
\\texttt{@ROTTA@}
\\end{tabular}}
```

::: {.content-visible when-format="epub"}
[Apri il @TITOLO@ → @ROTTA@](@URL@)
:::
"""


def scrivi_richiami() -> int:
    """Un frammento per rotta, da includere nel callout del suo capitolo."""
    CARTELLA_ROTTE.mkdir(parents=True, exist_ok=True)
    for rotta in ROTTE.values():
        codice = rotta.codice.lower()
        testo = (
            RICHIAMO.replace("@CODICE@", codice)
            .replace("@ROTTA@", f"{DOMINIO}/{codice}")
            .replace("@TITOLO@", rotta.titolo)
            .replace("@URL@", rotta.url)
        )
        (CARTELLA_ROTTE / f"{codice}.md").write_text(testo, encoding="utf-8")
    return len(ROTTE)


def righe() -> list[str]:
    fuori: list[str] = []
    for rotta in ROTTE.values():
        rotta_stampata = f"{DOMINIO}/{rotta.codice.lower()}"
        fuori.append(
            f"**{rotta.titolo}** · capitolo [-@{rotta.capitolo}] · `{rotta_stampata}`\n"
            f": {rotta.descrizione}\n"
        )
    return fuori


def main() -> None:
    corpo = "\n".join(righe())
    intestazione = (
        "<!-- File generato da codice/lab/genera_indice.py — non modificare a mano. -->\n\n"
    )
    DESTINAZIONE.write_text(intestazione + corpo, encoding="utf-8")
    print(f"indice dei lab: {len(ROTTE)} voci in {DESTINAZIONE.relative_to(ROOT)}")
    print(f"richiami nei capitoli: {scrivi_richiami()} in {CARTELLA_ROTTE.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
