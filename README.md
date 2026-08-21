# Non Fidarti di Me — il codice

> *Il trading spiegato con dati, statistica e codice che puoi rieseguire tu.*

Questo repository contiene **tutto il codice del libro**: i 21 laboratori, gli 8 calcolatori e il motore di calcolo `cvbook` che produce le figure stampate.

Il titolo del libro è un'istruzione, non una provocazione. Ogni affermazione del volume nasce da un calcolo, ogni calcolo è qui dentro, e ogni figura si riproduce eseguendo il codice sui **dati congelati** che il libro ha usato per stamparla. Se un numero non ti convince, aprilo e contestalo.

---

## Come si usa

### In un browser, senza installare niente

Ogni quaderno si apre in **Google Colab** con un clic. La prima cella scarica il motore `cvbook` e i dati che servono: non devi configurare nulla.

Nel libro ogni laboratorio ha accanto un QR e un indirizzo breve nella forma `lab.cryptoverso.net/l01`, che porta allo stesso quaderno. L'indirizzo breve diventa attivo con la pubblicazione del sito; i collegamenti Colab qui sotto funzionano già.

### Sul tuo computer

```bash
git clone https://github.com/cryptoverso-lab/non-fidarti-di-me.git
cd non-fidarti-di-me
uv sync
uv run jupyter lab codice/lab
```

Serve **Python 3.12 o superiore**. Con [uv](https://docs.astral.sh/uv/) le dipendenze sono bloccate da `uv.lock`, quindi ottieni le stesse versioni con cui il libro è stato stampato. Clonando il repository i quaderni riconoscono di essere in casa e usano i file locali invece di scaricarli.

---

## I 21 laboratori

Nell'ordine in cui compaiono nel libro.

| | Domanda a cui risponde | Apri |
|---|---|---|
| **Lab 1** | Quanti conti al dettaglio chiudono in perdita, e in quanto tempo | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_01_chi_perde.ipynb) |
| **Lab 2** | Curve di capitale generate dal solo caso, e le più belle fra mille | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_02_equity_casuali.ipynb) |
| **Lab 3** | Mortalità dei token e distorsione da sopravvivenza | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_03_cimitero_token.ipynb) |
| **Lab 4** | Avversione alle perdite e disposizione, misurate sui propri numeri | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_04_bias.ipynb) |
| **Lab 5** | Tre sguardi sugli stessi dati, e il test del vero contro il finto | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_05_misurare.ipynb) |
| **Lab 6** | Code grasse, curtosi e i venti giorni che decidono tutto | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_06_code_grasse.ipynb) |
| **Lab 7** | Correlazioni a finestre mobili e quanto salgono nei crolli | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_07_correlazioni.ipynb) |
| **Lab 8** | Componenti principali e numero effettivo di scommesse | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_08_acp.ipynb) |
| **Lab 9** | Volatilità mobile, persistenza dei regimi e durata dei periodi agitati | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_09_regimi.ipynb) |
| **Lab 10** | Più parametri, adattamenti perfetti e inutili | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_10_dimensionalita.ipynb) |
| **Lab 11** | Quante osservazioni servono per distinguere un vantaggio dal caso | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_11_potere.ipynb) |
| **Lab 12** | Un backtest onesto riga per riga, e il generatore del metro | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_12_backtest_base.ipynb) |
| **Lab 13** | Lookahead, test di invarianza e i cinque controlli sui dati | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_13_bias_dati.ipynb) |
| **Lab 14** | Venti strategie senza vantaggio e il correttore per test multipli | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_14_bias_metodo.ipynb) |
| **Lab 15** | Ottimizzare una regola senza senso, dentro e fuori campione | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_15_ottimizzazione.ipynb) |
| **Lab 16** | Sei regole da manuale misurate insieme, con i tre controlli | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_16_analisi_tecnica.ipynb) |
| **Lab 17** | Le due coordinate di un movimento, e il volume messo alla prova | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_17_prezzo_e_tempo.ipynb) |
| **Lab 18** | Mille traiettorie invece di una, e i tre numeri che decidono | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_18_montecarlo.ipynb) |
| **Lab 19** | Le cinque prove da fare al proprio ambiente di lavoro | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_19_strumenti.ipynb) |
| **Lab 20** | Seme del caso, vettorizzazione e riproducibilità | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_20_basi.ipynb) |
| **Lab 21** | Due implementazioni della stessa strategia: trova il lookahead | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/lab_21_ai.ipynb) |

## Gli 8 calcolatori

Strumenti da usare sui propri numeri, non dimostrazioni.

| | Cosa calcola | Apri |
|---|---|---|
| **Calcolatore 1** | Quanto serve guadagnare per recuperare una perdita | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/calc_01_recupero_perdite.ipynb) |
| **Calcolatore 2** | Costi cumulati su un anno di operatività, al variare della frequenza | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/calc_02_costi.ipynb) |
| **Calcolatore 3** | Tempo sotto il massimo e dimensione compatibile con la tua tolleranza | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/calc_03_stop_sizing.ipynb) |
| **Calcolatore 4** | Frazione ottimale, rischio di rovina e rischio complessivo | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/calc_04_dimensionamento.ipynb) |
| **Calcolatore 5** | Probabilità di un evento di custodia e costo della concentrazione | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/calc_05_custodia.ipynb) |
| **Calcolatore 6** | Attrito fiscale, perdite riportate e perdite scadute | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/calc_06_fisco.ipynb) |
| **Calcolatore 7** | Il Criterio eseguibile: domande senza risposta e metro del caso | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/calc_07_criterio.ipynb) |
| **Calcolatore 8** | Generatore del piano scritto e del registro delle operazioni | [Colab](https://colab.research.google.com/github/cryptoverso-lab/non-fidarti-di-me/blob/main/codice/lab/calc_08_piano.ipynb) |

---

## I dati

I quaderni **non chiamano nessuna API di mercato**. Usano snapshot congelati in `codice/dati/snapshot/`, gli stessi identici file con cui sono state prodotte le figure del libro: è la condizione perché la figura che ottieni sia la figura che stai leggendo.

Undici serie: cinque cripto dai dump pubblici di Binance — inclusa una che non esiste più, perché un cimitero senza lapidi non dimostra niente — più FTSE MIB, ENI, Enel, Intesa Sanpaolo, Generali ed EUR/USD.

Gli script in `codice/ingest/` documentano **come** quelle serie sono state costruite. Si eseguono a mano, una volta, e non servono per usare i quaderni.

---

## Struttura

```
codice/
├── lab/       i 29 quaderni, ciascuno in due formati:
│              .ipynb per Colab e .py in formato percent per leggere il diff
├── src/
│   └── cvbook/  il motore: metriche, simulazioni, grafica, regole del libro
├── dati/
│   └── snapshot/  le undici serie congelate (.parquet)
└── ingest/    come sono stati costruiti gli snapshot
```

Ogni quaderno esiste **due volte**, in `.ipynb` e in `.py`. Non è una duplicazione: il `.py` in formato percent è la versione che si legge in una revisione, perché un diff su un notebook JSON non si legge. I due formati sono tenuti allineati da `codice/lab/costruisci.py`.

---

## Errata

Gli errori trovati dopo la stampa sono raccolti in **[ERRATA.md](ERRATA.md)**, con la data della segnalazione e chi l'ha fatta.

Le segnalazioni sono benvenute: apri una *issue* in questo repository. Le correzioni sostanziali entrano nella ristampa successiva.

---

## Licenza

Il **codice** di questo repository — motore `cvbook`, laboratori, calcolatori, script — è rilasciato con licenza **MIT**: vedi [LICENSE](LICENSE).

Il **testo del libro** e le figure impaginate per la stampa non sono in questo repository e non sono coperti dalla licenza MIT: restano di Luigi Garone. Qui c'è il codice, ed è quello che serve per contestare i numeri.

---

## Perimetro

Questo materiale ha finalità **didattica e di ricerca**. Non è consulenza in materia di investimenti, non è una raccomandazione e non contiene segnali operativi. I calcolatori lavorano sui numeri che gli dài tu: servono a farti vedere le conseguenze di una scelta, non a suggerirtene una.

---

<div align="center">

<br>

<img src=".github/cryptoverso.svg" alt="Cryptoverso" width="56">

**[Cryptoverso](https://cryptoverso.net)**
Ricerca quantitativa sui mercati, formazione e software di analisi.

<sub>Software sviluppato da Logika.studio</sub>

</div>
