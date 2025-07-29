# 🤖 NetSeeker – Telegram Intelligence Bot

NetSeeker è un assistente digitale avanzato progettato per condurre ricerche online su persone e generare report PDF personalizzati. Il bot guida l’utente attraverso una conversazione interattiva, raccoglie dati, analizza piattaforme web e restituisce un documento dettagliato via Telegram o email.

---

## 🧠 Funzionalità principali

- ✍️ Raccolta dati: nome, cognome, anno di nascita, categorie da esplorare
- 🔍 Generazione di nickname e ricerca su decine di piattaforme (social, gaming, forum)
- 📄 Creazione automatica di report PDF con [ReportLab](https://www.reportlab.com/)
- 📤 Invio del report via Telegram o tramite email (SMTP)
- 📲 Interazione tramite pulsanti inline e flusso conversazionale multilingua
- 🗂️ Supporto per italiano, inglese, spagnolo e francese
- 📧 Possibilità di **impostare** o **cancellare** la propria email direttamente dal bot

---

## 🚀 Flusso utente

1. L’utente avvia il bot con `/start`
2. Inserisce nome, cognome e anno di nascita
3. Seleziona le categorie da analizzare
4. Il bot genera nickname e avvia la ricerca
5. Viene creato un report PDF con i risultati
6. L’utente riceve il file via Telegram o email (se ha impostato l’indirizzo)

---

## 🔧 Configurazione

### 1. Ottieni il token API di Telegram
- Vai su [BotFather](https://t.me/BotFather)
- Crea un nuovo bot con `/newbot`
- Copia il token fornito

### 2. Inserisci le credenziali nel file `main_telegram.py`

```python
TOKEN = "INSERISCI_IL_TUO_TOKEN"
EMAIL_ADDRESS = "tuo@email.com"
EMAIL_PASSWORD = "password_app_specifica"
SMTP_SERVER = "smtp.tuoprovider.com"
SMTP_PORT = 587
