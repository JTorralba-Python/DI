import os
import socket   
import arcpy
from Tkinter import *

WKSP = arcpy.env.workspace = arcpy.GetParameterAsText(0)

root = Tk()
root.title("Database Information")
root.geometry("640x480")

SBH = Scrollbar(root, orient=HORIZONTAL)
SBH.pack(side=BOTTOM, fill=X)

SBV = Scrollbar(root, orient=VERTICAL)
SBV.pack(side=RIGHT, fill=Y)

TXT = Text(root, wrap=NONE, xscrollcommand=SBH.set, yscrollcommand=SBV.set)
TXT.pack(expand=TRUE, fill=BOTH)
TXT.bind("<Configure>", lambda e: TXT.configure(width=e.width-10))
TXT.tag_configure('Header', foreground='Blue')
TXT.tag_configure('Error', foreground='Red')

SBH.config(command=TXT.xview)
SBV.config(command=TXT.yview)

def Header(String):
    TXT.insert(END, '%s\n' % String.rstrip(), 'Header')
    TXT.see(END)
    TXT.pack()
    TXT.update_idletasks()
    return;

def Console(String):
    TXT.insert(END, '%s\n' % String.rstrip())
    TXT.see(END)
    TXT.pack()
    TXT.update_idletasks()
    return;

def Except(String):
    TXT.insert(END, '%s\n' % String.rstrip(), 'Error')
    TXT.see(END)
    TXT.pack()
    TXT.update_idletasks()
    return;

def Start():
    Header('Connection Properties:')
    Console('')
    try:
        Describe = arcpy.Describe(WKSP)
        CP = Describe.connectionProperties

        Console('%-40s %s' % ('SERVER', CP.server.upper()))
        Console('%-40s %s' % ('INSTANCE:', CP.instance.upper()))

        global Database
        Database = CP.database
        Console('%-40s %s' % ('DATABASE:', Database))

        V = CP.version.upper().split('.')
        global Schema
        Schema = V[0]
        Version = V[1]
        Console('%-40s %s' % ('VERSION:', Version))

        if CP.authentication_mode == 'DBMS':
            Console('%-40s %s' % ('USER(DB):', CP.user.upper()))
        else:
            User = socket.getfqdn().split('.')[1].upper() + '\\' + os.getenv('username').upper()
            Console('%-40s %s' % ('USER(OS):', User))
        Console('')

        if Version == 'DEFAULT':
            Start2()
        else:
            Except('    VERSION must be "DEFAULT" to see all users connected to database.')
    except:
        Except('    Invalid SDE configuration file.')

def Start2():
    Header('Connected Clients:')
    Console('')
    try:
        SQL_Execute = arcpy.ArcSDESQLExecute(WKSP)
        if Schema == 'DBO':
            SQL_Select = "select distinct host_name, login_name from sys.dm_exec_sessions where database_id = (select database_id from sys.databases where name = '" + Database + "') order by login_name, host_name"
        else:
            SQL_Select = "select distinct host_name, login_name from sys.dm_exec_sessions where program_name like 'SDE%' order by login_name, host_name"
        views = SQL_Execute.execute(SQL_Select)
        for row in views:
            (Host, Login) = row
            Console(str(Login).upper() + ' on ' + str(Host).upper())
    except:
        Except('    "SYS.DM.EXEC_SESSIONS" access restricted.')
    finally:
        Console('')

    Header('Compression Status:')
    Console('')
    try:
        SQL = 'compress_end >= DATEADD(day,-15, GETDATE())'
        with arcpy.da.SearchCursor(Schema+'.SDE_compress_log', ('compress_start','compress_end','compress_status'), SQL) as cursor:
            for row in cursor:
                (CB, CE, CS) = row
                Console('%-40s %s' % (str(CE).split('.')[0], CS))
    except:
        Except('    "SDE_COMPRESS_LOG" access restricted.')
    finally:
        Console('')

    Header('Version State_ID:')
    Console('')
    try:
        with arcpy.da.SearchCursor(Schema+'.SDE_versions', ('name','state_id')) as cursor:
            for row in cursor:
                (VER, SID) = row
                Console("%-40s %s" % (str(VER).upper(), str(SID).split('.')[0]))
    except:
        Except('    "SDE_VERSIONS" access restricted.')

TXT.after(0,Start)
root.mainloop()
