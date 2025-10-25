import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv
import os
import wikipedia
from datetime import datetime

# --- Cargar variables desde .env ---
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

# --- Configuración de intents ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Función para obtener partidos de Premier League ---
def obtener_partidos_futbol():
    url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    if not FOOTBALL_API_KEY:
        return ["No tienes configurada la API KEY de Football-Data. Revisa tu archivo .env"]

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            return ["Acceso prohibido (403). Verifica tu API KEY o suscripción en football-data.org."]
        
        response.raise_for_status()
        data = response.json()

        partidos = []
        for match in data["matches"][:5]:
            local = match["homeTeam"]["name"]
            visitante = match["awayTeam"]["name"]
            fecha = match["utcDate"]
            partidos.append(f"{local} vs {visitante} el {fecha}")

        return partidos if partidos else ["No hay partidos próximos."]
    except requests.exceptions.RequestException as e:
        return [f"Error al obtener los partidos: {e}"]


# --- Función para buscar en Wikipedia ---
def buscar_wikipedia(consulta):
    try:
        wikipedia.set_lang("es")
        resultado = wikipedia.summary(consulta, sentences=4)
        return resultado
    except wikipedia.exceptions.DisambiguationError:
        return f"La búsqueda '{consulta}' es ambigua. Por favor sé más específico."
    except wikipedia.exceptions.PageError:
        return f"No se encontró ningún artículo relacionado con '{consulta}' en Wikipedia."

# --- Eventos ---
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Respondiendo a tus comandos ⚡"))
    print(f"✅ Bot conectado como {bot.user}")

# --- Comandos ---
@bot.command()
async def info(ctx):
    await ctx.send('¡Soy un bot creado por mi dueño SunTime!')

@bot.command()
async def crypto(ctx, coin: str):
    try:
        response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd')
        data = response.json()
        if coin in data:
            price = data[coin]['usd']
            await ctx.send(f'El precio de {coin} es ${price} USD')
        else:
            await ctx.send('No se encontró la criptomoneda especificada.')
    except Exception as e:
        await ctx.send('Hubo un error al consultar el precio de la criptomoneda')
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

# --- Respuestas automáticas ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    saludos = ["hola", "gola", "ola", "hi", "oa"]
    preguntas = ["¿como estás?", "como tas?", "como andas", "que tal"]
    respuestas = ["ando bien", "chill", "fino", "piola"]

    content = message.content.lower()

    if any(saludo in content for saludo in saludos):
        await message.channel.send(f'¡Hola {message.author.name}!')

    if any(pregunta in content for pregunta in preguntas):
        await message.channel.send("Bien, ¿y tú?")

    if any(respuesta in content for respuesta in respuestas):
        await message.channel.send(f'Me alegra saberlo')

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está en línea ✅')
    # Estado personalizado
    await bot.change_presence(
        activity=discord.Game(name="con SunTime 😎")  # Jugando
    )

# --- Ejecutar bot ---
bot.run(DISCORD_TOKEN)

