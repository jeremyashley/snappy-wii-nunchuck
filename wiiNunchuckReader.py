#
# code to read from i2c connected Wii Nunchuck
# sequence follows a simple state machine to encode events and states
#
# State : Events : Description
#   A   :   OK   : Initialise Timer
#   B   : OK NO  : Timer Countdown
#   C   : OK NO  : Initialise Device
#   D   :   OK   : Request Timer
#   E   : OK NO  : Request Device Info
#   F   :   OK   : Receive Timer
#   G   : OK NO  : Receive Device Info
#
stateIndex = 0
OP = ('A', 'B', 'C', 'D', 'B', 'E', 'F', 'B', 'G') 
OK = ( 1,   2,   3,   4,   5,   6,   7,   8,   3 )
NO = ( 0,   1,   0,   0,   4,   0,   0,   7,   0 )
event = "OK"

def wiiNunchuckTick():
    global stateIndex, event, OP, OK, NO
    op = OP[stateIndex]
    if (op == 'A'):
        event = setTimer(10)
    if (op == 'B'):
        event = checkTimer()
    if (op == 'C'):
        event = wiiNunchuckInit()
    if (op == 'D'):
        event = setTimer(5)
    if (op == 'E'):
        event = wiiRequestNunchuckState()
    if (op == 'F'):
        event = setTimer(5)
    if (op == 'G'):
        event = wiiReceiveNunchuckState()
        
    if (event == "OK"):
        stateIndex = OK[stateIndex]
    else:
        stateIndex = NO[stateIndex]
    

timerTicks = 0

def setTimer(ticks):
    global timerTicks
    timerTicks = ticks
    return "OK"

def checkTimer():
    global timerTicks
    if (timerTicks == 0):
        return "OK"
    timerTicks -= 1
    return "TICK"  

i2cRetries = 5 # It's possible this might need to be increased for really slow devices

def wiiNunchuckInit():
    i2cInit(True)
    bytesWritten = i2cWrite('\xA4\x40\x00', i2cRetries, False)
    return wiiNunchuckSuccess(3, bytesWritten)

success = False

def wiiNunchuckSuccess(expected, actual):
    global success
    success = ((getI2cResult() == 1) and (expected == actual))
    if (not success):
        return "FAIL"
    return "OK"


def wiiRequestNunchuckState():
    bytesWritten = i2cWrite('\xA4\x00', i2cRetries, False)
    return wiiNunchuckSuccess(2, bytesWritten)

response = ""

def wiiReceiveNunchuckState():
    global response
    response = i2cRead('\xA5', 6, i2cRetries, False)
    return wiiNunchuckSuccess(6, len(response))

def retrieveNunchuckState():
    global success, response
    if (success):
        return decodeWiiChuckResponse(response)

def retrieveEngineState():
    global stateIndex, event
    return "currentState: " + str(stateIndex) + " last event: " + event

def decodeWiiChuckResponse(response):
    aX= int(ord(response[0]))
    aY= int(ord(response[1]))
    byte5 = ord(response[5])
    xA= int((ord(response[2]) << 2) | ((byte5 >> 2) & 0x03))
    yA= int((ord(response[3]) << 2) | ((byte5 >> 4) & 0x03))
    zA= int((ord(response[4]) << 2) | ((byte5 >> 6) & 0x03))
    bC = bZ = 1
    if (byte5 & 0x03 == 0x00):
        bC = 0
    if (byte5 & 0x02 == 0x00):
        bZ = 0
    return chr(aX) + chr(aY) + chr(xA) + chr(yA) + chr(zA) + chr(bC) + chr(bZ)

@setHook(HOOK_10MS)
def readChuck():
    wiiNunchuckTick()
    

# possible alternate i2c device init send characters    
#    bytesWritten = i2cWrite('\xA4\x00\xFB\x00', retries, False)
#    bytesWritten = i2cWrite('\xA4\x00\xF0\x55', retries, False)
