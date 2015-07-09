import os
import shutil
import configparser
import sys
import time
import re
import urllib.request
import glob
from urllib.request import FancyURLopener

def get_latest_log(p):
	newest_time = 0
	newest_file = ""
	file_pattern = p + "/*_ragefire.txt"
	print( "Searching for files: " + file_pattern )

	for fname in glob.glob(file_pattern):
		file_time = os.path.getmtime(fname)
		if file_time > newest_time:
			newest_time = file_time
			newest_file = fname

	if newest_time == 0:
		sys.exit("HALT: No log exists" )

	print ( "Detected \'" + newest_file + "\' as newest log using it..." )

	pattern = re.compile(r".*eqlog_(?P<char>.*?)_ragefire.txt", re.VERBOSE)
	match = pattern.match(newest_file)

	if match is None:
		sys.exit("HALT: No log name is an invalid format" )

	char = match.group("char")

	return newest_file, char
	
def date_to_epoch(s):
	pattern = '%a %b %m %H:%M:%S %Y'
	epoch = int(time.mktime(time.strptime(s, pattern)))
	#print( "epoch = ", epoch )
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

def rfpiloop():

	line_time = int( config['State']['LastTimeCode'] )

	print("Scanning logs for new data...")

	with open(log_file) as f:
		for line in f:
		
			if "says, '" in line: continue
			if "tells you, '" in line: continue
			if "tells the group, '" in line: continue
			if "tells the guild, '" in line: continue
			if "tells the raid, '" in line: continue

			line_time = get_line_time( line )

			if line_time <= int( config['State']['LastTimeCode'] ):
				#print( "Skipping line " + str(line_time) + " because it is too old" )
				continue

			print( ".", end='' )
			sys.stdout.flush()

			if ", '" in line or "SYSTEMWIDE_MESSAGE" in line:
				class MyOpener(FancyURLopener):
					version = 'RFPILogger1'  
				
				myopener = MyOpener()
				url = "http://www.ragefireprices.info/api/in.php?submitter=" + str(character) + "&line=" + str(line)
				page = myopener.open(url)
	
	print ( "" )
	print ( "Done." )
	return line_time

## Prepare/setup/get our rfpi directory and Settings
config_file = "Settings.ini"
if os.path.exists(config_file):
	print("Settings.ini found, using it.")
	pass
else:
	sys.exit("Settings.ini not found!\n\nPlease create a file called Settings.ini in the following format:\n\n[Settings]\nCharacter=YourcharacterName\nLogDir=c:\path\\to\\eq1\\logs\\")

config = configparser.ConfigParser()

config['Settings'] = {'AutoDectectLog': False }
config['State'] = {'LastTimeCode': str(int(time.time())) }
				   
config.read(config_file)

## Check the log dir is accurate
log_dir = config['Settings']['LogDir']

if os.path.exists(log_dir):
	pass
else:
	sys.exit("HALT: EverQuest Log directory incorrect, check Settings.ini")

if config['Settings']['AutoDectectLog'] == True:
	log_file, character = get_latest_log( log_dir )
else:
	character = config['Settings']['Character']
	character = character.lower()
	character = character.title()
	
	## Define our log filename, check it exists 
	log_file = log_dir + "\eqlog_" + character + "_ragefire.txt"
	if os.path.exists(log_file):
		pass
	else:
		sys.exit("HALT: No log exists for " + character)

print( "Using Log: " + log_file )
print( "Using CharacterName: " + character )
print( "" )

## Loop		
while True:
	## Do our thang
	latest_epoch = rfpiloop()

	config['State']['LastTimeCode'] = str(latest_epoch)
	with open( config_file, 'w' ) as cf:
		config.write(cf)
	
	cf.close()

	time.sleep(10)
