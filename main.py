import asyncio
import time
import schedule
from datetime import datetime
from playwright.async_api import async_playwright
import requests
import os
from flask import Flask
import threading

# === TELEGRAM CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def enviar_telegram_mensagem(texto: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Erro ao enviar mensagem Telegram: {e}")

def enviar_telegram_imagem(imagem_path: str, legenda: str = None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(imagem_path, "rb") as f:
        try:
            requests.post(url, data={"chat_id": CHAT_ID, "caption": legenda or ""}, files={"photo": f}, timeout=30)
        except Exception as e:
            print(f"⚠️ Erro ao enviar imagem Telegram: {e}")

# === CONFIGURAÇÕES ===
URL = "https://statsxente.com/MZ1/Functions/lecturaEquipos2.0.php?noheader=true&idioma=ENGLISH&divisa=EUR&eloButtonType=2&eloButtonCat=SENIOR&idJugador=&idEquipo=&idLiga=&pais=Portugal&division=&fechMin=2019-10-10&fechMax=2100-10-10&edadMin=15&edadMax=45&salarioMin=0&salarioMax=1000000&valorMin=0&valorMax=30000000000000&valor23Min=0&valor23Max=30000000000000&valor21Min=0&valor21Max=30000000000000&valor18Min=0&valor18Max=30000000000000&valorNoNacMin=0&valorNoNacMax=30000000000000&equipo=&limite=1000&ordenar=elo_combined&numJugadores=0&valor11=0&valor=0&valor23=0&valor21=0&valor18=0&salario=0&edad=0&valor11_23=0&valor11_21=0&valor11_18=0&noNac=0&edadTop11=0&edadSenior=0&valorUPSenior=0&valorUPSUB23=0&valorUPSUB21=0&valorUPSUB18=0&elo=1&usuario=&elo21=1&elo23=1&elo18=1&elo_combined=1&liga_world=0&liga_world23=0&liga_world21=0&liga_world18=0&liga_juv23=0&liga_juv21=0&liga_juv18=0&transfer_value=1&transfer_valueMax=0"

IMAGEM_MULTIPLICADOR = 2

COORDENADAS = {
    "x": 360,
    "y": 10,
    "width": 1200,
    "height": 2120
}

async def tirar_screenshot():
    data_hoje = datetime.now().strftime("%d/%m/%y")
    hora_hoje = datetime.now().strftime("%H:%M")
    IMG_NAME = f"top_PT.png"

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] A capturar imagem...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1920, "height": 10800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        await page.goto(URL, wait_until="networkidle")

        # scroll e ajustes...
        await page.evaluate("""
            window.scrollTo(0, document.body.scrollHeight);
        """)

        await asyncio.sleep(2)

        await page.screenshot(path=IMG_NAME, clip=COORDENADAS)
        await browser.close()

        print(f"✅ Screenshot guardada como {IMG_NAME}")
        enviar_telegram_mensagem(f"✅ Screenshot capturada com sucesso às {hora_hoje} ({data_hoje})")
        enviar_telegram_imagem(IMG_NAME, legenda="📸 top_PT.png")

def tarefa_diaria():
    asyncio.run(tirar_screenshot())

# ===============================================================
# SERVIDOR FLASK PARA O RENDER + CRON-JOB.ORG
# ===============================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Screenshot bot is running on Render!"

@app.route("/run")
def run_screenshot():
    threading.Thread(target=tarefa_diaria).start()
    return "🚀 Screenshot task started!"

if __name__ == "__main__":
    # Se quiseres também manter o agendamento interno, ativa esta parte:
    schedule.every().day.at("10:00").do(tarefa_diaria)
    enviar_telegram_mensagem("🚀 Script iniciado no Render e pronto para tirar screenshots diárias.")
    print("⏳ Script iniciado. Vai tirar um screenshot por dia.")

    # Inicia o Flask em paralelo com o loop do schedule
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()

    while True:
        schedule.run_pending()
        time.sleep(60)