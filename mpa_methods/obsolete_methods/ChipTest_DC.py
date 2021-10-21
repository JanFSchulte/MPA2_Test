

t0 = time.time()
power_on()
sleep(1)
mpa_reset()
activate_I2C_chip()
align_out()
gnd_val = measure_gnd() # Measure the analog ground level
bias_val = calibrate_chip(gnd_val) # Calibrate the chip
bg_val = measure_bg()
thDAC = measure_DAC_testblocks(point = 5, bit = 8, step = 32, plot = 0, print_file = 0, filename = "../Th_DAC")
calDAC = measure_DAC_testblocks(point = 6, bit = 8, step = 32, plot = 0, print_file = 0, filename = "../Cal_DAC")
trimDAC_amplitude(20) # Optimal Trimming DAC obtained experimentally
sleep(3)
thLSB = np.mean((thDAC[:,160] - thDAC[:,0])/160)*1000 #LSB Threshold DAC in mV
calLSB = np.mean((calDAC[:,160] - calDAC[:,0])/160)*0.035/1.768*1000 #LSB Calibration DAC in fC
th_H = int(round(130*thLSB/1.456))
th_L = int(round(100*thLSB/1.456))
cal_H = 30#int(round(30*0.035/calLSB))
cal_L = 15#int(round(15*0.035/calLSB))
data_array,th_A, noise_A, pix_out = trimming_chip(s_type = "CAL", ref_val = th_H, nominal_DAC = cal_H, nstep = 1,      n_pulse = 200, iteration = 1, extract = 1, plot = 0, stop = 100, ratio = 2.36, print_file = 0)
data_array,th_B, noise_B, pix_out = trimming_chip(s_type = "CAL", ref_val = th_L, nominal_DAC = cal_L, nstep = 1,      n_pulse = 200, iteration = 1, extract = 1, plot = 0, stop = 100, ratio = 2.36, print_file = 0)
#scurve, th_B, noise_B = s_curve_rbr_fr(n_pulse = 200,  s_type = "CAL", ref_val = th_L, row = range(1,17), step = 1, start = 0, stop = 50, pulse_delay = 200, extract = 1, extract_val = cal_L, plot = 0, print_file =0)
gain = (th_H-th_L)/(th_A[1:1920] - th_B[1:1920]) * thLSB / calLSB # Average
t1 = time.time()


############ Digital Test #####################
###############################################
########### Analog pixel injection ############
###############################################
pix = []
pix.append(analog_pixel_test(print_log=0))
if len(pix[0]) > 0: pix.append(analog_pixel_test(print_log=0))
badpix = pix[0]
goodpix = []
for i in range(1, len(pix)):
    for j in badpix:
        if j not in pix[i]:
            goodpix.append(j)
for i in goodpix:
    badpix.remove(i)
anapix = badpix


###############################################
########### Memory test ############
###############################################
set_DVDD(1.2)
sleep(1)
pix = []
mempix = []
pix.append(mem_test(print_log=0, gate = 0))
if len(pix[0]) > 0: pix.append(mem_test(print_log=0))
badpix = pix[0]
goodpix = []
for i in range(1, len(pix)):
    for j in badpix:
        if j not in pix[i]:
            goodpix.append(j)
for i in goodpix:
    badpix.remove(i)
mempix.append(badpix)
badpix12 = badpix

set_DVDD(1.0)
sleep(1)
pix = []
mempix = []
pix.append(mem_test(print_log=0, gate = 0))
if len(pix[0]) > 0: pix.append(mem_test(print_log=0))
badpix = pix[0]
goodpix = []
for i in range(1, len(pix)):
    for j in badpix:
        if j not in pix[i]:
            goodpix.append(j)
for i in goodpix:
    badpix.remove(i)
mempix.append(badpix)
badpix10 = badpix

strip_in = strip_in_scan(n_pulse = 2, print_file = 0)
good_si = 0
for i in range(0,16):
    if (np.mean(strip_in[13,:] > 0.9) == 1):
        good_si = 1
#power_off()
t2 = time.time()

print
print "-------------------------------------"
print "-------------------------------------"
print "Analog Ground:       ", np.mean(gnd_val)
print "Bandgap value:       ", bg_val
print "Threshold LSB:       ", thLSB
print "Calibration LSB:     ", calLSB
print "Threshold Average:   ", np.mean(th_B[1:1920])
print "Th. Spread SD:       ", np.std(th_B[1:1920])
print "Noise Average:       ", np.mean(noise_B[1:1920])* calLSB * 6241.5
print "Noise Spread SD:     ", np.std(noise_B[1:1920])* calLSB * 6241.5
print "Gain Average:        ", np.mean(gain)
print "Gain SD:             ", np.std(gain)
print "Analog Elapsed Time: " + str(t1 - t0)
print "-------------------------------------"
print "-------------------------------------"
print "Pixel Failure:       ", len(anapix)
print "Memory Failure@1.20: ", len(badpix12)
print "Memory Failure@1.00: ", len(badpix10)
print "Strip In:            ", good_si
print "Total Elapsed Time:  ", str(t2 - t0)
print "-------------------------------------"
print "-------------------------------------"
