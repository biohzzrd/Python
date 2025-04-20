import telebot
import os
import socket
import uuid
import subprocess
import platform
from telebot import types
import struct

whitelist = {7310789701, 6092758478}

devicename = socket.gethostname()
ipv4 = socket.gethostbyname(devicename)
mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
    for elements in range(0, 8*6, 8)][::-1])


bot = telebot.TeleBot('7329710494:AAGPZpU5vWxC-ipCmfNfxJX_q82Hih-omBw')

def send_magic_packet(mac):
    mac_bytes = bytes.fromhex(mac.replace(':', '').replace('-', ''))
    packet = b'\xff' * 6 + mac_bytes * 16
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(packet, ('<broadcast>', 9))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"SPECIFIED MAC: {mac_address}; HOST NAME: {devicename}; IPv4: {ipv4}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Shutdown", "Execute", "Spotify")
    markup.row("Wakeup", "Contents", "Read")
    bot.send_message(message.chat.id, f"Choose a command to be executed on {devicename}", reply_markup=markup)

@bot.message_handler(commands=["cmds"])
def send_cmds(message):
    with open('commands.txt', 'r') as cmdslist:
        ls = cmdslist.read()
    bot.reply_to(message, ls)

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    print(f"{message.from_user.username} ({message.from_user.id}): {message.text}")
    text = message.text.lower()

    if text == "execute":
        if message.from_user.id in whitelist:
            msg = bot.send_message(message.chat.id, "Send me the command to execute.")
            bot.register_next_step_handler(msg, lambda m: execute_command(m))

    elif text == "shutdown":
        if message.from_user.id in whitelist:
            os.system("shutdown /s /t 0")
            bot.reply_to(message, "Shutting down now.")

    elif text == "spotify":
        if message.from_user.id in whitelist:
            try:
                subprocess.Popen(["spotify"]) if platform.system() == "Linux" else os.startfile("spotify")
                bot.reply_to(message, "Spotify launched.")
            except Exception as e:
                bot.reply_to(message, f"Failed to open Spotify: {e}")

    elif text == "wakeup":
        if message.from_user.id in whitelist:
            target_mac = "A8:A1:59:D7:D8:C1"
            try:
                send_magic_packet(target_mac)
                bot.reply_to(message, f"Wake-on-LAN packet sent to {target_mac}")
            except Exception as e:
                bot.reply_to(message, f"Failed to send WOL packet: {e}")

    elif text == "contents":
        if message.from_user.id in whitelist:
            msg = bot.send_message(message.chat.id, "Enter folder path to list contents:")
            bot.register_next_step_handler(msg, list_contents)

    elif text == "read":
        if message.from_user.id in whitelist:
            msg = bot.send_message(message.chat.id, "Send me the full file path to read:")
            bot.register_next_step_handler(msg, send_file)

def execute_command(message):
    try:
        os.system(message.text)
        output = subprocess.getoutput(message.text)
        bot.send_message(message.chat.id, f"Command output:\n{output[:4000]}") 
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

def list_contents(message):
    path = message.text.strip()
    if os.path.isdir(path):
        files = os.listdir(path)
        content = "\n".join(files)
        bot.send_message(message.chat.id, f"Contents of {path}:\n{content[:4000]}")
    else:
        bot.send_message(message.chat.id, f"{path} is not a valid folder.")

def send_file(message):
    filepath = message.text.strip()
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.send_message(message.chat.id, f"File not found: {filepath}")

bot.infinity_polling()