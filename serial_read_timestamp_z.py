import serial
import time as tm
import re
# reads serial in from rotation
# outputs angle 

# spmm=1000000 #steps per mm old
spmm=960411 #steps per mm
# ofsmm=37.5 # offset mm (=mm height at 0 steps), newly calibrated
ofsmm=5 # offset mm (=mm height at 0 steps) - adjusted to EPIC and actual scale

prevnum=0
dummy=0
steptolerance=3
ser = serial.Serial(
    port='COM14',
    baudrate=38400,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)
print("'EPIC Z shift- Log File")
print("")
print("'Date,Z.steps,Z.height_mm")

while(True):
    data=ser.readline() # is a bytes object
    ds=data.decode() #ds is a string object
    try:
      num=int(ds)
#      if abs(num)>spr/360 and abs(num-prevnum)>2 and num!=5000: # 5000 is read upon epic start
      if abs(num-prevnum)>steptolerance:
        st=tm.localtime()
        curr=tm.time()
        sec=st.tm_sec+ (curr % 1)
        tmstr=tm.strftime("%d/%m/%Y %H:%M",st)
        mm=(num/spmm)+ofsmm
        print(f"{tmstr}:{sec:06.3f},{num},{mm:.2f}")
        #print(tmstr+":%06.3f" % sec,num,"%.2f" % mm)
        prevnum=num # buffer last written value

    except:
      dummy=1
ser.close()
