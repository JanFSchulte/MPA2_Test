
################# Strip register map #########################
ssa_strip_reg_map_v1 = {}

ssa_strip_reg_map_v1['ENFLAGS']                = 0b00001
ssa_strip_reg_map_v1['SAMPLINGMODE']           = 0b00010
ssa_strip_reg_map_v1['GAINTRIMMING']           = 0b00011
ssa_strip_reg_map_v1['THTRIMMING']             = 0b00100
ssa_strip_reg_map_v1['HIPCUT']                 = 0b00101
ssa_strip_reg_map_v1['DigCalibPattern_L']      = 0b00110
ssa_strip_reg_map_v1['DigCalibPattern_H']      = 0b00111
ssa_strip_reg_map_v1['ReadCounter_MSB']        = 0b01000
ssa_strip_reg_map_v1['ReadCounter_LSB']        = 0b01001

################# Periphery register map #####################
ssa_peri_reg_map_v1 = {}

ssa_peri_reg_map_v1['ReadoutMode']            =  0
ssa_peri_reg_map_v1['ClusterCut']             =  1
ssa_peri_reg_map_v1['FE_Calibration']         =  2
ssa_peri_reg_map_v1['OutPattern0']            =  3
ssa_peri_reg_map_v1['OutPattern1']            =  4
ssa_peri_reg_map_v1['OutPattern2']            =  5
ssa_peri_reg_map_v1['OutPattern3']            =  6
ssa_peri_reg_map_v1['OutPattern4']            =  7
ssa_peri_reg_map_v1['OutPattern5']            =  8
ssa_peri_reg_map_v1['OutPattern6']            =  9
ssa_peri_reg_map_v1['OutPattern7']            = 10
ssa_peri_reg_map_v1['OutPattern7/FIFOconfig'] = 10
ssa_peri_reg_map_v1['FIFOconfig']             = 10
ssa_peri_reg_map_v1['Offset0']                = 11
ssa_peri_reg_map_v1['Offset1']                = 12
ssa_peri_reg_map_v1['Offset2']                = 13
ssa_peri_reg_map_v1['Offset3']                = 14
ssa_peri_reg_map_v1['Offset4']                = 15
ssa_peri_reg_map_v1['Offset5']                = 16
ssa_peri_reg_map_v1['ClockDeskewing']         = 17
ssa_peri_reg_map_v1['AsyncRead_StartDel_LSB'] = 18
ssa_peri_reg_map_v1['AsyncRead_StartDel_MSB'] = 19
ssa_peri_reg_map_v1['L1-Latency_LSB']         = 20
ssa_peri_reg_map_v1['L1-Latency_MSB']         = 21
ssa_peri_reg_map_v1['PhaseShiftClock']        = 22
ssa_peri_reg_map_v1['EdgeSel_T1']             = 23
ssa_peri_reg_map_v1['SLVS_pad_current']       = 24
ssa_peri_reg_map_v1['Bias_D5BFEED']           = 25
ssa_peri_reg_map_v1['Bias_D5PREAMP']          = 26
ssa_peri_reg_map_v1['Bias_D5TDR']             = 27
ssa_peri_reg_map_v1['Bias_D5ALLV']            = 28
ssa_peri_reg_map_v1['Bias_D5ALLI']            = 29
ssa_peri_reg_map_v1['Bias_D5DLLB']            = 30
ssa_peri_reg_map_v1['Bias_D5DAC8']            = 31
ssa_peri_reg_map_v1['Bias_THDAC']             = 32
ssa_peri_reg_map_v1['Bias_THDACHIGH']         = 33
ssa_peri_reg_map_v1['Bias_CALDAC']            = 34
ssa_peri_reg_map_v1['Bias_DL_en']             = 35
ssa_peri_reg_map_v1['Bias_DL_ctrl']           = 36
ssa_peri_reg_map_v1['Bias_TEST_LSB']          = 37
ssa_peri_reg_map_v1['Bias_TEST_MSB']          = 38
ssa_peri_reg_map_v1['LateralRX_L_DataPhase']  = 39
ssa_peri_reg_map_v1['LateralRX_R_DataPhase']  = 40
ssa_peri_reg_map_v1['LateralRX_L_SampleEdge'] = 41
ssa_peri_reg_map_v1['LateralRX_R_SampleEdge'] = 42
ssa_peri_reg_map_v1['Fuse_Mode']              = 43
ssa_peri_reg_map_v1['Fuse_Prog_b0']           = 44
ssa_peri_reg_map_v1['Fuse_Prog_b1']           = 45
ssa_peri_reg_map_v1['Fuse_Prog_b2']           = 46
ssa_peri_reg_map_v1['Fuse_Prog_b3']           = 47
ssa_peri_reg_map_v1['Fuse_Value_b0']          = 48
ssa_peri_reg_map_v1['Fuse_Value_b1']          = 49
ssa_peri_reg_map_v1['Fuse_Value_b2']          = 50
ssa_peri_reg_map_v1['Fuse_Value_b3']          = 51
ssa_peri_reg_map_v1['CalPulse_duration']      = 52
ssa_peri_reg_map_v1['SEU_Counter']            = 53
ssa_peri_reg_map_v1['ClkEnable_Code']         = 54

################# Analog MUX map #####################
analog_mux_map_v1 = {'highimpedence': 0x00}

analog_mux_map_v1['Bias_D5BFEED']          = 0b0000000000000001
analog_mux_map_v1['Bias_D5PREAMP']         = 0b0000000000000010
analog_mux_map_v1['Bias_D5TDR']            = 0b0000000000000100
analog_mux_map_v1['Bias_D5ALLV']           = 0b0000000000001000
analog_mux_map_v1['Bias_D5ALLI']           = 0b0000000000010000
analog_mux_map_v1['Bias_CALDAC']           = 0b0000000000100000
analog_mux_map_v1['Bias_BOOSTERBASELINE']  = 0b0000000001000000
analog_mux_map_v1['Bias_THDAC']            = 0b0000000010000000
analog_mux_map_v1['Bias_THDACHIGH']        = 0b0000000100000000
analog_mux_map_v1['Bias_D5DAC8']           = 0b0000001000000000
analog_mux_map_v1['VBG']                   = 0b0000010000000000
analog_mux_map_v1['GND']                   = 0b0000100000000000

print('- Loaded configuration for SSA v1')
