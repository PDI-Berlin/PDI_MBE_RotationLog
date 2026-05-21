import serial
import time as tm
import re
# reads serial in from rotation
# outputs angle 

spr=1706734
prevnum=0
dummy=0
steptolerance=3

ser = serial.Serial(
    port='COM13',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)
print("'EPIC Rotation Log File")
print("")
print("'Date,Rotation.steps,Rotation.deg")

while(True):
    data=ser.readline() # is a bytes object
    ds=data.decode() #ds is a string object
    try:
      num=int(ds)
      #if abs(num)>spr/360 and abs(num-prevnum)>2 and num!=5000: # 5000 is read upon epic start
      if abs(num)>spr/360 and abs(num-prevnum)>steptolerance:
        st=tm.localtime()
        curr=tm.time()
        sec=st.tm_sec+ (curr % 1)
        tmstr=tm.strftime("%d/%m/%Y %H:%M",st)
        rv=(num/spr)%1
        if rv<0:	# deal with negative steps!
          rv=1-rv
        dg=(360*rv)
        print(f"{tmstr}:{sec:06.3f},{num},{dg:.2f}")
        #print(tmstr+":%06.3f" % sec,num,"%.2f" % dg)
        prevnum=num # buffer last written value

    except:
      dummy=1
ser.close()
