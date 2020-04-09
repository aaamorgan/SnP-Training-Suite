# SnP-Training-Suite
## Description
The Sip 'N Puff (SnP) training suite emulates a SnP alt-drive for power wheelchairs. It reads in pressure values and outputs a state that is one of: hard sip, soft sip, nothing, soft puff, and hard puff. These states can be used to interface with other programs. 
## Setup
The Emulator currently requires the pressure values to come over a SPI bus (bus 0), which means it is easiest to use on a Pi because of the ease in enabling the SPI bus.

## Instructions for Sphinx Code Generation and Viewing
Start at step 4 if it does not need to be generated.
1. Install sphinx
``` python
    pip install sphinx
```
2. Navigate into docs directory.
3. Run ```.\make.bat html``` on Windows or ```make html``` on linux.
4. Look for ```docs/_build/index.html``` and copy its path.
5. Paste path in web browser.
