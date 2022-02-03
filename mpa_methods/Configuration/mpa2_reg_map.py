
mpa_peri_reg_map = {'test': 0xfff}
mpa_pixel_reg_map = {'test': 0xfff}
mpa_row_reg_map = {'test': 0xfff}
mpa_row_wr_reg = 0b1111001
mpa_row_ro0_reg = 0b1111010
mpa_row_ro1_reg = 0b1111011
################# Pixel register map #########################

mpa_pixel_reg_map['PixelEnables']      = 0b0000
mpa_pixel_reg_map['TrimDAC']            = 0b0001
mpa_pixel_reg_map['DigPattern']         = 0b0010
mpa_pixel_reg_map['-']                  = 0b0011
mpa_pixel_reg_map['AC_ReadCounterLSB']  = 0b0100
mpa_pixel_reg_map['AC_ReadCounterMSB']  = 0b0101

################# Memory register map #########################
mpa_row_reg_map['MemoryControl_1']              = (0b0000<<7) | mpa_row_wr_reg
mpa_row_reg_map['MemoryControl_2']              = (0b0001<<7) | mpa_row_wr_reg
mpa_row_reg_map['PixelControl']                 = (0b0010<<7) | mpa_row_wr_reg
mpa_row_reg_map['RingOscillator']               = (0b0011<<7) | mpa_row_wr_reg
mpa_row_reg_map['SRAM_BIST']                    = (0b0100<<7) | mpa_row_wr_reg
mpa_row_reg_map['RowLogic_BIST']                = (0b0101<<7) | mpa_row_wr_reg
mpa_row_reg_map['RowLogic_BIST_input_1']        = (0b0110<<7) | mpa_row_wr_reg
mpa_row_reg_map['RowLogic_BIST_input_2']        = (0b0111<<7) | mpa_row_wr_reg
mpa_row_reg_map['RowLogic_BIST_ref_output_1']   = (0b1000<<7) | mpa_row_wr_reg
mpa_row_reg_map['RowLogic_BIST_ref_output_2']   = (0b1001<<7) | mpa_row_wr_reg
mpa_row_reg_map['-']                            = (0b1010<<7) | mpa_row_wr_reg
mpa_row_reg_map['-']                            = (0b1011<<7) | mpa_row_wr_reg
mpa_row_reg_map['-']                            = (0b1100<<7) | mpa_row_wr_reg
mpa_row_reg_map['Mask']                         = (0b1101<<7) | mpa_row_wr_reg
mpa_row_reg_map['Async_SEUcntPixels']           = (0b1110<<7) | mpa_row_wr_reg
mpa_row_reg_map['Sync_SEUcntRow']               = (0b1111<<7) | mpa_row_wr_reg


################# Row register map - Read only #########################
mpa_row_reg_map['RowBIST_summary_reg']          = (0b0000<<7) | mpa_row_ro0_reg
mpa_row_reg_map['RO_Row_Del_LSB']   = (0b0001<<7) | mpa_row_ro0_reg
mpa_row_reg_map['RO_Row_Del_MSB']   = (0b0010<<7) | mpa_row_ro0_reg
mpa_row_reg_map['RO_Row_Inv_LSB']   = (0b0011<<7) | mpa_row_ro0_reg
mpa_row_reg_map['RO_Row_Inv_MSB']   = (0b0100<<7) | mpa_row_ro0_reg
mpa_row_reg_map['SRAM_BIST_done']               = (0b0101<<7) | mpa_row_ro0_reg
mpa_row_reg_map['SRAM_BIST_fail']               = (0b0110<<7) | mpa_row_ro0_reg


mpa_row_reg_map['BIST_SRAM_output_0']           = (0b0000<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_1']           = (0b0001<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_2']           = (0b0010<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_3']           = (0b0011<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_4']           = (0b0100<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_5']           = (0b0101<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_6']           = (0b0110<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_7']           = (0b0111<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_8']           = (0b1000<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_9']           = (0b1001<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_10']          = (0b1010<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_11']          = (0b1011<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_12']          = (0b1100<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_13']          = (0b1101<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_14']          = (0b1110<<7) | mpa_row_ro1_reg
mpa_row_reg_map['BIST_SRAM_output_15']          = (0b1111<<7) | mpa_row_ro1_reg


################# Periphery register map #####################

mpa_peri_reg_map['Control']=     0b1000100000000000
mpa_peri_reg_map['ECM']=            0b1000100000000001
mpa_peri_reg_map['LowPowerTL']=     0b1000100000000010
mpa_peri_reg_map['CodeDM8']=        0b1000100000000011
mpa_peri_reg_map['CodeM76']=        0b1000100000000100
mpa_peri_reg_map['CodeM54']=        0b1000100000000101
mpa_peri_reg_map['CodeM32']=        0b1000100000000110
mpa_peri_reg_map['CodeM10']=        0b1000100000000111
mpa_peri_reg_map['CodeP12']=        0b1000100000001000
mpa_peri_reg_map['CodeP34']=        0b1000100000001001
mpa_peri_reg_map['CodeP56']=        0b1000100000001010
mpa_peri_reg_map['CodeP78']=        0b1000100000001011
mpa_peri_reg_map['OutSetting_1_0']= 0b1000100000001100
mpa_peri_reg_map['OutSetting_3_2']= 0b1000100000001101
mpa_peri_reg_map['OutSetting_5_4']= 0b1000100000001110
mpa_peri_reg_map['InSetting_1_0']=  0b1000100000001111
mpa_peri_reg_map['InSetting_3_2']=  0b1000100000010000
mpa_peri_reg_map['InSetting_5_4']=  0b1000100000010001
mpa_peri_reg_map['InSetting_7_6']=  0b1000100000010010
mpa_peri_reg_map['InSetting_8']=    0b1000100000010011
mpa_peri_reg_map['EdgeSelTrig']=    0b1000100000010100
mpa_peri_reg_map['EdgeSelT1Raw']=   0b1000100000010101
mpa_peri_reg_map['ConfDLL']=        0b1000100000010110
mpa_peri_reg_map['CalLen']=	        0b1000100000010111
mpa_peri_reg_map['LatencyRx320']=   0b1000100000011000
mpa_peri_reg_map['LatencyRx40']=    0b1000100000011001
mpa_peri_reg_map['LFSR_data']=      0b1000100000011010
mpa_peri_reg_map['ConfSLVS']=       0b1000100000011011
mpa_peri_reg_map['TimeoutLimit']=   0b1000100000011100
mpa_peri_reg_map["-"]=              0b1000100000011101
mpa_peri_reg_map['SSAOffset_1']=	0b1000100000011110
mpa_peri_reg_map['SSAOffset_2']=    0b1000100000011111
mpa_peri_reg_map['ClkTreeControl']= 0b1000100000100000
mpa_peri_reg_map['EfuseMode']=      0b1000100000100001
mpa_peri_reg_map['EfuseProg0']=	    0b1000100000100010
mpa_peri_reg_map['EfuseProg1']=	    0b1000100000100011
mpa_peri_reg_map['EfuseProg2']=     0b1000100000100100
mpa_peri_reg_map['EfuseProg3']=     0b1000100000100101
mpa_peri_reg_map['RingOscillator']= 0b1000100000100110
mpa_peri_reg_map['CalDAC0'] =       0b1000100000100111
mpa_peri_reg_map['CalDAC1'] =       0b1000100000101000
mpa_peri_reg_map['CalDAC2'] =       0b1000100000101001
mpa_peri_reg_map['CalDAC3'] =       0b1000100000101010
mpa_peri_reg_map['CalDAC4'] =       0b1000100000101011
mpa_peri_reg_map['CalDAC5'] =       0b1000100000101100
mpa_peri_reg_map['CalDAC6'] =       0b1000100000101101
mpa_peri_reg_map['ThDAC0'] =        0b1000100000101110
mpa_peri_reg_map['ThDAC1'] =        0b1000100000101111
mpa_peri_reg_map['ThDAC2'] =        0b1000100000110000
mpa_peri_reg_map['ThDAC3'] =        0b1000100000110001
mpa_peri_reg_map['ThDAC4'] =        0b1000100000110010
mpa_peri_reg_map['ThDAC5'] =        0b1000100000110011
mpa_peri_reg_map['ThDAC6'] =        0b1000100000110100
mpa_peri_reg_map['A0']=             0b1000100000110101
mpa_peri_reg_map['A1']=             0b1000100000110110
mpa_peri_reg_map['A2']=             0b1000100000110111
mpa_peri_reg_map['A3']=             0b1000100000111000
mpa_peri_reg_map['A4']=             0b1000100000111001
mpa_peri_reg_map['A5']=             0b1000100000111010
mpa_peri_reg_map['A6']=             0b1000100000111011
mpa_peri_reg_map['B0']=             0b1000100000111100
mpa_peri_reg_map['B1']=             0b1000100000111101
mpa_peri_reg_map['B2']=             0b1000100000111110
mpa_peri_reg_map['B3']=             0b1000100000111111
mpa_peri_reg_map['B4']=             0b1000100001000000
mpa_peri_reg_map['B5']=             0b1000100001000001
mpa_peri_reg_map['B6']=             0b1000100001000010
mpa_peri_reg_map['C0']=             0b1000100001000011
mpa_peri_reg_map['C1']=             0b1000100001000100
mpa_peri_reg_map['C2']=             0b1000100001000101
mpa_peri_reg_map['C3']=             0b1000100001000110
mpa_peri_reg_map['C4']=             0b1000100001000111
mpa_peri_reg_map['C5']=             0b1000100001001000
mpa_peri_reg_map['C6']=             0b1000100001001001
mpa_peri_reg_map['D0']=             0b1000100001001010
mpa_peri_reg_map['D1']=             0b1000100001001011
mpa_peri_reg_map['D2']=             0b1000100001001100
mpa_peri_reg_map['D3']=             0b1000100001001101
mpa_peri_reg_map['D4']=             0b1000100001001110
mpa_peri_reg_map['D5']=             0b1000100001001111
mpa_peri_reg_map['D6']=             0b1000100001010000
mpa_peri_reg_map['E0']=             0b1000100001010001
mpa_peri_reg_map['E1']=             0b1000100001010010
mpa_peri_reg_map['E2']=             0b1000100001010011
mpa_peri_reg_map['E3']=             0b1000100001010100
mpa_peri_reg_map['E4']=             0b1000100001010101
mpa_peri_reg_map['E5']=             0b1000100001010110
mpa_peri_reg_map['E6']=             0b1000100001010111
mpa_peri_reg_map['F0']=             0b1000100001011000
mpa_peri_reg_map['F1']=             0b1000100001011001
mpa_peri_reg_map['F2']=             0b1000100001011010
mpa_peri_reg_map['F3']=             0b1000100001011011
mpa_peri_reg_map['F4']=             0b1000100001011100
mpa_peri_reg_map['F5']=             0b1000100001011101
mpa_peri_reg_map['F6']=             0b1000100001011110
mpa_peri_reg_map['-']=              0b1000100001011111
mpa_peri_reg_map['DL_en']=          0b1000100001100000
mpa_peri_reg_map['DL_ctrl0']=       0b1000100001100001
mpa_peri_reg_map['DL_ctrl1']=       0b1000100001100010
mpa_peri_reg_map['DL_ctrl2']=       0b1000100001100011
mpa_peri_reg_map['DL_ctrl3']=       0b1000100001100100
mpa_peri_reg_map['DL_ctrl4']=       0b1000100001100101
mpa_peri_reg_map['DL_ctrl5']=       0b1000100001100110
mpa_peri_reg_map['DL_ctrl6']=       0b1000100001100111
mpa_peri_reg_map['ADCcontrol']=     0b1000100001101000
mpa_peri_reg_map['ADCtrimming']=    0b1000100001101001
mpa_peri_reg_map['ADC_TEST_selection']= 0b1000100001101010
mpa_peri_reg_map['BypassMode']=     0b1000100001101011
mpa_peri_reg_map['Mask']=           0b1000100001101100
mpa_peri_reg_map['Async_SEUcntPeri']=   0b1000100001101101
mpa_peri_reg_map['Sync_SEUcntPeri']=    0b1000100001101110

################# Periphery register map - Read only #####################

mpa_peri_reg_map['ErrorL1']=        0b1001000000000000
mpa_peri_reg_map['Ofcnt']=          0b1001000000000001
mpa_peri_reg_map['EfuseValue0']=    0b1001000000000010
mpa_peri_reg_map['EfuseValue1']=        0b1001000000000011
mpa_peri_reg_map['EfuseValue2']=        0b1001000000000100
mpa_peri_reg_map['EfuseValue3']=        0b1001000000000101
mpa_peri_reg_map['DLLlocked']=      0b1001000000000110
mpa_peri_reg_map['RO_Inv_LSB']= 0b1001000000000111
mpa_peri_reg_map['RO_Inv_MSB']= 0b1001000000001000
mpa_peri_reg_map['RO_Del_LSB']= 0b1001000000001001
mpa_peri_reg_map['RO_Del_MSB']= 0b1001000000001010
mpa_peri_reg_map['ADC_output_LSB']=        0b1001000000001011
mpa_peri_reg_map['ADC_output_MSB']= 0b1001000000001100
mpa_peri_reg_map['L1_miss_pixel']=  0b1001000000001101
mpa_peri_reg_map['L1_miss_strip']=  0b1001000000001110
mpa_peri_reg_map['L1_OF_FIFO_pixel']=   0b1001000000001111
mpa_peri_reg_map['L1_OF_FIFO_strip']=   0b1001000000010000
mpa_peri_reg_map['OF_out_count']=   0b1001000000010001
mpa_peri_reg_map['OF_stub_count']=  0b1001000000010010