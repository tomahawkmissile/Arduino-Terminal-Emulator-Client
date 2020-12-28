import serial
from serial import SerialException
import os
import argparse
import sys
import subprocess
from subprocess import check_output
import time

if os.name == 'nt':
    import msvcrt
else:
    import termios
    import tty
    from select import select

port = None
args = None

def isData():
    return select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def printMassiveString(stdoutStr):
    stdoutStr = stdoutStr.replace("\\r", "")
    arr = stdoutStr.split("\\n")

    for elem in arr:
        if len(elem)<255:
            elem += '\n'
            port.write(elem.encode())
        else:
            for i in range(0, len(elem), 255):
                sub = None
                if len(elem) < i+255:
                    sub = elem[i:len(elem)]
                else:
                    sub = elem[i:i+255]
                elem += '\n'
                port.write(elem.encode())
        if port.in_waiting and args.verbose:
            line = port.readline()
            print(line.decode())
        time.sleep(0.1)

def execute(cmd):
    process = subprocess.Popen(args.continuous.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(process.stdout.readline, ""):
        yield stdout_line
    process.stdout.close()
    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, args.continuous)

def windows():
    try:
        output = ""
        while(port.isOpen()):
            if port.in_waiting and args.verbose:
                line = port.readline()
                print(line.decode())

            if args.command is None and args.continuous is None:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch == b'\r' or ch == b'\n':
                        output += '\n'
                        port.write(output.encode())
                        output = ""
                    else:
                        output += ch.decode()
            elif args.command is not None:
                process = subprocess.Popen(args.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                stdoutStr = str(stdout)
                printMassiveString(stdoutStr)
                sys.exit(0)
            else:
                for output_line in execute(args.continuous):
                    printMassiveString(output_line.decode())

            time.sleep(0.01)
    except KeyboardInterrupt:
        print('Exited')

def linux():
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        output = ""
        while(port.isOpen()):
            if port.in_waiting and args.verbose:
                line = port.readline()
                print(line.decode())
            if args.command is None and args.continuous is None:
                if isData():
                    c = sys.stdin.read(1)
                    if c == '\x1b': # escape key
                        break
                    elif c == '\n' or c == '\r':
                        output += '\n'
                        port.write(output.encode())
                        output = ""
                    else:
                        output += c
            elif args.command is not None:
                process = subprocess.Popen(args.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                stdoutStr = str(stdout)
                printMassiveString(stdoutStr)
                sys.exit(-1)
            else:
                for output_line in execute(args.continuous):
                    printMassiveString(output_line.decode())
        time.sleep(0.01)
    except KeyboardInterrupt:
        print('Exited')
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=str, help="select the serial port")
    parser.add_argument('--verbose', type=bool, nargs='?', const=True, help="whether or not incoming data should be printed here (defaults to true)")
    parser.add_argument('--command', type=str, nargs='?', const=None, help="If present, determines the command output to send to the serial port. Do not use with --continuous")
    parser.add_argument('--continuous', type=str, nargs='?', const=None, help="If present, sends a command output to the serial port that is continuous (e.g.) journalctl -fxe. Do not use with --command")
    args = parser.parse_args()
    try:
        port = serial.Serial(str(args.port), 115200)
    except SerialException:
        print("Invalid serial port")
        sys.exit(-1)

    # Wait for Arduino to boot
    time.sleep(5)

    port.write(str("COLOR=2044").encode())
    time.sleep(0.2)

    if os.name == 'nt':
        windows()
    else:
        linux()