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

# ⚙️ Scelte Implementative & Funzionalità Chiave

Questo progetto adotta scelte ingegneristiche mirate a garantire prestazioni ottimali, sicurezza e un'esperienza utente moderna e fluida:

### 1. Separazione Layer (DAL / Controller)
Tutte le query SQL crude sono isolate nella cartella `backend/dal/` (es. `user_dal.py`, `album_dal.py`, ecc.). I controller dei Blueprint Flask contengono esclusivamente la logica HTTP (validazione dei payload JSON, risposte e status code), migliorando la manutenibilità e la testabilità del codice.

### 2. Prevenzione Connection Leaks (Flask Context Teardown)
La funzione `get_db()` in `database.py` registra la connessione SQLite sull'oggetto globale di richiesta di Flask (`flask.g`). Tramite il decoratore `@app.teardown_appcontext` in `app.py`, Flask garantisce la chiusura automatica e pulita della connessione al database a fine richiesta HTTP, anche nel caso in cui vengano sollevate eccezioni.

### 3. Autenticazione Stateless JWT e Password Criptate
* L'autenticazione è totalmente stateless e basata su token **JWT (JSON Web Token)** inseriti nell'header HTTP `Authorization: Bearer <token>` ad ogni chiamata.
* Le password degli utenti non sono mai salvate in chiaro, ma gestite tramite hash crittografico PBKDF2 (`werkzeug.security`).
* Per modificare la password del profilo è obbligatorio inserire e verificare preventivamente la **password attuale** dell'utente. Le password hanno una validazione di sicurezza di minimo 8 caratteri.

### 4. Gestione Integrità dei Dati all'Eliminazione Utente (SET NULL)
Quando un utente collector cancella il proprio account:
* La sua collezione privata (copie fisiche) viene eliminata a cascata (`ON DELETE CASCADE`).
* Gli album da lui inseriti nel catalogo globale non vengono rimossi per non impoverire l'archivio della community. La loro paternità viene impostata a `NULL` nel database (`ON DELETE SET NULL`) e il frontend visualizza in sicurezza la dicitura **`Utente eliminato`** priva di collegamenti ipertestuali.

### 5. Combobox con Ricerca Autocompilante e Aggiunta Inline
I moduli di selezione nativi HTML (ingestibili in caso di cataloghi estesi) sono stati sostituiti da **Combobox personalizzate con overlay di chiusura**:
* Nella registrazione di una copia fisica, l'utente può cercare l'album scrivendo lettere o parole che filtrano i risultati in tempo reale.
* Nella creazione di un album, l'utente cerca l'artista digitando il nome e, se non presente, può crearlo ed associarlo all'istante con un singolo click tramite l'opzione dinamica `+ Crea e aggiungi "<Artista>"`.

### 6. Esportazione Dati e Statistiche Globali (Admin)
L'amministratore ha accesso ad un pannello statistico avanzato munito di grafici a ciambella (Donut Chart) implementati programmaticamente in SVG nativo (senza librerie esterne). Da questa schermata, l'admin può scaricare un report completo in formato **JSON** contenente l'istantanea di tutte le metriche aggregate del sistema.

### 7. Scala Cromatica per le Condizioni Fisiche
Le card di anteprima delle copie fisiche mostrano badge colorati dinamicamente in base alle condizioni per comunicare visivamente lo stato del supporto:
* **Nuovo**: Smeraldo (`text-emerald-400` / `bg-emerald-500/10`)
* **Come nuovo**: Azzurro Cielo (`text-sky-400` / `bg-sky-500/10`)
* **Buono**: Giallo Limone (`text-yellow-300` / `bg-yellow-500/10`)
* **Discreto**: Arancione (`text-orange-500` / `bg-orange-500/10`)
* **Rovinato**: Rosso/Rosa (`text-rose-500` / `bg-rose-500/10`)

---

## 🛠️ Tecnologie Utilizzate

### Backend (Python)
* **`Flask`**: Web server per le REST API.
* **`Flask-Cors`**: Middleware per la gestione delle Cross-Origin Resource Sharing.
* **`python-dotenv`**: Caricamento delle configurazioni dal file `.env`.
* **`PyJWT`**: Gestione, firma e validazione dei token JSON Web Token.
* **`sqlite3` (Nativo)**: Database relazionale embedded.

### Frontend (JavaScript)
* **`Vue.js 3`**: Presentation Layer basato su Composition API.
* **`Pinia`**: Gestione centralizzata dello stato di autenticazione e di sessione.
* **`Vue Router`**: Navigazione Single Page Application (SPA) con guardie di accesso basate su ruoli.
* **`Tailwind CSS`**: Styling responsive e interazioni grafiche fluide.
