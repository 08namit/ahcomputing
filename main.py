
import sqlite3
import time
import tkinter as tk
from tkinter import messagebox



# FR2

# Class definition for task object
class Task():
    taskID: int
    title: str
    due: int
    duration: int
    difficulty: int
    priority: float



# FR6

# Function to run query on calendar.db database
def runQuery(query):
    try:
        # Connect to database
        conn = sqlite3.connect("calendar.db")
        cursor = conn.cursor()

        # Execute query
        cursor.execute(query)

        # Save changes and close
        conn.commit()
        conn.close()

        return True
    
    # Query execution error
    except sqlite3.Error as error:
        return False


# Function to fetch data from calendar.db database
def fetchQuery(query):
    # Connect to database
    conn = sqlite3.connect("calendar.db")
    cursor = conn.cursor()

    # Execute query and fetch data
    cursor.execute(query)
    rows = cursor.fetchall()

    # Close connection and return data
    conn.close()
    return rows


# Function to fetch all data from Task table
def fetchTasks():
    # Fetch all data from Task table
    taskData = fetchQuery("SELECT * FROM Task;")

    # Initialise array of records to store all tasks
    taskArray = [Task() for i in range(len(taskData))]
    
    # Sync array of records with Task table
    for i in range(len(taskData)):
        taskArray[i].taskID = taskData[i][0]
        taskArray[i].title = taskData[i][1]
        taskArray[i].due = taskData[i][2]
        taskArray[i].duration = taskData[i][3]
        taskArray[i].difficulty = taskData[i][4]
        taskArray[i].priority = taskData[i][5]
    
    # Return array of records
    return taskArray



# FR5

# Function to create tables if they do not already exist
def tableCreation():
    # Creates Task table if not already there
    status = runQuery("""
    CREATE TABLE IF NOT EXISTS Task (
        taskID INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL CHECK (LENGTH(title) BETWEEN 1 AND 100),
        due INTEGER NOT NULL CHECK (due > 0),
        duration INTEGER NOT NULL CHECK (duration > 0),
        difficulty INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
        priority REAL NOT NULL
    );
    """)

    # Query error checking (same for all status variables)
    if not status:
        print()
        print("Query unsucessful")
        print()

    # Creates Task table if not already there
    status = runQuery("""
    CREATE TABLE IF NOT EXISTS Event (
        eventID INTEGER PRIMARY KEY AUTOINCREMENT,
        eventType TEXT NOT NULL CHECK (eventType IN ('task', 'commitment')),
        title TEXT NOT NULL CHECK (LENGTH(title) BETWEEN 1 AND 100),
        start INTEGER NOT NULL CHECK (start > 0),
        end INTEGER NOT NULL CHECK (end > 0),
        taskID INTEGER,
        FOREIGN KEY (taskID) REFERENCES Task(taskID)
    );
    """)

    # Query error checking
    if not status:
        print()
        print("Query unsucessful")
        print()



# FR15

# Converts datetime in YYYY-mm-dd HH:MM format to epoch timestamp
def DTToTS(value):
    try:
        obj = time.strptime(value, "%Y-%m-%d %H:%M")
        return int(time.mktime(obj))

    # Conversion error
    except ValueError:
        return None
    

# Converts epoch timestamp to datetime in YYYY-mm-dd HH:MM format
def TStoDT(value):
    try:
        obj = time.strftime("%Y-%m-%d %H:%M", time.localtime(value))
        return obj
    
    # Conversion error
    except ValueError:
        return None

    
# Function to check overlaps with other commitments when one is being added/edited
def checkOverlaps(tsStart, tsEnd, excludeID=None):
    # Fetch all event times and ids in chronological order
    eventTimes = fetchQuery("SELECT eventID, start, end FROM Event WHERE eventType = 'commitment' ORDER BY start ASC;")
    
    # Ensure end time is after start time
    if tsEnd <= tsStart:
        return False

    # Loop through all events
    for eventID, eventStart, eventEnd in eventTimes:

        # Check for overlaps with commitments (apart from original one where applicable)
        if tsStart < eventEnd and tsEnd > eventStart and eventID != excludeID:
            return False
        
    return True



# FR3/4

# Bubble sort algorithm to sort tasks in descending priority
def sortTasks(taskData):
    swap = True
    n = len(taskData)
    while swap:
        swap = False
        
        for i in range(n-1):

            # Sorting in descending order, so i priority < i+1 priority to trigger
            if taskData[i].priority < taskData[i+1].priority:
                taskData[i], taskData[i+1] = taskData[i+1], taskData[i]
                swap = True
                
        n -= 1
    
    # Return sorted task data
    return taskData



# FR13

# Function to calculate priority value of a task
def priority(tsDue, duration, difficulty, tsNow):
    # Use parameter values to calculate priority value
    daysTillDue = (tsDue - tsNow) / 86400
    priorityValue = (duration * difficulty) / (daysTillDue + 1)

    # Return calculated priority value
    return priorityValue


# Function to find first gap between events large enough to accomodate a task
def findGap(length, tsNow):
    # Fetch all event times in chronological order
    eventData = fetchQuery(f"SELECT start, end FROM Event WHERE end > {tsNow} ORDER BY start ASC;")

    # Loop to find gap between events
    for i in range(len(eventData)-1):
        gap = eventData[i+1][0] - eventData[i][1]
        
        # If valid gap found, return start time of gap
        if gap >= length:
            return eventData[i][1]
    
    # If there were no gaps between events large enough, return time after last event
    if len(eventData) > 0:
        return eventData[len(eventData)-1][1]
    
    # No events means a task cannot be arranged around events
    return None


# Function to reschedule all tasks when there is a change in the calendar
def reschedule():

    # Fetch all data from Task table and sync with taskData array of records
    taskData = fetchTasks()

    # Calculate the priority values for each task
    tsNow = int(time.time())
    for i in range(len(taskData)):
        taskData[i].priority = priority(
            taskData[i].due,
            taskData[i].duration,
            taskData[i].difficulty,
            tsNow
        )

    # Remove all tasks from Event table to allow for rescheduling
    status = runQuery("DELETE FROM Event WHERE eventType = 'task';")

    if not status:
        print("Rescheduling query error")

    # Sort all tasks in order of descending priority
    taskData = sortTasks(taskData)

    # Loop through all tasks
    for t in taskData:

        # Find first gap for task
        start = findGap(t.duration, tsNow)

        if start != None:

            end = start + t.duration

            status = runQuery(f"UPDATE Task SET priority = {t.priority} WHERE taskID = {t.taskID};")

            if not status:
                print("Rescheduling query error")

            # Schedule into the calendar
            status = runQuery(f"""
                INSERT INTO Event (eventType, title, start, end, taskID) 
                VALUES ('task', '{t.title}', {start}, {end}, {t.taskID});
            """)

            if not status:
                print("Rescheduling query error")



# FR14

# Function to check event title
def checkTitle(title):
    # Check title is 1-100 character string
    if type(title) == str:
        if len(title) >= 1 and len(title) <= 100:
            return True
        
    return False


# Function to check task difficulty
def checkDifficulty(strDifficulty):
    # Check if difficulty string can be converted into integer and between 1-5
    try:
        difficulty = int(strDifficulty)
        if difficulty >= 1 and difficulty <= 5:
            return True
        
        return False
    
    except ValueError:
        return False
    

# Function to check task duration
def checkDuration(strDuration):
    # Check if duration string can be converted into integer and greater than 0
    try:
        duration = int(strDuration)
        if duration > 0:
            return True
        
        return False
    
    except ValueError:
        return False
    

# Function to check eventID
def checkID(strID, eventType):
    try:
        idValue = int(strID)
        data = [] 

        if eventType == "commitment":
            data = fetchQuery(f"SELECT * FROM Event WHERE eventID = {idValue} AND eventType = 'commitment';")

        elif eventType == "task":
            data = fetchQuery(f"SELECT * FROM Event WHERE eventID = {idValue} AND eventType = 'task' AND taskID IS NOT NULL;")

        # Ensure exactly one record with the corresponding eventID exists
        if len(data) == 1:
            return True
        
        return False
    
    except ValueError:
        return False



# FR8

# Function to add new commitment
def addCommitment(title, start, end):
    tsStart = DTToTS(start)
    tsEnd = DTToTS(end)


    # Input validation
    if not checkTitle(title):
        return False, "Invalid title"

    if tsStart == None or tsEnd == None:
        return False, "Invalid start or end datetime (formatting or value issue)"
    
    if checkOverlaps(tsStart, tsEnd) == False:
        return False, "Invalid start or end datetime (overlapping or start >= end)"
       
    # Add new commitment to Event table
    status = runQuery(f"""
        INSERT INTO Event (eventType, title, start, end)
        VALUES ('commitment', '{title}', {tsStart}, {tsEnd});
    """)

    if not status:
        return False, "Query unsucessful"

    # Reschedule all events (called anytime the calendar is changed)
    reschedule()

    return True, ""



# FR9

# Function to add new task
def addTask(title, due, strMinutes, strDifficulty): 
    tsDue = DTToTS(due)
    tsNow = int(time.time())

    # Input validation
    if not checkTitle(title):
        return False, "Invalid title"
    
    if tsDue == None:
        return False, "Invalid due datetime (formatting or value issue)"
    
    if tsDue <= tsNow:
        return False, "Invalid due datetime (in the past)"
    
    if not checkDuration(strMinutes):
        return False, "Invalid duration"
    
    if not checkDifficulty(strDifficulty):
        return False, "Invalid difficulty"
    
    duration = int(strMinutes) * 60
    difficulty = int(strDifficulty)


    # Add new task to Task table
    status = runQuery(f"""
        INSERT INTO Task (title, due, duration, difficulty, priority) 
        VALUES ('{title}', {tsDue}, {duration}, {difficulty}, 0.0);         
    """)

    if not status:
        return False, "Query unsucessful"

    reschedule()
    return True, ""



# FR10

# Function to edit commitment
def editCommitment(strID, title, start, end):
    # Validate eventID
    if not checkID(strID, "commitment"):
        return False, "Invalid id"
    
    idValue = int(strID)

    # Fill in empty fields with original data
    currentCommitment = fetchQuery(f"SELECT title, start, end FROM Event WHERE eventID = {idValue};")

    if title == "":
        title = currentCommitment[0][0]

    if start == "":
        start = TStoDT(currentCommitment[0][1])

    if end == "":
        end = TStoDT(currentCommitment[0][2])

    tsStart = DTToTS(start)
    tsEnd = DTToTS(end)

    # Input validation
    if not checkTitle(title):
        return False, "Invalid title"

    if tsStart == None or tsEnd == None:
        return False, "Invalid start or end datetime (formatting or value issue)"
    
    if checkOverlaps(tsStart, tsEnd, excludeID=idValue) == False:
        return False, "Invalid start or end datetime (overlapping or start >= end)"
    
    # Update commitment in Event table
    status = runQuery(f"""
        UPDATE Event
        SET title = '{title}', start = {tsStart}, end = {tsEnd}
        WHERE eventID = {idValue};
    """)

    if not status:
        return False, "Query unsucessful"

    reschedule()
    return True, ""



# FR11

def editTask(strID, title, due, strMinutes, strDifficulty):
    # Validate eventID
    if not checkID(strID, "task"):
        return False, "Invalid id"
    
    eventID = int(strID)

    # Find corresponding taskID
    taskID = fetchQuery(f"SELECT taskID FROM Event WHERE eventID = {eventID}")[0][0]
    currentTask = fetchQuery(f"SELECT title, due, duration, difficulty FROM Task WHERE taskID = {taskID};")

    # Fill in empty fields with original data
    if title == "":
        title = currentTask[0][0]

    if due == "":
        due = TStoDT(currentTask[0][1])

    if strMinutes == "":
        strMinutes = str(int(currentTask[0][2] / 60))

    if strDifficulty == "":
        strDifficulty = str(currentTask[0][3])

    tsDue = DTToTS(due)
    tsNow = int(time.time())

    if not checkTitle(title):
        return False, "Invalid title"
    
    if tsDue == None:
        return False, "Invalid due datetime (formatting or value issue)"
    
    if tsDue <= tsNow:
        return False, "Invalid due datetime (in the past)"
    
    if not checkDuration(strMinutes):
        return False, "Invalid duration"
    
    if not checkDifficulty(strDifficulty):
        return False, "Invalid difficulty"
    
    duration = int(strMinutes) * 60
    difficulty = int(strDifficulty)

    # Update task in Task table
    status = runQuery(f"""
        UPDATE Task
        SET title = '{title}', due = {tsDue}, duration = {duration}, difficulty = {difficulty}
        WHERE taskID = {taskID};
    """)

    if not status:
        return False, "Query unsucessful"

    reschedule()
    return True, ""



# FR12

# Function to remove event
def removeEvent(strID):
    # Check event type
    if checkID(strID, "commitment"):
        eventID = int(strID)

        # Remove commitment from Event table
        status = runQuery(f"DELETE FROM Event WHERE eventID = {eventID};")

        if not status:
            return False, "Query unsucessful"
            
        reschedule()
        
    elif checkID(strID, "task"):
        eventID = int(strID)

        # Find corresponding taskID
        taskID = fetchQuery(f"SELECT taskID FROM Event WHERE eventID = {eventID}")[0][0]

        # Remove task from Event table
        status = runQuery(f"DELETE FROM Event WHERE eventID = {eventID};")

        if not status:
            return False, "Query unsucessful"

        # Remove task from Task table
        status = runQuery(f"DELETE FROM Task WHERE taskID = {taskID};")

        if not status:
            return False, "Query unsucessful"
            
        reschedule()

    else:
        return False, "Invalid id"
    
    return True, ""
    

    
# FR7

# Function to view all events
def viewEvents():
    # Fetch all data
    eventData = fetchQuery("SELECT * FROM Event ORDER BY start ASC;")

    print("Events:")
    print("eventID - type - title - start - end")

    # Loop through each row in eventData and display all details
    for e in eventData:
        print(e[0], "-", e[1], "-", e[2], "-", TStoDT(e[3]), "-", TStoDT(e[4]))


info = """
Menu options:
info - view program functions and input formats
addc - add new commitment
addt - add new task
editc - edit commitment
editt - edit task
remove - remove commitment
view - view all events
quit - quit program

Input formats:
title format - maximum 100 characters
datetime format - YYYY-MM-DD hh:mm
difficulty format - integer, 1-5
id format - as appears when viewing events
duration format - integer, number of minutes

When editing an event, leave a field blank if you do not want to edit it.
"""



# FR1/7

# User interface
def mainProgram():
    userInput = ""
    print()
    print("Welcome to the Smart Calendar")
    print("Enter info for a list of program functions and input formats")
    print()

    # Create tables if not already existing
    tableCreation()

    while userInput != "quit":
        userInput = input("> ")

        # Display information on how to use the program
        if userInput == "info":
            print(info)

        # Add new commitment
        elif userInput == "addc":
            print()
            print("Add new commitment")
            title = input("enter title > ")
            start = input("enter start datetime > ")
            end = input("enter end datetime > ")
            status, msg = addCommitment(title, start, end)

            print()

            if status:
                print("Successful!")
            else:
                print(msg)

            print()

        # Add new task
        elif userInput == "addt":
            print()
            print("Add new task")
            title = input("enter title > ")
            due = input("enter due datetime > ")
            minutes = input("enter duration > ")
            difficulty = input("enter difficulty > ")
            status, msg = addTask(title, due, minutes, difficulty)

            print()

            if status:
                print("Successful!")
            else:
                print(msg)

            print()

        # Edit commitment
        elif userInput == "editc":
            print()
            print("Edit commitment")
            id = input("enter id > ")
            title = input("enter new title > ")
            start = input("enter new start datetime > ")
            end = input("enter new end datetime > ")
            status, msg = editCommitment(id, title, start, end)
            print()

            if status:
                print("Successful!")
            else:
                print(msg)

            print()

        # Edit task
        elif userInput == "editt":
            print()
            print("Edit task")
            id = input("enter id > ")
            title = input("enter new title > ")
            due = input("enter new due datetime > ")
            minutes = input("enter duration > ")
            difficulty = input("enter new difficulty > ")
            status, msg = editTask(id, title, due, minutes, difficulty)
            print()

            if status:
                print("Successful!")
            else:
                print(msg)

            print()

        # Remove event
        elif userInput == "remove":
            print()
            print("Remove event")
            id = input("enter id > ")
            status, msg = removeEvent(id)
            print()

            if status:
                print("Successful!")
            else:
                print(msg)

            print()

        # View all events
        elif userInput == "view":
            print()
            viewEvents()
            print()

        # Invalid input
        elif userInput != "quit":
            print()
            print("Invalid input")
            print()
        
mainProgram()