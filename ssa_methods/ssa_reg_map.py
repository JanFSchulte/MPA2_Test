
ssa_peri_reg_map = {'test': 0xfff}
ssa_strip_reg_map = {'test': 0xfff}

################# Strip register map #########################

ssa_strip_reg_map['ENFLAGS']                = 0b00001
ssa_strip_reg_map['SAMPLINGMODE']           = 0b00010
ssa_strip_reg_map['GAINTRIMMING']           = 0b00011
ssa_strip_reg_map['THTRIMMING']             = 0b00100
ssa_strip_reg_map['HIPCUT']                 = 0b00101
ssa_strip_reg_map['DigCalibPattern_L']      = 0b00110
ssa_strip_reg_map['DigCalibPattern_H']      = 0b00111
ssa_strip_reg_map['ReadCounter_MSB']        = 0b01000
ssa_strip_reg_map['ReadCounter_LSB']        = 0b01001

################# Periphery register map #####################


ssa_peri_reg_map['ReadoutMode']            =  0       
ssa_peri_reg_map['ClusterCut']             =  1      
ssa_peri_reg_map['FE_Calibration']         =  2          
ssa_peri_reg_map['OutPattern0']            =  3       
ssa_peri_reg_map['OutPattern1']            =  4       
ssa_peri_reg_map['OutPattern2']            =  5       
ssa_peri_reg_map['OutPattern3']            =  6       
ssa_peri_reg_map['OutPattern4']            =  7       
ssa_peri_reg_map['OutPattern5']            =  8       
ssa_peri_reg_map['OutPattern6']            =  9       
ssa_peri_reg_map['OutPattern7/FIFOconfig'] = 10                  
ssa_peri_reg_map['Offset0']                = 11   
ssa_peri_reg_map['Offset1']                = 12   
ssa_peri_reg_map['Offset2']                = 13   
ssa_peri_reg_map['Offset3']                = 14   
ssa_peri_reg_map['Offset4']                = 15   
ssa_peri_reg_map['Offset5']                = 16   
ssa_peri_reg_map['ClockDeskewing']         = 17          
ssa_peri_reg_map['AsyncRead_StartDel_LSB'] = 18                  
ssa_peri_reg_map['AsyncRead_StartDel_MSB'] = 19                  
ssa_peri_reg_map['L1-Latency_LSB']         = 20          
ssa_peri_reg_map['L1-Latency_MSB']         = 21          
ssa_peri_reg_map['PhaseShiftClock']        = 22           
ssa_peri_reg_map['EdgeSel_T1']             = 23      
ssa_peri_reg_map['SLVS_pad_current']       = 24            
ssa_peri_reg_map['Bias_D5BFEED']           = 25        
ssa_peri_reg_map['Bias_D5PREAMP']          = 26         
ssa_peri_reg_map['Bias_D5TDR']             = 27      
ssa_peri_reg_map['Bias_D5ALLV']            = 28       
ssa_peri_reg_map['Bias_D5ALLI']            = 29       
ssa_peri_reg_map['Bias_D5DLLB']            = 30       
ssa_peri_reg_map['Bias_D5DAC8']            = 31       
ssa_peri_reg_map['Bias_THDAC']             = 32    
ssa_peri_reg_map['Bias_THDACHIGH']         = 33        
ssa_peri_reg_map['Bias_CALDAC']            = 34     
ssa_peri_reg_map['Bias_DL_en']             = 35      
ssa_peri_reg_map['Bias_DL_ctrl']           = 36        
ssa_peri_reg_map['Bias_TEST_LSB']          = 37         
ssa_peri_reg_map['Bias_TEST_MSB']          = 38         
ssa_peri_reg_map['LateralRX_L_DataPhase']  = 39                 
ssa_peri_reg_map['LateralRX_R_DataPhase']  = 40                 
ssa_peri_reg_map['LateralRX_L_SampleEdge'] = 41                  
ssa_peri_reg_map['LateralRX_R_SampleEdge'] = 42                  
ssa_peri_reg_map['Fuse_Mode']              = 43     
ssa_peri_reg_map['Fuse_Prog_b0']           = 44        
ssa_peri_reg_map['Fuse_Prog_b1']           = 45        
ssa_peri_reg_map['Fuse_Prog_b2']           = 46        
ssa_peri_reg_map['Fuse_Prog_b3']           = 47        
ssa_peri_reg_map['Fuse_Value_b0']          = 48       
ssa_peri_reg_map['Fuse_Value_b1']          = 49       
ssa_peri_reg_map['Fuse_Value_b2']          = 50       
ssa_peri_reg_map['Fuse_Value_b3']          = 51       
ssa_peri_reg_map['CalPulse_duration']      = 52             
ssa_peri_reg_map['SEU_Counter']            = 53     
ssa_peri_reg_map['ClkEnable_Code']         = 54  




