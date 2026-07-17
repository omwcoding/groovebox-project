# Mint — Your collection. In Mint condition.

Mint è un'applicazione web moderna e premium progettata per i collezionisti di supporti musicali fisici (vinili, CD, cassette). L'applicazione consente agli utenti di catalogare la propria collezione privata (il **Vault**), gestire una lista dei desideri (**Wishlist**), e condividere la propria passione tramite un **Profilo Pubblico** condivisibile in sola lettura.

Il progetto segue un'architettura rigorosa a **3 layer**:
1. **Presentation Layer:** SPA reattiva in Vue 3 (Composition API), Pinia (gestione dello stato), Vue Router, Vite e Tailwind CSS v4.
2. **Business Logic Layer:** REST API in Python Flask e PyJWT per autenticazione stateless basata su token.
3. **Data Access Layer:** Connessione a database remoto **PostgreSQL su Supabase** con query SQL parametriche crude (NO ORM).

---

## 🚀 Caratteristiche Principali

*   **Il Vault**: Gestione della collezione personale a scaffale visivo (con visualizzazione 3D/dorso dei dischi) o griglia, con filtri per formato, genere, anno e stato di conservazione.
*   **Ricerca Unificata & Zero-Click Import**: Ricerca integrata che interroga contemporaneamente il DB locale ed il database globale di **Discogs API**. L'importazione e la creazione di artisti/album avviene in background al momento dell'aggiunta al Vault.
*   **Wishlist (Wantlist)**: Gestione dei dischi desiderati con possibilità di promozione immediata ("Ho comprato questo disco") a copia fisica nel Vault compilando formato, condizione e note personali.
*   **Profilo Pubblico Condivisibile**: Possibilità di rendere il proprio profilo pubblico (attivando `is_public` nelle impostazioni) per generare un link `/share/{username}` di sola lettura, completo di statistiche e ultimi acquisti.
*   **Supabase Storage**: Archiviazione cloud delle immagini delle copertine degli album, delle foto degli artisti e degli avatar degli utenti.
*   **Spotify Search Integration**: Collegamento rapido per ascoltare l'album su Spotify direttamente dalla scheda di dettaglio.

---

## 📂 Struttura del Progetto

*   **`frontend/`**: Single Page Application in Vue 3 (Vite, JavaScript, Pinia, Vue Router, Tailwind CSS v4 con estensioni Glassmorphism custom).
*   **`backend/`**: REST API in Python Flask (Flask, Flask-Cors, python-dotenv, venv `.venv`, connessioni PostgreSQL remote via `psycopg2`).

---

## 🛠️ Come Iniziare

### 1. Configurazione del Backend (Flask)

1.  Entra nella cartella del backend:
    ```bash
    cd backend
    ```
2.  Crea l'ambiente virtuale python:
    ```bash
    python -m venv .venv
    ```
3.  Attiva il virtual environment:
    *   **Windows (PowerShell)**:
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
    *   **Linux/macOS**:
        ```bash
        source .venv/bin/activate
        ```
4.  Installa le dipendenze richieste:
    ```bash
    pip install -r requirements.txt
    ```
5.  Configura le variabili di ambiente:
    Copia il file `.env.example` in `.env` e configura la chiave di Flask, le credenziali Discogs e quelle di Supabase:
    ```bash
    cp .env.example .env
    ```
    *(Su Windows PowerShell usa `Copy-Item .env.example .env`)*

    Apri il file `.env` appena generato ed inserisci i tuoi valori:
    ```env
    SECRET_KEY=la_tua_chiave_segreta_jwt
    DISCOGS_CONSUMER_KEY=la_tua_consumer_key_discogs
    DISCOGS_CONSUMER_SECRET=il_tuo_consumer_secret_discogs
    DATABASE_URL=postgresql://postgres.[username]:[password]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require
    SUPABASE_URL=https://[ref].supabase.co
    SUPABASE_ANON_KEY=la_tua_anon_key_supabase
    ```
6.  Inizializza la connessione al database remoto ed esegui il seeding dei dati iniziali (con gli account di default `admin` e `test`):
    ```bash
    python core/database.py
    ```
7.  Avvia il server Flask:
    ```bash
    python app.py
    ```
    L'API del backend sarà disponibile su `http://127.0.0.1:5000/`. Puoi verificare lo stato su `http://127.0.0.1:5000/api/health`.

### 2. Configurazione del Frontend (Vue)

1.  Entra nella cartella del frontend:
    ```bash
    cd frontend
    ```
2.  Installa le dipendenze:
    ```bash
    npm install
    ```
3.  Avvia il server di sviluppo Vite (configurato con proxy inverso verso la porta 5000):
    ```bash
    npm run dev
    ```
    L'applicazione frontend sarà disponibile su `http://localhost:5173/`.

---

## 🛠️ Tecnologie Utilizzate

*   **`Flask`**: Micro-framework web flessibile scelto per il Business Logic Layer (REST API).
*   **`Vue.js 3`**: Presentation Layer reattivo sviluppato tramite **Composition API** e sintassi `<script setup>`.
*   **`PostgreSQL (Supabase)`**: Database relazionale cloud ad alte prestazioni per la persistenza dei dati.
*   **`Supabase Storage`**: Object storage sicuro per il salvataggio degli asset multimediali (copertine, avatar).
*   **`Tailwind CSS`**: Utility-first CSS framework per lo sviluppo rapido di un'interfaccia responsive ed animata.
*   **`Vite`**: Build tool di nuova generazione per il caricamento a caldo (HMR) e l'ottimizzazione degli asset in produzione.

---

## 📚 Librerie & Dipendenze principali

### Backend (Python)
*   **`psycopg2-binary`**: Driver PostgreSQL per Python.
*   **`Flask-CORS`**: Gestione Cross-Origin Resource Sharing.
*   **`PyJWT`**: Autenticazione stateless tramite JWT token.
*   **`requests`**: Client HTTP per l'integrazione Discogs.
*   **`supabase`**: SDK Python per l'upload degli asset su Supabase Storage.

### Frontend (JavaScript)
*   **`Pinia`**: Gestione reattiva dello stato globale di autenticazione.
*   **`Vue Router`**: Router SPA con guardie di accesso basate su ruoli e token.
