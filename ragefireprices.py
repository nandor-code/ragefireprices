import os
import shutil
import configparser
import sys
import time
import re
import urllib.request
import glob
from urllib.request import FancyURLopener

def get_latest_log(p,server):
	newest_time = 0
	newest_file = ""
	file_pattern = p + "/*_" + server + ".txt"
	print( "Searching for files: " + file_pattern )

	for fname in glob.glob(file_pattern):
		file_time = os.path.getmtime(fname)
		if file_time > newest_time:
			newest_time = file_time
			newest_file = fname

	if newest_time == 0:
		sys.exit("HALT: No log exists" )

	print ( "------------Scanning Logs------------" )
	print ( "Detected \'" + newest_file + "\' as newest log using it." )

	pattern = re.compile(r".*eqlog_(?P<char>.*?)_" + server + ".txt", re.VERBOSE)
	match = pattern.match(newest_file)

	if match is None:
		sys.exit("HALT: No log name is an invalid format" )

	char = match.group("char")

	print( "Using Log: " + newest_file )
	print( "Using CharacterName: " + char )
	print ( "--------Done Scanning Logs--------" )

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

	ret_time = int( config['State']['LastTimeCode'] )
	
	print( "------------Starting Parse------------" )
	print( "Using Start Time: " + time.strftime( "%a %b %d %H:%M:%S %Y", time.localtime( ret_time ) ) )
	#print("Scanning logs for new data...")

	with open(log_file) as f:
		for line in f:
		
			if "says, '" in line: continue
			if "tells you, '" in line: continue
			if "tells the group, '" in line: continue
			if "tells the guild, '" in line: continue
			if "tells the raid, '" in line: continue
			if "you say, '" in line: continue
			if "] you told" in line: continue
			if "you tell your party, '" in line: continue
			if "you say to your guild, '" in line: continue

			line_time = get_line_time( line )
			
			## Skip lines older than last seen time
			if line_time <= int( config['State']['LastTimeCode'] ):
				continue

			ret_time = line_time

			print( ".", end='' )
			sys.stdout.flush()

			line = clean_line( line )

			if ", '" in line or "SYSTEMWIDE_MESSAGE" in line:
				class MyOpener(FancyURLopener):
					version = 'RFPILogger1' 
				
				try:
					myopener = MyOpener()
					url = "http://ragefireprices.info/api/in.php?c=" + str(character) + "&p=" + str(password) + "&s=" + str(server) + "&v=" + str(pversion) + "&l=" + str(line)
					page = myopener.open(url)
					print(str(line))
				except socket.gaierror:
					print("::: Connection Error, line unsent :::")
					continue

				
	print( "------------Parse Complete------------" )
	return ret_time

	
## Parser start time
p_start_time = int(time.time())
	
	
## Prepare/setup/get our rfpi directory and Settings
config_file = "Settings.ini"
if os.path.exists(config_file):
	print("Settings.ini found, using it.")
	pass
else:
	sys.exit("Settings.ini not found!\n\nPlease create a file called Settings.ini in the following format:\n\n[Settings]\nCharacter=YourcharacterName\nLogDir=c:\path\\to\\eq1\\logs\\")

global config

config = configparser.ConfigParser()
config['Settings'] = {'AutoDectectLog': "False" }
config['State'] = {'LastTimeCode': str(int(time.time())) }
				   
config.read(config_file)

pversion = "2.3.1"
password = config['Settings']['password']
server = config['Settings']['server']
server = server.lower()
while server not in ["ragefire","lockjaw"]:
	sys.exit("HALT: Server entered in settings.ini not supported. Ragefire or Lockjaw only")

## Check the log dir is accurate
global log_dir
log_dir = config['Settings']['LogDir']

if os.path.exists(log_dir):
	pass
else:
	sys.exit("HALT: EverQuest Log directory incorrect, check Settings.ini")

global log_file
global character

if config['Settings']['autodectectlog'] != "True":
	character = config['Settings']['Character']
	character = character.lower()
	character = character.title()
	
	## Define our log filename, check it exists 
	log_file = log_dir + "\eqlog_" + character + "_" + server + ".txt"
	if os.path.exists(log_file):
		pass
	else:
		sys.exit("HALT: No log exists for " + character)

# seed the last time code with the start-time of the parser so we ignore really old lines between parses.
config['State']['LastTimeCode'] = str(p_start_time) 

## Loop		
while True:
	## Do our thang
	if config['Settings']['AutoDectectLog'] == "True":
		log_file, character = get_latest_log(log_dir,server)

	latest_epoch = rfpiloop(server,pversion)

	config['State']['LastTimeCode'] = str(latest_epoch)
	with open( config_file, 'w' ) as cf:
		config.write(cf)
	
	cf.close()

	time.sleep(10)
