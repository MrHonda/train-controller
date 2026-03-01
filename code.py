import time
import board
import analogio
import digitalio
import usb_hid
import struct

import encoder_handler

# --- KALIBRACE ---
MIN_RAW = [
    1000,
    700,
    650,
    550,
    800,
]

MAX_RAW = [
    29800,
    28600,
    27800,
    28000,
    28100,
]

# --- VYHLAZOVÁNÍ (SMOOTHING) ---
# Hodnota mezi 0.01 a 1.0. 
# - Menší číslo (např. 0.05) = silnější vyhlazení, ale páčka může působit "gumově" a opožděně.
# - Větší číslo (např. 0.3) = rychlejší reakce, ale menší vyhlazení.
SMOOTHING_FACTOR = 0.15 

# Pole pro uchování předchozích hodnot pro každou z 5 os
smoothed_raw = [None] * 5

# --- HARDWARE: ANALOG ---
adc = analogio.AnalogIn(board.GP26)
s0 = digitalio.DigitalInOut(board.GP18)
s0.direction = digitalio.Direction.OUTPUT
s1 = digitalio.DigitalInOut(board.GP17)
s1.direction = digitalio.Direction.OUTPUT
s2 = digitalio.DigitalInOut(board.GP16)
s2.direction = digitalio.Direction.OUTPUT

# --- HARDWARE: ENKODÉR ---
# Enkodéry obsazují bity (tlačítka) 0 až 7
encoders = [
    encoder_handler.Encoder(board.GP15, board.GP14),  # Enkodér 1 (Bity 0, 1)
    encoder_handler.Encoder(board.GP13, board.GP12),  # Enkodér 2 (Bity 2, 3)
    encoder_handler.Encoder(board.GP11, board.GP10),  # Enkodér 3 (Bity 4, 5)
    encoder_handler.Encoder(board.GP9, board.GP8)     # Enkodér 4 (Bity 6, 7)
]

# --- HARDWARE: TLAČÍTKA ---
# Mapa tlačítek: (Pin, Index bitu)
# Používej indexy 8 až 15, protože 0-7 už mají enkodéry.
BUTTON_MAP = [
    (board.GP19, 8),
    (board.GP20, 9),
    (board.GP21, 10),
    (board.GP22, 11),
    (board.GP3, 12),
    (board.GP2, 13),
]

buttons = []
for pin, bit_index in BUTTON_MAP:
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    # ZMĚNA ZDE: Použijeme Pull.DOWN, protože spínáš proti 3.3V
    btn.pull = digitalio.Pull.DOWN 
    buttons.append((btn, bit_index))


# --- USB ---
gamepad_device = None
for device in usb_hid.devices:
    if device.usage == 0x05 and device.usage_page == 0x01:
        gamepad_device = device
        break

if not gamepad_device:
    print("CHYBA: Gamepad nenalezen!")
    while True: time.sleep(1)

report = bytearray(8)

# --- POMOCNÉ FUNKCE ---
def read_adc(channel):
    s0.value = (channel & 1)
    s1.value = (channel >> 1) & 1
    s2.value = (channel >> 2) & 1
    time.sleep(0.001)
    return adc.value

def map_range(x, in_min, in_max, out_min, out_max):
    if (in_max - in_min) == 0: return out_min
    val = (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min
    return val

def ziskej_data_kanalu(channel):
    global smoothed_raw
    
    raw = read_adc(channel)
    
    # Aplikace vyhlazení (EMA filter)
    if smoothed_raw[channel] is None:
        smoothed_raw[channel] = raw # První načtení rovnou uložíme, aby to nezačínalo od nuly
    else:
        smoothed_raw[channel] = (raw * SMOOTHING_FACTOR) + (smoothed_raw[channel] * (1.0 - SMOOTHING_FACTOR))
    
    # Ořezání a mapování už děláme s VYHLAZENOU hodnotou
    clamped = int(smoothed_raw[channel])
    
    if clamped < MIN_RAW[channel]: clamped = MIN_RAW[channel]
    if clamped > MAX_RAW[channel]: clamped = MAX_RAW[channel]
    
    mapped = map_range(clamped, MIN_RAW[channel], MAX_RAW[channel], 0, 127)
    perc = int((mapped / 127) * 100)
    
    # Vracíme aktuální vyhlazený raw, mapovanou hodnotu a procenta
    return int(smoothed_raw[channel]), int(mapped), perc

# --- HLAVNÍ SMYČKA ---
print(f"Start: Raw {MIN_RAW}-{MAX_RAW} -> Axis 0-127")
labels = ["X", "Y", "Z", "Rx", "Ry", "Rz"]

while True:
    final_axes = []
    print_str = ""
    buttons_state = 0
    
    # 1. ČTENÍ VŠECH 4 ENKODÉRŮ
    for index, enc in enumerate(encoders):
        state = enc.update()
        base_bit = index * 2 
        
        if state == 1: # VLEVO
            buttons_state |= (1 << base_bit)
            # print(f"Enc {index+1}: VLEVO")
            
        elif state == 2: # VPRAVO
            buttons_state |= (1 << (base_bit + 1))
            # print(f"Enc {index+1}: VPRAVO")

    # 2. ČTENÍ KLASICKÝCH TLAČÍTEK
    for btn, bit_index in buttons:
        # ZMĚNA ZDE: btn.value je True, když je tlačítko stisknuto a přivádí 3.3V
        if btn.value: 
            buttons_state |= (1 << bit_index)
            # print(f"Btn {bit_index+1}")
    
    # 3. ČTENÍ ANALOGOVÝCH OS
    for i in range(5):
        raw, joy_val, perc = ziskej_data_kanalu(i)
        final_axes.append(joy_val)
        print_str += f"P{i+1}({labels[i]}): {raw:5d}->{joy_val:3d} ({perc:3d}%) | "

    # print(print_str)

    # 4. ODESLÁNÍ DO USB
    while len(final_axes) < 6:
        final_axes.append(0)

    struct.pack_into(
        '<HBBBBBB', report, 0,
        buttons_state,
        final_axes[0], final_axes[1], final_axes[2], final_axes[3], final_axes[4], final_axes[5]
    )

    try:
        gamepad_device.send_report(report)
    except Exception:
        pass

    time.sleep(0.01)