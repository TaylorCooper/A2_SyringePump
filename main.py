"""
    Author:
        Taylor Cooper
    Description:
        Load a recipe file and run basic recipes for injecting and extracting.              
    Date Created:
        Aug 20, 2014 2:16:50 PM
    
    Arguments and Inputs:
        Recipe File:
            cycles = int, number of cycles
            dia = float, inner diameter of syringe in mm
            cmd1 = INF,
    Outputs:
        Serial commands to syringe pump
    Dependencies:
        pyserial (in cmdline: pip install pyserial)
                  
    History:                  
    --------------------------------------------------------------
    Date:    
    Author:    Taylor Cooper
    Modification:    
     --------------------------------------------------------------
"""

import serial, time, collections

class syringePump():
    """
    Description:  Loads a recipe file and sends commands to pump over serial.
    Input: COM port, recipe file or 
    Output: Commands to syringe pump
    """
    
    def __init__(self, port, recipe):
        """ Use port=2 for COM3, windows indexing is weird.
        """
        
        # Inputs: set port and read recipe
        self.port = port
        if  not isinstance(recipe, basestring):   
            self.cycles = recipe[0]
            self.diameter = recipe[1]
            self.cmds = recipe[2]
        else:
            self.cycles, self.diameter, self.cmds = self.readRecipe(recipe)
        
        # Internal stuff
        self.timeout = 8
        self.timeout_delay = 2
        
        # Buffer
        self.pumpBuffer = collections.deque()

        # Open port, nominal baudrate = 19200 no reason to change it 
        self.ser = serial.Serial(self.port, baudrate=19200, timeout=1)
        time.sleep(1)
        
        # Initialize diameter
        self.sendPumpCmd('*RESET',delay=1) # Reset pump, wait longer
        self.sendPumpCmd('DIA'+str(self.diameter)) # Assign syringe diameter
              

    def readPump(self):
        """ Read chars from the serial port buffer well it is not empty.
        """        
        s = ""
        
        # Read serial into buffer and then pop out to s for return
        while self.ser.inWaiting() > 0:

            l = self.ser.read(1) #Read 1 BYTE
            self.pumpBuffer.append(l)
            
            while len(self.pumpBuffer) > 0:
                s = s + self.pumpBuffer.popleft()

        return s
    

    def sendPumpCmd(self, s, delay=0.2):
        """ String is written directly to serial port.
        """
        
        # Send and recieve cmd
        cmd = s + '\x0D' # Carriage return required
        self.ser.write(cmd)
        time.sleep(delay) # Delay before syringe can respond
        r = self.readPump()
        
        # Let the user know what happened
        print 'SentCmd: ', s, ' ||  Received:', r
        

    def readRecipe(self, path):
        """ Reads recipe stored at file path.
        """
        
        fo = open(path, "rb")
        cmds = []
        
        for line in fo:
            if line[0] == '#': # Comment character
                continue
            elif "cycles" in line:
                if '#' in line: line = line.split('#')[0] # Remove post comments
                cycles = int(line.split('=')[1])
            elif "diameter" in line:
                if '#' in line: line = line.split('#')[0]
                diameter = float(line.split('=')[1])  # Delay in seconds
            else:
                if '#' in line: line = line.split('#')[0]
                line = line.replace('\n','')
                line = line.replace('\r','')
                if line != '':
                    cmds.append(line)
        
        print 'Loaded recipe: '
        print cycles, diameter, cmds
        return cycles, diameter, cmds

    def runRecipe(self):
        """ Runs recipe according to what was loaded.
        """

        for i in range(self.cycles):
            for cmd in self.cmds:
                self.sendPumpCmd(cmd)
            
        self.ser.close()
    
    def flushLine(self, flushLength=200):
        """ Flush line to remove air
        """
        
        self.sendPumpCmd('RAT 1000 UM')
        self.sendPumpCmd('VOL '+ str(flushLength))
        self.sendPumpCmd('DIR INF')
        self.sendPumpCmd('RUN')


exampleRecipe = [
                 1, # Number of times commands are looped
                 7.0, # Inner diameter of syringe
                 
                 # Pre-formated commands
                 ['PHN 1', # Step 1
                 'FUN RAT', # Not sure what this is for..
                 'RAT 1000 UM', # Set pump rate in ul/min
                 'VOL 1000', # Set volume in ul
                 'DIR INF', # Set direction (infusion, depress syringe)
                 'PHN 2', # Step 2 executes after step 1 completes
                 'FUN RAT',
                 'RAT 1000 UM',
                 'VOL 1000',
                 'DIR WDR',
                 'PHN 3',
                 'FUN STP',
                 'RUN'] # Step 3 executes after step 1 completes
                 ]

recipePath = 'recipe.txt'

if __name__ == '__main__':
    sp = syringePump(3, recipePath)
#     sp.flushLine() # Call this command to remove air at the end of tube
    sp.runRecipe()



    