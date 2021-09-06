import Gpib
ProbeStation = Gpib.Gpib(1,22)
for i in range(5,188):
    try:
        probe = MPAProbeTest(f"../MPA2_Results/Lot1_Wafer6/chip{i}", mpa.chip, mpa.i2c, FC7, mpa.cal, mpa.test, mpa.bias)
        probe.RUN(chipinfo=99, N=i)
    except:
        print("ERROR")
    ProbeStation.write("StepNextDie")
