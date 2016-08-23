import os
import shutil
import configparser
import sys
import time
import re
import urllib.request
import glob
import logging
from urllib.request import FancyURLopener

def get_latest_log(p,server):

	global p_loops
	p_loops = p_loops + 1


	newest_time = 0
	newest_file = ""
	file_pattern = p + "/*_" + server + ".txt"
	if p_loops == 1:
		print("[@]  Searching: " + file_pattern)

	for fname in glob.glob(file_pattern):
		file_time = os.path.getmtime(fname)
		if file_time > newest_time:
			newest_time = file_time
			newest_file = fname

	if newest_time == 0:
		print("\033[91m[X] Cannot find log file")
		print("[X] Parser will close automatically in 60 seconds \033[0m")	
		logging.error("Log file is incorrectly named")
		time.sleep(60)
		sys.exit()

	if p_loops == 1:
		print ("[@]  Detected: " + newest_file)

	pattern = re.compile(r".*eqlog_(?P<char>.*?)_" + server + ".txt", re.VERBOSE)
	match = pattern.match(newest_file)

	if match is None:
		print("\033[91m[X] Invalid log file")
		print("[X] Parser will close automatically in 60 seconds \033[0m")	
		logging.error("Log file is incorrectly named")
		time.sleep(60)
		sys.exit()

	char = match.group("char")

	if p_loops == 1:
		print("[@]  Character: " + char)
		print("[@]  Server: " + server)
		print("#####################################################")
		print("############   Beginning Live Parse   ##############")
		print("#####################################################")

	char = char.lower()
	char = char.title()

	return newest_file, char
	
def date_to_epoch(s):
	pattern = '%a %b %d %H:%M:%S %Y'
	epoch = int(time.mktime(time.strptime(s, pattern)))
	return epoch

def get_line_time(s):
	pattern = re.compile(r"\[(?P<date>.*?)\].*", re.VERBOSE)
	match = pattern.match(s)

	if match is None:
		return 0

	date = match.group("date")

	# convert to epoch.
	epoch = date_to_epoch(date)
	
	return epoch

def clean_line(s):
	clean_s = ""

	for	c in s:
		if( ord( c ) < 128 ):
			clean_s += c

	return clean_s

def rfpiloop(server,pversion):

	# Let the user know something is
	# happening with tick/tock
	print("[/] check")
	
	ret_time = int( config['state']['LastTimeCode'] )

	with open(log_file) as f:
		for line in f:
		
			if "says, '" in line: continue
			if "tells you, '" in line: continue
			if "tells the group, '" in line: continue
			if "tells the guild, '" in line: continue
			if "tells the raid, '" in line: continue
			if "You say, '" in line: continue
			if "You told " in line: continue
			if "You tell your party, '" in line: continue
			if "You say to your guild, '" in line: continue
			if "You tell your raid, '" in line: continue

			line_time = get_line_time( line )
			
			# Skip lines older than last seen time
			if line_time <= int( config['state']['LastTimeCode'] ):
				continue

			ret_time = line_time

			#print( ".", end='' )
			sys.stdout.flush()

			line = clean_line( line )

			if ", '" in line or "SYSTEMWIDE_MESSAGE" in line:
				class MyOpener(FancyURLopener):
					version = 'RFPILogger1' 
				
				try:
					myopener = MyOpener()
					url = "http://ragefireprices.info/api/in.php?c=" + str(character) + "&s=" + str(server) + "&v=" + str(pversion) + "&l=" + str(line)
					page = myopener.open(url)
					print("[+]  " + str(line))
				except socket.gaierror:
					print("[-]  Connection error, previous line unsent")
					continue

				
	return ret_time



# Initialise
os.system("mode con cols=100 lines=40")	
print("#####################################################")
print("##########                                ##########")		
print("##########   RagefirePrices.info Parser   ##########")
print("##########                                ##########")		
print("#####################################################")		
		
# Parser start time
p_start_time = int(time.time())

# Check/create parser error logs
logging.basicConfig(filename='parserdebug.log',level=logging.DEBUG,format='%(asctime)s %(message)s')

# Loop counter
p_loops = 0
	
# Prepare/setup/get our rfpi directory and settings
config_file = "settings.ini"
if os.path.exists(config_file):
	print("[@]  settings.ini found")
	pass
else:
	print("\033[91m[X] Could not find settings.ini file")
	print("[X] Parser will close automatically in 60 seconds \033[0m")	
	logging.error("Failed to open settings.ini file")
	time.sleep(60)
	sys.exit()
	

global config

config = configparser.ConfigParser()
config['autod'] = {'AutoDectectLog': "False" }
config['state'] = {'LastTimeCode': str(int(time.time())) }
				   
config.read(config_file)

pversion = "4"
server = config['settings']['server']
server = server.lower()
while server not in ["ragefire","lockjaw","phinigel"]:
	print("\033[91m[X] Server entered in settings.ini is not supported")
	print("[X] Ragefire, Lockjaw or Phinigel only")
	print("[X] Parser will close automatically in 60 seconds \033[0m")	
	logging.error("Server not supported")
	time.sleep(60)
	sys.exit()

# Check the log dir is accurate
global log_dir
log_dir = config['settings']['LogDir']

if os.path.exists(log_dir):
	pass
else:
	print("\033[91m[X] Could not find EverQuest Logs directory, please check settings.ini")
	print("[X] Parser will close automatically in 60 seconds \033[0m")	
	logging.error("Could not find EverQuest Logs directory")
	time.sleep(60)
	sys.exit()

global log_file
global character

if config['autod']['autodectectlog'] != "True":
	character = config['settings']['Character']
	character = character.lower()
	character = character.title()
	
	# Define our log filename, check it exists 
	log_file = log_dir + "\eqlog_" + character + "_" + server + ".txt"
	if os.path.exists(log_file):
		pass
	else:
		print("\033[91m[X] Could not find log file for " + character)
		print("[X] Parser will close automatically in 60 seconds \033[0m")	
		logging.error("Could not find character log file")
		time.sleep(60)
		sys.exit()

# seed the last time code with the start-time of the parser so we ignore really old lines between parses.
config['state']['LastTimeCode'] = str(p_start_time) 

# Loop		
while True:
	# Do our thang
	if config['autod']['AutoDectectLog'] == "True":
		log_file, character = get_latest_log(log_dir,server)

	latest_epoch = rfpiloop(server,pversion)

	config['state']['LastTimeCode'] = str(latest_epoch)
	with open( config_file, 'w' ) as cf:
		config.write(cf)
	
	cf.close()
	time.sleep(10)