import logging
import sys
import threading
import time
import tkinter as tk
from random import randint
from tkinter import BOTH, LEFT, RIGHT, IntVar, StringVar, Text, messagebox, ttk
import pickle,os
import keyboard as kb
from queue import Queue

#logger to log in errors
logging.basicConfig(
    handlers=[logging.FileHandler('logfile.log', 'w', 'utf-8')],
    format='%(levelname)s: %(asctime)s: %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.DEBUG #CRITICAL ERROR WARNING  INFO    DEBUG    NOTSET 
)

class App(tk.Frame):
    def __init__(self):
        super().__init__()
        self.initGUI()      #intialize gui
        self.setCenter()    #default position of form
        
    
    def initGUI(self):

        self.color="dodger blue"
        self.master.title("AutoTyperPRO")
        self.pack(fill=BOTH,expand=True)
        self.grid(padx=20,pady=2,sticky="we")
        self.master.configure(bg=self.color)
        self.configure(bg=self.color)
        
        #various variables for tracking
        self.focused=""     #save latest focused entry
        self.entries = ""   #save all created entry boxes
        self.event = ""     #threading wait event
        self.textvar=[]     #text variable for entry box
        self.running= False #variable to stop loop function inside texttype 
        self.runningThreads=[]#save all created threads for access
        self.sendEnter=IntVar(value=0) #Tracking send Enter key or not
        self.logIt= IntVar(value=0)
        #create StringVar list to attach with entry        
        [self.textvar.append([StringVar() for j in range(0,4)]
                        ) for i in range(0,5)]  # pupulate text variable with StringVar
        #create tasks
        self.tasks = ""      # Queue(maxsize=0)
        
        
        #Heading Labels         
        tk.Label(self,text='Text',background="dodger blue",font=("Verdana",15)).grid(row=0,column=0,padx=5)
        tk.Label(self,text='Interval Delay \nSeconds(10-3600)',background=self.color,font=("Verdana",15)).grid(row=0,column=1,padx=7)
        tk.Label(self,text='Random \n Threshhold-MS(100-10000)\nStart        End',background=self.color,font=("Verdana",15)).grid(row=0,column=2,columnspan=3,sticky="ew")
                        
        #function to generate entry fields
        
        def makeentry(parent,howmany,pos, width=None,caption=None,textvariable=None,font=None,**options):
            #Label(parent, text=caption).grid(row=pos[0],column=pos[1])
            
            entries=[] #save all entry box
            for i in range(0,howmany):
                temp=[]#temporary saving entry box
                for j in range(0,4):
                    if j ==3:
                        tk.Label(self,text="___",background="dodger blue").grid(row=pos[0]+i+1,column=pos[1]+j)
                        entry=tk.Entry(parent,width=width[j] ,textvariable=textvariable[i][j],font=font,**options)
                        entry.grid(row=pos[0]+i+1,column=pos[1]+j+1,padx=10,pady=5,ipadx=2,ipady=3)
                        temp.append(entry)
                    else:                       
                        entry=tk.Entry(parent,width=width[j] ,textvariable=textvariable[i][j],font=font, **options)
                        entry.grid(row=pos[0]+i+1,column=pos[1]+j,padx=10,pady=5,ipadx=2,ipady=3)
                        temp.append(entry)

                entries.append(temp)
            return entries
        
        #data  saved in file
        def saveData(data):
            try:

                with open("data.txt","wb") as fl:
                    pickle.dump(data,fl)
            except TypeError as e:
                logging.info("Data Can't be saved",e)
        
        #load data from file

        def loadData():
            data=""
            try:
                with open('data.txt',"rb") as fl:
                    if os.path.getsize("data.txt")>0:
                        data = pickle.load(fl)
                        for i,dt in enumerate(data):
                            for j in range(0,4):
                                self.textvar[i][j].set(data[i][j])
                            
            except FileNotFoundError:
                pass    


        #validate and populate data
        def populateData():
            entrybox =["Text","Seconds","MS-Start","MS-End"]
            Empty = False
            data=[]
            count =0
            for i in range(0,5):
                temp=[]
                val = self.textvar[i][0].get()
                print(val)
                if not  val =="":
                    
                    vals =self.textvar[i][1:4]
                    temp.append(val)
                    
                    
                    for j,val in enumerate(vals):
                        val=val.get()
                        if val=="":
                            messagebox.showinfo("Empty Value Error",f'{entrybox[j+1]} can not be empty ')
                            self.entries[i][j+1].focus_set()
                            Empty= True
                            break
                            
                        elif j==0:
                            if int(val) < 10 or int(val)>3600:
                                messagebox.showinfo("Value Error",f'{entrybox[j+1]} Values must between 10 to 3600 ')
                                self.entries[i][j+1].focus_set()
                                Empty= True
                                break
                        elif j==1:
                            if int(val)<100 or int(val)>10000:
                                messagebox.showinfo("Value Error",f'{entrybox[j+1]} Values must between 100 to 10000 ')
                                self.entries[i][j+1].focus_set()
                                Empty= True
                                break
                        elif j==2:
                                prevVal=int(vals[j-1].get())
                                val =int(val)
                                if int(val)<100 or int(val)>10000:
                                    messagebox.showinfo("Value Error",f'{entrybox[j+1]} Values must between 100 to 10000 ')
                                    self.entries[i][j+1].focus_set()
                                    Empty= True
                                    break

                                if val < prevVal:
                                
                            
                                    messagebox.showinfo("Value Error",f'{entrybox[j+1]} Values must be greater than Start MS {val} ')
                                    self.entries[i][j+1].focus_set()
                                    Empty= True
                                    break
                                
                                    
                        
                        temp.append(val)
                    count +=1
                    data.append(temp)
                else:
                    if count<1:
                        messagebox.showinfo("Empty Value Error",f'{entrybox[0]} can not be empty ')
                        self.entries[0][0].focus_set()
                        Empty=True
                        break
                    else:
                        break
            if not Empty:
                return data
            else:   

                return None            

        #print data to what ever output is available

        def outputText(boolEnter):
            while not self.event.isSet():
                while not self.tasks.empty():
                
                    kb.write(self.tasks.get())
                    if boolEnter:
                        kb.press_and_release("enter")
                    
                
                self.event.wait(2)


        #function to send keyboard keys or text:
        def addText(text,interval,startThold,endThold,logit):
            while not self.event.isSet():
                interval = float(interval) + float(randint(startThold,endThold)/1000)
                self.event.wait(interval)
                self.tasks.put(text)
                if logit:
                    logging.info(f'text : {interval}') #just enable this in order to see logs 

            
            
                 
        #get focused element
        '''        
        def remember_focus(event):
            self.focused = event.widget
        '''
       #temporary disable Entries
        def disableEntries():
            for et in self.entries:
                for e in et:
                    e['state']='disabled'

        def enableEntries():
            for et in self.entries:
                for e in et:
                    e['state']='normal'


       
        def stopThreads():
            self.event.set()
            self.btnStop["text"]="stopping"

            th = threading.enumerate()
            time.sleep(2)
            
            self.tasks.empty()
            enableEntries()
            self.running=False
            self.btnStart['state']='normal'
            self.btnStart["state"]="normal"
            self.btnStart["text"]="start"
            self.btnStop["text"]="stopped"
            self.running= False
                

       #function start button
        
        def btnStartEnt():

            data=populateData()
            if not data ==  None:

                saveData(data) #save current stat of data

                enter = self.sendEnter.get()#check if send enter is checked
                self.event =threading.Event()#thread event
                self.running= True
                self.tasks =  Queue(maxsize=0)
        
                #disable Entries to receive any text while running
                disableEntries()
                #start queue thread
                updateThread = threading.Thread(target=outputText,args=(enter,))
                updateThread.start()
                
                for d in data:
                    if not d[0] =="":
                        text = d[0]          
                        interval= int(d[1])
                        startThold=int(d[2])
                        endThold=int(d[3])
                        logit = self.logIt.get()
                        #start all threads based on populated text box
                        try:
                            th = threading.Thread(target=addText,args=(text,interval,startThold,endThold,logit))
                            self.runningThreads.append(th)
                            th.start()
                        except KeyboardInterrupt as e:
                            logging.debug(e)
                            stopThreads()
                        except Exception as ex:
                            logging.debug(ex)
                            stopThreads()
                    
                self.btnStart["text"]="processing"
                self.btnStart["state"]="disable"
                
                
                self.btnStop["state"]="normal"
                self.btnStop["text"]="stop"
                
            
        #function to exit form
        def exitForm(self):
                if self.running:
                    stopThreads()
                    self.master.quit()    
                else:
                    self.master.quit()

        
        #stop button 
        def btnStopEnt(self):
            if self.running:
                stopThreads()
    


        #local variables to create entry widget        
        pos=[0,0]

        width=[25,5,5,5]
    
        howmany=5
        big_font =('Verdana',20)
        small_font=('Verdana',12)
        #entry widgets created
        self.entries = makeentry(self,howmany=howmany,pos=pos,width=width,textvariable=self.textvar,font=big_font)
        
        #frame 1 created to store chkEnter
        self.frame1=tk.Frame(self)
        self.frame1.grid(row=6,column=0,sticky="w",padx=7,pady=10)

        #self chkEnter widget to track if enter key to send or not       
        self.chkEnter=tk.Checkbutton(self.frame1,text="Send Enter",variable=self.sendEnter,font=small_font,bg=self.color,height=1,onvalue=1,offvalue=0)
        self.chkEnter.pack(side=LEFT)
    
        #enable or disable logging
        self.chkLogging=tk.Checkbutton(self.frame1,text="Enable Logging",variable=self.logIt, font=small_font,bg=self.color,height=1,onvalue=1,offvalue=0)
        self.chkLogging.pack(side=LEFT)
        
        #iterate over all widgets
        def getChildren (wid) :
            childList = wid.winfo_children()

            for item in childList :
                if item.winfo_children() :
                    childList.extend(item.winfo_children())

            return childList


        #change Color
        #function to change color

        wlist = self.master.winfo_children()
        def changeColor(event):


            widgets = getChildren(self.master)
            self.color=self.cmbColor.get()
            
            
            for w in widgets:
                if not (isinstance(w,tk.Entry) or isinstance(w,ttk.Combobox)):
                       w.configure(bg=self.color)
            self.master.configure(bg=self.color)
            style.map('TCombobox', fieldbackground=[('readonly',self.color)])
            style.map('TCombobox', selectbackground=[('readonly', self.color)])
        

        
        colorlabel= tk.Label(self.frame1,text="Color:",font=small_font,bg=self.color,width=10).pack(side=LEFT,padx=3)
        colors=sorted(["dodger blue","orchid4", 'sea green','dark khaki','dark green','chocolate1','orange red',
        'sea green3','Deep Sky Blue2','tan4'])
        
        self.cmbColor = ttk.Combobox(self.frame1,values=colors,font=small_font,width=10,state='readonly')
        self.cmbColor.current(0)
        self.cmbColor.pack(side=LEFT)
        self.cmbColor.bind("<<ComboboxSelected>>",changeColor)
        style=ttk.Style()
        style.map('TCombobox', fieldbackground=[('readonly','white')])

        style.map('TCombobox', selectbackground=[('readonly', 'white')])
        style.map('TCombobox', selectforeground=[('readonly', 'black')])

        #just created this to accept pixel for height and width
        img =tk.PhotoImage(width=1,height=1)
 
        #frame 2 to store start and save button
        self.frame2=tk.Frame(self,bg= "dodger blue")
        self.frame2.grid(row=7,column=0,sticky="w",padx=7,pady=7)
    
        #button start widget
        
        self.btnStart = tk.Button(self.frame2,text="Start" ,font=small_font,bg=self.color,disabledforeground="white",width=10,height=1,command=btnStartEnt)
        self.btnStart.pack(side=LEFT)
        
        #button stop widget
        self.btnStop = tk.Button(self.frame2,text="Not Running",font=small_font,bg=self.color,width=10,command=lambda:btnStopEnt(self))
        self.btnStop.pack(side=LEFT,padx=20)
        
        #root form close event tracking and binding function btnstopent to clean close
        self.master.protocol("WM_DELETE_WINDOW",lambda:exitForm(self))
        
        #after form loaded
        loadData()
       

        self.color=self.cmbColor.get()   
    #put the form center of the screen based on clients screen
    def setCenter(self):
        self.master.resizable(0,0)
        
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        w =1100
        h = 450
        x = (sw-w)/2
        y = (sh-h)/2
        
        self.master.geometry('%dx%d+%d+%d'%(w,h,x,y))
    
#driver function to run program
def main():
    win =tk.Tk()
    app = App()
    win.mainloop()

if __name__ == "__main__":
    main()
 
"""
 AutoTyper with Random Intervals
    Copyright (C) 2020  Nick Greising

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
