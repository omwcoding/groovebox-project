# GrooveBox Project

GrooveBox è un'applicazione web universitaria progettata per i collezionisti di supporti musicali fisici (vinili, CD, cassette). L'applicazione consente agli utenti di catalogare la propria collezione privata collaborando contemporaneamente a un database musicale comunitario globale.

Il progetto segue rigorosamente un'architettura logica a **3 layer**:
1. **Presentation Layer:** Vue.js 3 (Composition API), Pinia (gestione dello stato), Vue Router, Vite e Tailwind CSS v4.
2. **Business Logic Layer:** Python Flask e PyJWT (autenticazione stateless).
3. **Data Access Layer:** SQLite3 nativo con query SQL parametrizzate ed eliminazioni gestite via cascade del database (NO ORM).

---

## Struttura del Progetto

* **`frontend/`**: Single Page Application in Vue 3 (Vite, JavaScript, Pinia, Vue Router, Tailwind CSS v4 con estensioni Glassmorphism custom).
* **`backend/`**: REST API in Python Flask (Flask, Flask-Cors, python-dotenv, venv `.venv`, connessioni SQLite3 gestite a livello di richiesta HTTP).

---

## Come Iniziare

### 1. Configurazione del Backend (Flask)

1. Entra nella cartella del backend:
   ```bash
   cd backend
   ```
2. Attiva il virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   * **Linux/macOS**:
     ```bash
     source .venv/bin/activate
     ```
3. Configura le variabili di ambiente:
   Copia il file `.env.example` in `.env` e personalizza la chiave segreta:
   ```bash
   cp .env.example .env
   ```
   *(Su Windows PowerShell usa `Copy-Item .env.example .env`)*
4. Ripristina il database (con creazione tabelle ed eliminazione a cascata):
   ```bash
   python database.py
   ```
5. (Opzionale) Esegui il seed di grandi dimensioni per avere 50 utenti, 120 album, 60 artisti e 250 copie:
   ```bash
   python seed_large.py
   ```
6. Avvia il server Flask:
   ```bash
   python app.py
   ```
   L'API del backend sarà disponibile su `http://127.0.0.1:5000/`. Puoi verificare lo stato su `http://127.0.0.1:5000/api/health`.

### 2. Configurazione del Frontend (Vue)

1. Entra nella cartella del frontend:
   ```bash
   cd frontend
   ```
2. Installa le dipendenze (se non già fatto):
   ```bash
   npm install
   ```
3. Avvia il server di sviluppo Vite (configurato con proxy inverso verso la porta 5000):
   ```bash
   npm run dev
   ```
   L'applicazione frontend sarà disponibile su `http://localhost:5173/`.

---
---

# 📝 NOTA TEMPORANEA (Da eliminare prima del push finale)

*Questa sezione riassume le scelte implementative, le librerie utilizzate e gli use case da testare prima di procedere con l'affinamento grafico finale.*

## 🧠 Scelte Implementative Chiave

1. **Separazione DAL / Controller (Rotte):**
   Tutte le query SQL crude sono state isolate nella cartella `backend/dal/` (es. `user_dal.py`, `album_dal.py`, ecc.). I controller dei Blueprint Flask contengono esclusivamente la logica HTTP (validazione, rotte e risposte JSON), migliorando drasticamente la manutenibilità.

2. **Gestione del Ciclo di Vita del Database (Zero Connection Leaks):**
   La funzione `get_db()` in `database.py` registra la connessione SQLite su `flask.g` (l'oggetto globale di richiesta di Flask). Tramite il decoratore `@app.teardown_appcontext` in `app.py`, Flask garantisce la chiusura automatica della connessione a fine richiesta HTTP, anche nel caso in cui le query sollevino delle eccezioni.

3. **Creazione Atomica a Cascata (Endpoint Transazionale):**
   Per evitare che il frontend debba coordinare 3 chiamate HTTP sequenziali per creare un "Nuovo Disco" (Artista -> Album -> Copia), abbiamo implementato l'endpoint `/api/copies/cascade`. Questo esegue la ricerca/creazione di artisti e album e l'associazione della copia fisica all'interno di una singola transazione transazionale SQL (`with conn:`). In caso di errore intermedio, viene eseguito il rollback impedendo la creazione di elementi orfani nel catalogo comune.

4. **Integrità dei Dati su Eliminazione Collector:**
   Quando un utente collector elimina il proprio account:
   * Le sue copie fisiche private vengono rimosse automaticamente a livello DB tramite le chiavi esterne configurate con `ON DELETE CASCADE`.
   * Gli album da lui pubblicati (che appartengono al catalogo comunitario) non vengono eliminati, ma la loro paternità viene trasferita nel DAL all'utente amministratore predefinito (`id_user = 1`), preservando l'integrità del catalogo globale.

5. **Centralizzazione Costanti e Formati Condivisi:**
   Per rispettare il principio DRY, formati e condizioni del disco sono stati centralizzati in `frontend/src/constants/music.js` e limitati ai valori richiesti:
   * **Formati:** Vinile, CD, Cassetta
   * **Condizioni:** Nuovo, Come nuovo, Buono, Discreto, Rovinato

---

## 📚 Librerie Utilizzate Spiegate

### Backend (Python)
* **`Flask`**: Framework web leggero scelto come Business Logic Layer per gestire le richieste REST API.
* **`Flask-Cors`**: Middleware per abilitare la condivisione delle risorse tra domini diversi (CORS), necessario affinché il frontend (porta 5173) comunichi con il backend (porta 5000).
* **`python-dotenv`**: Carica le variabili di ambiente dal file `.env` (come la `SECRET_KEY` per JWT).
* **`PyJWT`**: Libreria per generare e verificare i token JWT per l'autenticazione stateless.
* **`werkzeug.security`**: Fornisce `generate_password_hash` e `check_password_hash` per salvare in modo sicuro gli hash delle password (algoritmo bcrypt/scrypt di default).
* **`sqlite3` (Nativo)**: Modulo Python standard per connettersi al database embedded SQLite3.

### Frontend (JavaScript)
* **`Vue.js 3`**: Framework per il Presentation Layer (Composition API per un codice modulare).
* **`Pinia`**: Store per la gestione dello stato globale dell'applicazione (in particolare la sessione utente e il token JWT in `stores/auth.js`).
* **`Vue Router`**: Gestisce la navigazione SPA e implementa i controlli di accesso (`requiresAuth` e ruoli `collector` o `administrator` via navigation guard).
* **`Tailwind CSS v4`**: Utilizzato per lo styling responsive.

---

## 🧪 Casi d'Uso (Use Case) da Testare Domani

Prima di passare all'affinamento estetico definitivo, testa i seguenti flussi:

### 1. Autenticazione e Sicurezza
- [ ] **Registrazione Collector:** Registra un nuovo utente con dati validi. Verifica che la password venga memorizzata come hash nel DB.
- [ ] **Controllo Duplicati:** Tenta di registrare un utente con lo stesso username o email e assicurati che restituisca errore `409 Conflict`.
- [ ] **Login & Rilascio JWT:** Effettua il login con credenziali corrette (verifica il salvataggio in `localStorage`) ed errate (verifica l'errore `401 Unauthorized`).
- [ ] **Scadenza Token:** Modifica a mano o elimina il token da `localStorage` e tenta di navigare su pagine protette; verifica il redirect a `/login`.

### 2. Gestione Catalogo (Album e Artisti)
- [ ] **Aggiunta Album (Collector):** Crea un album inserendo titolo, genere, anno e associandovi uno o più artisti esistenti.
- [ ] **Creazione Artista Inline:** Dal form di creazione dell'album, aggiungi un artista inline e verifica che compaia immediatamente nella lista degli associati.
- [ ] **Modifica/Eliminazione Album (Solo Admin):** Accedi come collector e verifica che non ci siano i pulsanti di modifica/rimozione album nella pagina di dettaglio. Accedi come admin, modifica i dati dell'album e poi eliminalo (verifica la rimozione a cascata delle associazioni).

### 3. Gestione Collezione Privata
- [ ] **Aggiunta Copia da Catalogo:** Dalla pagina di dettaglio di un album del catalogo, clicca su "Aggiungi alla mia collezione" e verifica l'inserimento.
- [ ] **Aggiunta a Cascata (Nuovo Disco):** Dalla pagina "La tua collezione" -> Tab "Nuovo Disco", inserisci un album e un artista inesistenti. Verifica che vengano inseriti nel catalogo comune e che la copia venga registrata in un unico click.
- [ ] **Modifica/Rimuovi Copia:** Modifica le note, formato o condizione di una propria copia. Rimuovi la copia e verifica che sia sparita solo dalla tua collezione (mentre l'album rimane a catalogo).

### 4. Gestione Amministrativa (Utenti e Stats)
- [ ] **Moderazione Utenti (Admin):** Accedi come admin, visita `/users` e visualizza l'elenco dei collector.
- [ ] **Eliminazione Utente (Transazione DAL):** Elimina un utente collector che possiede sia copie fisiche che album da lui creati a catalogo. Verifica che:
  * L'utente sia eliminato.
  * Le sue copie fisiche siano cancellate.
  * Gli album da lui creati **siano ancora presenti** ma associati a `@admin`.
- [ ] **Dashboard Statistiche (Admin):** Visita `/stats` e verifica che i contatori totali e i grafici di distribuzione (es. formati più collezionati) siano coerenti con il seed.
