"c:\Program Files\Atmel\Atmel Studio 6.1\atbackend\atprogram.exe" -t jtagicemkii -i jtag -d at32uc3a3256 erase 
"c:\Program Files\Atmel\Atmel Studio 6.1\atbackend\atprogram.exe" -t jtagicemkii -i jtag -d at32uc3a3256 erase -up
"c:\Program Files\Atmel\Atmel Studio 6.1\atbackend\atprogram.exe" -t jtagicemkii -i jtag -d at32uc3a3256 read -o 0x80800000 -s 128
"c:\Program Files\Atmel\Atmel Studio 6.1\atbackend\atprogram.exe" -t jtagicemkii -i jtag -d at32uc3a3256 program -c -f d:\fc7_mmc.hex
"c:\Program Files\Atmel\Atmel Studio 6.1\atbackend\atprogram.exe" -t jtagicemkii -i jtag -d at32uc3a3256 read -o 0x80800000 -s 128
