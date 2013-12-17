infinite-play
=============

This python script allows you to automatically append random songs at the end of your MPD playlist.

It uses the asynchronous interface to an MPD server. When this script notices that the last song of the playlist is playing, it inserts a new one.
Once the automatically added songs have finishded playing, they are removed from the playlist, leaving it as it was before.

By default, this script chooses any random song from the MPD database. It is possible to restrict this choice by specifying a blacklist playlist. Any songs contained in the blacklist will not be added.


Dependencies:

https://github.com/Mic92/python-mpd2
