#!/usr/bin/python3

from datetime import datetime
import mysql.connector
import random
import simpleaudio as sa
import threading
import time
import urwid
import edsom_db

cursor = u"\u2588"
wave_obj = sa.WaveObject.from_wave_file("./media/electype.wav")
audio = True
status_box_width = 80
status_box_height = 8

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
	global cnn
	cmd = cnn.cursor()
	query = """SELECT * FROM event_FSDJump WHERE event_id = %s;"""
	cmd.execute(query, (peId,))
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0
	LinePrint("{0}  FSD Hyperspace Jump Complete, System Name: {1}, Jump Distance: {2} ly, Fuel Consumed: {3} Mg".format(row[1],row[2],row[20],row[21]))
	# Factions
	#query = """SELECT * FROM event_FSDJump_Factions WHERE event_id = %s;"""
	#cmd.execute(query, (peId,))
	#rows = cmd.fetchall()
	#if cmd.rowcount > 0:
	#	LinePrint("*** System Factions ***")
	#	for row in rows:
	#		LinePrint("  Name:{0:<20} Gov:{1:<10} Allegiance:{2:<10} Infl.:{3:<10} State:{4:<10}".format(row[1][:20],row[3][:10],row[5][:10],str(row[4])[:10],row[2][:10]))
	return 1

def ProcessFSDTarget(peId):
	global cnn
	cmd = cnn.cursor()
	query = """SELECT * FROM event_FSDTarget WHERE event_id = %s;"""
	cmd.execute(query, (peId,))
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0
	LinePrint("{0}  FSD Destination Selected, System Name: {1}, Jumps Remaining In Current Route: {2}".format(row[1],row[2],row[4])) 
	return 1

def ProcessScan(peId):
	global cnn
	cmd = cnn.cursor()
	query = """SELECT * FROM event_Scan WHERE event_id = %s;"""
	cmd.execute(query, (peId,))
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0
	LinePrint("{0}  Scan Type: {1} Name: {2} Star: {3} Planet: {4}".format(row[1],row[2],row[3],row[10],row[16]))
	return 1

def ProcessStartJump(peId):
	global cnn
	cmd = cnn.cursor()
	query = """SELECT * FROM event_StartJump WHERE event_id = %s;"""
	cmd.execute(query, (peId,))
	row = cmd.fetchone()
	if cmd.rowcount != 1:
		return 0
	if row[2] == "Hyperspace":
		LinePrint("{0}  FSD Hyperspace Jump Initiated, Destination System: {1} Star Class: {2}".format(row[1],row[3],row[5]))
	elif row[2] == "Supercruise":
		LinePrint("{0}  FSD Engaging Supercruise")
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

def Server():
	global eId, eType
	LinePrint("Initiating Event Server...{0}".format(eId))
	while True:
		nId, nType = GetNextEvent()
		if nId != 0:
			eId, eType = nId, nType
			pr = ProcessEvent(eId, eType)
			if pr == 0:
				LinePrint("Received Event ID: {0}, Event Type: {1}".format(eId,eType))
		else:
			time.sleep(1)

def LinePrint(text):
	global status_box, cursor, audio
	status_box.set_focus(len(status_box.body)-1)
	for x in range(1,len(text)+1):
		tmp = status_box.body[len(status_box.body)-1].original_widget
		tmp.set_text("{0}{1}".format(text[0:x],cursor))
		loop.draw_screen()
		if audio == True and ord(text[x-1:x]) != 32 and x%2 == 1:
			wave_obj.play()
		time.sleep(0.04)
	tmp = status_box.body[len(status_box.body)-1].original_widget
	tmp.set_text(text[0:x])
	status_box.body.append(urwid.AttrMap(urwid.Text(cursor, wrap='clip'), None, focus_map='reversed'))
	status_box.set_focus(len(status_box.body)-1)
	if len(status_box.body) > 50:
		status_box.body.remove(status_box.body[0])
	loop.draw_screen()
	time.sleep(0.04)

def AddRandomEvent():
	global cnn
	cmd = cnn.cursor()
	# Get random number
	query = """SELECT CAST((RAND()*(SELECT COUNT(1) FROM event WHERE type IN ('FSDJump','FSDTarget','Scan','StartJump')))+1 AS UNSIGNED);"""
	cmd.execute(query)
	row = cmd.fetchone()
	offset = row[0]
	# get event
	query = """SELECT id, type FROM event WHERE type IN ('FSDJump','FSDTarget','Scan','StartJump') LIMIT 1 OFFSET """ + str(offset)
	cmd.execute(query)
	row = cmd.fetchone()
	ProcessEvent(row[0], row[1])

def keypresses(key):
	if key in ('q', 'Q'):
		raise urwid.ExitMainLoop()
	elif key in ('e', 'E'):
		AddRandomEvent()

def init_status_box():
	body = []
	status_box = urwid.ListBox(urwid.SimpleFocusListWalker(body))
	status_box.body.append(urwid.AttrMap(urwid.Text(cursor, wrap='clip'), None, focus_map='reversed'))
	status_box.set_focus(len(status_box.body)-1)
	return status_box

def init_interface(status_box):
	pad = urwid.Padding(status_box)
	lb = urwid.LineBox(pad,title='Events',title_align='left')
	pad2 = urwid.Padding(lb, width=('relative',status_box_width))
	fill = urwid.Filler(pad2, 'top', status_box_height)
	return fill

def start_server(a, b): # TODO: Complains it's receiving 2 parameters if we don't have (a, b) here
	x = threading.Thread(target=Server, daemon=True)
	x.start()

cnn.autocommit = True

eId, eType = GetLastEvent()

status_box = init_status_box()
interface = init_interface(status_box)
loop = urwid.MainLoop(interface, unhandled_input=keypresses)
loop.set_alarm_in(1, start_server)
loop.run()
