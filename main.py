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
            requests.post(
                url,
                data={"chat_id": CHAT_ID, "caption": legenda or ""},
                files={"photo": f},
                timeout=30
            )
        except Exception as e:
            print(f"⚠️ Erro ao enviar imagem Telegram: {e}")

# === CONFIGURAÇÕES ===
URL = "https://statsxente.com/MZ1/Functions/lecturaEquipos2.0.php?noheader=true&idioma=ENGLISH&divisa=EUR&eloButtonType=2&eloButtonCat=SENIOR&idJugador=&idEquipo=&idLiga=&pais=Portugal&division=&fechMin=2019-10-10&fechMax=2100-10-10&edadMin=15&edadMax=45&salarioMin=0&salarioMax=1000000&valorMin=0&valorMax=30000000000000&valor23Min=0&valor23Max=30000000000000&valor21Min=0&valor21Max=30000000000000&valor18Min=0&valor18Max=30000000000000&valorNoNacMin=0&valorNoNacMax=30000000000000&equipo=&limite=1000&ordenar=elo_combined"

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
    IMG_NAME = "top_PT.png"

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] A capturar imagem...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1920, "height": 10800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        await page.goto(URL, wait_until="networkidle")
        await asyncio.sleep(3)

        # Scroll progressivo
        await page.evaluate("""
            (async () => {
                const delay = ms => new Promise(res => setTimeout(res, ms));
                let totalHeight = 0;
                const distance = 500;
                while (totalHeight < document.body.scrollHeight) {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    await delay(200);
                }
            })();
        """)

        # Esperar que todos os emblemas tenham carregado
        await page.evaluate("""
            (async () => {
                const imgs = Array.from(document.querySelectorAll('img[src*="badge.php?team_id="]'));
                await Promise.all(imgs.map(img => {
                    if (img.complete && img.naturalHeight !== 0) return Promise.resolve();
                    return new Promise(resolve => { img.onload = resolve; img.onerror = resolve; });
                }));
            })();
        """)

        # Ajustar visualização
        await page.evaluate("document.body.style.overflow='hidden'; document.body.style.zoom='100%';")

        # Aumentar emblemas
        await page.evaluate(f"""
            document.querySelectorAll('img[src*="badge.php?team_id="]').forEach(img => {{
                let rect = img.getBoundingClientRect();
                img.style.setProperty('width', (rect.width * {IMAGEM_MULTIPLICADOR}) + 'px', 'important');
                img.style.setProperty('height', (rect.height * {IMAGEM_MULTIPLICADOR}) + 'px', 'important');
            }});
        """)

        # Esconder última coluna e ajustar larguras
        await page.evaluate("""
            const table = document.querySelector('table');
            if(table){
                table.style.tableLayout = 'fixed';
                table.style.width = '1200px';
                const rows = table.querySelectorAll('tr');
                rows.forEach(row => {
                    const visibleCells = Array.from(row.querySelectorAll('th, td'))
                                              .filter(cell => window.getComputedStyle(cell).display !== 'none');
                    if(visibleCells.length > 0){
                        const lastVisible = visibleCells[visibleCells.length - 1];
                        lastVisible.style.display = 'none';
                        if(visibleCells[0]) { visibleCells[0].style.width = '10px'; visibleCells[0].style.minWidth = '10px'; }
                        if(visibleCells[1]) { visibleCells[1].style.width = '200px'; visibleCells[1].style.minWidth = '200px'; }
                        if(visibleCells[2]) { visibleCells[2].style.width = '100px'; visibleCells[2].style.minWidth = '100px'; }
                        if(visibleCells[3]) { visibleCells[3].style.width = '50px'; visibleCells[3].style.minWidth = '50px'; }
                        if(visibleCells[4]) { visibleCells[4].style.width = '50px'; visibleCells[4].style.minWidth = '50px'; }
                        if(visibleCells[5]) { visibleCells[5].style.width = '50px'; visibleCells[5].style.minWidth = '50px'; }
                        if(visibleCells[6]) { visibleCells[6].style.width = '50px'; visibleCells[6].style.minWidth = '50px'; }
                        if(visibleCells[7]) { visibleCells[7].style.width = '75px'; visibleCells[7].style.minWidth = '75px'; }
                        if(visibleCells[8]) { visibleCells[8].style.width = '50px'; visibleCells[8].style.minWidth = '50px'; }
                    }
                });
            }
        """)

        # Adicionar € na 8ª coluna
        await page.evaluate("""
            const table = document.querySelector('table');
            if (table) {
                const rows = table.querySelectorAll('tr');
                rows.forEach((row, index) => {
                    if (index === 0) return;
                    const visibleCells = Array.from(row.querySelectorAll('td'))
                                              .filter(cell => window.getComputedStyle(cell).display !== 'none');
                    if (visibleCells.length >= 8) {
                        const cell = visibleCells[7];
                        if (!cell.innerText.includes('€')) {
                            cell.innerText = cell.innerText.trim() + ' €';
                        }
                    }
                });
            }
        """)

        # Centralizar headers
        await page.evaluate("""
            (function(){
                const table = document.querySelector('table');
                if(!table) return;
                table.querySelectorAll('th').forEach(th => { th.style.textAlign = 'center'; });
                Array.from(table.querySelectorAll('tr')).forEach(tr => {
                    const first = tr.children && tr.children[0];
                    if(!first || !first.innerText) return;
                    const t0 = first.innerText.trim().toLowerCase();
                    if(t0.startsWith('pos') || t0 === 'pos' || t0.includes('pos,')){
                        Array.from(tr.children).forEach(cell => { cell.style.textAlign = 'center'; });
                    }
                });
                const headerNames = ['pos','team','division','elo score','u23 elo score','u21 elo score','u18 elo score','transfer cost','average elo'];
                Array.from(table.querySelectorAll('tr')).forEach(tr => {
                    const texts = Array.from(tr.children).map(c=> (c.innerText||'').trim().toLowerCase()).join(' ');
                    let count = 0;
                    for(const h of headerNames){ if(texts.includes(h)) count++; }
                    if(count >= 3){ Array.from(tr.children).forEach(cell => { cell.style.textAlign = 'center'; }); }
                });
            })();
        """)

        # Ajustar topo (.caja_mensaje_75)
        await page.evaluate("""
            const table = document.querySelector('table');
            const topBox = document.querySelector('.caja_mensaje_75');
            if(table && topBox){
                topBox.style.width = table.offsetWidth + 'px';
                topBox.style.boxSizing = 'border-box';
            }
        """)

        # Atualizar texto da caixa
        await page.evaluate("""
            var elem = document.querySelector('.caja_mensaje_75');
            if(elem){
                var original_text = elem.innerText;
                var num = original_text.match(/\\([0-9]+)\\/);
                if(num){
                    elem.innerText = "Top Teams in Portugal (All Categories) [" + num[1] + " Teams]";
                }
            }
        """)

        # Adicionar "Last Update"
        await page.evaluate(f"""
            var headerDiv = document.getElementById('customHeaderDiv');
            if(headerDiv) headerDiv.remove();
            const header = document.createElement('div');
            header.id = 'customHeaderDiv';
            header.innerText = "Last Update: {data_hoje} {hora_hoje}";
            header.style.color = 'red';
            header.style.fontSize = '16px';
            header.style.fontWeight = 'bold';
            header.style.position = 'absolute';
            header.style.top = '10px';
            header.style.left = '370px';
            header.style.background = 'transparent';
            header.style.zIndex = '9999';
            header.style.pointerEvents = 'none';
            const titulo = document.querySelector('.caja_mensaje_75');
            if(titulo) titulo.insertAdjacentElement('afterend', header);
        """)

        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)

        # Tirar screenshot
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
    # Agendamento diário
    schedule.every().day.at("10:00").do(tarefa_diaria)
    enviar_telegram_mensagem("🚀 Script iniciado no Render e pronto para tirar screenshots diárias.")
    print("⏳ Script iniciado. Vai tirar um screenshot por dia.")

    # Iniciar Flask em paralelo
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()

    while True:
        schedule.run_pending()
        time.sleep(60)