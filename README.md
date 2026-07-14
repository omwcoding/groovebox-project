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

## Integrazione Discogs API

GrooveBox è ora integrato con le **API di Discogs** (tramite autenticazione Consumer Key/Secret) per arricchire dinamicamente il catalogo comunitario:
* **Ricerca & Importazione**: Gli utenti Collector e Admin possono cercare album e artisti direttamente su Discogs e importarli localmente con un singolo clic.
* **Metadati Completi**: L'importazione compila automaticamente titolo, anno, generi musicali e stili, etichetta discografica, numero di catalogo, codice a barre e paese di stampa.
* **Tracklist & Biografie**: Vengono salvate le tracklist complete dei brani ed il profilo biografico dell'artista.
* **Download degli Asset**: Copertine e foto degli artisti vengono scaricate sul server locale in modo deterministico (riutilizzate se presenti in caso di reset DB) ed eliminate fisicamente alla cancellazione dell'album/artista.

---

## Come Iniziare

### 1. Configurazione del Backend (Flask)

1. Entra nella cartella del backend:
   ```bash
   cd backend
   ```
2. Crea l'ambiente virtuale python:
   ```bash
   python -m venv .venv
   ```
3. Attiva il virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   * **Linux/macOS**:
     ```bash
     source .venv/bin/activate
     ```
4. Installa le dipendenze richieste:
   ```bash
   pip install -r requirements.txt
   ```
5. Configura le variabili di ambiente:
   Copia il file `.env.example` in `.env` e configura la chiave di Flask e le credenziali delle API di Discogs:
   ```bash
   cp .env.example .env
   ```
   *(Su Windows PowerShell usa `Copy-Item .env.example .env`)*

   Apri il file `.env` appena generato ed inserisci i tuoi valori:
   ```env
   SECRET_KEY=la_tua_chiave_segreta_jwt
   DISCOGS_CONSUMER_KEY=la_tua_consumer_key_discogs
   DISCOGS_CONSUMER_SECRET=il_tuo_consumer_secret_discogs
   ```
6. Inizializza il database (con creazione tabelle ed eliminazione a cascata):
   ```bash
   python core/database.py
   ```
7. (Opzionale) Esegui il seed di grandi dimensioni per avere 50 utenti, 120 album, 60 artisti e 250 copie:
   ```bash
   python seed_large.py
   ```
8. Avvia il server Flask:
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

## 🛠️ Tecnologie Utilizzate
* **`Flask`**: Micro-framework web flessibile scelto per il Business Logic Layer (REST API).
* **`Vue.js 3`**: Presentation Layer reattivo sviluppato tramite **Composition API** e sintassi `<script setup>`.
* **`SQLite 3`**: Database relazionale embedded leggero gestito tramite query crude parametrizzate.
* **`Tailwind CSS`**: Utility-first CSS framework per lo sviluppo rapido di un'interfaccia responsive ed animata.
* **`Vite`**: Build tool di nuova generazione per il caricamento a caldo (HMR) e l'ottimizzazione degli asset in produzione.

## 📚 Librerie & Dipendenze

### Backend (Python)
* **`Flask-CORS`**: Abilita la Cross-Origin Resource Sharing (CORS) per far comunicare frontend e backend su porte diverse.
* **`PyJWT`**: Gestisce la cifratura, firma e decodifica dei token JWT per l'autenticazione stateless.
* **`Werkzeug`**: Fornisce utility per l'hashing sicuro delle password (`werkzeug.security`) e la bonifica dei nomi dei file caricati (`werkzeug.utils.secure_filename`).
* **`python-dotenv`**: Carica le configurazioni e le chiavi segrete dal file `.env` nelle variabili d'ambiente.
* **`requests`**: Client HTTP leggero per interagire con le API REST di Discogs ed effettuare il download delle immagini.

### Frontend (JavaScript)
* **`Pinia`**: Store globale per la gestione centralizzata della sessione utente e persistenza del token JWT.
* **`Vue Router`**: Router ufficiale per la navigazione SPA con guardie di accesso basate su permessi e ruoli.
