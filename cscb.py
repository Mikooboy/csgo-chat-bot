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
from math import *
from random import randrange
from termcolor import colored
from time import sleep
from os import path

# Config
api_key = '' # Insert your Steam Web API key here

tn_host = "127.0.0.1"
tn_port = "2121"
cfg_path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\csgo\\cfg\\"

def steamid_to_64bit(steamid):
    steam64id = 76561197960265728 # I honestly don't know where
                                    # this came from, but it works...
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
	procList = []
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

def main():
	if (len(sys.argv) > 1):
		if (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
			print(colored("Run with no arguments to initiate and connect to csgo", attrs=['bold']))
			print(colored("Make sure you set up csgo to receive connections with this launch option: -netconport "+str(tn_port), attrs=['bold']))
	
	# Make sure cs:go is running before trying to connect
	if not processExists("csgo.exe"):
		print("Waiting for csgo to start... ")
		while not processExists("csgo.exe"):
			sleep(0.25)
		sleep(10)

	# Initialize csgo telnet connection
	print("Trying " + tn_host + ":" + tn_port + "...")
	try:
		tn = telnetlib.Telnet(tn_host, tn_port)
	except ConnectionRefusedError:
		# Retry in 10 seconds
		sleep(10)
		pass
	try:
		tn = telnetlib.Telnet(tn_host, tn_port)
	except ConnectionRefusedError:
		print("Connection refused. Make sure you have the following launch option set:")
		print(colored("  -netconport "+str(tn_port), attrs=['bold']))
		sys.exit(1)
	tn.write(b"echo CSCTL Active, use chat or echo in console to execute commands\n")
	tn.read_until(b"commands")
	print("Successfully Connected")
	
	print("Listening for command from console")
	
	while True:
		# Capture console output until we encounter our exec string
		result = tn.expect([b"!calc", b"!help", b"!info"])

		# Calculator
		if (result[0] == 0):
			sleep(0.7) # csgo chat cooldown

			splitted 		= result[2].decode("utf-8").split(": ")
			splitted_again 	= splitted[len(splitted)-1].split(" !")
			calc 			= splitted_again[0]
			print(calc)

			answer = "Error"

			try:
				answer = eval(calc, {'sqrt': sqrt, 'pow': pow})
			except:
				pass

			tokens 		= []
			tokenizer 	= re.compile(r'\s*([()+*/-]|\d+)')
			current_pos = 0

			while current_pos < len(calc):
				match = tokenizer.match(calc, current_pos)

				if match is None:
					answer = "SyntaxError"
					tokens = []
					break

				tokens.append(match.group(1))
				current_pos = match.end()

			separated = " ".join(str(x) for x in tokens)

			run(tn, "say " + separated + " = " + str(answer))
			print(separated + " = " + str(answer))



		# help
		if (result[0] == 1):
			sleep(0.7) # csgo chat cooldown

			run(tn, "say List of commands: !​help, <name> !​info, <math> !​calc")
			print("!help")
		


		# Player info
		if (result[0] == 2):
			sleep(0.7) # csgo chat cooldown

			kdratio 	= "N/A" # Kill Death Ratio
			timeplayed 	= "N/A" #time played
			rounds 		= "N/A"

			game_info 	= True
			hour_info 	= True

			splitted 	= result[2].decode("utf-8").split(" ")
			name 		= splitted[len(splitted)-2]

			matching 	 = 0
			matching_map = 0

			run(tn, "status")
			status = tn.expect([b"#end"])
			lines 	= status[2].decode("utf-8").splitlines()
			
			for i in lines:
				if name.lower() in i.lower():
					matching = i
			
			for i in lines:
				if "map" in i.lower():
					matching_map = i
			
			mapName = matching_map.split()
			mapName = mapName[2]

			if (matching == 0) or (len(name) < 2):
				run(tn, "say Error: Invalid name")
				print("Error: Invalid name")
			else:
				try:
					if (api_key == ''):
						raise

					match_split = matching.split()

					playerId = None

					for i in match_split:
						if "steam_1" in i.lower():
							playerId = i
					
					playerId64 = steamid_to_64bit(playerId)

					print("Request info for: " + str(name))

					url 	= 'https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=730&key=' + api_key + '&steamid='
					url2 	= 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=' + api_key + '&steamid='
					final_url 	= url + str(playerId64)
					final_url2 	= url2 + str(playerId64)
					try:
						r = requests.get(final_url).json()
						stats = {
							'total_kills' 	: r['playerstats']['stats'][0]['value'], #total kills
							'total_deaths' 	: r['playerstats']['stats'][1]['value'], #total deaths
							'map_rounds'	: "N/A"
						}

						for i in (r['playerstats']['stats']):
							id = i['name']
							if ("rounds" in id) and (mapName in id):
								stats['map_rounds'] = i['value']

						kd = stats['total_kills']/stats['total_deaths'] #kill death ratio

						rounds 	= str(stats['map_rounds'])
						kdratio 	= str("{:.2f}".format(kd)) # Kill Death Ratio
					except:
						game_info = False

					try:
						r2 = requests.get(final_url2).json()
						games = r2['response']['games'] #total time played

						for i in games:
							id = i['appid']
							if (id == 730):
								time_played = i['playtime_forever']

						hours = time_played/60 #minute to hours
						timeplayed 	= str(floor(hours)) #time played
					except:
						hour_info = False
					
					if (not game_info) and (not hour_info):
						run(tn, "say Error: Game and hour info private")
						sleep(0.7)
					elif (not game_info):
						run(tn, "say Error: Game info private")
						sleep(0.7)
					elif (not hour_info):
						run(tn, "say Error: Hour info private")
						sleep(0.7)

					run(tn, "say " + str(name) + " | K/D: " + str(kdratio) + " Hours: " + str(timeplayed) + " " + str(mapName) + ": " + str(rounds) + " rounds")
					print(str(name) + " | K/D: " + str(kdratio) + " Hours: " + str(timeplayed) + " " + str(mapName) + ": " + str(rounds) + " rounds")
				except:
					run(tn, "say Error: Couldn't retrieve info")
					print("Error: Couldn't retrieve info")
					print("Make sure that the API key is correct")



if __name__== "__main__":
  main()
