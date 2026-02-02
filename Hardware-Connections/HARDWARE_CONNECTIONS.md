# Hardware Connections Guide: Smart Rural Triage Station

**Final Phase Implementation Guide (Qwiic Edition)**

This document provides the exact wiring instructions for your build using **Modulino Qwiic Sensors** and the **Separate Audio/OLED Modules**.

> [!IMPORTANT]
> **Safety First:** Disconnect power while wiring.
> *   **Qwiic/I2C Devices:** Daisy-chain them together.
> *   **Analog/Digital Devices:** Use Jumper Wires to the headers.

---

## Component Checklist
-   **Main Board:** Arduino UNO Q
-   **I2C/Qwiic Chain:** Modulino Knob, Modulino Movement, Modulino Temp, Modulino Buzzer, OLED Display (128x64).
-   **Analog/Digital (Pinned):** MAX9814 Mic, 2x Servos, LEDs.

---

## Step 1: The Qwiic Daisy Chain (Data Bus)
Connect these components in a chain using Qwiic cables (or wire them all to the same SDA/SCL pins if they don't have Qwiic ports).

1.  **Arduino Qwiic Port** ➡️ **OLED Display**
2.  **OLED Display** ➡️ **Modulino Knob**
3.  **Modulino Knob** ➡️ **Modulino Temperature**
4.  **Modulino Temperature** ➡️ **Modulino Movement**
5.  **Modulino Movement** ➡️ **Modulino Buzzer**
    *   *(Order does not matter, just chain them all together).*

> **OLED Note:** If your OLED does not have a Qwiic connector:
> *   **VCC** → 3.3V
> *   **GND** → Black Rail
> *   **SDA** → Arduino SDA
> *   **SCL** → Arduino SCL

---

## Step 2: The Audio Module (MAX9814)
The Microphone is **Analog**, not I2C. It must effectively "listen" to values.

*   **VCC:** Connect to **3.3V** (or 5V if supported, 3.3V is safer).
*   **GND:** Connect to **Black Rail (GND)**.
*   **OUT:** Connect to **Arduino Pin A1**.
    *   *(We use A1 because standard A0 might be default for other tests).*

---

## Step 3: Actuators (Servos & LEDs)
These require high power and specific signal pins. Use Jumper Wires.

### 1. Servo Motor 1 (Progress Bar)
*   **Red:** 5V Rail
*   **Brown/Black:** GND Rail
*   **Orange (Signal):** **Pin D9**

### 2. Servo Motor 2 (Result Indicator)
*   **Red:** 5V Rail
*   **Brown/Black:** GND Rail
*   **Orange (Signal):** **Pin D10**

### 3. Status LEDs (Visual Indicators)
*   **Positive (+):** **Pin D6** (Series Resistor 220Ω recommended).
*   **Negative (-):** GND Rail.

---

## ✅ Final Verification
- [ ] **I2C/Qwiic:** Are all Modulinos + OLED connected?
- [ ] **Mic:** Is MAX9814 connected to A1?
- [ ] **Servos:** Are they on D9/D10 and powered by 5V?
- [ ] **Webcam:** Plugged into USB?


