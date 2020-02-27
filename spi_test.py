import spidev
import time
bus = 0

device = 0

spi = spidev.SpiDev()

spi.open(bus, device)

# Speed should be faster than 10kHz as recommended by ADC data sheet
spi.max_speed_hz = 16000
spi.bits_per_word = 8

# Think this corresponds to the ADC sampling when the clock (or select?) has a rising edge
# and shift out data on a falling edge
spi.mode = 0b10
spi.threewire = False

# CS active low?
spi.cshigh = False

try:
  while True:
    # Idk how to get it to read 12 bits
    data_bytes = spi.readbytes(2)
    print(data_bytes)
    # MSB is 5 bits of first received byte
    data_MSB = (data_bytes[0] & 0x1F) << 7
    # LSB has extra bit at end
    data_LSB = data_bytes[1] >> 1
    print(data_MSB, data_LSB)
    data = data_MSB+data_LSB
    print(data)
    time.sleep(0.1)
   # break
except KeyboardInterrupt:
  spi.close()
  exit()
spi.close()
  
