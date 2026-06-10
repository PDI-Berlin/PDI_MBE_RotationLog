import serial
import time as tm
import os
import sys
from datetime import datetime

# ── SINGLE INSTANCE LOCK ──────────────────────────────────────────────────────
LOCK_FILE = f"{os.path.basename(__file__)}.lock"

try:
    lock_fd = open(LOCK_FILE, 'ab')
    if os.name == 'nt':
        import msvcrt
        try:
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
        except IOError:
            lock_fd.close()
            print(f"\n⚠️ WARNING: This script is already running in another terminal!")
            print("Please close the other instance before running this one.")
            sys.exit(1)
    else:
        import fcntl
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            lock_fd.close()
            print(f"\n⚠️ WARNING: This script is already running in another terminal!")
            sys.exit(1)
except Exception as e:
    print(f"Lockfile initialization failed: {e}")
    sys.exit(1)
# ──────────────────────────────────────────────────────────────────────────────

# ── Configuration ─────────────────────────────────────────────────────────────
OUTPUT_BASE_DIR  = r"c:\EPIC\Latest\Logs"   
PORT             = 'COM13'
BAUDRATE         = 9600
SPR              = 1706734                  # steps per revolution
STEP_TOLERANCE   = 3                        # minimum step change to log

# LOG FILENAMES
LOG_STEPS_FILE   = "Sub.Rot.Steps.txt"
LOG_ANGLE_FILE   = "Sub.Rot.Angle.txt"
# ──────────────────────────────────────────────────────────────────────────────


def write_to_log(filename, header_cols, data_line):
    """
    Appends one data line to a daily log file.
    Creates the dated folder and writes the header if the file is new.
    """
    now = datetime.now()
    dated_dir = os.path.join(
        OUTPUT_BASE_DIR,
        now.strftime("%Y"),
        now.strftime("%Y_%m_%d")
    )
    os.makedirs(dated_dir, exist_ok=True)

    file_path = os.path.join(dated_dir, filename)
    file_exists = os.path.isfile(file_path)

    with open(file_path, 'a', encoding='utf-8') as f:
        if not file_exists:
            f.write(f"EPIC {filename.replace('.txt', '')} Log File\n\n")
            f.write(f"{header_cols}\n")
        f.write(data_line + "\n")


prevnum = 0
prevh=-1

ser = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)
print("'EPIC Rotation Log File")
print("")
print("'Date,Rotation.steps,Rotation.deg")

try:
    while True:
        data = ser.readline()	# read data from serial port (cr/lf terminated string)
        st = tm.localtime()	# get timestamp
        curr = tm.time()	# get timestamp
        h=st.tm_hour

        ds = data.decode(encoding='utf-8', errors='ignore').strip()

        try:
            num = int(ds)
            if (abs(num) > SPR/360 and abs(num - prevnum) > STEP_TOLERANCE) or (h!=prevh):
                sec = st.tm_sec + (curr % 1)
                tmstr = tm.strftime("%d/%m/%Y %H:%M", st)
                ts = f"{tmstr}:{sec:06.3f}"                
                rv = (num / SPR) % 1
                dg = 360 * rv
                
                # Print to terminal 
                print(f"{ts},{num},{dg:.2f}")
                
                # Write to two separate log targets simultaneously
                write_to_log(LOG_STEPS_FILE, "'Date,Rotation.steps", f"{ts},{num}")
                write_to_log(LOG_ANGLE_FILE, "'Date,Rotation.deg", f"{ts},{dg:.2f}")
                
                prevnum = num
                prevh=h
        except ValueError:
            pass
        except Exception as e:
            print(f"Warning: {e}")

except KeyboardInterrupt:
    print("\nStopping.")
finally:
    ser.close()    
    try:
        lock_fd.close()
    except Exception:
        pass
    try:
        os.remove(LOCK_FILE)
    except Exception:
        pass