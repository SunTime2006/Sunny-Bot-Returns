
import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv
import os
import wikipedia
from datetime import datetime

load_dotenv()


def obtener_partidos_futbol(fecha):
    try:

        datetime.strptime(fecha, '%Y-%m-%d')
        RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
        RAPIDAPI_HOST = os.getenv('RAPIDAPI_HOST')
        URL = 'https://bet36528.p.rapidapi.com/matches_bet365'
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }
        querystring = {
            "sport": "soccer",
            "country": "spain",
            "competition": "premier-league",
            "match_urls": "false"
        }

        response = requests.get(URL, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        partidos = []

        for key in data:
            partido = data[key]
            if partido['date'] == fecha:
                local = partido['home_team']
                visitante = partido['away_team']
                hora = partido['time']
                resultado = f"{local} vs {visitante} a las {hora}"
                partidos.append(resultado)
        return partidos if partidos else ["No se encontraron partidos para el día especificado."]
    except ValueError:
         return["Formato de fecha incorrecto: Usa el formato YYYY-MM-DD"]
    except requests.exceptions.RequestException as e:
        return[f"Error al realizar la solicitud: {e}"]

def buscar_wikipedia(consulta):
    try:
        wikipedia.set_lang("es")
        resultado = wikipedia.summary(consulta, sentences=4)
        return resultado
    except wikipedia.exceptions.DisambiguationError as e:
        return f"La búsqueda '{consulta} es ambigua. Por favor sé más específico."
    except wikipedia.exceptions.PageError as e:
        return f"No se encontró ningún artículo relacionado con '{consulta}' en Wikipedia."

token = os.getenv('token')

intents = discord.Intents.all()
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


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
            await ctx.send(f'El precio de {coin} es ${price} usd')
        else:
            await ctx.send('No se encontró la criptomoneda específica')
    except Exception as e:
        await ctx.send('Hubo un error al consultar el precio de la criptomoneda')
        print(e)

@bot.command()
async def wiki(ctx, *, consulta):
    try:
        resultado = buscar_wikipedia(consulta)
        await ctx.send(resultado)
    except Exception as e:
        await ctx.send(f"Error al realizar la búsqueda en Wikipedia: {e}")

@bot.command()
async def partidos(ctx, fecha):
    try:
        partidos = obtener_partidos_futbol(fecha)
        for partido in partidos:
            await ctx.send(partido)
    except Exception as e:
        await ctx.send(f"Error al obtener los partidos: {e}")
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    contenido = message.content.lower()

    # Lista de saludos que quieres reconocer
    saludos = ["hola", "gola", "ola", "hi", "oa"]
    if any(saludo in contenido for saludo in saludos):
        await message.channel.send(f'¡Hola {message.author.name}!')

    # Lista de preguntas tipo "¿cómo estás?"
    estados = ["¿como estás?", "como tas?", "como andas", "que tal"]
    if any(estado in contenido for estado in estados):
        await message.channel.send("Bien, ¿y tú?")
    
    # Procesar comandos después de tus respuestas personalizadas
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está en línea ✅')
    # Estado personalizado
    await bot.change_presence(
        activity=discord.Game(name="con SunTime 😎")  # Jugando
    )

bot.run(token)


