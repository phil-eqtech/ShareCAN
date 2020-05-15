<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.0" language="fr">
<context>
    <name>MainWindow</name>
    <message>
        <source>APP_NAME</source>
        <translation>Share-CAN</translation>
    </message>
    <message>
        <source>LOGIN_TITLE</source>
        <translation>Authentification</translation>
    </message>
    <message>
        <source>USERNAME</source>
        <translation>Username :</translation>
    </message>
    <message>
        <source>PROFILE_NAME</source>
        <translation>Profile name :</translation>
    </message>
    <message>
        <source>PASSWORD</source>
        <translation>Password :</translation>
    </message>
    <message>
        <source>LOGIN_BTN</source>
        <translation>Login</translation>
    </message>
    <message>
        <source>NEW_USER_PROMPT</source>
        <translation>Please choose your username, profile name and password to create an account.</translation>
    </message>
    <message>
        <source>HIDE_MENU</source>
        <translation>Hide menu</translation>
    </message>
    <message>
        <source>SHOW_MENU</source>
        <translation>Show menu</translation>
    </message>
    <message>
        <source>NOTES</source>
        <translation>Notepad</translation>
    </message>
    <message>
        <source>CMD_EDITOR</source>
        <translation>Command editor</translation>
    </message>
    <message>
        <source>ECU_MAP_SCAN_UDS</source>
        <translation>ECU/UDS map</translation>
    </message>
    <message>
        <source>CAN_BTN</source>
        <translation>CAN</translation>
    </message>
    <message>
        <source>LIN_BTN</source>
        <translation>LIN</translation>
    </message>
    <message>
        <source>KLN_BTN</source>
        <translation>K-Line</translation>
    </message>
    <message>
        <source>DISPLAY</source>
        <translation>DISPLAY</translation>
    </message>
    <message>
        <source>MASK_STATIC</source>
        <translation>Mask static frames :</translation>
    </message>
    <message>
        <source>KEEP_DURATION</source>
        <translation>Mask after :</translation>
    </message>
    <message>
        <source>SIGNAL_SRC</source>
        <translation>Signals source :</translation>
    </message>
    <message>
        <source>SNAP_ID</source>
        <translation>Snap frames</translation>
    </message>
    <message>
        <source>SNAP_ID_TOOLTIP</source>
        <translation>Store frames values and highlight only non stored values</translation>
    </message>
    <message>
        <source>CLEAR_SNAP_TOOLTIP</source>
        <translation>Clear snap</translation>
    </message>
    <message>
        <source>CLEAR_SNAP</source>
        <translation>Clear snap</translation>
    </message>
    <message>
        <source>ANALYSIS</source>
        <translation>Analysis</translation>
    </message>
    <message>
        <source>ENGINE_CODE</source>
        <translation>Engine code</translation>
    </message>
    <message>
        <source>MODEL</source>
        <translation>Model</translation>
    </message>
    <message>
        <source>MANUFACTURER</source>
        <translation>Manufacturer</translation>
    </message>
    <message>
        <source>SESSION_NAME</source>
        <translation>Nom :</translation>
    </message>
    <message>
        <source>SESSION_FRAMES</source>
        <translation>Frames :</translation>
    </message>
    <message>
        <source>LIVE</source>
        <translation>Live</translation>
    </message>
    <message>
        <source>REC</source>
        <translation>Record</translation>
    </message>
    <message>
        <source>PAUSE</source>
        <translation>Pause</translation>
    </message>
    <message>
        <source>REPLAY</source>
        <translation>Replay</translation>
    </message>
    <message>
        <source>FORENSIC</source>
        <translation>Forensic</translation>
    </message>
    <message>
        <source>NEW</source>
        <translation>New</translation>
    </message>
    <message>
        <source>SAVE</source>
        <translation>Save</translation>
    </message>
    <message>
        <source>LOAD</source>
        <translation>Load</translation>
    </message>
    <message>
        <source>FILTERS</source>
        <translation>FILTERS</translation>
    </message>
    <message>
        <source>NO_SESSION</source>
        <translation>No active session</translation>
    </message>
    <message>
        <source>ID</source>
        <translation>Id</translation>
    </message>
    <message>
        <source>BUS</source>
        <translation>Bus</translation>
    </message>
    <message>
        <source>ECU</source>
        <translation>Ecu</translation>
    </message>
    <message>
        <source>DATA</source>
        <translation>Data</translation>
    </message>
    <message>
        <source>ASCII</source>
        <translation>Ascii</translation>
    </message>
    <message>
        <source>COUNT</source>
        <translation>Count</translation>
    </message>
    <message>
        <source>PERIOD</source>
        <translation>Period</translation>
    </message>
    <message>
        <source>TIME</source>
        <translation>Time</translation>
    </message>
    <message>
        <source>SIGNAL</source>
        <translation>Signals</translation>
    </message>

    <name>LOGIN</name>
    <message>
        <source>USER_NAME_TOO_SHORT</source>
        <translation>The username must be at least 1 character</translation>
    </message>
    <message>
        <source>INVALID_PWD</source>
        <translation>Incorrect password.</translation>
    </message>
    <message>
        <source>INVALID_USERNAME</source>
        <translation>Incorrect username.</translation>
    </message>

    <name>GENERIC</name>
    <message>
        <source>SAVE</source>
        <translation>Save</translation>
    </message>
    <message>
        <source>CLOSE</source>
        <translation>Close</translation>
    </message>
    <message>
        <source>CANCEL</source>
        <translation>Cancel</translation>
    </message>
    <message>
        <source>LOAD</source>
        <translation>Load</translation>
    </message>
    <message>
        <source>DELETE</source>
        <translation>Delete</translation>
    </message>

    <name>COMMAND</name>
    <message>
        <source>HELP_TXT</source>
        <translation>Command editor quick guide
------------------------------------------------

- Constant frame : frame sent at a specific interval
If interval = 0, frame is sent once, at the beginning
- Active frame : send a static or dynamic frame (fuzzing)
- Pause : pause, in ms

ID and BYTE value must be written as hex value, without the '0x'

To generate dynamic frame, the following special characters are available :

- [A@B] : Fuzz field from A value to B value.
Exemple : [00@FF] means fuzz from 0 to 255.
Warning : A must be lower than B value, and only one frame can be fuzz at a time

- $I : is the current ID of the fuzz frame
- $1 à $8 : return the value of the byte 1 to 8 of the fuzz frame

The '$' special characters are useful to generate complementary frames, like reccurent 'Tester Present' when fuzzing UDS commands.
      </translation>
    </message>
</context>
</TS>
