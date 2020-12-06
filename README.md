# Arduino UART Terminal Emulator Client
### Python script to communicate with Arduino over serial

### Usage: python3 arduino_terminal.py <--verbose> --port=<serial port> [--command=<command>]

Verbose mode means that the program will print any response over serial back to this console.  
Command is the command to be run and echoed to the serial port. Alternatively, you can exclude this argument and just type to the serial port manually.  

Note: when using linux, the serial port is not the one that looks like /dev/ttyX ! The one you're looking for is in /dev/serial/by-id/