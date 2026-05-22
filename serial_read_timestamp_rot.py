import serial
import time as tm
import os
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
OUTPUT_BASE_DIR  = r"c:\EPIC\Latest\Logs"   # same destination as LR script
PORT             = 'COM13'
BAUDRATE         = 9600
SPR              = 1706734                  # steps per revolution
STEP_TOLERANCE   = 3                        # minimum step change to log
LOG_FILENAME     = "sub_Rotation.txt"       # output filename
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


# reads serial in from rotation
# outputs angle
prevnum = 0

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
        data = ser.readline()
        ds = data.decode()
        try:
            num = int(ds)
            if abs(num) > SPR/360 and abs(num - prevnum) > STEP_TOLERANCE:
                st = tm.localtime()
                curr = tm.time()
                sec = st.tm_sec + (curr % 1)
                tmstr = tm.strftime("%d/%m/%Y %H:%M", st)
                ts = f"{tmstr}:{sec:06.3f}"
                rv = (num / SPR) % 1
                dg = 360 * rv
                print(f"{ts},{num},{dg:.2f}")
                write_to_log(LOG_FILENAME, "'Date,Rotation.steps,Rotation.deg", f"{ts},{num},{dg:.2f}")
                prevnum = num
        except ValueError:
            pass
        except Exception as e:
            print(f"Warning: {e}")

except KeyboardInterrupt:
    print("\nStopping.")
finally:
    ser.close()