import mpd
import time
import argparse
from random import randint

parser = argparse.ArgumentParser()
parser.add_argument('--hostname', type=str, default="localhost")
parser.add_argument("--port", type=int, default=6600)
parser.add_argument("--blacklist", type=str, action="append")
parser.add_argument("--logfile", type=str)

args = parser.parse_args()

reconnect = False
client = mpd.MPDClient()
client.connect(args.hostname, args.port)
addedSongs = []
lastPlaylistId = -1
completeList = []

last_modified = {}
previous_last_modified = {}

if args.blacklist:
	for blacklist in args.blacklist:
		previous_last_modified[blacklist] = 0

def filterList(item, blacklists):
	if("file" in item):
		path = item["file"]
		for blacklist in blacklists:
			if (path in blacklist):
				return False

		return True
		'''
		if (path.find("VIDEO") == -1 and path.find("perusse") == -1) :
			return True
		else:
			print(path + " semi-blacklisted")
			return False
		'''
	else:
		return False

def addRandom():
	global addedSongs
	global completeList
	choice = completeList[randint(0,len(completeList)-1)]
	print(("Adding " + choice["file"]).encode("utf-8"))
	if args.logfile:
		with open(args.logfile, "a") as f:
			f.write(choice["file"]+"\n")
	songid = int(client.addid(choice["file"]))
	addedSongs.append(songid)


def updateList():
	global completeList
	blacklists = []
	if args.blacklist:
		for blacklist in args.blacklist:
			try:
				blacklists.append(client.listplaylist(blacklist))
			except:
				pass
	completeList = client.listall()
	completeList = [item for item in completeList if filterList(item, blacklists)]

updateList()

while(True):
	try:
		if(reconnect == True):
			reconnect = False
			client = mpd.MPDClient()
			client.connect(args.hostname, args.port)

		idle = client.idle("database", "stored_playlist", "player", "playlist")
		print(idle)
		if "database" in idle:
			updateList()

		# update if blacklist file modified
		if "stored_playlist" in idle:
			must_update = False
			playlists = client.listplaylists()
			for playlist in playlists:
				if playlist["playlist"] in args.blacklist:
					last_modified[playlist["playlist"]] = time.mktime(time.strptime(playlist["last-modified"], "%Y-%m-%dT%H:%M:%SZ"))
					if last_modified[playlist["playlist"]] > previous_last_modified[playlist["playlist"]] :
						must_update = True
						previous_last_modified [playlist["playlist"]] = last_modified[playlist["playlist"]] 
			if must_update:
				updateList()

		status = client.status()
		print(status)
	
		# Clean the playlist of added songs
		if ("songid" in status and "song" in status):
			playlistinfo = client.playlistinfo()
			#print(addedSongs)
			for i in reversed(range(0,int(status["song"]))):
				#print(int(playlistinfo[i]["id"]))
				if (int(playlistinfo[i]["id"]) in addedSongs):
					print("Removing "+playlistinfo[i]["file"])
					try:
						client.deleteid(int(playlistinfo[i]["id"]))
					except(mpd.CommandError):
						pass
					addedSongs.remove(int(playlistinfo[i]["id"]))
				'''
				no more songs to remove
				We ignore the last addition because it could be the playing song
				'''
				if not addedSongs[0:-2]:
					break

			# songs added but not found?
			if addedSongs[0:-2]:
				currentIds = []
				for i in playlistinfo:
					currentIds.append(int(i["id"]))
				for songid in addedSongs:
					if(songid not in currentIds):
						addedSongs.remove(songid)
	
		# The player is at the last song
		if ("song" in status and "playlistlength" in status):
			song = int(status["song"])
			playlistlength = int(status["playlistlength"])
			#print(str(song) + " " + str(playlistlength))
			if (song+1 == playlistlength) :
				addRandom()
		
		# The player has stopped and there is no current song
		if ("state" in status):
			if(status["state"] == "stop"):
				if ("song" not in status and lastPlaylistId == status["playlist"]):
					addRandom()
					#client.play(int(status["playlistlength"]))
					client.playid(addedSongs[-1])
		
		lastPlaylistId = status["playlist"]
	
	except(mpd.ConnectionError, ConnectionRefusedError):
		print("Error!")
		time.sleep(10)
		reconnect = True
