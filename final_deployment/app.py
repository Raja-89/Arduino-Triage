import time
import threading
import serial
import json
import sounddevice as sd
import numpy as np
import glob
import os
import subprocess
from flask import Flask, render_template, jsonify

# --- CONFIG ---
BAUD_RATE = 115200
app = Flask(__name__)

# --- GLOBAL STATE ---
system_state = {
    "knob_val": 0, "mode": "IDLE", "temp": 25.0, "movement": 0, "audio_level": 0,   
    "diagnosis": "Connecting...", "risk_level": "LOW", "connected_port": "None"
}

# --- AGGRESSIVE CONNECTION LOGIC ---
def force_release_port(port):
    """ Tries to kill whatever is holding the port """
    print(f"🔨 Forcing release of {port}...")
    try:
        subprocess.run(f"fuser -k -9 {port}", shell=True)
        time.sleep(1)
    except: pass

def find_mcu_port():
    print("------- AGGRESSIVE CONNECT -------")
    
    # Try ttyHS1 (Most likely on UNO Q)
    target = '/dev/ttyHS1'
    
    print(f"Trying {target}...")
    try:
        s = serial.Serial(target, BAUD_RATE, timeout=0.5)
        print(" SUCCESS (Open)!")
        return s
    except serial.SerialException as e:
        if "busy" in str(e).lower() or "denied" in str(e).lower():
             print(" Port is BUSY. Attempting to kill config process...")
             force_release_port(target)
             try:
                 time.sleep(1)
                 s = serial.Serial(target, BAUD_RATE, timeout=0.5)
                 print(" SUCCESS (After Kill)!")
                 return s
             except Exception as e2:
                 print(f" Still failing: {e2}")
    
    # Fallback: ttyS0 (Standard)
    target = '/dev/ttyS0'
    print(f"Trying {target}...")
    try:
        force_release_port(target)
        s = serial.Serial(target, BAUD_RATE, timeout=0.5)
        print(" SUCCESS (ttyS0)!")
        return s
    except: pass

    print("❌ CRITICAL: ALL PORTS LOCKED.")
    return None

# --- SERIAL THREAD ---
ser = None
def serial_loop():
    global ser
    while True:
        try:
            if ser is None:
                ser = find_mcu_port()
                if ser:
                    system_state["connected_port"] = ser.portstr
                    system_state["diagnosis"] = "Connected"
                else:
                    time.sleep(5) 
                    continue

            if ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith("{"):
                        data = json.loads(line)
                        system_state["knob_val"] = data.get("knob", 0)
                        system_state["temp"] = data.get("temp", 25.0)
                        system_state["movement"] = data.get("movement", 0)
                        
                        if system_state["mode"] == "IDLE":
                            if system_state["knob_val"] < 300: 
                                system_state["diagnosis"] = "Select: HEART Mode"
                            elif system_state["knob_val"] < 700: 
                                system_state["diagnosis"] = "Select: LUNG Mode"
                            else: 
                                system_state["diagnosis"] = "Select: CALIBRATION"
                except: pass
        except Exception as e:
            print(f"⚠️ SERIAL LOST: {e}")
            ser = None
            time.sleep(1)
        time.sleep(0.01)

# --- AUDIO & FLASK ---
def audio_callback(indata, frames, time, status):
    system_state["audio_level"] = int(np.linalg.norm(indata) * 10)
def start_audio_stream():
    try: sd.InputStream(callback=audio_callback).start()
    except: pass

def send_mcu_command(c):
    if ser:
        try: ser.write((json.dumps(c)+"\n").encode())
        except: pass

def run_exam():
    system_state["mode"] = "EXAMINING"
    send_mcu_command({"progress": 0, "result": 90, "relay": 0})
    for i in range(0, 101, 2): 
        if system_state["movement"]==1: send_mcu_command({"buzzer":2000}); time.sleep(0.5); send_mcu_command({"buzzer":0})
        system_state["diagnosis"] = f"Recording... {i}%"
        send_mcu_command({"progress": int(i * 1.8)}) 
        time.sleep(0.1) 
    score = 0
    if system_state["audio_level"]>20: score+=1
    if system_state["temp"]>30: score+=1
    system_state["mode"]="RESULT"
    if score>=2: system_state["risk_level"]="HIGH"; system_state["diagnosis"]="ABNORMALITY"; send_mcu_command({"result":180,"buzzer":1000})
    elif score==1: system_state["risk_level"]="MEDIUM"; system_state["diagnosis"]="Warning"; send_mcu_command({"result":90,"buzzer":0})
    else: system_state["risk_level"]="LOW"; system_state["diagnosis"]="Normal"; send_mcu_command({"result":0,"buzzer":0})
    time.sleep(0.5); send_mcu_command({"buzzer":0}) 

@app.route('/')
def i(): return render_template('index.html')
@app.route('/status')
def s(): return jsonify(system_state)
@app.route('/start_exam', methods=['POST'])
def st(): 
    if system_state["mode"]=="IDLE": threading.Thread(target=run_exam).start(); return jsonify({"s":"started"})
    return jsonify({"s":"busy"})
@app.route('/reset', methods=['POST'])
def r(): 
    system_state["mode"]="IDLE"; system_state["diagnosis"]="Ready"; system_state["risk_level"]="LOW"
    send_mcu_command({"progress":0,"result":90,"buzzer":0}); return jsonify({"s":"reset"})

if __name__ == '__main__':
    t = threading.Thread(target=serial_loop); t.daemon = True; t.start()
    start_audio_stream()
    app.run(host='0.0.0.0', port=5000)
