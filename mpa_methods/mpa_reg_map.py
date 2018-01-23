
mpa_peri_reg_map = {'test': 0xfff}
mpa_pixel_reg_map = {'test': 0xfff}

################# Strip register map #########################

mpa_pixel_reg_map['ENFLAGS']            = 0b0000
mpa_pixel_reg_map['SAMPLINGMODE']       = 0b0001
mpa_pixel_reg_map['GAINTRIMMING']       = 0b0010
mpa_pixel_reg_map['ClusterCut']         = 0b0011
mpa_pixel_reg_map['HIPCUT']             = 0b0100
mpa_pixel_reg_map['DigCalibPattern']    = 0b0101
mpa_pixel_reg_map['ReadCounter_LSB']    = 0b1001
mpa_pixel_reg_map['ReadCounter_MSB']    = 0b1010

################# Periphery register map #####################

mpa_peri_reg_map['ReadoutMode']=   0b1000100000000000
mpa_peri_reg_map['ECM']=            0b1000100000000001
mpa_peri_reg_map['RetimePix']=      0b1000100000000010
mpa_peri_reg_map['LowPowerTL']=     0b1000100000000011
mpa_peri_reg_map['ChipN']=          0b1000100000000100
mpa_peri_reg_map['CodeDM8']=        0b1000100000000101
mpa_peri_reg_map['CodeM76']=        0b1000100000000110
mpa_peri_reg_map['CodeM54']=        0b1000100000000111
mpa_peri_reg_map['CodeM32']=        0b1000100000001000
mpa_peri_reg_map['CodeM10']=        0b1000100000001001
mpa_peri_reg_map['CodeP12']=        0b1000100000001010
mpa_peri_reg_map['CodeP34']=        0b1000100000001011
mpa_peri_reg_map['CodeP56']=        0b1000100000001100
mpa_peri_reg_map['CodeP78']=        0b1000100000001101
mpa_peri_reg_map['OutSetting_0']=   0b1000100000001110
mpa_peri_reg_map['OutSetting_1']=   0b1000100000001111
mpa_peri_reg_map['OutSetting_2']=   0b1000100000010000
mpa_peri_reg_map['OutSetting_3']=   0b1000100000010001
mpa_peri_reg_map['OutSetting_4']=   0b1000100000010010
mpa_peri_reg_map['OutSetting_5']=   0b1000100000010011
mpa_peri_reg_map['InSetting_0']=	0b1000100000010100
mpa_peri_reg_map['InSetting_1']=	0b1000100000010101
mpa_peri_reg_map['InSetting_2']=	0b1000100000010110
mpa_peri_reg_map['InSetting_3']=	0b1000100000010111
mpa_peri_reg_map['InSetting_4']=	0b1000100000011000
mpa_peri_reg_map['InSetting_5']=	0b1000100000011001
mpa_peri_reg_map['InSetting_6']=	0b1000100000011010
mpa_peri_reg_map['InSetting_7']=	0b1000100000011011
mpa_peri_reg_map['InSetting_8']=	0b1000100000011100
mpa_peri_reg_map['EdgeSelTrig']=	0b1000100000011101
mpa_peri_reg_map['EdgeSelT1Raw']=	0b1000100000011110
mpa_peri_reg_map['ConfDLL']=        0b1000100000011111
mpa_peri_reg_map['PhaseShift']=     0b1000100000100000
mpa_peri_reg_map['CalLen']=         0b1000100000100001
mpa_peri_reg_map['LatencyRx320']=	0b1000100000100010
mpa_peri_reg_map['LatencyRx40']=	0b1000100000100011
mpa_peri_reg_map['LFSR_data']=      0b1000100000100100
mpa_peri_reg_map['ClkEnable']=      0b1000100000100101
mpa_peri_reg_map['ConfSLVS']=       0b1000100000100110
mpa_peri_reg_map['SEUcntPeri']=     0b1000100000100111
mpa_peri_reg_map['ErrorL1']=        0b1000100000101000
mpa_peri_reg_map['OFcnt']=          0b1000100000101001
mpa_peri_reg_map['L1OffsetPeri_1']=	0b1000100000101010
mpa_peri_reg_map['L1OffsetPeri_2']=	0b1000100000101011
mpa_peri_reg_map['SSAOffset_1']=	0b1000100000101100
mpa_peri_reg_map['SSAOffset_2']=	0b1000100000101101
mpa_peri_reg_map['EfuseMode']=      0b1000100000110010
mpa_peri_reg_map['EfuseProg0']=     0b1000100000110011
mpa_peri_reg_map['EfuseProg1']=     0b1000100000110100
mpa_peri_reg_map['EfuseProg2']=     0b1000100000110101
mpa_peri_reg_map['EfuseProg3']=     0b1000100000110110
mpa_peri_reg_map['EfuseValue0']=	0b1000100000110111
mpa_peri_reg_map['EfuseValue1']=	0b1000100000111000
mpa_peri_reg_map['EfuseValue2']=	0b1000100000111001
mpa_peri_reg_map['EfuseValue3']=	0b1000100000111010
mpa_peri_reg_map['CalDAC0']=        0b1000100001000000
mpa_peri_reg_map['CalDAC1']=        0b1000100001000001
mpa_peri_reg_map['CalDAC2']=        0b1000100001000010
mpa_peri_reg_map['CalDAC3']=        0b1000100001000011
mpa_peri_reg_map['CalDAC4']=        0b1000100001000100
mpa_peri_reg_map['CalDAC5']=        0b1000100001000101
mpa_peri_reg_map['CalDAC6']=        0b1000100001000110
mpa_peri_reg_map['ThDAC0']=         0b1000100001000111
mpa_peri_reg_map['ThDAC1']=         0b1000100001001000
mpa_peri_reg_map['ThDAC2']=         0b1000100001001001
mpa_peri_reg_map['ThDAC3']=         0b1000100001001010
mpa_peri_reg_map['ThDAC4']=         0b1000100001001011
mpa_peri_reg_map['ThDAC5']=         0b1000100001001100
mpa_peri_reg_map['ThDAC6']=         0b1000100001001101
mpa_peri_reg_map['A0']=             0b1000100001001110
mpa_peri_reg_map['A1']=             0b1000100001001111
mpa_peri_reg_map['A2']=             0b1000100001010000
mpa_peri_reg_map['A3']=             0b1000100001010001
mpa_peri_reg_map['A4']=             0b1000100001010010
mpa_peri_reg_map['A5']=             0b1000100001010011
mpa_peri_reg_map['A6']=             0b1000100001010100
mpa_peri_reg_map['B0']=             0b1000100001010101
mpa_peri_reg_map['B1']=             0b1000100001010110
mpa_peri_reg_map['B2']=             0b1000100001010111
mpa_peri_reg_map['B3']=             0b1000100001011000
mpa_peri_reg_map['B4']=             0b1000100001011001
mpa_peri_reg_map['B5']=             0b1000100001011010
mpa_peri_reg_map['B6']=             0b1000100001011011
mpa_peri_reg_map['C0']=             0b1000100001011100
mpa_peri_reg_map['C1']=             0b1000100001011101
mpa_peri_reg_map['C2']=             0b1000100001011110
mpa_peri_reg_map['C3']=             0b1000100001011111
mpa_peri_reg_map['C4']=             0b1000100001100000
mpa_peri_reg_map['C5']=             0b1000100001100001
mpa_peri_reg_map['C6']=             0b1000100001100010
mpa_peri_reg_map['D0']=             0b1000100001100011
mpa_peri_reg_map['D1']=             0b1000100001100100
mpa_peri_reg_map['D2']=             0b1000100001100101
mpa_peri_reg_map['D3']=             0b1000100001100110
mpa_peri_reg_map['D4']=             0b1000100001100111
mpa_peri_reg_map['D5']=             0b1000100001101000
mpa_peri_reg_map['D6']=             0b1000100001101001
mpa_peri_reg_map['E0']=             0b1000100001101010
mpa_peri_reg_map['E1']=             0b1000100001101011
mpa_peri_reg_map['E2']=             0b1000100001101100
mpa_peri_reg_map['E3']=             0b1000100001101101
mpa_peri_reg_map['E4']=             0b1000100001101110
mpa_peri_reg_map['E5']=             0b1000100001101111
mpa_peri_reg_map['E6']=             0b1000100001110000
mpa_peri_reg_map['F0']=             0b1000100001110001
mpa_peri_reg_map['F1']=             0b1000100001110010
mpa_peri_reg_map['F2']=             0b1000100001110011
mpa_peri_reg_map['F3']=             0b1000100001110100
mpa_peri_reg_map['F4']=             0b1000100001110101
mpa_peri_reg_map['F5']=             0b1000100001110110
mpa_peri_reg_map['F6']=             0b1000100001110111
mpa_peri_reg_map['TEST0']=          0b1000100001111000
mpa_peri_reg_map['TEST1']=          0b1000100001111001
mpa_peri_reg_map['TEST2']=          0b1000100001111010
mpa_peri_reg_map['TEST3']=          0b1000100001111011
mpa_peri_reg_map['TEST4']=          0b1000100001111100
mpa_peri_reg_map['TEST5']=          0b1000100001111101
mpa_peri_reg_map['TEST6']=          0b1000100001111110
mpa_peri_reg_map['TESTMUX']=        0b1000100001111111
mpa_peri_reg_map['DL_en']=          0b1000100010000000
mpa_peri_reg_map['DL_ctrl0']=       0b1000100010000001
mpa_peri_reg_map['DL_ctrl1']=       0b1000100010000010
mpa_peri_reg_map['DL_ctrl2']=       0b1000100010000011
mpa_peri_reg_map['DL_ctrl3']=       0b1000100010000100
mpa_peri_reg_map['DL_ctrl4']=       0b1000100010000101
mpa_peri_reg_map['DL_ctrl5']=       0b1000100010000110
mpa_peri_reg_map['DL_ctrl6']=       0b1000100010000111
