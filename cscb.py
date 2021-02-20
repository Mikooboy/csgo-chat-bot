import sys
import telnetlib
import psutil
import signal
import binascii
import random
import datetime
import re
import hashlib
import requests
import shlex
import os
import time
import pickle
import math
from threading import Thread
from pydicti import dicti
from texttable import Texttable
from math import *
from random import randrange
from time import sleep
from os import path
import info
import urllib3
import config as cfg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

start_time = time.time()

colors = {
	"green" : "",
	"blue" : "",
	"darkblue" : "",
	"darkred" : "",
	"gold" : "",
	"lightgreen" : "",
	"lightred" : "",
	"lime" : "",
	"orchid" : "",
}

clear = lambda: os.system('cls')
clear()

def steamid_to_64bit(steamid):
    steam64id = 76561197960265728 # I honestly don't know where this came from, but it works...
    id_split = steamid.split(":")
    steam64id += int(id_split[2]) * 2 # again, not sure why multiplying by 2...
    if id_split[1] == "1":
        steam64id += 1
    return steam64id

def signal_handler(signal, frame):
	print("\nquitting...")
	sys.exit(0)

# List PIDs of processes matching processName
def processExists(processName):
	for proc in psutil.process_iter(['name']):
		if proc.info['name'].lower() == processName.lower():
			return True
	return False

# Runs commands on the csgo console
def run(txn, command):
	cmd_s = command + "\n"
	txn.write(cmd_s.encode('utf-8'))
	sleep(0.005)

signal.signal(signal.SIGINT, signal_handler)

def change_clan():
	try:
		tn2 = telnetlib.Telnet(cfg.settings["tn_host"], cfg.settings["tn_port"])
		id_list = cfg.settings["clan_id_list"]
		print("started changing clan")

		stop = -1
		i = 0
		while (stop != 0):
			stop = tn2.expect([b"!abort_clan"], timeout=0.25)
			stop = stop[0]
			run(tn2, "cl_clanid \"" + str(id_list[i]) + "\"")
			if (i == 3):
				i = 0
			else:
				i += 1
	except:
		pass
	print("stopped changing clan")

def get_players_and_map(name, tn):
    status_start = 0
    player_lines = []

    run(tn, "status")
    status = tn.expect([b"#end"], timeout=1)
    lines = status[2].decode("utf-8").splitlines()

    lines.pop(len(lines) - 1)

    j = 0
    for i in lines:
        if "# userid" in i.lower():
            status_start = j
        j = j + 1

    player_lines = lines[status_start + 1:]

    for i in lines:
        if "map" in i.lower():
            matching_map = i
    
    mapName = matching_map.split()
    mapName = mapName[2]

    return [player_lines, mapName]

def parse_name(player_line):
    line_split = shlex.split(player_line)
    name = line_split[3]
    name = name.replace('"', "")
    return name

def main():
	if (len(sys.argv) > 1):
		if (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
			print("Run with no arguments to initiate and connect to csgo")
			print("Make sure you set up csgo to receive connections with this launch option: -netconport " + str(cfg.settings["tn_port"]))
	
	# Make sure cs:go is running before trying to connect
	if not processExists("csgo.exe"):
		print("Waiting for csgo to start... ")
		while not processExists("csgo.exe"):
			sleep(0.25)
		sleep(10)

	# Initialize csgo telnet connection
	print("Trying " + cfg.settings["tn_host"] + ":" + cfg.settings["tn_port"] + "...")
	try:
		tn = telnetlib.Telnet(cfg.settings["tn_host"], cfg.settings["tn_port"])
	except ConnectionRefusedError:
		# Retry in 10 seconds
		sleep(10)
		pass
	try:
		tn = telnetlib.Telnet(cfg.settings["tn_host"], cfg.settings["tn_port"])
	except ConnectionRefusedError:
		print("Connection refused. Make sure you have the following launch option set:")
		print("  -netconport "+str(cfg.settings["tn_port"]))
		sys.exit(1)
	tn.write(b"echo CSCTL Active, use chat or echo in console to execute commands\n")
	tn.read_until(b"commands")
	print("Successfully Connected!")

	sleep(1)
	clear()
	
	print("Listening for commands from console...")

	lastQuote = ""

	info_list = dicti()

	while True:
		# Capture console output until we encounter our exec string
		result = tn.expect([b"!calc\r\n", b"!help\r\n", b"!info\r\n", b"\* !info \r\n", b"!swquote\r\n", b" connected.", b"!bot", b"!clan", b"!clear"])



		# Calculator
		if (result[0] == 0):
			try:
				sleep(0.7)

				splitted = result[2].decode("utf-8").split(": ")
				splitted_again = splitted[len(splitted)-1].split(" !")
				calc = splitted_again[0]
				print(calc)

				answer = "Error"

				try:
					answer = eval(calc, {'sqrt': sqrt, 'pow': pow})
				except:
					pass

				run(tn, "say " + str(calc) + " = " + str(answer))
				print(answer)
			except:
				pass



		# help
		if (result[0] == 1):
			try:
				sleep(0.7)

				run(tn, "say List of commands: !​help, <name> !​info, <math> !​calc, !​swquote")
				print("!help")
			except:
				pass
		


		# Player info
		if (result[0] == 2) or (result[0] == 3):
			try:
				sleep(0.7)

				results = result[2].decode("utf-8").splitlines()
				name = info.get_name(results)

				for i in info_list:
					if name.lower() in i.lower():
						name = i

				if (name != "*all* ") & (name in info_list):
					try:
						run(tn, "say " + name + " | " + str(info_list[name]))
					except:
						print("Couldn't retrieve info")
				elif (name != "*all* ") & (not name in info_list):
					try:
						PlayersAndMap = get_players_and_map(name, tn)
						players = PlayersAndMap[0]
						name_found = False
						for i in players:
							if name.lower() in i.lower():
								name = i
								name_found = True

						if (name_found == False):
							run(tn, "say Error: Invalid name")
						else:
							name = parse_name(name)

							print("fetching player info table")
							run(tn, "say Fetching player info table...")
							info_list = info.getInfo("*all* ", tn)
							sleep(0.7)
							run(tn, "say " + name + " | " + str(info_list[name]))
							print(name + " | " + str(info_list[name]))
					except:
						print("Couldn't retrieve info")
				elif (name == "*all* "):
					try:
						info_list = info.getInfo(name, tn)
					except:
						print("Couldn't retrieve info")
				else:
					run(tn, "say Error: Invalid name")
			except:
				pass
			


		# Star Wars Quote
		if (result[0] == 4):
			try:
				sleep(0.7)

				url = 'http://swquotesapi.digitaljedi.dk/api/SWQuote/RandomStarWarsQuote'

				r = requests.get(url, verify=False).json()

				quote = r['content']

				while (quote == lastQuote):
					r = requests.get(url, verify=False).json()
					quote = r['content']

				lastQuote = quote

				quote = quote.replace(";", ".")

				run(tn, "say " + str(quote))
				print(quote)
			except:
				run(tn, "say Error: Failed to retrieve quote")
				print("failed to get quote")

		

		# clear console on connect
		if (result[0] == 5):
			try:
				run(tn, "name")
				result2 = tn.expect([b"- Current user name"])
				name_line = result2[2].decode("utf-8").splitlines()
				name = name_line[len(name_line) - 1]
				name = shlex.split(name)
				name = name[2]

				connect_name = result[2].decode("utf-8").splitlines()
				connect_name = connect_name[len(connect_name) - 1]
				connect_name = connect_name.replace(" connected.", "")

				if (name == connect_name):
					run(tn, "clear")
					print("Console cleared")
					run(tn, "*all* !info")
			except:
				pass


		
		# bot info
		if (result[0] == 6):
			try:
				uptime = floor(time.time() - start_time)
				bot_seconds = uptime % 3600 % 60
				bot_minutes = uptime % 3600 // 60
				bot_hours = uptime // 3600

				run(tn, "name")
				result2 = tn.expect([b"- Current user name"])
				name_line = result2[2].decode("utf-8").splitlines()
				name = name_line[len(name_line) - 1]
				name = shlex.split(name)
				name = name[2]

				run(tn, "playerchatwheel . \"Chatbot Uptime: " + str(bot_hours) + "h " + str(bot_minutes) + "m " + str(bot_seconds) + "s\"")
				run(tn, "playerchatwheel . \"Chatbot Listening to port: " + str(cfg.settings["tn_port"]) + "\"")
				run(tn, "playerchatwheel . \"Chatbot Host: " + str(name) + "\"")
			except:
				pass



		# Clan tag changer
		if (result[0] == 7):
			try:
				thread1 = Thread(target=change_clan)
				thread1.start()
			except:
				pass


		
		# clear chat
		if (result[0] == 8):
			try:
				run(tn, "say                                   ")
			except:
				pass


if __name__== "__main__":
  main()