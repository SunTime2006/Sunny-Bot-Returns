import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv
import os
import wikipedia
import random
from datetime import datetime
import time
import re

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='?', intents=intents)

_recent_responses = {}
DUPLICATE_WINDOW = 5.0

def _normalize_text(s: str) -> str:
    """Quita espacios extras, normaliza a minúsculas y reemplaza saltos de línea por espacios."""
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r'\s+', ' ', s)
    return s

def _prune_recent():
    """Elimina entradas antiguas del diccionario para que no crezca indefinidamente."""
    now = time.time()
    stale_keys = [k for k, t in _recent_responses.items() if now - t > DUPLICATE_WINDOW * 2]
    for k in stale_keys:
        _recent_responses.pop(k, None)

def obtener_partidos_futbol():
    url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    if not FOOTBALL_API_KEY:
        return ["No tienes configurada la API KEY de Football-Data. Revisa tu archivo .env"]

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 403:
            return ["Acceso prohibido (403). Verifica tu API KEY o suscripción en football-data.org."]

        response.raise_for_status()
        data = response.json()

        partidos = []
        for match in data.get("matches", [])[:5]:
            local = match["homeTeam"]["name"]
            visitante = match["awayTeam"]["name"]
            fecha = match["utcDate"]
            partidos.append(f"{local} vs {visitante} el {fecha}")

        return partidos if partidos else ["No hay partidos próximos."]
    except requests.exceptions.RequestException as e:
        return [f"Error al obtener los partidos: {e}"]

def buscar_wikipedia(consulta):
    try:
        wikipedia.set_lang("es")
        resultado = wikipedia.summary(consulta, sentences=4)
        return resultado
    except wikipedia.exceptions.DisambiguationError:
        return f"La búsqueda '{consulta}' es ambigua. Por favor sé más específico."
    except wikipedia.exceptions.PageError:
        return f"No se encontró ningún artículo relacionado con '{consulta}' en Wikipedia."
    except Exception as e:
        return f"Ocurrió un error al buscar en Wikipedia: {e}"


@bot.event
async def on_ready():
    print(f'Bot {bot.user} está en línea')
    await bot.change_presence(activity=discord.Game(name="Jugando con SunTime 😎"))


@bot.event
async def on_message(message):
    if message.author == bot.user or message.webhook_id is not None:
        return

    content_raw = message.content or ""
    if not content_raw.strip():
        await bot.process_commands(message)
        return

    content = _normalize_text(content_raw)

    _prune_recent()

    key = (message.channel.id, message.author.id, content)
    now = time.time()

    if key in _recent_responses and (now - _recent_responses[key]) <= DUPLICATE_WINDOW:
        await bot.process_commands(message)
        return

    saludos = {"hola", "gola", "ola", "hi", "oa"}
    preguntas = {"¿como estás?", "como tas?", "como andas", "que tal", "como estas"}
    respuestas = {"ando bien", "chill", "fino", "piola"}
    elogios = {"que educado"}

    sent = False

    words = set(re.findall(r"\b\w+\b", content))

    if words & saludos:
        await message.channel.send(f'¡Hola {message.author.name}!')
        sent = True

    elif any(preg in content for preg in preguntas):
        await message.channel.send("Bien, ¿y tú?")
        sent = True

    elif any(resp in content for resp in respuestas):
        await message.channel.send("¡Me alegra saberlo!")
        sent = True

    elif any(el in content for el in elogios):
        await message.channel.send("¡Siempre lo soy!")
        sent = True

    if sent:
        _recent_responses[key] = now

    await bot.process_commands(message)


@bot.command()
async def info(ctx):
    await ctx.send('¡Soy un bot creado por mi dueño SunTime!')

@bot.command()
async def list(ctx):
    await ctx.send('Lista de comandos: '
    '?info: Información del bot'
    '?crypto [tipo de moneda]: Tipo de cambio'
    '?wiki [nombre de la búsqueda]: Buscar un tema en la Wikipedia'
    '?partidos [fecha AÑO-MES-DIA]: Buscar una fecha de un partido'
    '?receta [nombre del plato]: Buscar una receta de un plato'
    '?recetaaleatoria: Muestre una receta al azar'
    '?dados: Juego de dados'
    '?coin: Juego de cara o cruz'
    '?pregunta [pregunta]: Juego de preguntas'
    '?adivina: Adivinanza de un número')

@bot.command()
async def crypto(ctx, coin: str):
    try:
        coin = coin.lower()
        response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd', timeout=10)
        data = response.json()

        if coin in data:
            price = data[coin]['usd']
            await ctx.send(f'El precio de **{coin.upper()}** es **${price} USD**')
            return

        response_fx = requests.get(f'https://api.exchangerate.host/latest?base={coin.upper()}&symbols=USD', timeout=10)
        data_fx = response_fx.json()

        if 'rates' in data_fx and 'USD' in data_fx['rates']:
            rate = data_fx['rates']['USD']
            await ctx.send(f'1 {coin.upper()} = {rate:.4f} USD')
        else:
            await ctx.send('No se encontró la moneda o criptomoneda especificada.')
    except Exception as e:
        await ctx.send('Hubo un error al consultar el valor.')
        print(e)

@bot.command()
async def wiki(ctx, *, consulta):
    resultado = buscar_wikipedia(consulta)
    await ctx.send(resultado)

@bot.command()
async def partidos(ctx):
    partidos = obtener_partidos_futbol()
    for partido in partidos:
        await ctx.send(partido)

@bot.command()
async def receta(ctx, *, nombre: str):
    try:
        from bs4 import BeautifulSoup
        url = "https://www.yanuq.com/recetasperuanasp.asp"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        nombre_lower = nombre.lower()
        resultados = []

        for a in soup.find_all("a", href=True):
            texto = a.get_text(strip=True)
            if nombre_lower in texto.lower():
                href = a['href']
                link = href if href.startswith("http") else f"https://www.yanuq.com/{href.lstrip('/')}"
                resultados.append(f" **{texto}** — {link}")

        if resultados:
            await ctx.send("\n".join(resultados[:5]))
        else:
            await ctx.send(f"No encontré recetas que contengan **{nombre}** en Yanuq.com")
    except Exception as e:
        await ctx.send("Ocurrió un error al buscar la receta en Yanuq.")
        print(e)

@bot.command()
async def recetaaleatoria(ctx):
    try:
        url = "https://www.themealdb.com/api/json/v1/1/random.php"
        res = requests.get(url, timeout=10)
        data = res.json()
        meal = data["meals"][0]
        titulo = meal["strMeal"]
        categoria = meal["strCategory"]
        area = meal["strArea"]
        instrucciones = meal["strInstructions"][:400] + "..."
        imagen = meal["strMealThumb"]

        await ctx.send(f"**{titulo}** ({categoria}, {area})\n\n {instrucciones}\n\n {imagen}")
    except Exception as e:
        await ctx.send("Error al obtener una receta aleatoria.")
        print(e)

@bot.command()
async def dados(ctx):
    numero = random.randint(1, 6)
    await ctx.send(f'Has sacado un **{numero}**!')

@bot.command()
async def coin(ctx):
    resultado = random.choice(["Cara", "Cruz"])
    await ctx.send(f' Ha salido **{resultado}**!')

@bot.command()
async def pregunta(ctx, *, texto):
    respuestas = [
        "Sí.", "No.", "Tal vez.", "Claro que sí.", "Definitivamente no.",
        "Pregúntame más tarde.", "No estoy seguro", "Probablemente sí."
    ]
    await ctx.send(f' {random.choice(respuestas)}')

@bot.command()
async def adivina(ctx):
    numero = random.randint(1, 10)
    await ctx.send(" Estoy pensando en un número del 1 al 10. ¡Adivina!")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=10)
        if msg.content.isdigit() and int(msg.content) == numero:
            await ctx.send(" ¡Correcto! Adivinaste el número.")
        else:
            await ctx.send(f" No era ese. El número era **{numero}**.")
    except:
        await ctx.send(f" Tardaste demasiado. El número era **{numero}**.") 

bot.run(DISCORD_TOKEN)
