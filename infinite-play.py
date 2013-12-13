import mpd
import time
from random import randint

reconnect = False
client = mpd.MPDClient()
client.connect('music.dorsal.polymtl.ca', 6600)
addedSongs = []
lastPlaylistId = -1
completeList = []
previous_last_modified = 0

def filterList(item, blacklist):
	if("file" in item):
		path = item["file"]
		if (path in blacklist):
			return False
		else:
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
	with open("dj.log", "a") as f:
		f.write(choice["file"]+"\n")
	songid = int(client.addid(choice["file"]))
	addedSongs.append(songid)


def updateList():
	global completeList
	blacklist = client.listplaylist("dj-blacklist")
	completeList = client.listall()
	completeList = [item for item in completeList if filterList(item, blacklist)]

updateList()

while(True):
	try:
		if(reconnect == True):
			reconnect = False
			client = mpd.MPDClient()
			client.connect("music.dorsal.polymtl.ca", 6600)

		idle = client.idle("database", "stored_playlist", "player", "playlist")
		print(idle)
		if "database" in idle:
			updateList()

		# update if blacklist file modified
		if "stored_playlist" in idle:
			playlists = client.listplaylists()
			for playlist in playlists:
				if playlist["playlist"] == "dj-blacklist":
					last_modified = time.mktime(time.strptime(playlist["last-modified"], "%Y-%m-%dT%H:%M:%SZ"))
					if last_modified > previous_last_modified:
						updateList()
						previous_last_modified = last_modified

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
