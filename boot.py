import usb_hid

# Nastavení Gamepadu: Rozsah -127 až 127, 32 tlačítek
GAMEPAD_REPORT_DESCRIPTOR = bytes((
    0x05, 0x01,  # Usage Page (Generic Desktop Ctrls)
    0x09, 0x05,  # Usage (Game Pad)
    0xA1, 0x01,  # Collection (Application)
    0x85, 0x04,  #   Report ID (4)
    
    # --- 32 Tlačítek (4 byty) ---
    0x05, 0x09,  # Usage Page (Button)
    0x19, 0x01,  # Usage Minimum (Button 1)
    0x29, 0x20,  # Usage Maximum (Button 32) <--- ZMĚNA (0x20 je 32 v hex)
    0x15, 0x00,  # Logical Minimum (0)
    0x25, 0x01,  # Logical Maximum (1)
    0x75, 0x01,  # Report Size (1 bit)
    0x95, 0x20,  # Report Count (32)       <--- ZMĚNA (0x20 je 32 v hex)
    0x81, 0x02,  # Input (Data,Var,Abs)
    
    # --- 6 Os (X, Y, Z, Rx, Ry, Rz) - (6 bytů) ---
    0x05, 0x01,  # Usage Page (Generic Desktop Ctrls)
    0x09, 0x30,  # Usage (X)
    0x09, 0x31,  # Usage (Y)
    0x09, 0x32,  # Usage (Z)
    0x09, 0x33,  # Usage (Rx)
    0x09, 0x34,  # Usage (Ry)
    0x09, 0x35,  # Usage (Rz)
    
    0x15, 0x81,  # LOGICAL MINIMUM (-127) 
    0x25, 0x7F,  # LOGICAL MAXIMUM (127)
    0x75, 0x08,  # Report Size (8 bitů)
    0x95, 0x06,  # Report Count (6 os)
    0x81, 0x02,  # Input
    
    0xC0         # End Collection
))

gamepad = usb_hid.Device(
    report_descriptor=GAMEPAD_REPORT_DESCRIPTOR,
    usage_page=0x01,
    usage=0x05,
    report_ids=(4,),
    in_report_lengths=(10,),  # <--- ZMĚNA: 4 byty (tlačítka) + 6 bytů (osy) = 10 bytů celkem
    out_report_lengths=(0,)
)

usb_hid.enable((gamepad,))