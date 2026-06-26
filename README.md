# Groovebox Project

A modern web application skeleton built with a **Vue 3 (TypeScript/Vite)** frontend and a **Flask** backend.

## Project Structure

- **`frontend/`**: Vue 3 Single Page Application (Vite, JavaScript, Pinia, Vue Router, ESLint, Prettier, and Tailwind CSS v4).
- **`backend/`**: Python Flask REST API (Flask, Flask-Cors, python-dotenv, with `.venv` virtual environment).

## Getting Started

### 1. Backend (Flask)

To run the Flask backend:

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Linux/macOS**:
     ```bash
     source .venv/bin/activate
     ```
3. Start the development server:
   ```bash
   python app.py
   ```
   The backend will start on `http://127.0.0.1:5000/`. You can test the health endpoint at `http://127.0.0.1:5000/api/health`.

### 2. Frontend (Vue)

To run the Vue frontend:

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will run on `http://localhost:5173/`.
