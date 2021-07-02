#!/usr/bin/python3

import curses
import mysql.connector
import simpleaudio as sa
import time
import threading
import edsom_db

def GetLastEvent():
	global cnn
	cmd = cnn.cursor()
	query = "SELECT id, type FROM event WHERE id = (SELECT MAX(id) FROM event WHERE parsed = 'Y');"
	cmd.execute(query)
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0, 0
	else:
		return row[0], row[1]

def GetNextEvent():
	global cnn
	cmd = cnn.cursor()
	query = """SELECT id, type FROM event WHERE id = (SELECT MIN(id) FROM event WHERE id > %s) AND parsed = 'Y';"""
	cmd.execute(query, (eId,))
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0, 0
	else:
		return row[0], row[1]

def ProcessFSDJump(peId):
	cmd = cnn.cursor()
	query = """SELECT * FROM event_FSDJump WHERE event_id = %s;"""
	cmd.execute(query, (peId,))
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0
	LinePrint("[{0}] -Jump COMPLETE- SystemName: {1}, Coords: {2} {3} {4} Distance:{5}\n".format(row[0],row[2],row[4],row[5],row[6],row[20]))
	# Factions
	query = """SELECT * FROM event_FSDJump_Factions WHERE event_id = %s;"""
	cmd.execute(query, (peId,))
	rows = cmd.fetchall()
	if cmd.rowcount > 0:
		LinePrint("*** System Factions ***\n")
		for row in rows:
			LinePrint("  Name:{0:<20} Gov:{1:<10} Allegiance:{2:<10} Infl.:{3:<10} State:{4:<10}\n".format(row[1][:20],row[3][:10],row[5][:10],str(row[4])[:10],row[2][:10]))
	#
	return 1

def ProcessFSDTarget(peId):
	cmd = cnn.cursor()
	query = """SELECT * FROM event_FSDTarget WHERE event_id = %s;"""
	cmd.execute(query, (peId,))
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0
	LinePrint("[{0}] FSDTarget Name: {1}, SystemAddress: {2}, Remaining Jumps: {3}\n".format(row[0],row[2],row[3],row[4])) 
	return 1

def ProcessScan(peId):
	cmd = cnn.cursor()
	query = """SELECT * FROM event_Scan WHERE event_id = %s;"""
	cmd.execute(query, (peId,))
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0
	LinePrint("[{0}] Scan Type:{1} Name:{2} Star:{3} Planet:{4}\n".format(row[0],row[2],row[3],row[10],row[16]))
	return 1

def ProcessStartJump(peId):
	cmd = cnn.cursor()
	query = """SELECT * FROM event_StartJump WHERE event_id = %s;"""
	cmd.execute(query, (peId,))
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0
	LinePrint("[{0}] Engaging FrameShift Drive:{1} Dest:{2} Star Class:{3}\n".format(row[0],row[2],row[3],row[5])) 
	return 1

def ProcessEvent(peId, peType):
	res = 0
	if peType == 'FSDJump':
		res = ProcessFSDJump(peId)
	elif peType == 'FSDTarget':
		res = ProcessFSDTarget(peId)
	elif peType == 'Scan':
		res = ProcessScan(peId)
	elif peType == 'StartJump':
		res = ProcessStartJump(peId)
	return res

def Server(name, thing):
	global win, eId, eType
	LinePrint("Server running...{0}\n".format(eId))
	while True:
		nId, nType = GetNextEvent()
		if nId != 0:
			#win.addstr("server(1) nId:{0}\n".format(nId))
			eId, eType = nId, nType
			pr = ProcessEvent(eId, eType)
			if pr == 0:
				LinePrint("Received Event ID: {0}, Event Type: {1}\n".format(eId,eType))
		else:
			#win.addstr("server(2) nId:{0}\n".format(nId))
			time.sleep(1)

def LinePrint(msg):
	global win
	i = 0;
	j = 0;
	while(i < len(msg)):
		c = msg[i]
		try:
			win.addch(c)
		except:
			win.addstr(" [ERR] ")
		i += 1
		j += 1
		if j == 2:
			j = 0
		if ord(c) != 32 and j == 1 and audio == True:
			play_obj = wave_obj.play()
		time.sleep(0.05)
		win.refresh()

wave_obj = sa.WaveObject.from_wave_file("./media/electype.wav")
audio = False
stdscr = curses.initscr()
win = curses.newwin(curses.LINES, curses.COLS, 0, 0)
win.timeout(100)
curses.raw()
win.keypad(True)
win.scrollok(0)
curses.noecho()
#curses.start_color()
#curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
#win.attron(curses.color_pair(1))
LinePrint("Initiating [{0},{1}]...\n".format(curses.COLS,curses.LINES))

cnn.autocommit = True

eId, eType = GetLastEvent()

x = threading.Thread(target=Server, args=(1,2), daemon=True)
x.start()

finished = False
while not finished:
	win.refresh()
	k = win.getch()
	if k != -1:
		LinePrint("You pressed {0}\n".format(chr(k)))
		if (k == ord("q")):
			finished = True

win.addstr("*** Finished! ***\n")

win.refresh()
win.getch()
#win.attroff(curses.color_pair(1))
curses.endwin()

