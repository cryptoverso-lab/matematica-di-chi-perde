"""Da una figura del kernel a un file SVG pesato, leggibile e senza `<style>`.

Quattro cose accadono qui, e nessuna delle quattro e' cosmetica.

1. **`svgo` come sottoprocesso**, con il binario gia' installato nel repo del
   sito e la versione pinnata dal suo lockfile. Nessun pacchetto nuovo, in
   nessuno dei due repository: il peso del bundle si misura sull'artefatto
   ottimizzato, quindi ottimizzare e' parte della produzione e non una rifinitura
   facoltativa. Se il binario non c'e', l'ingest si ferma NOMINANDO il comando —
   pubblicare senza ottimizzare significherebbe misurare il budget sul file
   sbagliato.
2. **`inlineStyles` + `convertStyleToAttrs`**, cosi' il
   `<style>*{stroke-linejoin:round;stroke-linecap:butt}</style>` che matplotlib
   mette in ogni figura sparisce. E' contratto (04-UI-SPEC §3.3, D-71) e non
   preferenza: la Fase 2 ha verbalizzato «tag `<style>`: 0» come misura su cui
   poggia l'eccezione `style-src 'unsafe-inline'` della CSP, e le figure vanno
   in linea nell'HTML servito. Misurato: le due opzioni non costano peso, lo
   TOLGONO (75 125 byte contro 84 851 sulla prima figura di `lab_05`).
3. **La sola `font-family` riscritta** (04-UI-SPEC §3.2). La catena del libro
   (`Linux Libertine G`, `Libertinus Serif`, …) non esiste nei browser. Colori,
   geometrie e dati NON si toccano: ricolorare la figura per adattarla al tema
   pubblicherebbe una figura diversa da quella che Colab produce, che e'
   l'anti-pattern 1 della fase.
4. **Il budget applicato qui** (D-45), con la mitigazione dentro il messaggio,
   perche' la riparazione sta nel quaderno e non in questo file (D-32).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .comune import ProblemaDiIngest, normalizza

#: I due budget, DUPLICATI DI PROPOSITO da `scripts/labs/contenuto.mjs` del repo
#: del sito (`BUDGET_FIGURA_BYTE`, `BUDGET_PAGINA_BYTE`), dove valgono gli stessi
#: 180 e 300 KB.
#:
#: La duplicazione e' D-08: i due repository devono poter diventare rossi
#: INDIPENDENTEMENTE. Se il numero vivesse in un posto solo, il repository che
#: cambia una figura scoprirebbe il problema nel deploy dell'altro — che e'
#: esattamente il difetto che D-08 esiste per impedire. Quando uno dei due si
#: muove, si muove anche l'altro: sono due misure della stessa regola, non due
#: regole.
BUDGET_FIGURA_BYTE = 180 * 1024
BUDGET_PAGINA_BYTE = 300 * 1024

#: La mitigazione, con il valore misurato a cui riporta. Sta nel messaggio
#: perche' un errore che dice «troppo grande» manda a cercare, e uno che dice
#: quale riga scrivere manda a riparare. La riga e' provata, non citata: la
#: variante rasterizzata di `lab_18` e' versionata come fixture nel repo del
#: sito e il suo gate pretende che passi (04-05).
MITIGAZIONE = (
    "  Si ripara NEL QUADERNO, non qui (D-32): `rasterized=True` sull'artista\n"
    "  denso piu' `print_figure_kwargs={'dpi': 72}` riporta la figura di `lab_18`\n"
    "  da 2 146 KB a 149,0 KB — il 93% in meno — senza togliere una traiettoria e\n"
    "  senza perdere uno solo dei suoi 32 `<text>` (04-RESEARCH §3.2, misurato)."
)

#: Lo stack tipografico del sito, in UNA variabile CSS e non ricopiato.
#: `src/app/globals.css` dichiara `--font-mono: var(--font-plex-mono),
#: ui-monospace, 'Cascadia Mono', monospace`: scrivere qui la catena per esteso
#: significherebbe tenerne una copia in un altro repository, che al primo cambio
#: di carattere del sito diventa la catena di ieri stampata in 40 figure. Il
#: fallback dentro la `var()` serve al caso in cui il file venga aperto fuori
#: dalla pagina, dove la variabile non esiste.
FONT_DEL_SITO = "var(--font-mono,ui-monospace,monospace)"

#: `font-family` nelle due forme che puo' avere: dichiarazione dentro un
#: `style="…"` (com'e' nel file grezzo di matplotlib) e attributo di
#: presentazione (`font-family="…"`, com'e' dopo `convertStyleToAttrs`). Le due
#: non convivono, ma la riscrittura passa prima di `svgo` e potrebbe un giorno
#: passare dopo: coprirle entrambe costa una riga.
#:
#: LA CLASSE ESCLUDE `;`, `"` e `}` E NON L'APICE. Matplotlib scrive
#: `font-family: 'Linux Libertine G', 'Libertinus Serif', …`, con gli apici
#: dentro il valore: una classe che si fermasse all'apice sostituirebbe la sola
#: parola `font-family:` lasciando in coda la catena originale — misurato, ed e'
#: esattamente cio' che questa versione della regex ripara.
_FONT_ATTRIBUTO = re.compile(r'font-family="[^"]*"')
_FONT_DICHIARAZIONE = re.compile(r'font-family\s*:[^;"}]*')

#: `width` e `height` fissi sull'elemento radice: si tolgono perche' la figura
#: deve essere fluida nella colonna (04-UI-SPEC §3.3). Il `viewBox` resta ed e'
#: cio' che conserva le proporzioni: una figura senza `viewBox` e senza misure
#: non ha piu' una forma.
_MISURE_FISSE = re.compile(r'\s(?:width|height)="[^"]*"')


def comando_svgo(sito: Path) -> list[str]:
    """Il comando da eseguire, o un arresto che NOMINA il comando mancante.

    Si guarda `node_modules/.bin/svgo`, che e' cio' che `pnpm install` produce:
    la sua assenza significa che le dipendenze del sito non sono installate, e
    il rimedio e' una riga sola. Su Windows lo shim eseguibile e' il `.CMD`
    accanto — lo `.bin/svgo` senza estensione e' uno script di shell che
    `CreateProcess` non sa lanciare.
    """
    dichiarato = sito / "node_modules" / ".bin" / "svgo"
    if not dichiarato.exists():
        raise ProblemaDiIngest(
            f"`svgo` non e' installato nel repo del sito: manca "
            f"`node_modules/.bin/svgo`.\n"
            "  Si installa con `pnpm install` dentro il checkout del sito.\n"
            "  L'ingest non ottimizza in silenzio: il budget delle figure si "
            "misura DOPO `svgo`,\n"
            "  e misurarlo su un file non ottimizzato significherebbe misurare "
            "l'artefatto sbagliato."
        )
    if os.name == "nt":
        scorciatoia = dichiarato.with_suffix(".CMD")
        if scorciatoia.exists():
            return [str(scorciatoia)]
    return [str(dichiarato)]


#: La configurazione di `svgo`, accanto a questo modulo perche' e' parte
#: dell'ingest: e' il file che decide che cosa la figura pubblicata contiene.
CONFIGURAZIONE_SVGO = Path(__file__).with_name("svgo.config.mjs")


def ottimizza(svg: str, comando: list[str], dove: str) -> str:
    """`svgo` sul markup, per sottoprocesso, senza toccare il disco.

    Ingresso e uscita passano per `stdin`/`stdout`: una figura che vive in
    memoria non ha bisogno di un file temporaneo, e un file temporaneo in piu'
    e' un file che un giro interrotto lascia indietro.
    """
    esito = subprocess.run(  # noqa: S603 — comando costruito da un percorso verificato
        [*comando, "--config", str(CONFIGURAZIONE_SVGO), "-i", "-", "-o", "-"],
        input=svg,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if esito.returncode != 0:
        raise ProblemaDiIngest(
            f"{dove}: `svgo` ha rifiutato la figura (uscita {esito.returncode}).\n"
            f"  {esito.stderr.strip()}"
        )
    return esito.stdout


def riscrivi_carattere(svg: str) -> tuple[str, int]:
    """L'UNICA riscrittura ammessa: la `font-family` (04-UI-SPEC §3.2).

    Restituisce anche quante ne ha toccate, perche' «ho riscritto il carattere»
    e «non ho trovato niente da riscrivere» sono due esiti diversi e il secondo
    va visto.
    """
    riscritte = len(_FONT_ATTRIBUTO.findall(svg)) + len(_FONT_DICHIARAZIONE.findall(svg))
    svg = _FONT_ATTRIBUTO.sub(f'font-family="{FONT_DEL_SITO}"', svg)
    svg = _FONT_DICHIARAZIONE.sub(f"font-family:{FONT_DEL_SITO}", svg)
    return svg, riscritte


def rendi_fluida(svg: str, dove: str) -> str:
    """`viewBox` garantito, `width`/`height` fissi rimossi.

    Il `viewBox` non si inventa: se manca, la figura non ha proporzioni e
    toglierle le misure la farebbe collassare. Si pretende invece di trovarlo —
    matplotlib lo emette sempre — e la sua assenza e' un arresto, non una
    riparazione a indovinare.
    """
    apertura = svg.find(">")
    if apertura == -1 or not svg.lstrip().startswith("<svg"):
        raise ProblemaDiIngest(
            f"{dove}: la figura non comincia con un elemento `<svg`."
        )
    radice = svg[: apertura + 1]
    if "viewBox=" not in radice:
        raise ProblemaDiIngest(
            f"{dove}: la figura non dichiara un `viewBox`.\n"
            "  Senza, togliere `width` e `height` la farebbe collassare, e "
            "lasciarli la renderebbe rigida\n"
            "  nella colonna di lettura (04-UI-SPEC §3.3)."
        )
    return _MISURE_FISSE.sub("", radice) + svg[apertura + 1 :]


def _peso(byte: int) -> str:
    """`184320` → `184 320 byte (180,0 KB)`. Le due unita' insieme: una si
    confronta con il budget, l'altra si legge. Stessa forma del gate del sito.
    """
    gruppi = f"{byte:,}".replace(",", " ")
    kb = f"{byte / 1024:,.1f}".replace(",", " ").replace(".", ",")
    return f"{gruppi} byte ({kb} KB)"


class Figure:
    """Il trattamento delle figure di UN lab, con il budget di pagina in mano.

    E' una classe e non una funzione perche' il budget per pagina e' una somma:
    va tenuta mentre le figure passano una per una, e controllata quando sono
    finite. Una funzione pura avrebbe dovuto ricevere tutte le figure insieme,
    cioe' tenerle tutte in memoria per poter fallire sull'ultima.
    """

    def __init__(self, sito: Path, codice: str, cartella: Path | None) -> None:
        self.comando = comando_svgo(sito)
        self.codice = codice
        #: `None` significa «tratta ma non scrivere»: e' il modo in cui
        #: `--sorgente --sito` rifa' a mano una prova in negativo — ottimizza,
        #: verifica le invarianti e applica il budget — senza lasciare file
        #: dentro il checkout del sito. Una prova che sporca il repository e'
        #: una prova che nessuno rifara'.
        self.cartella = cartella
        self.pesate: list[tuple[str, int]] = []
        self.riscritture = 0

    def tratta(self, identificativo: str, svg: str) -> tuple[str, int]:
        """Una figura: ottimizzata, riscritta, pesata, scritta. Torna `(file, byte)`.

        L'ordine conta. Il carattere si riscrive PRIMA di `svgo`, cosi' e' la
        stringa corta a essere minimizzata e deduplicata; le misure fisse si
        tolgono DOPO, perche' sono un ritocco all'elemento radice e non
        c'e' ragione di farlo attraversare l'ottimizzatore. Il peso si misura
        alla fine, sui byte che il file avra' davvero.
        """
        dove = f"{self.codice}/{identificativo}"

        svg, riscritte = riscrivi_carattere(svg)
        self.riscritture += riscritte
        svg = normalizza(self.ottimizzato(svg, dove))
        svg = rendi_fluida(svg, dove)
        self.verifica_invarianti(svg, dove)

        byte = len(svg.encode("utf-8"))
        if byte > BUDGET_FIGURA_BYTE:
            raise ProblemaDiIngest(
                f"{dove}: la figura pesa {_peso(byte)}, il budget per figura e' "
                f"{_peso(BUDGET_FIGURA_BYTE)}.\n" + MITIGAZIONE
            )

        relativo = f"figure/{identificativo}.svg"
        if self.cartella is not None:
            percorso = self.cartella / "figure" / f"{identificativo}.svg"
            percorso.parent.mkdir(parents=True, exist_ok=True)
            # `newline=""` per la stessa ragione di `scrivi_json`: su Windows
            # Python tradurrebbe ogni `\n` in `\r\n`, il file peserebbe piu' del
            # numero scritto nel bundle, e il gate del sito — che PESA il file
            # invece di crederci — direbbe che i due numeri non coincidono.
            with percorso.open("w", encoding="utf-8", newline="") as file:
                file.write(svg)

        self.pesate.append((identificativo, byte))
        return relativo, byte

    def ottimizzato(self, svg: str, dove: str) -> str:
        return ottimizza(svg, self.comando, dove)

    @staticmethod
    def verifica_invarianti(svg: str, dove: str) -> None:
        """Le due proprieta' per cui la figura viene resa in linea invece che
        dentro un `<img>`. Sono le stesse che `verify:labs` ri-misura dal lato
        del sito (D-08): qui e' la sorgente che deve produrle.
        """
        if "<style" in svg:
            raise ProblemaDiIngest(
                f"{dove}: la figura contiene ancora un `<style>` dopo `svgo`.\n"
                "  Le figure vanno IN LINEA nell'HTML servito, e la Fase 2 ha "
                "verbalizzato «tag `<style>`: 0»\n"
                "  come misura su cui poggia l'eccezione `style-src "
                "'unsafe-inline'` della CSP (D-71).\n"
                "  Le opzioni `inlineStyles` + `convertStyleToAttrs` di "
                "`svgo.config.mjs` esistono per questo."
            )
        if "<text" not in svg:
            raise ProblemaDiIngest(
                f"{dove}: la figura non contiene nemmeno un `<text`.\n"
                "  E' il sintomo di `svg.fonttype` lasciato al default `'path'` "
                "(P-7): le etichette degli assi\n"
                "  diventano curve, la figura resta identica a vedersi e torna "
                "OPACA ai crawler e alle sintesi\n"
                "  vocali — cioe' perde la ragione per cui viene resa in linea."
            )

    def verifica_budget_di_pagina(self) -> None:
        """La somma, controllata quando le figure del lab sono finite.

        E' un controllo diverso da quello per figura e non uno piu' severo:
        nessuna delle figure di una pagina puo' sfondare il proprio budget e la
        pagina affondare lo stesso. Sono i Core Web Vitals a sommare, non a
        guardare il massimo.
        """
        totale = sum(byte for _, byte in self.pesate)
        if totale <= BUDGET_PAGINA_BYTE:
            return
        elenco = ", ".join(f"{nome} {byte:_} B".replace("_", " ") for nome, byte in self.pesate)
        nessuna_sfonda = all(byte <= BUDGET_FIGURA_BYTE for _, byte in self.pesate)
        coda = (
            "  Nessuna di loro sfonda il proprio budget: e' il TOTALE che "
            "affonda i Core Web Vitals,\n  ed e' per questo che i due controlli "
            "sono due e non uno.\n"
            if nessuna_sfonda
            else ""
        )
        raise ProblemaDiIngest(
            f"{self.codice}: le {len(self.pesate)} figure della pagina pesano "
            f"{_peso(totale)}, il budget per pagina e' {_peso(BUDGET_PAGINA_BYTE)}.\n"
            f"  Le figure che lo compongono: {elenco}.\n" + coda + MITIGAZIONE
        )
