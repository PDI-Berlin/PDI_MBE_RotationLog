import serial
import time as tm
import os
import sys
from datetime import datetime

# ── SINGLE INSTANCE LOCK ──────────────────────────────────────────────────────
LOCK_FILE = f"{os.path.basename(__file__)}.lock"

try:
    lock_fd = open(LOCK_FILE, 'ab+')
    if os.name == 'nt':  
        import msvcrt
        try:
            lock_fd.seek(0)
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
        except IOError:
            print(f"\n⚠️ WARNING: This script is already running in another terminal!")
            print("Please close the other instance before running this one.")
            sys.exit(1)
    else:  
        import fcntl
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print(f"\n⚠️ WARNING: This script is already running in another terminal!")
            sys.exit(1)
except Exception as e:
    print(f"Lockfile initialization failed: {e}")
    sys.exit(1)
# ──────────────────────────────────────────────────────────────────────────────

# ── Configuration ─────────────────────────────────────────────────────────────
OUTPUT_BASE_DIR  = r"c:\EPIC\Latest\Logs"   
PORT             = 'COM14'
BAUDRATE         = 38400
SPMM             = 960411                   # steps per mm
OFFSET_MM        = 5                        # height in mm at 0 steps
STEP_TOLERANCE   = 3                        # minimum step change to log
# LOG FILENAMES
LOG_STEPS_FILE   = "Sub.ZShift.Steps.txt"
LOG_HEIGHT_FILE  = "Sub.ZShift.Height.txt"
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

ser = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

print("'EPIC Zshift Log File")
print("")
print("'Date,Z.steps,Z.height_mm")

try:
    while True:
        data = ser.readline()
        ds = data.decode(encoding='utf-8', errors='ignore').strip()
        try:
            num = int(ds)
            if abs(num - prevnum) > STEP_TOLERANCE:
                st = tm.localtime()
                curr = tm.time()
                sec = st.tm_sec + (curr % 1)
                tmstr = tm.strftime("%d/%m/%Y %H:%M", st)
                ts = f"{tmstr}:{sec:06.3f}"
                
                mm = (num / SPMM) + OFFSET_MM
                
                # Print to terminal 
                print(f"{ts},{num},{mm:.2f}")
                
                # Write to two separate log targets simultaneously ──
                write_to_log(LOG_STEPS_FILE, "'Date,Z.steps", f"{ts},{num}")
                write_to_log(LOG_HEIGHT_FILE, "'Date,Z.height_mm", f"{ts},{mm:.2f}")
                
                prevnum = num
        except ValueError:
            pass
        except Exception as e:
            print(f"Warning: {e}")

except KeyboardInterrupt:
    print("\nStopping.")
finally:
    ser.close()