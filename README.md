# NetSeeker

Benvenuto nel **Telegram PDF Bot**, un assistente intelligente che ti permette di:

- ✍️ Ricevere input testuali dagli utenti
- 📄 Generare file PDF personalizzati
- 📤 Inviarli direttamente via Telegram o tramite email
- 📲 Interagire con pulsanti inline e comandi intuitivi

Questo bot è pensato per semplificare la creazione e la condivisione di documenti, tutto direttamente da Telegram.

---

## 🧠 Come funziona

Il bot guida l'utente attraverso una conversazione interattiva. Ecco il flusso tipico:

1. L'utente avvia il bot con `/start`
2. Inserisce un testo o una richiesta
3. Il bot genera un PDF con `reportlab`
4. L'utente può scegliere se scaricarlo o inviarlo via email
5. Il bot invia il file come allegato o lo spedisce tramite SMTP

---

## 🔧 Configurazione

### 1. Ottieni il token API di Telegram

- Vai su [BotFather](https://t.me/BotFather)
- Crea un nuovo bot con `/newbot`
- Copia il **token API** fornito

### 2. Inserisci le credenziali nel codice

Nel file `main_telegram.py`, cerca le seguenti variabili e personalizzale:

```python
TOKEN = "INSERISCI_IL_TUO_TOKEN"
EMAIL_ADDRESS = "tuo@email.com"
EMAIL_PASSWORD = "password_app_specifica"
SMTP_SERVER = "smtp.tuoprovider.com"
SMTP_PORT = 587
