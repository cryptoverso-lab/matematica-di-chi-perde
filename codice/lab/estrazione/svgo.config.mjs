/**
 * La configurazione di `svgo` per le figure dei lab.
 *
 * E' un file JavaScript dentro un repository Python perche' `svgo` e' un
 * programma Node: la sua configurazione va scritta nella lingua che lui legge,
 * e `svgo@4` accetta solo `.js` / `.mjs` / `.cjs`. Sta accanto al modulo che lo
 * invoca (`figure.py`) invece che nella radice del repository, cosi' non viene
 * scambiato per la configurazione di un progetto Node che qui non esiste.
 *
 * IL BINARIO NON E' QUI. `svgo@4.0.2` e' quello gia' installato nel repo del
 * SITO, con la versione pinnata dal suo lockfile: questo repository non ha un
 * `package.json` e non ne acquista uno per un'ottimizzazione.
 *
 * LE DUE OPZIONI CHE CONTANO, e perche' non sono una preferenza:
 *
 * - `inlineStyles` con `onlyMatchedOnce: false` e `convertStyleToAttrs`
 *   eliminano il `<style>*{stroke-linejoin:round;stroke-linecap:butt}</style>`
 *   che matplotlib mette in OGNI figura. Le figure vanno in linea nell'HTML
 *   servito, e la Fase 2 ha verbalizzato «tag `<style>`: 0» come misura su cui
 *   poggia l'eccezione `style-src 'unsafe-inline'` della CSP: senza queste due
 *   opzioni quella misura diventerebbe falsa il giorno della prima pagina di
 *   lab (04-UI-SPEC §3.3, D-71).
 * - `onlyMatchedOnce: false` e' obbligatorio, non un di piu': il selettore di
 *   matplotlib e' `*`, quindi corrisponde a molti elementi, e col default
 *   (`true`) `inlineStyles` lo lascerebbe dov'e'.
 *
 * MISURATO, perche' il sospetto e' legittimo: inlinare un selettore universale
 * potrebbe gonfiare il file. Non succede — `svgo` risolve le proprieta'
 * ereditate sull'elemento radice e ricompatta. Sulla prima figura di `lab_05`:
 * 168 482 byte grezzi, 84 851 col preset di default (che lascia il `<style>`),
 * **75 125 con questa configurazione**. Meno peso e zero `<style>`.
 */
export default {
  multipass: true,
  plugins: [
    { name: 'preset-default' },
    { name: 'inlineStyles', params: { onlyMatchedOnce: false } },
    'convertStyleToAttrs',
  ],
}
