/**
 * Mint - Frontend Entry Point
 * ================================
 * Inizializza l'applicazione Vue 3, registra il gestore di stato Pinia, 
 * configura il client-side routing con Vue Router e monta l'app sul DOM.
 */

import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
