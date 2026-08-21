"""L'ingest legge i sorgenti, e i suoi fallimenti hanno un nome.

Questi test non eseguono nessun quaderno: leggono. Sono quindi veloci e girano
anche con `-m "not lento"`, che e' il modo in cui la suite viene lanciata
mentre si lavora — un controllo che gira solo nella corsa lunga e' un controllo
che si scopre rotto tardi.

Cinque cose sono asserite qui, e ognuna corrisponde a un difetto misurato:

1. `lab_17` dichiara OTTO serie su due righe: una regex a riga singola ne
   leggerebbe sei, e il `Dataset` JSON-LD della pagina direbbe il falso (P-10);
2. `lab_02` ne dichiara ZERO, e zero e' un risultato valido, non un errore;
3. una serie che il registro non conosce ferma l'ingest NOMINANDOLA;
4. una forma di `prepara` illeggibile e una cella di setup assente lo fermano
   NOMINANDO IL FILE;
5. lo stesso sorgente in CRLF e in LF produce blocchi e impronte identici, che
   e' cio' che tiene fermo il gate di parita' del sito fra Windows e il runner
   Linux (D-46).

Uso:  uv run python -m pytest codice/testing/test_estrazione.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[2]
LAB = RADICE / "codice" / "lab"
sys.path.insert(0, str(RADICE / "codice" / "src"))
sys.path.insert(0, str(LAB))

# Si importa dai MODULI, non da un barrel: dopo la divisione di 04-08 l'ingest
# e' un pacchetto, e un `import estrai_bundle` che ri-esportasse tutto avrebbe
# lasciato questi test identici — cioe' avrebbe reso la divisione invisibile,
# che e' il modo di non farla.
from estrazione import prosa  # noqa: E402
from estrazione.celle import cella_di_setup, celle_del_sorgente  # noqa: E402
from estrazione.comune import ProblemaDiIngest  # noqa: E402
from estrazione.dataset import (  # noqa: E402
    CAMPI_DI_PROVENIENZA,
    provenienza_delle_serie,
    serie_dichiarate,
)
from estrazione.esecuzione import (  # noqa: E402
    CARATTERI_MASSIMI,
    CELLA_DI_RESA,
    _tronca,
)
from estrazione.figure import (  # noqa: E402
    BUDGET_FIGURA_BYTE,
    BUDGET_PAGINA_BYTE,
    FONT_DEL_SITO,
    Figure,
    riscrivi_carattere,
)
from estrazione.sorgente import ATTESI, estrai_dal_sorgente  # noqa: E402

#: Un LaTeX qualunque, scritto come stringa grezza: il backslash e' un
#: carattere del TeX, non un escape di Python.
LATEX = r"\sigma^2"

REGISTRO = json.loads((RADICE / "codice" / "dati" / "registro.json").read_text(encoding="utf-8"))


def _serie_di(nome_file: str) -> list[str]:
    percorso = LAB / nome_file
    celle = celle_del_sorgente(percorso)
    setup = cella_di_setup(celle, percorso)
    return serie_dichiarate(setup, percorso)


def _copia_con(tmp_path: Path, nome_file: str, prima: str, dopo: str) -> Path:
    """Una copia di un sorgente vero con UNA cosa cambiata.

    Si parte sempre da un file reale: un sorgente inventato dentro il test
    proverebbe che l'ingest rifiuta un file inventato, non che rifiuta il
    sorgente vero con un difetto dentro.
    """
    testo = (LAB / nome_file).read_text(encoding="utf-8")
    assert prima in testo, f"il sorgente {nome_file} non contiene piu' {prima!r}"
    copia = tmp_path / nome_file
    copia.write_text(testo.replace(prima, dopo, 1), encoding="utf-8", newline="\n")
    return copia


# ------------------------------------------------------------------ #
# I dataset: multiriga, vuoto, e cio' che il registro non conosce     #
# ------------------------------------------------------------------ #


def test_lab_17_dichiara_otto_serie_su_due_righe() -> None:
    serie = _serie_di("lab_17_prezzo_e_tempo.py")
    assert serie == [
        "btcusdt",
        "ethusdt",
        "solusdt",
        "ftsemib",
        "eni",
        "enel",
        "intesa",
        "generali",
    ], "la chiamata di lab_17 sta su due righe: leggerne sei significa pubblicare il falso (P-10)"


def test_lab_02_non_usa_dataset_e_non_e_un_errore() -> None:
    assert _serie_di("lab_02_equity_casuali.py") == []


def test_una_serie_fuori_dal_registro_ferma_l_ingest_nominandola(tmp_path: Path) -> None:
    copia = _copia_con(
        tmp_path,
        "lab_05_misurare.py",
        'avvio.prepara(["btcusdt", "ethusdt", "solusdt"])',
        'avvio.prepara(["inesistente"])',
    )
    celle = celle_del_sorgente(copia)
    setup = cella_di_setup(celle, copia)
    serie = serie_dichiarate(setup, copia)

    with pytest.raises(ProblemaDiIngest) as fallimento:
        provenienza_delle_serie(serie, copia)

    messaggio = str(fallimento.value)
    assert "`inesistente`" in messaggio, "il rifiuto deve nominare la serie, non l'indice"
    assert "registro.json" in messaggio


def test_una_forma_di_prepara_illeggibile_ferma_l_ingest_nominando_il_file(
    tmp_path: Path,
) -> None:
    copia = _copia_con(
        tmp_path,
        "lab_05_misurare.py",
        'avvio.prepara(["btcusdt", "ethusdt", "solusdt"])',
        "avvio.prepara(SERIE_SCELTE)",
    )
    celle = celle_del_sorgente(copia)
    setup = cella_di_setup(celle, copia)

    with pytest.raises(ProblemaDiIngest) as fallimento:
        serie_dichiarate(setup, copia)

    messaggio = str(fallimento.value)
    assert copia.name in messaggio
    assert "Name" in messaggio, "il rifiuto dice quale forma ha trovato, non solo che non va"


def test_la_cella_di_setup_assente_ferma_l_ingest_nominando_il_file(tmp_path: Path) -> None:
    testo = (LAB / "lab_05_misurare.py").read_text(encoding="utf-8")
    inizio = testo.index("# %%\n# Setup")
    fine = testo.index("# %%", inizio + 4)
    copia = tmp_path / "lab_05_senza_setup.py"
    copia.write_text(testo[:inizio] + testo[fine:], encoding="utf-8", newline="\n")

    with pytest.raises(ProblemaDiIngest) as fallimento:
        estrai_dal_sorgente(copia)

    messaggio = str(fallimento.value)
    assert copia.name in messaggio
    assert "avvio.prepara" in messaggio


# ------------------------------------------------------------------ #
# La provenienza si COPIA, campo per campo                            #
# ------------------------------------------------------------------ #


def test_la_provenienza_coincide_col_registro_campo_per_campo() -> None:
    percorso = LAB / "lab_05_misurare.py"
    serie = _serie_di("lab_05_misurare.py")
    provenienza = provenienza_delle_serie(serie, percorso)

    assert sorted(provenienza) == sorted(serie)
    for nome in serie:
        atteso = REGISTRO[nome]
        for campo in CAMPI_DI_PROVENIENZA:
            assert provenienza[nome][campo] == atteso[campo], (
                f"{nome}.{campo} e' stato riformattato invece di essere copiato (D-20)"
            )
        # `byte` e' l'unico campo che il registro non porta: si misura sul file
        # che il registro stesso indica.
        assert provenienza[nome]["byte"] == (RADICE / atteso["file"]).stat().st_size


def test_nessuna_impronta_viene_ricalcolata() -> None:
    """Le sha256 del bundle sono quelle del registro, cifra per cifra."""
    percorso = LAB / "lab_05_misurare.py"
    provenienza = provenienza_delle_serie(_serie_di("lab_05_misurare.py"), percorso)
    for nome, voce in provenienza.items():
        assert voce["sha256"] == REGISTRO[nome]["sha256"]
        assert len(voce["sha256"]) == 64 and voce["sha256"].islower()


# ------------------------------------------------------------------ #
# CRLF e LF: lo stesso contenuto, la stessa impronta                  #
# ------------------------------------------------------------------ #


def test_crlf_e_lf_producono_gli_stessi_blocchi(tmp_path: Path) -> None:
    testo = (LAB / "lab_05_misurare.py").read_text(encoding="utf-8")
    lf = tmp_path / "lf.py"
    crlf = tmp_path / "crlf.py"
    lf.write_bytes(testo.replace("\r\n", "\n").encode("utf-8"))
    crlf.write_bytes(testo.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))

    da_lf = estrai_dal_sorgente(lf)
    da_crlf = estrai_dal_sorgente(crlf)

    assert da_lf.blocchi == da_crlf.blocchi
    assert da_lf.prosa == da_crlf.prosa
    assert da_lf.titolo == da_crlf.titolo
    assert json.dumps(da_lf.blocchi, ensure_ascii=False) == json.dumps(
        da_crlf.blocchi, ensure_ascii=False
    )


# ------------------------------------------------------------------ #
# La prosa: tutto il corpus, e il fallimento sulla forma nuova        #
# ------------------------------------------------------------------ #


def _sorgenti() -> list[Path]:
    from cvbook.link import ROTTE

    return [LAB / rotta.file for rotta in ROTTE.values()]


def test_il_corpus_intero_si_converte_senza_costrutti_sconosciuti() -> None:
    """Le 221 celle markdown dei 29 sorgenti, una per una.

    Il numero e' RIMISURATO qui e non copiato dalla ricerca, che contava 191
    celle markdown su 373 totali: da allora ogni cella ha guadagnato la sua
    citazione in inglese, e il corpus e' cresciuto a 403 celle. Un conteggio
    ereditato invece che rimisurato sarebbe stato verde su un corpus che non
    esiste piu'.
    """
    celle = titoli = formule = 0
    for percorso in _sorgenti():
        estrazione = estrai_dal_sorgente(percorso)
        celle += sum(1 for blocco in estrazione.blocchi if blocco["tipo"] == "prosa")
        titoli += estrazione.sostituzioni_titolo
        formule += estrazione.formule

    assert celle == 221, "celle di prosa convertite"
    assert titoli == ATTESI["titolo"], (
        "il titolo del libro compare una volta per file: un'occorrenza in piu' "
        "o in meno va guardata prima che finisca in 58 file del bundle (D-64)"
    )
    assert formule == 0, (
        "oggi nei sorgenti non ci sono formule: la capacita' esiste, il "
        "contenuto no, e LAB-02 resta parziale (D-48)"
    )


def test_i_conteggi_pinnati_valgono_sul_corpus_intero() -> None:
    magic = raw = 0
    for percorso in _sorgenti():
        estrazione = estrai_dal_sorgente(percorso)
        magic += estrazione.magic
        raw += estrazione.sostituzioni_raw

    assert magic == ATTESI["magic"]
    assert raw == ATTESI["raw_base"]


@pytest.mark.parametrize(
    ("intruso", "atteso"),
    [
        ("Vedi la [documentazione](https://esempio.invalido).", "un link markdown"),
        ("![figura](x.png)", "un'immagine"),
        ("<div>ciao</div>", "HTML grezzo"),
        ("Un testo ~~barrato~~.", "un testo barrato"),
        ("Un asterisco * spaiato.", "un asterisco spaiato"),
    ],
)
def test_una_forma_non_prevista_ferma_l_ingest_nominando_file_e_cella(
    tmp_path: Path, intruso: str, atteso: str
) -> None:
    copia = _copia_con(
        tmp_path,
        "lab_05_misurare.py",
        "# ## 1. Tre sguardi",
        f"# ## 1. Tre sguardi\n#\n# {intruso}",
    )

    with pytest.raises(ProblemaDiIngest) as fallimento:
        estrai_dal_sorgente(copia)

    messaggio = str(fallimento.value)
    assert copia.name in messaggio
    assert "cella" in messaggio, "il rifiuto nomina la cella, non solo il file"
    assert atteso in messaggio


def test_il_convertitore_rende_i_costrutti_misurati() -> None:
    """Un caso per costrutto, cosi' che il verde dica anche che cosa produce."""
    resa = prosa.converti(
        "## Titolo\n"
        "\n"
        "Un *corsivo*, un **grassetto** e del `codice`.\n"
        "\n"
        "---\n"
        "\n"
        "> Una citazione.\n"
        "\n"
        "1. prima\n"
        "2. seconda\n"
        "\n"
        "- punto\n"
        "\n"
        "| a | b |\n"
        "|---|---|\n"
        "| 1 | 2 |\n",
        "prova, cella 0",
    )

    for atteso in (
        "<h2>Titolo</h2>",
        "<em>corsivo</em>",
        "<strong>grassetto</strong>",
        "<code>codice</code>",
        "<hr />",
        "<blockquote><p>Una citazione.</p></blockquote>",
        "<ol><li>prima</li><li>seconda</li></ol>",
        "<ul><li>punto</li></ul>",
        "<table><thead><tr><th>a</th><th>b</th></tr></thead>",
    ):
        assert atteso in resa.html


def test_la_capacita_sulle_formule_esiste_anche_se_il_contenuto_no() -> None:
    """D-48: si riconosce `$…$` e `$$…$$`, e lo si marca per il componente.

    Oggi nel corpus non c'e' un solo `$`. La regola si scrive lo stesso, perche'
    e' la capacita' che LAB-02 chiede — e finche' non arrivano celle di formula
    dal repo del libro, LAB-02 resta consegnato parzialmente.
    """
    resa = prosa.converti(
        f"La varianza ${LATEX}$ e:\n\n$${LATEX} = 1$$\n",
        "prova, cella 0",
    )
    assert resa.formule == 2
    assert 'data-formula="in-linea"' in resa.html
    assert 'data-formula="blocco"' in resa.html
    assert resa.testi_formula == [LATEX, LATEX + " = 1"]


# ------------------------------------------------------------------ #
# Il troncamento: si dichiara o non si fa (D-33)                      #
# ------------------------------------------------------------------ #


def test_trenta_righe_passano_intere_e_dichiarano_comunque_il_totale() -> None:
    """`righeTotali` viaggia SEMPRE, anche quando non si e' tagliato nulla.

    E' la forma piu' forte del vincolo: il contratto del sito lo pretende
    obbligatorio in ogni caso, perche' «obbligatorio se un altro campo vale
    true» e' una relazione che il JSON Schema non sa esprimere.
    """
    uscita = _tronca("\n".join(f"riga {n}" for n in range(1, 31)))
    assert uscita.troncato is False
    assert uscita.righe_totali == 30
    assert len(uscita.testo.split("\n")) == 30


def test_trentuno_righe_diventano_trenta_e_il_totale_resta_trentuno() -> None:
    uscita = _tronca("\n".join(f"riga {n}" for n in range(1, 32)))
    assert uscita.troncato is True
    assert uscita.righe_totali == 31
    assert len(uscita.testo.split("\n")) == 30


def test_una_riga_sola_ma_lunghissima_viene_tagliata_lo_stesso() -> None:
    """Il caso che il conteggio delle righe non vede: un `print` di un array
    senza a capo. Senza il tetto in caratteri passerebbe intero — una riga sola,
    e nessun troncamento — trascinando in pagina decine di migliaia di caratteri.
    """
    uscita = _tronca("x" * (CARATTERI_MASSIMI + 500))
    assert uscita.troncato is True
    assert uscita.righe_totali == 1
    assert len(uscita.testo) == CARATTERI_MASSIMI


def test_la_cella_di_resa_chiede_svg_e_testo_che_resta_testo() -> None:
    """Le due righe che decidono se la figura e' leggibile.

    `figure_formats = ['svg']` cambia il formato (il default dell'inline backend
    e' PNG, e nessun lab dichiara il formato); `svg.fonttype = 'none'` decide se
    le etichette restano testo o diventano tracciati. Sono asserite qui perche'
    la cella e' una costante: una modifica distratta non produrrebbe nessun
    errore, produrrebbe 40 figure opache.
    """
    assert "InlineBackend.figure_formats = ['svg']" in CELLA_DI_RESA
    assert "svg.fonttype'] = 'none'" in CELLA_DI_RESA
    assert "'dpi': 72" in CELLA_DI_RESA


def test_la_cella_di_resa_non_entra_mai_fra_i_blocchi() -> None:
    """P-5, dal lato che il gate del sito ri-misura.

    Il bundle non deve MAI contenere `InlineBackend`: e' infrastruttura
    aggiunta in memoria dall'ingest, non contenuto del lab, e non sta nei
    sorgenti del libro. `verify:labs` lo rifiuta; qui e' la sorgente che deve
    rispettarlo.
    """
    estrazione = estrai_dal_sorgente(LAB / "lab_05_misurare.py")
    for blocco in estrazione.blocchi:
        assert "InlineBackend" not in blocco.get("sorgente", "")


# ------------------------------------------------------------------ #
# Le figure: la sola `font-family`, e le due invarianti dell'SVG      #
# ------------------------------------------------------------------ #

#: Un `<text>` come matplotlib lo scrive davvero, ricopiato da una figura vera
#: di `lab_05_misurare`. Non e' un SVG inventato: e' la forma esatta che la
#: riscrittura deve incontrare, apici compresi — ed e' su quegli apici che la
#: prima versione della regex si e' rotta.
TEXT_DI_MATPLOTLIB = (
    '<g id="text_1"><text style="font-size:7px;font-family: \'Linux Libertine G\', '
    "'Libertinus Serif', 'Linux Libertine O', 'DejaVu Serif', serif;fill:#151b4d\" "
    'x="51.677" y="262.028">2018</text></g>'
)


def test_la_riscrittura_tocca_la_font_family_e_nient_altro() -> None:
    """L'unica riscrittura ammessa (04-UI-SPEC §3.2).

    Colori, geometrie e dati NON si toccano: ricolorare la figura per adattarla
    al tema pubblicherebbe una figura diversa da quella che Colab produce.
    Il test lo asserisce nelle due direzioni — la catena del libro sparisce, e
    tutto il resto della stringa e' identico carattere per carattere.
    """
    riscritto, quante = riscrivi_carattere(TEXT_DI_MATPLOTLIB)

    assert quante == 1
    assert "Libertine" not in riscritto
    assert FONT_DEL_SITO in riscritto
    assert "fill:#151b4d" in riscritto
    assert 'x="51.677" y="262.028"' in riscritto
    assert "font-size:7px" in riscritto
    assert ">2018</text>" in riscritto


def test_la_catena_del_libro_ha_gli_apici_e_la_regex_non_ci_si_ferma() -> None:
    """Il difetto misurato, tenuto fermo da un test.

    Una classe di caratteri che escludesse l'apice avrebbe sostituito la sola
    parola `font-family:` lasciando in coda la catena originale — e la figura
    sarebbe uscita con `var(--font-mono,…)'Linux Libertine G',…`, cioe' con un
    carattere che nel browser del lettore non esiste. E' successo, e questo
    test e' la ragione per cui non succede piu'.
    """
    riscritto, _ = riscrivi_carattere(TEXT_DI_MATPLOTLIB)
    assert "Linux Libertine" not in riscritto


def test_una_figura_senza_text_viene_rifiutata() -> None:
    """P-7: e' il sintomo di `svg.fonttype` lasciato al default `'path'`.

    Le etichette degli assi diventano curve, la figura resta identica a vedersi
    e torna OPACA ai crawler e alle sintesi vocali — cioe' perde la ragione per
    cui viene resa in linea invece che come immagine.
    """
    with pytest.raises(ProblemaDiIngest) as fallimento:
        Figure.verifica_invarianti('<svg viewBox="0 0 1 1"><path d="M0 0"/></svg>', "l05/c01-1")
    assert "<text" in str(fallimento.value)
    assert "l05/c01-1" in str(fallimento.value)


def test_una_figura_con_style_viene_rifiutata() -> None:
    """D-71: la misura della CSP della Fase 2 («tag `<style>`: 0») deve restare
    vera anche quando le figure entrano in linea nell'HTML servito.
    """
    with pytest.raises(ProblemaDiIngest) as fallimento:
        Figure.verifica_invarianti(
            '<svg viewBox="0 0 1 1"><style>*{fill:red}</style><text>1</text></svg>',
            "l05/c01-1",
        )
    assert "<style>" in str(fallimento.value)
    assert "unsafe-inline" in str(fallimento.value)


def test_i_budget_sono_quelli_del_gate_del_sito() -> None:
    """I due numeri sono duplicati DI PROPOSITO da `scripts/labs/contenuto.mjs`.

    La duplicazione e' D-08 — i due repository devono poter diventare rossi
    indipendentemente — e un test che li pinna e' cio' che rende visibile il
    giorno in cui uno dei due si muove da solo.
    """
    assert BUDGET_FIGURA_BYTE == 180 * 1024
    assert BUDGET_PAGINA_BYTE == 300 * 1024
