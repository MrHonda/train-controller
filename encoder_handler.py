import rotaryio

class Encoder:
    def __init__(self, pin_dt, pin_clk):
        self.encoder = rotaryio.IncrementalEncoder(pin_dt, pin_clk)
        self.last_position = self.encoder.position

    def update(self):
        """
        Zkontroluje, zda se enkodér pohnul.
        Vrací číslo tlačítka (bitmasku):
        0 = nic
        1 = pohyb vlevo (Tlačítko 1)
        2 = pohyb vpravo (Tlačítko 2)
        """
        current_position = self.encoder.position
        diff = current_position - self.last_position
        self.last_position = current_position

        if diff > 0:
            return 2  # (1 << 1) -> Bit pro druhé tlačítko
        elif diff < 0:
            return 1  # (1 << 0) -> Bit pro první tlačítko
        else:
            return 0