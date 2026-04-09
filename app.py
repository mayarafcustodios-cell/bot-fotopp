import os
os.system("playwright install")
from flask import Flask, render_template
from threading import Thread
import time
from playwright.sync_api import sync_playwright
from twilio.rest import Client
import os

app = Flask(__name__)

rodando = False
status = "Parado"

EVENTOS = [
    {"id": "238042", "nome": "Maratona SP"},
    {"id": "245033", "nome": "Corrida Esperança"}
]

EMAIL = os.getenv("EMAIL")
SENHA = os.getenv("SENHA")

ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
FROM_NUMBER = os.getenv("FROM_NUMBER")
TO_NUMBER = os.getenv("TO_NUMBER")

def enviar_sms(msg):
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    client.messages.create(body=msg, from_=FROM_NUMBER, to=TO_NUMBER)

def bot():
    global rodando, status

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://dashboard.fotop.com/login")
        page.fill('input[type="email"]', EMAIL)
        page.fill('input[type="password"]', SENHA)
        page.click('button[type="submit"]')
        page.wait_for_timeout(5000)

        while rodando:
            status = "Monitorando..."

            page.goto("https://dashboard.fotop.com/eventos/proximos/?categoria=1")
            page.wait_for_timeout(3000)

            for evento in EVENTOS:
                ev = page.locator(f"text={evento['id']}")

                if ev.count() > 0:
                    card = ev.first.locator("xpath=ancestor::div")
                    botao = card.locator("text=Participar")

                    if botao.count() > 0:
                        status = f"Entrando em {evento['nome']}"

                        try:
                            botao.click()
                            page.wait_for_timeout(2000)

                            enviar_sms(f"Entrou: {evento['nome']}")
                            status = "INSCRITO!"
                            rodando = False
                            return
                        except:
                            status = "Erro ao tentar"
                            rodando = False
                            return

            time.sleep(10)

@app.route("/")
def index():
    return f"""
    <h1>Bot Fotop</h1>
    <h2>Status: {status}</h2>
    <a href='/start'><button>Iniciar</button></a>
    <a href='/stop'><button>Parar</button></a>
    """

@app.route("/start")
def start():
    global rodando
    if not rodando:
        rodando = True
        Thread(target=bot).start()
    return "Iniciado"

@app.route("/stop")
def stop():
    global rodando
    rodando = False
    return "Parado"

app.run(host="0.0.0.0", port=3000)
