import json, requests, asyncio, os, smtplib, threading
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import CommandHandler, ApplicationBuilder, Application, CommandHandler, MessageHandler, CallbackQueryHandler,ConversationHandler, ContextTypes, filters
from reportlab.lib.pagesizes import A4
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO
from email.message import EmailMessage

TOKEN = "tuo-token"
NOME, COGNOME, ANNO, CATEGORIE = range(4)
EMAIL = range(1)
EMAIL_FILE = "email_utenti.json"

with open("siti.json", "r", encoding="utf-8") as f:
    categorie_json = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm *NetSeeker*, your digital assistant for online investigations.\n\n"
        "🔎 Want to quickly discover someone's profiles? I can search across dozens of platforms: social networks, forums, gaming sites, and more.\n\n"
        "📄 At the end, I'll provide a complete PDF report with all the results found, ready to share or archive.\n\n"
        "💡 It's simple: I'll ask for name, surname, birth year (if known), and the categories of sites to explore.\nYou can customize the search as you like!\n\n",
        parse_mode="Markdown"
    )
    await update.message.reply_text("📧 Type /setemail to set the email address to which reports will be sent. \nType /delemail to delete the email associated with your account.", parse_mode="Markdown")
    await update.message.reply_text("🚀 Let's get started. Enter the *first name* of the person to search:", parse_mode="Markdown")
    return NOME

async def ricevi_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome"] = update.message.text.strip()
    await update.message.reply_text("🏷️ Now enter the surname:")
    return COGNOME

async def ricevi_cognome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cognome"] = update.message.text.strip()
    await update.message.reply_text("📅 Enter the birth year (e.g. 1990) or *X* if unknown:", parse_mode="Markdown")
    return ANNO

async def ricevi_anno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anno_input = update.message.text.strip()

    if anno_input.lower() == "x":
        context.user_data["anno"] = ""
        context.user_data["categorie"] = []
        await mostra_categorie(update, context)
        return CATEGORIE

    if not anno_input.isdigit() or len(anno_input) != 4:
        await update.message.reply_text("❗ Please enter a valid year (e.g. 1990) or 'X' if unknown.")
        return ANNO

    anno = int(anno_input)
    anno_corrente = datetime.now().year

    if anno > anno_corrente:
        await update.message.reply_text(f"🚫 The year {anno} is in the future! Please enter a valid year or 'X'.")
        return ANNO

    if anno < 1900:
        await update.message.reply_text("📜 The year is too far in the past. Please enter a year from 1900 onward.")
        return ANNO

    context.user_data["anno"] = str(anno)
    context.user_data["categorie"] = []
    await mostra_categorie(update, context)
    return CATEGORIE

async def mostra_categorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categorie = context.user_data.get("categorie", [])

    buttons = [
        [InlineKeyboardButton(
            f"{'✅' if cat in categorie else '❌'} {cat}",
            callback_data=cat
        )]
        for cat in categorie_json
    ]
    buttons.append([InlineKeyboardButton("▶️ Start Search", callback_data="inizia")])
    reply_markup = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.message.edit_text(
            "🎯 Select the categories to explore.\nClick to toggle each one. \nWhen you're ready, press ▶️ *Start Search.*",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🎯 Select the categories to explore.\nClick to toggle each one. \nWhen you're ready, press ▶️ *Start Search.*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def seleziona_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data

    categorie = context.user_data.setdefault("categorie", [])

    if cat == "inizia":
        if not categorie:
            await query.message.edit_text("⚠️ Please select at least one category before starting.")
            return CATEGORIE
        await query.message.edit_text("🔍 Starting the search... Get ready to explore the web!")
        await avvia_ricerca(query, context)
        return ConversationHandler.END

    if cat in categorie: 
        categorie.remove(cat)
    else:
        categorie.append(cat)

    await mostra_categorie(update, context)
    return CATEGORIE

def genera_nickname(nome, cognome, anno=None):
    base = nome.lower()
    cog = cognome.lower()
    nicknames = [
        f"{base}{cog}", f"{base}.{cog}", f"{base}_{cog}",
        f"{base}.{cog}_", f"_{base}{cog}_", f"{cog}{base}",
        f"{base}._.{cog}", f"{cog}._.{base}", f"{base}_{cog}_",
        f"{base}{cog}0", f"_{base}_{cog}"
    ]
    if anno and len(anno) >= 2:
        anno_fin = anno[-2:]
        nicknames.append(f"{base}.{cog}.{anno_fin}")
        nicknames.append(f"{base}_{cog}.{anno_fin}")
    return nicknames

async def aggiorna_messaggio(messaggio, frasi, stop_event):
    i = 0
    while not stop_event.is_set():
        frase = frasi[i % len(frasi)]
        try:
            await messaggio.edit_text(frase)
        except Exception as e:
            print(f"Errore aggiornamento messaggio: {e}")
            break
        await asyncio.sleep(5)  # Aspetta 5 secondi tra gli aggiornamenti
        i += 1
  # se il messaggio viene cancellato o modificato altrove

def ricerca_sincrona(nicknames, categorie):
    risultati = {}
    for username in nicknames:
        for cat in categorie:
            for piattaforma, url_template in categorie_json[cat].items():
                url = url_template.replace("{username}", username)
                try:
                    response = requests.get(url, timeout=5)
                    html = response.text
                    soup = BeautifulSoup(html, "html.parser")
                    testo = soup.get_text()
                    if response.status_code == 200 and len(html) > 500:
                        if any(x in testo for x in ["Spiace", "non è disponibile", "corrotto", "rimossa"]):
                            continue
                        risultati.setdefault(username, []).append(f"{piattaforma}: {url}")
                except:
                    continue
    return risultati

async def avvia_ricerca(query, context):
    nome = context.user_data["nome"]
    cognome = context.user_data["cognome"]
    anno = context.user_data["anno"]
    categorie = context.user_data["categorie"]
    email = context.user_data.get("email") or carica_email_persistente(query.from_user.id)
    nicknames = genera_nickname(nome, cognome, anno)

    messaggi_attesa = [
        "🕵️ Digging through the web...",
        "🔎 Analyzing digital profiles...",
        "📡 Searching for online traces...",
        "💬 Querying servers...",
        "🧠 Cross-referencing data...",
        "🧾 Compiling the report..."
    ]

    messaggio_attesa = await query.message.reply_text(messaggi_attesa[0])
    stop_event = threading.Event()

    # 🔄 Avvia aggiornamento messaggio in parallelo
    asyncio.create_task(aggiorna_messaggio(messaggio_attesa, messaggi_attesa[1:], stop_event))

    risultati = {}

    def ricerca_thread():
        nonlocal risultati
        risultati = ricerca_sincrona(nicknames, categorie)
        stop_event.set()  # ferma l’aggiornamento del messaggio

    thread = threading.Thread(target=ricerca_thread)
    thread.start()

    # ⏳ Aspetta che il thread finisca
    while thread.is_alive():
        await asyncio.sleep(1)

    # 🗑️ Elimina il messaggio di attesa
    try:
        await messaggio_attesa.delete()
    except:
        pass

    # 🧾 Genera PDF
    pdf_buffer = genera_pdf(nome, cognome, categorie, risultati)
    pdf_buffer.seek(0)

    # 📎 Invia il PDF
    await query.message.reply_document(document=InputFile(pdf_buffer, filename=f"report_{nome}_{cognome}.pdf"))

    # 📬 Invio via email se presente
    if email:
        try:
            invia_email(email, pdf_buffer, f"report_{nome}_{cognome}.pdf")
            await query.message.reply_text(f"📬 Report sent to {email}")
        except Exception as e:
            await query.message.reply_text(f"⚠️ Error sending email: {e}")

    # ✅ Messaggio finale
    await query.message.reply_text(
        "✅ Done! Your report is ready.\n"
        "Thanks for using *NetSeeker*. If you want to do another search, type /start.",
        parse_mode="Markdown"
    )
async def salva_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if "@" in email and "." in email:
        context.user_data["email"] = email
        salva_email_persistente(update.effective_user.id, email)
        await update.message.reply_text(f"✅ Email saved: {email}\nFuture reports will be sent there.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Invalid email. Please try again.")
        return EMAIL

def salva_email_persistente(user_id, email):
    data = {}

    if os.path.exists(EMAIL_FILE):
        try:
            with open(EMAIL_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        except json.JSONDecodeError:
            print("⚠️ File JSON corrotto. Verrà sovrascritto.")
            data = {}

    data[str(user_id)] = email

    with open(EMAIL_FILE, "w") as f:
        json.dump(data, f, indent=4)

def carica_email_persistente(user_id):
    if os.path.exists(EMAIL_FILE):
        with open(EMAIL_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(user_id))
    return None

async def set_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📧 Please send me your email to receive future reports:")
    return EMAIL

def invia_email(email_destinatario, pdf_buffer, nome_file):
    pdf_buffer.seek(0)  # 🔁 Assicurati che il buffer sia all'inizio

    msg = EmailMessage()
    msg["Subject"] = "Report NetSeeker"
    msg["From"] = "email-bot"
    msg["To"] = email_destinatario
    msg.set_content("Here is your report generated by NetSeeker.")

    msg.add_attachment(pdf_buffer.read(), maintype="application", subtype="pdf", filename=nome_file)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("email-bot", "application-password")
        smtp.send_message(msg)

async def delemail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 🔧 Rimuovi da context.user_data
    if "email" in context.user_data:
        del context.user_data["email"]

    # 🔧 Rimuovi anche da salvataggio persistente (se usi un file o DB)
    rimuovi_email_persistente(user_id)

    await update.message.reply_text("🗑️ Your email has been deleted from your account.")

import json
import os

def rimuovi_email_persistente(user_id):
    path = "email_utenti.json"
    if not os.path.exists(path):
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {}

    if str(user_id) in data:
        del data[str(user_id)]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

async def delemail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 🔧 Rimuovi da memoria temporanea
    context.user_data.pop("email", None)

    # 🔧 Rimuovi da file persistente
    rimuovi_email_persistente(user_id)

    await update.message.reply_text("🗑️ Your email has been deleted from your account.")

def genera_pdf(nome, cognome, categorie, risultati):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"🧾 Report for: {nome} {cognome}")
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"📅 Selected categories: {', '.join(categorie)}")
    y -= 40

    for nickname, links in risultati.items():
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"🔎 {nickname}")
        y -= 20
        c.setFont("Helvetica", 11)
        if links:
            for link in links:
                c.drawString(60, y, f"• {link}")
                y -= 15
                if y < 50:
                    c.showPage()
                    y = height - 50
        else:
            c.drawString(60, y, "❌ No results found.")
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50

    c.save()
    buffer.seek(0)
    return buffer

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_nome)],
        COGNOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_cognome)],
        ANNO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_anno)],
        CATEGORIE: [CallbackQueryHandler(seleziona_categoria)],
    },
    fallbacks=[],
    per_message=False,
)

email_handler = ConversationHandler(
    entry_points=[CommandHandler("setemail", set_email)],
    states={EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, salva_email)]},
    fallbacks=[],
    per_message=False,
)

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("delemail", delemail))
application.add_handler(email_handler)
application.add_handler(conv_handler)
application.run_polling()
print("Bot is running...")
