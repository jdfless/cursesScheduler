import curses
import MySQLdb
import getpass
import datetime

#global variables
minYsize = 21 	#currently limited by add page
minXsize = 52	#currently limited by add page

#used for sql statements
username = getpass.getuser()
adid = 0
sortType = 'ta'
backPage = 'm'	#also can be 'a', 'd', 's', 'h'

#strings used on multiple pages
colA = "Date"
colB = "Time"
colC = "Name"
colD = "Email"
info = "Press 'h' for help"
nextPage = "; 'n' for next page"
prevPage = "; 'p' for previous page"
noDelete = "; you have no appointments"

#global list variables for printed appointment info
students = []
dates = []
times = []
emails = []

def exitApplication():
	cur.close()		#close cursor
	db.close()		#close database
	curses.endwin()	#endwin
	exit(0)			#exit cleanly

#header used by main and delete pages
def header(heading, screen, dims):
	#set up cli
	split = (dims[1] - 17) / 2
	screen.border(0)					#renders wrong with cygwin
	screen.addstr(1,1, heading)
	screen.hline(2,1, 0, dims[1]-2)
	screen.addstr(3,1, colA)
	screen.vline(3,9,0, dims[0]-5)
	screen.addstr(3,10, colB)
	screen.vline(3,16,0, dims[0]-5)
	screen.addstr(3,17, colC)
	screen.vline(3,17+split,0, dims[0]-5)
	screen.addstr(3,17+split+1, colD)
	screen.hline(4,1, 0, dims[1]-2)

#puts up unique header for confirming delete
def confirmDeleteHeader(heading, screen, dims):
	#set up delete page header
	split = (dims[1] - 17) / 2
	screen.border(0)					#renders wrong with cygwin
	screen.addstr(1,1, heading)
	screen.hline(2,1, 0, dims[1]-2)
	screen.addstr(3,1, colA)
	screen.vline(3,9,0, 3)
	screen.addstr(3,10, colB)
	screen.vline(3,16,0, 3)
	screen.addstr(3,17, colC)
	screen.vline(3,17+split,0, 3)
	screen.addstr(3,17+split+1, colD)
	screen.hline(4,1, 0, dims[1]-2)

#put up footer with page turn instructions
def footer(screen, dims, more):
	#instructions at end
	screen.hline(dims[0]-3,1,0,dims[1]-2)
	screen.addstr(dims[0]-2,1, info)
	#case for on first page with more to show
	if more == 1:
		screen.addstr(dims[0]-2, len(info)+1, nextPage)
	#case for middle pages, can go forward or back
	if more == 2:
		screen.addstr(dims[0]-2, len(info)+1, nextPage)
		screen.addstr(dims[0]-2, len(nextPage)+len(info)+1, prevPage)
	#case for last page
	if more == 3:
		screen.addstr(dims[0]-2, len(info)+1, prevPage)
	if more == 4:
		screen.addstr(dims[0]-2, len(info)+1, noDelete)

#display the appointments on the main page and delete pages
#sizes of students and emails are dynamic
def appts(screen, dims, rpp, page):	
	n = (dims[1] - 17) / 2 #let students and emails each use half of the remaining size after date and time
	i = 5
	if page < 0:
		page = 0
	j = page * rpp
	start = j
	end = j + rpp-1
	if rpp == 1:
		end = start
	#test so no out of index if page has more space than results needed to print
	if end > len(dates) - 1:
		last = len(dates) - 1
	else:
		last = end

	#get data from server
	getApptData(sortType)

	while j <= last:
		#addnstr only adds max of n chars so no overflow
		screen.addstr(i,1, dates[j])
		screen.addstr(i,10,times[j])
		screen.addnstr(i,17,students[j], n)
		screen.addnstr(i,17+n+1,emails[j], n-2)
		screen.hline(i+1,1, 0, dims[1]-2)
		i += 2
		j += 1

	more = 0
	if end < len(dates)-1:
		more = 1
	if end < len(dates)-1 and start > rpp-1:
		more = 2
	if start > rpp-1 and last == len(dates)-1:
		more = 3
	if len(dates) == 0:
		more = 4

	return more

#main screen to show the appointments
def mainScreen(screen, dims):
	global rpp
	global page
	global sortType
	global backPage
	getApptData(sortType)
	heading = "Appointments for " + str(username) + " -"
	key = -1		#for key presses
	page = 0
	rpp = (dims[0]-7)/2
	screenSizeCheck(dims)
	if len(dates) <= rpp:
		maxPage = 0
	elif len(dates) % rpp == 0:
		maxPage = len(dates) / rpp - 1
	else:
		maxPage = len(dates) / rpp
	orig = dims[0]
	more = 0
	while 1:				

		screen.clear()
		curses.noecho()
		curses.curs_set(0)
		dims = screen.getmaxyx()		#get screen dimensions
		screenSizeCheck(dims)
		rpp = (dims[0]-7)/2				#max number results per page
		if orig != dims[0]:				#reset to first page on vertical resize
			page = 0
			if len(dates) <= rpp:
				maxPage = 0
			elif len(dates) % rpp == 0:
				maxPage = len(dates) / rpp - 1
			else:
				maxPage = len(dates) / rpp
			orig = dims[0]
						
		
		header(heading, screen, dims)
		more = appts(screen, dims, rpp, page) #add sortBy as param
		footer(screen, dims, more)
		
		screen.refresh()
		key = screen.getch()
		if key == ord('n') and page < maxPage:
			page += 1
		if key == ord('p') and page > 0:
			page -= 1
		if key == ord('h'):
			backPage = 'm'
			helpScreen(screen, dims)
		if key == ord('a'):
			backPage = 'm'
			addAppointment(screen, dims)
		if key == ord('d') and len(dates) > 0:
			backPage = 'm'
			deleteAppt(screen, dims, rpp, page)
		if key == ord('s'):
			backPage = 'm'
			sortType = sortAppts(screen, dims)
		if key == ord('b') and backPage != 'm':
			bP = backPage
			backPage = 'm'
			goBack(screen, dims, bP)
		if key == ord('q'):
			exitApplication()

#show table for basic controls
def helpScreen(screen, dims):
	global sortType
	global backPage
	screenSizeCheck(dims)
	#strings
	instructs = "Here are the instructions for this CLI:"
	helpStrings = []	#list for easier printing
	quit = "To QUIT - "
	helpStrings.append(quit)
	add = "To ADD an appointment - "
	helpStrings.append(add)
	delete = "To DELETE an appointment - "
	helpStrings.append(delete)
	sort = "To SORT by name, date, or time - "
	helpStrings.append(sort)
	main = "To go to the MAIN screen - "
	helpStrings.append(main)
	back = "To go BACK to the last screen - "
	helpStrings.append(back)
	helpS = "To go to this HELP screen - "
	helpStrings.append(helpS)

	longStr = 0
	for i in helpStrings:
		if len(i) > longStr:
			longStr = len(i)

	helpKeys = []
	quitKey = "press 'q'"
	helpKeys.append(quitKey)
	addKey = "press 'a'"
	helpKeys.append(addKey)
	delKey = "press 'd'"
	helpKeys.append(delKey)
	sortKey = "press 's'"
	helpKeys.append(sortKey)
	mainKey = "press 'm'"
	helpKeys.append(mainKey)
	backKey = "press 'b'"
	helpKeys.append(backKey)
	helpKey = "press 'h'"
	helpKeys.append(helpKey)

	longKeyStr = 0
	for i in helpKeys:
		if len(i) > longKeyStr:
			longKeyStr = len(i)


	key = -1
	while 1:	#b is used to go back to last screen
		screen.clear()
		curses.noecho()
		curses.curs_set(0)
		dims = screen.getmaxyx()
		screenSizeCheck(dims)
		#give necessary instructions
		screen.border(0)
		screen.addstr(1,1, instructs)
		screen.hline(2,1,0,dims[1]-2)

		lineLen = longStr + 1 + longKeyStr
		indent = 5
		#add all instruction strings
		y = 3
		for theStr in helpStrings:
			x = indent	#give some spacing from edge
			screen.addstr(y, x, theStr)
			y += 1
			screen.hline(y, x, 0, lineLen)
			y += 1
		screen.vline(3, indent+longStr, 0, len(helpKeys)*2-1)
		y = 3
		for theKeyStr in helpKeys:
			x = indent + longStr + 1
			screen.addstr(y, x, theKeyStr)
			y += 2
		screen.vline(3, indent+lineLen, 0, len(helpKeys)*2-1)

		screen.refresh()
		key = screen.getch()
		if key == ord('q'):
			exitApplication()
		if key == ord('a'):
			backPage = 'h'
			addAppointment(screen, dims)
		if key == ord('d')  and len(dates) > 0:
			backPage = 'h'
			deleteAppt(screen, dims, rpp, page)
		if key == ord('d') and len(dates) == 0: 	#nothing to delete, go homeh
			backPage = 'h'
			mainScreen(screen, dims)
		if key == ord('s'):
			backPage = 'h'
			sortType = sortAppts(screen, dims)
		if key == ord('m'):
			backPage = 'h'
			mainScreen(screen, dims)
		if key == ord('b') and backPage != 'h':
			bP = backPage
			backPage = 'h'
			goBack(screen, dims, bP)
	return

#function to decide where to put cursor x-coordinate for delete page navigation
def getCursX(y, rpp, page):
	dims = screen.getmaxyx()
	i = (y - 5) / 2 + (page * rpp)
	x = len(students[i]) + 17
	split = (dims[1] - 17) / 2
	
	if len(students[i]) >= split:
		return 16 + split		#puts cursor at end of name if name will overflow
	else:
		return x

#screen to select appointment to delete
def deleteAppt(screen, dims, rpp, page):
	#like homescreen but numbered
	global backPage
	delHeading = "To DELETE hit 'd'. Use up/down arrows to select."
	key = -1		#for key presses
	page = 0
	y = 5
	dims = screen.getmaxyx()
	rpp = (dims[0]-7)/2
	screenSizeCheck(dims)
	x = getCursX(y, rpp, page)
	if len(dates) <= rpp:
		maxPage = 0
	elif len(dates) % rpp == 0:
		maxPage = len(dates) / rpp - 1
	else:
		maxPage = len(dates) / rpp
	orig = dims[0]
	more = 0
	while 1:				

		curses.noecho()
		screen.clear()
		dims = screen.getmaxyx()		#get screen dimensions
		screenSizeCheck(dims)
		rpp = (dims[0]-7)/2				#max number results per page
		if orig != dims[0]:				#reset to first page on vertical resize
			page = 0
			y = 5
			x = getCursX(y, rpp, page)
			if len(dates) <= rpp:
				maxPage = 0
			elif len(dates) % rpp == 0:
				maxPage = len(dates) / rpp - 1
			else:
				maxPage = len(dates) / rpp
			orig = dims[0]
						
		
		header(delHeading, screen, dims)
		more = appts(screen, dims, rpp, page) #add sortBy as param
		footer(screen, dims, more)
		
		screen.move(y, x)
		curses.curs_set(1)

		screen.refresh()
		key = screen.getch()
		if key == curses.KEY_DOWN:
			if page < maxPage:
				if y <= rpp*2+1:
					y += 2
					x = getCursX(y, rpp, page)
				else:
					page += 1
					y = 5
					x = getCursX(y, rpp, page)
			#we are on last page here
			else:
				onLast = len(dates) - (rpp * maxPage)
				if y <= onLast*2+1:
					y += 2
					x = getCursX(y, rpp, page)
		if key == curses.KEY_UP:
			if y >= 7:
				y -= 2
				x = getCursX(y, rpp, page)
			else:
				if page > 0:
					page -= 1
					y = 5 + ((rpp - 1)*2)		#set y to bottom of prev page
					x = getCursX(y, rpp, page)
		if key == ord('n') and page < maxPage:
			page += 1
			y = 5
			x = getCursX(y, rpp, page)
		if key == ord('p') and page > 0:
			page -= 1
			y = 5
			x = getCursX(y, rpp, page)
		if key == ord('m'):
			curses.curs_set(0)
			backPage = 'd'
			mainScreen(screen, dims)
		if key == ord('h'):
			curses.curs_set(0)
			backPage = 'd'
			helpScreen(screen, dims)
		if key == ord('a'):
			curses.curs_set(0)
			backPage = 'd'
			addAppointment(screen, dims)
		if key == ord('s'):
			curses.curs_set(0)
			backPage = 'd'
			sortAppts(screen, dims)
		if key == ord('b') and backPage != 'd':
			bP = backPage
			backPage = 'd'
			goBack(screen, dims, bP)
		if key == ord('q'):
			exitApplication()
		if key == ord('d'):
			curses.curs_set(0)
			confirmDelete(y, rpp, page)

	curses.curs_set(0)
	mainScreen(screen, dims)

#confirm you have selected the correct appointment to delete
def confirmDelete(yVal, rpp, page):
	global backPage
	confDelHeading = "Are you sure you wish to DELETE this appointment?"
	delYes = "To confirm DELETE, press 'y'"
	delNo = "To go BACK, press 'b'"
	key = -1
	while key != ord('b'):				#q is used to quit

		screen.clear()
		dims = screen.getmaxyx()		#get screen dimensions
		screenSizeCheck(dims)
		confirmDeleteHeader(confDelHeading, screen, dims)
		n = (dims[1] - 17) / 2
		i = (yVal - 5) / 2 + (page * rpp)
		screen.addstr(5,1, dates[i])
		screen.addstr(5,10,times[i])
		screen.addnstr(5,17,students[i], n)
		screen.addnstr(5,17+n+1,emails[i], n-2)
		screen.hline(6,1, 0, dims[1]-2)
		screen.addstr(7, 5, delYes)
		screen.addstr(8, 5, delNo)
		
		key = screen.getch()
		if key == ord('q'):
			exitApplication()
		if key == ord('m'):
			#do nothing  -no delete
			backPage = 'd'
			mainScreen(screen, dims)
		if key == ord('n'):
			#don't delete
			deleteAppt(screen, dims, rpp, page)
		if key == ord('y'):
			#delete from table
			name = students[i].split(None, 1)
			first = name[0]
			last = name[1]
			time = times[i]
			date = dates[i]
			email = emails[i]
			hour = time[0:2]
			minute = time[3:5]
			seconds = '00'
			mil = '20'
			if time[5] == 'p':
				h = int(hour)
				h += 12
				hour = str(h)
			elif hour == '12' and time[5] == 'a':
				hour = '00'
			time = hour + ":" + minute + ":" + seconds
			year = mil + date[6:]
			month = date[0:2]
			day = date[3:5]
			date = year + "-" + month + "-" + day
			apptTime = date + " " + time
			delSQL = "DELETE FROM Appointments WHERE firstname = '%s' and lastname = '%s' and appointment_time = '%s' and student_email = '%s' and adid = '%d'" % (first, last, apptTime, email, adid)
			try:
				cur.execute(delSQL)
				db.commit()
			except:
				db.rollback()

			backPage = 'd'
			mainScreen(screen, dims) 
	return

#add appointments to server
def addAppointment(screen, dims):
	global backPage
	#strings
	addIntro = "Add a new appointment:"
	
	askFirst = 		"First name: "
	askLast =  		"Last name: "
	
	askYear = 		"Year (yy): "
	askMonth = 		"Month (mm): "
	askDay = 		"Day (dd): "	

	askTime = 		"Time (hh:mm): "
	askMeridiem = 	"AM or PM: "

	askEmail = "Email: "
	
	longStr = len(askTime)

	askStrings = []
	askStrings.extend((askFirst, askLast, askYear, askMonth, askDay,
		askTime, askMeridiem, askEmail))

	cancelCode = 'ccc'
	askClear = "To cancel this add, type '" + cancelCode + "' and hit enter."

	errorMsg = "-Error, that data wasn't formatted correctly."
	clearErr =   "                                               "	#long blank string to overwrite error msg
	confirmAdd = "Press 'y' to enter data, or 'm' to go to main."
	successMsg = "Appointment added successfully."
	navMsg = "Press 'a' to add another, or 'm' to go to main."
	

	instructY = 20
	msgY = 19
	indent = 5
	key = -1
	while 1:
		while 1:
			screen.clear()
			curses.noecho()
			curses.curs_set(0)
			dims = screen.getmaxyx()
			screenSizeCheck(dims)
			screen.border(0)
			screen.addstr(1,1, addIntro)
			screen.hline(2,1,0,dims[1]-2)
			y = 3
			for aStr in askStrings:
				screen.addstr(y, indent, aStr)
				y += 1
				screen.hline(y, indent, 0, dims[1]-1-indent)
				y += 1
			y = 3
			screen.vline(y, indent + longStr, 0, len(askStrings)*2-1)
			x = indent + longStr + 1
			#verify add is correct
			screen.addstr(instructY, indent, confirmAdd)
			#get key to continue
			key = screen.getch()
			if key == ord('q'):
				exitApplication()
			if key == ord('m'):
				backPage = 'a'
				mainScreen(screen, dims)
			if key == ord('n'):				#included as opposite to y for usablity			
				backPage = 'a'
				mainScreen(screen, dims)
			if key == ord('h'):
				backPage = 'a'
				helpScreen(screen, dims)
			if key == ord('d'):
				backPage = 'a'
				deleteAppt(screen, dims, rpp, page)
			if key == ord('s'):
				backPage = 'a'
				sortAppts(screen, dims)
			if key == ord('b') and backPage != 'a':
				bP = backPage
				backPage = 'a'
				goBack(screen, dims, bP)
			if key == ord('y'):
				break
			#on 'y' initialize apptData and move forward
		screen.addstr(instructY, indent, clearErr)
		apptData = []
		for i in range(0, len(askStrings)):
			dims = screen.getmaxyx()
			screenSizeCheck(dims)
			screen.move(y,x)
			curses.curs_set(1)
			curses.echo()
			
			s = screen.getstr(y,x)
			if s == cancelCode:
				curses.curs_set(0)
				curses.noecho()
				addAppointment(screen, dims)
			
			#need prev for full date validation
			prev = []
			#need to send month and year for day validation
			if i == 3:						#if i is day
				prev.append(apptData[2])	#send year
			if i == 4:
				prev.append(apptData[2])
				prev.append(apptData[3])	#send month
			
			#first results test
			testResults = testData(i, s, prev)
			#if fail, print msgs, and keep trying
			while testResults[0] < 0:
				dims = screen.getmaxyx()
				screenSizeCheck(dims)
				screen.addstr(instructY, indent, askClear)
				screen.addstr(msgY, indent, errorMsg)
				j = len(s)
				#delete what was previously written
				while j > 0:
					screen.addch(y, x, ' ')	#to delete char but delchar ruins border
					x += 1
					j -= 1
				#reset x
				x = indent + longStr + 1
				s = screen.getstr(y,x)
				#check if cancelCode
				if s == cancelCode:
					curses.curs_set(0)
					curses.noecho()
					addAppointment(screen, dims)
				#test results again - continue loop
				testResults = testData(i, s, prev)
			#results are good	
			s = testResults[1]
			#add to data to be sent to DB
			apptData.append(s)
			#clear all messages
			screen.addstr(msgY, indent, clearErr)
			screen.addstr(instructY, indent, clearErr)
			#increment y by two
			y += 2

		#reset curses settings
		curses.noecho()
		curses.curs_set(0)
		#send to db here
		#apptData holds data to send
		first = apptData[0]
		last = apptData[1]
		email = apptData[7]
		time = apptData[5]
		hour = time[0:2]
		minute = time[3:]
		seconds = '00'
		mil = '20'
		if apptData[6] == 'PM':
			h = int(hour)
			h += 12
			hour = str(h)
		elif hour == '12' and apptData[6] == 'AM':
			hour = '00'
		time = hour + ":" + minute + ":" + seconds
		year = mil + apptData[2]
		month = apptData[3]
		day = apptData[4]
		date = year + "-" + month + "-" + day
		apptTime = date + " " + time
		insertAppt = "INSERT INTO Appointments (firstname, lastname, student_email, appointment_time, adid) VALUES ('%s', '%s', '%s', '%s', '%d')" % (first, last, email, apptTime, adid)
		try:
			cur.execute(insertAppt)
			db.commit()
		except:
			screen.endwin()
			print "Inserting new appointment failed."
			db.rollback()
			exitApplication()

		#print success msg
		screen.addstr(msgY, indent, successMsg)
		screen.addstr(instructY, indent, navMsg)
		screen.refresh()
		#get keys to navigate
		key = screen.getch()
		dims = screen.getmaxyx()
		screenSizeCheck(dims)
		if key == ord('q'):
			exitApplication()
		if key == ord('h'):
			backPage = 'a'
			helpScreen(screen, dims)
		if key == ord('m'):
			backPage = 'a'
			mainScreen(screen, dims)
		if key == ord('d'):
			backPage = 'a'
			deleteAppt(screen, dims, rpp, page)
		if key == ord('s'):
			backPage = 'a'
			sortAppts(screen, dims)
		if key == ord('b') and backPage != 'a':
			bP = backPage
			backPage = 'a'
			goBack(screen, dims, bP)

	mainScreen(screen, dims)

#data verification for adding to server
#appointments can be added up to 'addDays' days old, but only appts in last 12 hrs will be shown
def testData(type, data, monthYear):
	addDays = 1
	ok = -1
	goodData = ''
	if type == 0:
		#fname
		if not data.isalpha():
			return ok, goodData
		else:
			ok = 1
			goodData = data
	elif type == 1:
		#lname
		if not data.isalpha():
			return ok, goodData
		else:
			ok = 1
			goodData = data
	elif type == 2:
		#year
		try:
			year = int(data)
		except ValueError:
			return ok, goodData
		today = datetime.date.today() - datetime.timedelta(days=addDays)
		thisYear = int(today.strftime('%y'))
		if year < thisYear:
			return ok, goodData
		elif year > 99:
			return ok, goodData
		else:
			goodData = str(year)
			ok = 1
			return ok, goodData 

	elif type == 3:
		#month
		try:
			month = int(data)
		except ValueError:
			return ok, goodData
		#fail returns
		if month < 1:
			return ok, goodData
		elif month > 12:
			return ok, goodData
		tooOld = datetime.date.today() - datetime.timedelta(days=addDays) #get date, seven days ago
		year = int(monthYear[0])
		yearChk = int(tooOld.strftime('%y'))
		monthChk = int(tooOld.strftime('%m'))
		if month < monthChk and year <= yearChk:
			return ok, goodData
		#good returns
		elif month < 10:
			ok = 1
			goodData = '0' + str(month)
			return ok, goodData
		else:
			ok = 1
			goodData = str(month)
			return ok, goodData

	elif type == 4:
		#day
		#check if leap year
		#year and month already valid
		year = int(monthYear[0])
		leap = 0
		if year % 4 == 0:
			leap = 1
		month = int(monthYear[1])
		#validate days in month
		longMonths = [1,3,5,7,8,10,12]	#all have 31 days
		monthType = -1
		if month in longMonths:	#1-31 ok
			monthType = 0
		elif month == 2:		#1-28 only
			monthType = 2
		elif month == 2 and leap == 1: #1-29 ok
			monthType = 3
		else:					#1-30 ok
			monthType = 1

		try:
			day = int(data)
		except ValueError:
			return ok, goodData
		#fail statements
		if day < 1:
			ok = -1
			return ok, goodData
		elif day > 31:				#always bad if more than 31
			ok = -1
			return ok, goodData
		elif day > 28 and monthType == 2:	#fail if feb, not leap year
			ok = -1
			return ok, goodData
		elif day > 29 and monthType == 3:	#fail if feb, is leap year
			return ok, goodData
		elif day > 30 and monthType == 1:	#fail if more than 30, not longMonth
			return ok, goodData
		#check not in past
		tooOld = datetime.date.today() - datetime.timedelta(days=addDays) #get date, seven days ago
		year = '20' + monthYear[0]
		year = int(year)
		thisDate = datetime.date(year, month, day)
		if thisDate < tooOld:
			return ok, goodData
		#data validated
		elif day < 10:
			goodData = '0' + str(day)
			ok = 1
			return ok, goodData
		else:
			goodData = str(day)
			ok = 1
			return ok, goodData
	elif type == 5:
		#time
		if len(data) < 4 or len(data) > 5:
			return ok, goodData
		timeData = data.split(":")
		if len(timeData) != 2:
			return ok, goodData
		try:
			hour = int(timeData[0])
		except ValueError:
			return ok, goodData		
		try:
			minute = int(timeData[1])
		except ValueError:
			return ok, goodData
		if hour < 1:
			return ok, goodData
		elif hour > 12:
			return ok, goodData
		elif hour < 10:
			goodData = '0' + str(hour)
		else:
			goodData = str(hour)

		if minute < 0:
			return ok, goodData
		elif minute > 59:
			return ok, goodData
		elif minute < 10:
			goodData += ':'
			goodData += '0'
			goodData += str(minute)
			ok = 1
			return ok, goodData
		else:
			ok = 1
			goodData += ':'
			goodData += str(minute)
			return ok, goodData
	elif type == 6:
		#meridiem
		goodAM = ['a', 'am', 'AM', 'A', 'Am', 'aM']
		goodPM = ['p', 'P', 'pm', 'pM', 'Pm', 'PM']
		#success cases
		if data in goodAM:
			return 1, 'AM'
		elif data in goodPM:
			return 1, 'PM'
		#fail case
		else:
			return ok, goodData
	elif type == 7:
		#email
		#check for only one @
		#remove whitespace
		noSpaceData = data.replace(" ", "")
		emailData = noSpaceData.split("@")
		if len(emailData) != 2:
			return ok, goodData
		
		#check for at least one dot in second part
		temp = emailData[1].split(".")
		if len(temp) < 2:
			return ok, goodData
		#check for no two dots next to each other ex@bad..com
		dotdot = emailData[1]
		#fail if last char is a dot
		if dotdot[-1] == ".":
			return ok, goodData

		prevDot = 0
		i = 0
		while i < len(dotdot):
			if dotdot[i] == "." and prevDot == 1:
				return ok, goodData
			
			if dotdot[i] == ".":
				prevDot = 1
			else:
				prevDot = 0
			i += 1
		#most basic checking done
		#rebuild email with no whitespace and accept
		email = emailData[0] + "@" + emailData[1]
		ok = 1
		goodData = str(email)
		return ok, goodData

	else:
		curses.endwin()
		print "Error, verification out of range."
		exitApplication()
	
	return ok, goodData

#sorts results by calling for new data from the server based on user input
def sortAppts(screen, dims):
	global sortType
	global backPage
	sortIntro = "How would you like to sort?"

	firstSort = "To sort by FIRST name - "
	firstKey = "press 'f'"
	lastSort = "To sort by LAST name - "
	lastKey = "press 'l'"
	timeSort = "To sort by TIME - "
	timeKey = "press 't'"

	sortStrings = []
	sortStrings.extend((firstSort, lastSort, timeSort))
	keyStrings = []
	keyStrings.extend((firstKey, lastKey, timeKey))

	#used for first and last confirmation
	az = "To sort A - Z - "
	azKey = "press 'a'"
	za = "To sort Z - A - "
	zaKey = "press 'z'"
	#used for time
	close = "To sort time ASCENDING - "
	far = "To sort time DESCENDING - "
	ascKey = "press 'a'"
	desKey = "press 'd'"
	#for erasing
	blank = " "

	indent = 5
	y = 3
	key = -1
	while 1:
		screen.clear()
		curses.noecho()
		curses.curs_set(0)
		dims = screen.getmaxyx()
		screenSizeCheck(dims)
		screen.border(0)
		screen.addstr(1,1, sortIntro)
		screen.hline(2,1,0,dims[1]-2)
		y = 3
		for aStr in sortStrings:
			screen.addstr(y, indent, aStr)
			y += 1
			screen.hline(y, indent, 0, dims[1]-2-indent)
			y += 1
		y = 3
		x = indent + len(far)
		screen.vline(y, x, 0, len(sortStrings)*2-1)
		x += 2
		for keyStr in keyStrings:
			screen.addstr(y, x, keyStr)
			y += 1
			screen.hline(y, indent, 0, dims[1]-2-indent)
			y += 1
		x = indent
		screen.refresh()
		key = screen.getch()
		if key == ord('q'):
			exitApplication()
		if key == ord('h'):
			backPage = 's'
			helpScreen(screen, dims)
		if key == ord('m'):
			backPage = 's'
			mainScreen(screen, dims)
		if key == ord('d'):
			backPage = 's'
			deleteAppt(screen, dims, rpp, page)
		if key == ord('a'):
			backPage = 's'
			addAppointment(screen, dims)
		if key == ord('b') and backPage != 's':
			bP = backPage
			backPage = 's'
			goBack(screen, dims, bP)
		if key == ord('f'):
			#ask for type of sort (ascending/descending)
			screen.addstr(y, x, "Sorting by FIRST name:")
			y += 1
			screen.hline(y, x, 0, dims[1]-2-indent)
			y += 1
			screen.addstr(y, x, az)
			y += 1
			screen.hline(y, x, 0, dims[1]-2-indent)
			y += 1
			screen.addstr(y, x, za)
			y += 1
			screen.hline(y, x, 0, dims[1]-2-indent)
			#edit
			y -= 3
			x = indent + len(far)
			screen.vline(y, x, 0, 3)
			x += 2
			screen.addstr(y, x, azKey)
			y += 2
			screen.addstr(y, x, zaKey)
			y += 1
			x = indent
			screen.refresh()
			while 1:
				key = screen.getch()
				if key == ord('a'):
					#sort by first name a-z
					sortType = 'fa'
					backPage = 's'
					mainScreen(screen, dims)
				if key == ord('z'):
					#sort by first name z-a
					sortType = 'fz'
					backPage = 's'
					mainScreen(screen, dims)
				if key == ord('q'):
					exitApplication()
				if key == ord('b'):
					#erase and return to main sort
					i = 0
					j = 0
					while i < 5:
						while j <= dims[1]-2-indent:
							screen.addstr(y, x, blank)
							x += 1
							j += 1
						x = indent
						y -= 1
						i += 1
					screen.refresh()
					key = -1
					break

		if key == ord('l'):
			screen.addstr(y, x, "Sorting by LAST name:")
			y += 1
			screen.hline(y, x, 0, dims[1]-2-indent)
			y += 1
			screen.addstr(y, x, az)
			y += 1
			screen.hline(y, x, 0, dims[1]-2-indent)
			y += 1
			screen.addstr(y, x, za)
			y += 1
			screen.hline(y, x, 0, dims[1]-2-indent)
			y -= 3
			x = indent + len(far)
			screen.vline(y, x, 0, 3)
			x += 2
			screen.addstr(y, x, azKey)
			y += 2
			screen.addstr(y, x, zaKey)
			y += 1
			x = indent
			screen.refresh()
			while 1:
				key = screen.getch()
				if key == ord('a'):
					#sort by last name a-z
					sortType = 'la'
					backPage = 's'
					mainScreen(screen, dims)
				if key == ord('z'):
					#sort by last name z-a
					sortType = 'lz'
					backPage = 's'
					mainScreen(screen, dims)
				if key == ord('q'):
					exitApplication()
				if key == ord('b'):
					#erase and return to main sort
					i = 0
					j = 0
					while i < 5:
						while j <= dims[1]-2-indent:
							screen.addstr(y, x, blank)
							x += 1
							j += 1
						x = indent
						y -= 1
						i += 1
					screen.refresh()
					key = -1
					break

		if key == ord('t'):
			screen.addstr(y, x, "Sorting by TIME:")
			y += 1
			screen.hline(y, x, 0, dims[1]-2-indent)
			y += 1
			screen.addstr(y, x, close)
			y += 1
			screen.hline(y, x, 0, dims[1]-2-indent)
			y += 1
			screen.addstr(y, x, far)
			y += 1
			screen.hline(y, x, 0, dims[1]-2-indent)
			y -= 3
			x = indent + len(far)
			screen.vline(y, x, 0, 3)
			x += 2
			screen.addstr(y, x, ascKey)
			y += 2
			screen.addstr(y, x, desKey)
			y += 1
			x = indent
			screen.refresh()
			while 1:
				key = screen.getch()
				if key == ord('a'):
					#sort by time asc
					sortType = 'ta'
					backPage = 's'
					mainScreen(screen, dims)
				if key == ord('d'):
					#sort by time des
					sortType = 'td'
					backPage = 's'
					mainScreen(screen, dims)
				if key == ord('q'):
					exitApplication()
				if key == ord('b'):
					#erase and return to main sort
					i = 0
					j = 0
					while i < 5:
						while j <= dims[1]-2-indent:
							screen.addstr(y, x, blank)
							x += 1
							j += 1
						x = indent
						y -= 1
						i += 1
					screen.refresh()
					key = -1
					break
	return sortType

#backPage keeps track of previous page, this returns there on 'b' press
def goBack(screen, dims, backPage):
	curses.noecho()
	curses.curs_set(0)
	if backPage == 'm':
		mainScreen(screen, dims)
	elif backPage == 'h':
		helpScreen(screen, dims)
	elif backPage == 'a':
		addAppointment(screen, dims)
	elif backPage == 'd':
		deleteAppt(screen, dims, rpp, page)
	elif backPage == 's':
		sortAppts(screen, dims)
	else:
		curses.endwin()
		print "Something went wrong with the backPage value."
		exitApplication()

#gets data from mysql server, stores in lists
def getApptData(sortType):
	global students
	global dates
	global times
	global emails
	#clear all globals
	students = []
	dates = []
	times = []
	emails = []
	#locals
	fname = []
	lname = []
	datetimes = []

	#appointments will only be shown that are in the future or 12 hours behind present time
	displayTime = datetime.datetime.today() - datetime.timedelta(hours=12)
	showTime = displayTime.strftime('%Y-%m-%d %H:%M:%S')

	#get data from server
	#decide statment based on sortType
	if sortType == 'fa':
		selectAppts = "SELECT firstname, lastname, appointment_time, student_email FROM Appointments WHERE adid = '%d' and appointment_time > '%s' ORDER BY firstname ASC" % (adid, showTime)
	elif sortType == 'fz':
		selectAppts = "SELECT firstname, lastname, appointment_time, student_email FROM Appointments WHERE adid = '%d' and appointment_time > '%s' ORDER BY firstname DESC" % (adid, showTime)
	elif sortType == 'la':
		selectAppts = "SELECT firstname, lastname, appointment_time, student_email FROM Appointments WHERE adid = '%d' and appointment_time > '%s' ORDER BY lastname ASC" % (adid, showTime)
	elif sortType == 'lz':
		selectAppts = "SELECT firstname, lastname, appointment_time, student_email FROM Appointments WHERE adid = '%d' and appointment_time > '%s' ORDER BY lastname DESC" % (adid, showTime)
	elif sortType == 'td':
		selectAppts = "SELECT firstname, lastname, appointment_time, student_email FROM Appointments WHERE adid = '%d' and appointment_time > '%s' ORDER BY appointment_time DESC" % (adid, showTime)
	else:
		selectAppts = "SELECT firstname, lastname, appointment_time, student_email FROM Appointments WHERE adid = '%d' and appointment_time > '%s' ORDER BY appointment_time ASC" % (adid, showTime)
		#SELECT firstname, lastname, appointment_time, student_email FROM Appointments WHERE adid = 9 and appointment_time > "2014-11-24 18:00:00" ORDER BY appointment_time ASC
	#run query
	try:
		cur.execute(selectAppts)
	except:
		print "Unable to select data from server."
		exit(1)
	serverData = cur.fetchall()
	n = 0
	if not serverData:
		print "No data."
		students = []
		dates = []
		times = []
	else:
		for row in serverData:
			fname.append(row[0])
			lname.append(row[1])
			datetimes.append(row[2])
			emails.append(row[3])
	#format into students, dates, times
	n = 0
	while n < len(fname):
		#put fname, lname into students
		f = str(fname[n])
		l = str(lname[n])
		st = f + " " + l
		students.append(st)
		#get date
		dt = datetimes[n]
		dates.append(dt.strftime('%m/%d/%y'))
		t = dt.strftime('%H:%M')
		getMer = int(t[0:2])
		if getMer < 12:
			mer = 'a'
		else:
			mer = 'p'
		t = dt.strftime('%I:%M')
		t += mer
		times.append(t)
		n += 1
	return

#ensures screen is sufficiently large enough to run without crashing
def screenSizeCheck(dims):
	if dims[0] < minYsize or dims[1] < minXsize:
		curses.endwin()
		print "Your terminal window is too small to run this application."
		print "Please increase the size of your terminal and try again."
		print "The terminal size must be at least " + str(minXsize) + "x" + str(minYsize)
		print "The application was forced to close."
		exitApplication()
	else:
		return

#cleans out old appointments from the database - if older than 120 days, they are deleted
def cleanOldData():
	oldestOk = datetime.datetime.today() - datetime.timedelta(days=120)
	thresholdTime = oldestOk.strftime('%Y-%m-%d %H:%M:%S')
	cleanSQL = "DELETE FROM Appointments WHERE appointment_time < '%s'" % (thresholdTime)
	try:
		cur.execute(cleanSQL)
		db.commit()
	except:
		db.rollback()

#returns the advisor id which will be a global variable
def getAdid():
	#sql statements for username:
	selectADID = "SELECT id FROM Advisors WHERE username = '%s'" % (username)
	insertUser = "INSERT INTO Advisors (username) VALUES ('%s')" % (username)
	#try and get adid
	try:
		cur.execute(selectADID)
	except:
		print "Unable to select data from server."
		exit(1)
	#store results in r (currently as tuple)
	r = cur.fetchone()
	#if nothing in r - user not yet in db
	if not r:
		#add user to db
		try:
			cur.execute(insertUser)
			db.commit()
		except:
			print "Inserting new user failed."
			db.rollback()
			exit(1)
		#get new adid
		cur.execute(selectADID)
		#store in r
		r = cur.fetchone()

	#cast adid as int - r is a tuple, first is adid
	adid = int(r[0])
	return adid

#main
#connect to db - have db and cur as globals
myHost = 'mysql.cs.orst.edu'
myUser = 'cs419-group0'
myPass = 'A8bHZBpG6WWhT2Zj'
myDBname = 'cs419-group0'

#establish connection
try:
	db = MySQLdb.connect(host=myHost, user=myUser, passwd=myPass, db=myDBname)
except MySQLdb.Error as e:
	print type(e).__name__ + ": #" + str(e.args[0])
	print e.args[1]
	print "Could not connect to MySQL database."
	exit(1)

#get cursor
try:
	cur = db.cursor() #now connected with cursor object cur
except MySQLdb.Error as e:
	print type(e).__name__ + ": #" + str(e.args[0])
	print e.args[1]
	print "Could not establish MySQL cursor."
	exit(1)

#remove appointments more than 120 days old
cleanOldData()
#set global adid
adid = getAdid()

#initiate curses cli - screen, dims and key as globals
screen = curses.initscr()	#start a new screen
curses.curs_set(0)			#doesn't work with cygwin
screen.keypad(1)			#allow for arrow keys and escape sequences
curses.noecho()				#don't show key presses
dims = screen.getmaxyx()	#get screen dimensions
screenSizeCheck(dims)
#global variables for current page and results per page
page = 0
rpp = (dims[0]-7)/2 #7 is headings and borders

#run program
mainScreen(screen, dims)
#end program
exitApplication()
