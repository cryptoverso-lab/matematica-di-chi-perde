"""Infrastruttura dei link — un solo posto in cui vive il dominio.

Un QR stampato non si corregge piu': per questo i link del libro non puntano
mai a GitHub o a Colab, ma a una rotta di redirect che controlliamo noi.
Cambiare dominio significa cambiare una riga qui e rigenerare il PDF.

Il dominio e l'organizzazione sono di Cryptoverso (decisione del 19 agosto
2026): Logika.studio resta il partner tecnico, non il titolare. Il dominio e'
in delega: finche' non risolve, `codice/figure/genera_redirect.py` si rifiuta
di rigenerare i QR.

Questo modulo e' anche la fonte unica dell'indice dei lab stampato in fondo al
libro: ogni rotta dichiara il capitolo che la cita, e `codice/lab/genera_indice.py`
trasforma questa mappa nella tabella del manoscritto. Se una rotta non ha un
capitolo, o un capitolo cita una rotta che non esiste, il gate se ne accorge.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Dominio-ancora stampato nei QR. UNICO punto in cui compare.
DOMINIO = "lab.cryptoverso.net"

#: Organizzazione GitHub che ospita il libro, e nome della repository.
#: Sono l'unico punto in cui compaiono: repo, Colab e riga di avvio dei
#: quaderni nascono da qui, quindi spostare il libro sotto un'altra
#: organizzazione e' cambiare questa riga e rieseguire i generatori.
ORG = "cryptoverso-lab"
REPO_NOME = "matematica-di-chi-perde"

#: Destinazioni vere, modificabili in qualsiasi momento senza toccare la carta.
REPO = f"https://github.com/{ORG}/{REPO_NOME}"
COLAB_BASE = f"https://colab.research.google.com/github/{ORG}/{REPO_NOME}/blob/main"

#: File grezzi: il motore `cvbook` e gli snapshot dati che i quaderni scaricano.
RAW_BASE = f"https://raw.githubusercontent.com/{ORG}/{REPO_NOME}/main"

#: La riga di bootstrap che Colab esegue per prima, in ognuno dei quaderni.
#: E' scritta dentro i sorgenti dei lab (li' non c'e' ancora `cvbook` da
#: importare): `codice/lab/costruisci.py --sincronizza` la ricopia da qui, e il
#: gate in `test_quaderni.py` verifica che nessun quaderno se ne sia allontanato.
URL_AVVIO = f"{RAW_BASE}/codice/lab/avvio.py"


@dataclass(frozen=True)
class Rotta:
    codice: str        # rotta stampata, es. "L03"
    destinazione: str  # dove porta oggi
    descrizione: str
    capitolo: str      # etichetta Quarto del capitolo che la cita
    titolo: str        # etichetta stampata: "Lab 3" / "Calcolatore 1"
    file: str          # sorgente .py in formato percent

    @property
    def url(self) -> str:
        """L'indirizzo che finisce nel QR e nel testo stampato."""
        return f"https://{DOMINIO}/{self.codice.lower()}"


def _rotta(codice: str, file: str, descrizione: str, capitolo: str) -> Rotta:
    numero = int(codice[1:])
    titolo = f"{'Lab' if codice[0] == 'L' else 'Calcolatore'} {numero}"
    return Rotta(
        codice=codice,
        destinazione=f"{COLAB_BASE}/codice/lab/{file}",
        descrizione=descrizione,
        capitolo=capitolo,
        titolo=titolo,
        file=file.replace(".ipynb", ".py"),
    )


#: Mappa completa delle rotte, **nell'ordine in cui compaiono nel libro**.
#: Ogni voce qui deve avere un notebook che gira in CI, e ogni notebook deve
#: essere citato da un capitolo.
ROTTE: dict[str, Rotta] = {
    r.codice: r
    for r in [
        _rotta("L01", "lab_01_chi_perde.ipynb",
               "Quanti conti al dettaglio chiudono in perdita, e in quanto tempo",
               "sec-cap-01"),
        _rotta("C01", "calc_01_recupero_perdite.ipynb",
               "Quanto serve guadagnare per recuperare una perdita",
               "sec-cap-02"),
        _rotta("C02", "calc_02_costi.ipynb",
               "Costi cumulati su un anno di operatività, al variare della frequenza",
               "sec-cap-03"),
        _rotta("L02", "lab_02_equity_casuali.ipynb",
               "Curve di capitale generate dal solo caso, e le più belle fra mille",
               "sec-cap-04"),
        _rotta("L03", "lab_03_cimitero_token.ipynb",
               "Mortalità dei token e distorsione da sopravvivenza",
               "sec-cap-05"),
        _rotta("L04", "lab_04_bias.ipynb",
               "Avversione alle perdite e disposizione, misurate sui propri numeri",
               "sec-cap-06"),
        _rotta("L05", "lab_05_misurare.ipynb",
               "Tre sguardi sugli stessi dati, e il test del vero contro il finto",
               "sec-cap-08"),
        _rotta("L06", "lab_06_code_grasse.ipynb",
               "Code grasse, curtosi e i venti giorni che decidono tutto",
               "sec-cap-09"),
        _rotta("C03", "calc_03_stop_sizing.ipynb",
               "Tempo sotto il massimo e dimensione compatibile con la tua tolleranza",
               "sec-cap-10"),
        _rotta("L07", "lab_07_correlazioni.ipynb",
               "Correlazioni a finestre mobili e quanto salgono nei crolli",
               "sec-cap-11"),
        _rotta("L08", "lab_08_acp.ipynb",
               "Componenti principali e numero effettivo di scommesse",
               "sec-cap-12"),
        _rotta("L09", "lab_09_regimi.ipynb",
               "Volatilità mobile, persistenza dei regimi e durata dei periodi agitati",
               "sec-cap-regimi"),
        _rotta("L10", "lab_10_dimensionalita.ipynb",
               "Più parametri, adattamenti perfetti e inutili",
               "sec-cap-13"),
        _rotta("L11", "lab_11_potere.ipynb",
               "Quante osservazioni servono per distinguere un vantaggio dal caso",
               "sec-cap-14"),
        _rotta("L12", "lab_12_backtest_base.ipynb",
               "Un backtest onesto riga per riga, e il generatore del metro",
               "sec-cap-15"),
        _rotta("L13", "lab_13_bias_dati.ipynb",
               "Lookahead, test di invarianza e i cinque controlli sui dati",
               "sec-cap-16"),
        _rotta("L14", "lab_14_bias_metodo.ipynb",
               "Venti strategie senza vantaggio e il correttore per test multipli",
               "sec-cap-17"),
        _rotta("L15", "lab_15_ottimizzazione.ipynb",
               "Ottimizzare una regola senza senso, dentro e fuori campione",
               "sec-cap-18"),
        _rotta("L16", "lab_16_analisi_tecnica.ipynb",
               "Sei regole da manuale misurate insieme, con i tre controlli",
               "sec-cap-tecnica"),
        _rotta("L17", "lab_17_prezzo_e_tempo.ipynb",
               "Le due coordinate di un movimento, e il volume messo alla prova",
               "sec-cap-ciclica"),
        _rotta("L18", "lab_18_montecarlo.ipynb",
               "Mille traiettorie invece di una, e i tre numeri che decidono",
               "sec-cap-19"),
        _rotta("C04", "calc_04_dimensionamento.ipynb",
               "Frazione ottimale, rischio di rovina e rischio complessivo",
               "sec-cap-20"),
        _rotta("C05", "calc_05_custodia.ipynb",
               "Probabilità di un evento di custodia e costo della concentrazione",
               "sec-cap-custodia"),
        _rotta("C06", "calc_06_fisco.ipynb",
               "Attrito fiscale, perdite riportate e perdite scadute",
               "sec-cap-fisco"),
        _rotta("L19", "lab_19_strumenti.ipynb",
               "Le cinque prove da fare al proprio ambiente di lavoro",
               "sec-cap-21"),
        _rotta("L20", "lab_20_basi.ipynb",
               "Seme del caso, vettorizzazione e riproducibilità",
               "sec-cap-22"),
        _rotta("L21", "lab_21_ai.ipynb",
               "Due implementazioni della stessa strategia: trova il lookahead",
               "sec-cap-23"),
        _rotta("C07", "calc_07_criterio.ipynb",
               "Il Criterio eseguibile: domande senza risposta e metro del caso",
               "sec-cap-24"),
        _rotta("C08", "calc_08_piano.ipynb",
               "Generatore del piano scritto e del registro delle operazioni",
               "sec-cap-25"),
    ]
}


#: Rotte di servizio: stampate nel colophon, non legate a un quaderno.
#: Vivono qui per la stessa ragione delle altre — un indirizzo stampato non si
#: corregge piu', quindi la destinazione deve restare modificabile.
ROTTE_SERVIZIO: dict[str, tuple[str, str]] = {
    "errata": (
        f"{REPO}/blob/main/ERRATA.md",
        "Errori segnalati dai lettori e correzioni, con la data di ciascuna",
    ),
    "codice": (
        REPO,
        "Il codice che produce ogni figura e ogni numero del libro",
    ),
}


#: Le pagine legali di Cryptoverso, dove vivono titolare, diritti, reclamo e
#: cookie policy. Il dominio del libro e' un sottodominio di quel sito: la sua
#: pagina non ricopia quei dati, li linka.
#:
#: E' il principio gia' scritto nell'informativa di Cryptoverso — «due copie
#: degli stessi dati divergono alla prima variazione» — applicato qui: se il
#: titolare cambia, cambia in un posto solo.
SITO_CRYPTOVERSO = "https://cryptoverso.net"

#: Il recapito per l'esercizio dei diritti, stampato SOLO sulla pagina web del
#: sottodominio — nel libro non compare nessuna email, e non deve comparire.
#:
#: Sta qui, e non e' una duplicazione di comodo. La pagina rimanda a
#: `cryptoverso.net` per diritti e reclamo, ma titolare e recapito no: senza
#: quei due dati non si esercita nessun diritto, e il 28 agosto 2026 e' stato
#: misurato che `cryptoverso.net` **su HTTPS non risponde affatto** — il dominio
#: canonico risolve ancora al parcheggio del fornitore. Un'informativa la cui
#: unica strada verso un diritto e' un collegamento cieco non e' un rimando: e'
#: un vicolo. Quando il sito sara' deployato questi due dati resteranno
#: comunque i suoi, e l'informativa di Cryptoverso resta quella che fa fede.
RECAPITO = "info@cryptoverso.net"

PAGINE_LEGALI = {
    "privacy": f"{SITO_CRYPTOVERSO}/note-legali/privacy",
    "cookie": f"{SITO_CRYPTOVERSO}/note-legali/cookie",
}

#: Lo strumento con cui si misurano le visite alle rotte, se ce n'e' uno.
#: `None` = nessuno, e la pagina lo dichiara insieme all'impegno gia' preso
#: sul sito: se un giorno entrera', sara' uno strumento che non archivia nulla
#: sul dispositivo di chi legge e produce solo conteggi aggregati di pagina.
#: Valorizzandolo con il nome del servizio, la pagina lo nomina.
MISURA: str | None = None


def url_informativa() -> str:
    """L'indirizzo della pagina, che il libro nomina senza stamparlo."""
    return f"https://{DOMINIO}/privacy"


def url_servizio(nome: str) -> str:
    """URL stampato di una rotta di servizio."""
    if nome not in ROTTE_SERVIZIO:
        raise KeyError(f"rotta di servizio inesistente: {nome!r}")
    return f"https://{DOMINIO}/{nome}"


def url(codice: str) -> str:
    """URL stampato per una rotta. Solleva se la rotta non esiste."""
    if codice not in ROTTE:
        raise KeyError(f"rotta inesistente: {codice!r}")
    return ROTTE[codice].url


def tabella_redirect() -> list[tuple[str, str]]:
    """(rotta, destinazione) per generare le pagine di redirect."""
    return [(r.codice.lower(), r.destinazione) for r in ROTTE.values()]


if __name__ == "__main__":
    print(f"dominio: {DOMINIO}  ({len(ROTTE)} rotte)")
    for r in ROTTE.values():
        print(f"  {r.titolo:16s} {r.url:40s} {r.capitolo}")
