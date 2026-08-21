# Consegna dei quaderni — che cosa deve essere vero perché funzionino

Questa pagina non descrive il codice: descrive le **condizioni** perché i 29
collegamenti Colab, i download e la catena automatica verso il sito funzionino
davvero. Sono cose che stanno fuori dal repository — visibilità, segreti,
variabili — e che nessun test può rendere verdi da solo.

Si legge prima di pubblicare, e si rilegge il giorno in cui qualcosa smette di
funzionare.

---

## 0. Stato misurato il 2026-08-21

| Fatto | Misura | Comando |
|---|---|---|
| il repository esiste ed è **pubblico** | `"visibility": "public"`, `"private": false` | `curl -s https://api.github.com/repos/<org>/<repo>` |
| la pagina risponde a chi non ha credenziali | `200` | `curl -o /dev/null -w '%{http_code}' https://github.com/<org>/<repo>` |
| `avvio.py` è scaricabile da `raw` | `200` | `curl -o /dev/null -w '%{http_code}' https://raw.githubusercontent.com/<org>/<repo>/main/codice/lab/avvio.py` |
| i 29 `.ipynb` sono tracciati sul ramo pubblicato | `29` | `git ls-tree -r --name-only origin/main -- codice/lab \| grep -c ipynb` |
| ramo di default | `main` | `curl -s https://api.github.com/repos/<org>/<repo>` |

**Ma il ramo pubblicato è indietro.** Alla stessa data il checkout locale ha
**15 commit** che `origin/main` non ha, e fra questi ci sono le correzioni della
coda inglese e i tre quaderni ricostruiti. Finché non vengono pubblicati, un
lettore che apre un quaderno da Colab legge una versione vecchia — e il sito
pubblica l'impronta di un file diverso da quello che GitHub serve.

> **Passo manuale, per Luigi:** `git push origin main` dal checkout locale. È
> l'unico modo perché quanto sopra diventi vero anche per chi legge.

Organizzazione, nome del repository e ramo si leggono da
`codice/src/cvbook/link.py`, che ne è la **sede unica**: `costruisci.py --sincronizza`
riscrive da lì la prima cella di tutti e 29 i quaderni. Non vanno battuti a mano
da nessun'altra parte.

---

## 1. Il repository deve essere PUBBLICO — è una precondizione, non una preferenza

La documentazione ufficiale di Google (`googlecolab/colabtools`,
`notebooks/colab-github-demo.ipynb`) separa i due casi senza sfumature:

> «Colab can load **public** github notebooks directly, **with no required
> authorization step**.»
> «Loading a notebook from a **private** GitHub repository is possible, but
> requires an additional step to allow Colab to access your files.» — e quel
> passo è un OAuth che **il lettore** dovrebbe autorizzare.

Se il repository torna privato si rompono **tre cose**, non una:

1. **I 29 collegamenti «Apri in Colab».** Il flusso privato non passa dalla URL
   diretta `…/blob/…`: passa dal navigatore di Colab dopo un'autorizzazione. E
   comunque non basterebbe, perché richiede che il lettore **abbia accesso al
   repository** — cosa che chi compra il libro non ha e non può avere.
2. **Tutti i download** (`.ipynb`, `.py`, gli snapshot Parquet):
   `raw.githubusercontent.com` su un repository privato risponde `404` senza un
   token.
3. **La prima cella di ogni quaderno**, anche per chi il quaderno lo aprisse in
   un altro modo: quella cella scarica `avvio.py` da `raw`, e senza token prende
   `404`. Il quaderno muore all'avvio, sulla macchina di chiunque, **autore
   compreso**.

Un repository privato non rende i lab «disponibili a chi ha accesso»: li rende
**non funzionanti per tutti**.

---

## 2. L'errore di Colab non distingue «non esiste» da «è privato»

Misurato in un browser reale: il messaggio che Colab mostra è **identico** nei
due casi. Dall'esterno non si distinguono, e chi diagnostica guardando Colab
cerca il problema sbagliato.

**La diagnosi si fa su `raw.githubusercontent.com`**, che risponde `404` in
entrambi i casi ma è interrogabile senza browser e senza sessione:

```bash
curl -o /dev/null -w '%{http_code}\n' \
  https://raw.githubusercontent.com/<org>/<repo>/main/codice/lab/avvio.py
```

È esattamente ciò che fa `pnpm verify:raggiungibilita` dal lato del sito, ed è
il motivo per cui il suo messaggio d'errore nomina **entrambe** le cause: «il
repository non è pubblicato **oppure non è pubblico**». Un controllo che ne
nominasse una sola manderebbe a cercare dalla parte sbagliata una volta su due.

---

## 3. I segreti e le variabili della Action

`.github/workflows/quaderni.yml` esegue i quaderni, valida il bundle e apre una
PR **su un altro repository** — quello del sito, che è privato. Il
`GITHUB_TOKEN` che GitHub fornisce da solo **non basta per costruzione**: è
limitato al repository che lo emette. Serve una credenziale esplicita.

Da creare in `Settings > Secrets and variables > Actions` **di questo
repository**:

| Nome | Tipo | Che cosa deve avere | Perché |
|---|---|---|---|
| `REPO_SITO` | Variable | `<organizzazione>/<repository>` del repo del sito | Il nome del repository è configurazione e non si scrive in un file (D-14/D-57). Se manca, il workflow si ferma al primo step invece di far ripiegare il checkout sul repository corrente |
| `TOKEN_SITO_LETTURA` | Secret | Fine-grained PAT, **solo** il repository del sito, permesso **`Contents: Read-only`** | Il job che ESEGUE i quaderni deve entrare nel repo del sito (che è privato) per il contratto del bundle, il registro delle rotte, gli `alt` già scritti e `svgo`. Non deve poterci scrivere |
| `TOKEN_PR_SITO` | Secret | Fine-grained PAT, **solo** il repository del sito, permessi **`Contents: Read and write`** e **`Pull requests: Read and write`** | Serve a spingere un ramo e ad aprire la PR. Vive nel job che **non esegue** una riga dei quaderni: un token che scrive altrove non deve stare nello stesso ambiente in cui gira del codice |

Si creano da `GitHub > Settings > Developer settings > Personal access tokens >
Fine-grained tokens`, scegliendo **«Only select repositories»** e selezionando
il solo repository del sito. Due token e non uno: la differenza fra leggere e
scrivere è l'unica cosa che separa un incidente da un danno.

Serve inoltre che **Actions sia abilitato** su questo repository
(`Settings > Actions > General`): un workflow committato in un repository con le
Action disattivate non gira e non lo dice.

---

## 4. Il nome del repository: la finestra si è chiusa, e va detto

La raccomandazione della ricerca era netta: **dare al repository un nome legato
al progetto e non al titolo del libro**, perché il titolo può cambiare ancora
(sottotitolo, edizione, traduzione) mentre il repository ospita il codice.
Misurato su otto rinomine reali, `raw.githubusercontent.com` continua a servire
il vecchio nome con un `200` diretto e byte identici, e Colab continua ad aprire
i quaderni — **ma il redirect vale finché nessuno riusa il vecchio nome**, e
GitHub lo dichiara esplicitamente.

Finché il repository non era pubblicato, cambiare nome costava **un comando**
(`REPO_NOME` in `codice/src/cvbook/link.py`, più `costruisci.py --sincronizza`).
Dal 2026-08-21 il repository è pubblicato: **quel costo non è più zero.** Oggi
una rinomina lascia dietro di sé un redirect da mantenere per sempre e una
regola da non violare mai — «non riusare mai il nome vecchio» — che vive nella
testa di una persona e non in un gate.

Resta una scelta di Luigi. Va fatta **prima** che il libro sia in mano ai
lettori e che i quaderni finiscano salvati su Drive con la URL originale nella
prima cella: da quel momento il redirect non è più una comodità, è l'unica cosa
che li tiene vivi.

---

## 5. Le variabili che il sito legge, e il valore che devono avere

Il sito non conosce né l'organizzazione né il repository: li legge da tre
variabili, più una quarta che accende lo stato «pubblicato» sulle 62 pagine.
Vanno impostate nel progetto del sito (Vercel) **e** come variabili di
repository per la sua CI, che le usa nel gate di raggiungibilità.

| Variabile | Valore dopo la pubblicazione | Che cosa succede se manca |
|---|---|---|
| `NEXT_PUBLIC_NOTEBOOKS_GITHUB_ORG` | l'organizzazione dichiarata in `codice/src/cvbook/link.py` | la build si ferma: lo schema la pretende non vuota |
| `NEXT_PUBLIC_NOTEBOOKS_GITHUB_REPO` | il nome del repository dichiarato nello stesso file | idem |
| `NEXT_PUBLIC_NOTEBOOKS_REF` | `main` (il ramo di default misurato) | idem |
| `NEXT_PUBLIC_NOTEBOOKS_PUBBLICATO` | `2026-08-21` — la data di creazione del repository, in forma `AAAA-MM-GG` | resta vuota, e **vuota significa «non ancora pubblicato»**: le 62 pagine dichiarano lo stato invece di mostrare un bottone che porta a un 404 |

`NEXT_PUBLIC_NOTEBOOKS_PUBBLICATO` è **il passo manuale** che accende lo stato
pubblicato: nessuna Action lo valorizza, ed è voluto — è una data che qualcuno
deve affermare, non dedurre.

---

## 6. L'ordine dei passi

1. `git push origin main` — i quaderni pubblicati diventano quelli veri (§0).
2. Verificare i tre `200` di §0 senza credenziali (browser in incognito o `curl`).
3. Abilitare Actions su questo repository.
4. Creare `REPO_SITO`, `TOKEN_SITO_LETTURA` e `TOKEN_PR_SITO` (§3).
5. Lanciare il workflow **Quaderni** a mano (`Run workflow`): il primo giro è
   anche la sua prima prova reale.
6. Impostare le quattro variabili del sito (§5), compresa la data.
7. Rilanciare la CI del sito: `pnpm verify:raggiungibilita` smette di dichiararsi
   inerte e verifica davvero le 29 destinazioni.

I passi 1-4 e 6 sono manuali perché richiedono credenziali che nessuno script
possiede. Gli altri li fa la macchina.
