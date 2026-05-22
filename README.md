# PDI MBE Serial Data Loggers

Two scripts that read real-time position data from lab instruments over serial
ports and write timestamped logs to a shared daily output folder.

- **`serial_read_timestamp_rotation.py`** — reads rotation angle from the sample stage (COM13)
- **`serial_read_timestamp_z.py`** — reads vertical Z position from the Z-shift stage (COM14)

Both scripts run continuously alongside the LR watchdog and write their output
into the same dated folder structure.

---

## Requirements

- Python 3.x
- `pyserial` library

```
pip install pyserial
```

---

## Usage

Each script runs independently in its own terminal:

```
python serial_read_timestamp_rotation.py
python serial_read_timestamp_z.py
```

Both run until stopped with `Ctrl+C`. The serial port is closed cleanly on exit.

---

## Configuration

All settings are at the top of each script:

**Rotation script:**
```python
OUTPUT_BASE_DIR = r"c:\EPIC\Latest\Logs"
PORT            = 'COM13'
BAUDRATE        = 9600
SPR             = 1706734    # steps per full revolution
STEP_TOLERANCE  = 3          # minimum step change before logging
```

**Z script:**
```python
OUTPUT_BASE_DIR = r"c:\EPIC\Latest\Logs"
PORT            = 'COM14'
BAUDRATE        = 38400
SPMM            = 960411     # steps per mm
OFFSET_MM       = 5          # height in mm at 0 steps
STEP_TOLERANCE  = 3          # minimum step change before logging
```

---

## Output structure

Both scripts write into the same dated folder as the LR watchdog logs:

```
c:\EPIC\Latest\Logs\
└── YYYY\
    └── YYYY_MM_DD\
        ├── LR.txt            ← from pdi_lr_watchdog
        ├── LR_meta.txt       ← from pdi_lr_watchdog
        ├── Rotation.txt      ← from serial_read_timestamp_rotation
        └── Zshift.txt        ← from serial_read_timestamp_z
```

A new dated subfolder is created automatically each day. If a file doesn't exist
yet for that day it is created with a header — otherwise data is appended.

### Rotation.txt

```
EPIC Rotation Log File

'Date,Rotation.steps,Rotation.deg
21/05/2026 14:32:05.123,853367,180.00
21/05/2026 14:32:08.456,1280050,269.87
```

### Zshift.txt

```
EPIC Zshift Log File

'Date,Z.steps,Z.height_mm
21/05/2026 14:32:05.123,0,5.00
21/05/2026 14:32:09.774,960411,6.00
```

---

## How it works

Both scripts follow the same logic:

1. Read a line from the serial port (`ser.readline()`)
2. Decode and parse it as an integer (step count from the motor controller)
3. Apply a `STEP_TOLERANCE` filter — ignore readings where the position
   has not changed by more than 3 steps (eliminates noise)
4. Convert steps to physical units (degrees or mm)
5. Print the timestamped line to console — EPIC captures this
6. Write the same line to the daily log file

The rotation script applies an additional filter: readings below 1° of movement
(`abs(num) > SPR/360`) are also ignored.

---

## Timestamp format

Timestamps are generated at the moment a valid reading passes the filter:

```
DD/MM/YYYY HH:MM:SS.mmm
```

Example: `21/05/2026 14:32:05.123`

---

## Testing without hardware

Each script has a corresponding test file that replaces the serial port with a
software mock — no hardware or extra software needed:

```
python test_rotation.py
python test_zshift.py
```

Test files use a `FakeSerial` class that replays a list of predefined step values,
including edge cases (noise below tolerance, non-integer lines, direction reversal)
so all filter paths can be verified locally.

---

## Notes

- Both scripts can run simultaneously — they use different COM ports and write
  to different files in the same output folder.
- `STEP_TOLERANCE = 3` matches the original lab scripts. Adjust if the instrument
  produces excessive noise at rest.
- The `'` prefix on header lines is EPIC's comment syntax — it tells EPIC to treat
  those lines as metadata rather than data rows.
- `timeout=1` is set on the serial connection so `readline()` does not block
  indefinitely if the instrument stops sending data.
