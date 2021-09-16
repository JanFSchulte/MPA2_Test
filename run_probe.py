import Gpib
import csv
ProbeStation = Gpib.Gpib(1,22)
for i in range(6,188):
    try:
        gnd = -1000
        bg = -1000
        pos = -1000
        wafer_n = -1000
        lot = -1000
        status = -1000
        process = -1000
        adc_ref = -1000
        mpa.pwr.on()
        mpa.init( reset_chip =1, reset_board = 1)
        FC7.activate_I2C_chip()
        gnd = mpa.bias.measure_gnd()
        bg = mpa.bias.measure_bg()
        pos, wafer_n, lot, status, process, adc_ref = mpa.chip.ctrl_base.read_fuses()
        with open('../MPA2_Results/Wafer6_bg_efuse/gnd_bg.csv', 'a') as csvfile:   
            file = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
            file.writerow([i ,gnd, bg, pos, wafer_n, lot, status, process, adc_ref])
        mpa.pwr.off()
    except:
        print("ERROR")
    ProbeStation.write("StepNextDie")
