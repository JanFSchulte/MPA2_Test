/******************************************************************************
* SSA ASIC (CMS Outer-Tracker PixelStrip-Module)                              *
* A. Caratelli, D. Ceresa, S. Scarfi, G. Bergamin, K. Kloukinas (CERN EP-ESE) *
*******************************************************************************/

// --> Se cambi questi indirizzi ricorda di ri-sintetizzare il modulo strip-cell oltre al top

// Sim Generic
`define dl 0.1ns
//`define SSA_StripCellTMR_use_gatelevel
//`define SSA_TrigData_use_gatelevel

`define makedefault(X)  '{default: X}

`define BLK0 2'd0 // R/W register block

    `define adr_Ring_oscillator_ctrl              5'd0
        `define reg_Ring_oscillator_ctrlA         "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[0][7:0]"
        `define reg_Ring_oscillator_ctrlB         "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[0][7:0]"
        `define reg_Ring_oscillator_ctrlC         "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[0][7:0]"
        `define loc_Ring_oscillator_ctrl          7:0

    `define adr_control_1                            5'd1
        `define reg_control_1A                       "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[1][7:0]"
        `define reg_control_1B                       "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[1][7:0]"
        `define reg_control_1C                       "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[1][7:0]"
        `define loc_ReadoutMode                      2:0
        `define func_ReadoutModeA                    "Periphery.ReadoutModeA[2:0]"
        `define func_ReadoutModeB                    "Periphery.ReadoutModeB[2:0]"
        `define func_ReadoutModeC                    "Periphery.ReadoutModeC[2:0]"
        `define loc_EdgeSel_T1                       3
        `define func_EdgeSel_T1A                     "Periphery.EdgeSel_T1A"
        `define func_EdgeSel_T1B                     "Periphery.EdgeSel_T1B"
        `define func_EdgeSel_T1C                     "Periphery.EdgeSel_T1C"
        `define loc_L1Offset_H                       4
        `define func_L1Offset_HA                     "Periphery.L1OffsetA[8]"
        `define func_L1Offset_HB                     "Periphery.L1OffsetB[8]"
        `define func_L1Offset_HC                     "Periphery.L1OffsetC[8]"
        `define loc_memory_select                    6:5
        `define func_memory_selectA                  "Periphery.memory_selectA[1:0]"
        `define func_memory_selectB                  "Periphery.memory_selectB[1:0]"
        `define func_memory_selectC                  "Periphery.memory_selectC[1:0]"
        `define adr_control_1_unused                 7
        `define adr_control_1_T1_or_CLK_select       7


    `define adr_control_2                            5'd2
        `define reg_control_2A                       "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[2][7:0]"
        `define reg_control_2B                       "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[2][7:0]"
        `define reg_control_2C                       "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[2][7:0]"
        `define loc_ClusterCut                       3:0
        `define func_ClusterCutA                     "Periphery.Config_ClusterCutA[3:0]"
        `define func_ClusterCutB                     "Periphery.Config_ClusterCutB[3:0]"
        `define func_ClusterCutC                     "Periphery.Config_ClusterCutC[3:0]"
        `define loc_CalPulse_duration                7:4
        `define func_CalPulse_durationA              "Periphery.CalPulseSync.DurationA[3:0]"
        `define func_CalPulse_durationB              "Periphery.CalPulseSync.DurationB[3:0]"
        `define func_CalPulse_durationC              "Periphery.CalPulseSync.DurationC[3:0]"

    `define adr_control_3                            5'd3
        `define reg_control_3A                       "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[3][7:0]"
        `define reg_control_3B                       "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[3][7:0]"
        `define reg_control_3C                       "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[3][7:0]"
        `define loc_L1Offset_L                       7:0
        `define func_L1Offset_LA                     "Periphery.L1OffsetA[7:0]"
        `define func_L1Offset_LB                     "Periphery.L1OffsetB[7:0]"
        `define func_L1Offset_LC                     "Periphery.L1OffsetC[7:0]"

    `define adr_ClockDeskewing_coarse                5'd4
        `define reg_ClockDeskewing_coarseA           "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[4][7:0]"
        `define reg_ClockDeskewing_coarseB           "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[4][7:0]"
        `define reg_ClockDeskewing_coarseC           "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[4][7:0]"
        `define loc_PhaseShiftClock                  2:0
        `define func_PhaseShiftClockA                "Periphery.Clk_manage.Clock_Divider_40_sys.PhaseShiftA[2:0]"
        `define func_PhaseShiftClockB                "Periphery.Clk_manage.Clock_Divider_40_sys.PhaseShiftB[2:0]"
        `define func_PhaseShiftClockC                "Periphery.Clk_manage.Clock_Divider_40_sys.PhaseShiftC[2:0]"
        `define func_PhaseShiftClockDigitalFE_A      "DigitalFE.PhaseShiftClockA[2:0]"
        `define func_PhaseShiftClockDigitalFE_B      "DigitalFE.PhaseShiftClockB[2:0]"
        `define func_PhaseShiftClockDigitalFE_C      "DigitalFE.PhaseShiftClockC[2:0]"
        `define loc_ClockDeskewing_coarse_unused     7:3

    `define adr_ClockDeskewing_fine                  5'd5
        `define reg_ClockDeskewing_fineA             "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[5][7:0]"
        `define reg_ClockDeskewing_fineB             "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[5][7:0]"
        `define reg_ClockDeskewing_fineC             "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[5][7:0]"
        `define loc_DLL_value                        3:0
        `define func_DLL_valueA                      "Periphery.Clk_manage.DLL_PhaseA[3:0]"
        `define func_DLL_valueB                      "Periphery.Clk_manage.DLL_PhaseB[3:0]"
        `define func_DLL_valueC                      "Periphery.Clk_manage.DLL_PhaseC[3:0]"
        `define loc_DLL_chargepump                   5:4
        `define func_DLL_chargepumpA                 "Periphery.Clk_manage.DLL_CP_ctrA[1:0]"
        `define func_DLL_chargepumpB                 "Periphery.Clk_manage.DLL_CP_ctrB[1:0]"
        `define func_DLL_chargepumpC                 "Periphery.Clk_manage.DLL_CP_ctrC[1:0]"
        `define loc_DLL_bypass                       6
        `define func_DLL_bypassA                     "Periphery.Clk_manage.DLL_BypassA"
        `define func_DLL_bypassB                     "Periphery.Clk_manage.DLL_BypassB"
        `define func_DLL_bypassC                     "Periphery.Clk_manage.DLL_BypassC"
        `define loc_DLL_Enable                       7
        `define func_DLL_EnableA                     "Periphery.Clk_manage.DLL_EnableA"
        `define func_DLL_EnableB                     "Periphery.Clk_manage.DLL_EnableB"
        `define func_DLL_EnableC                     "Periphery.Clk_manage.DLL_EnableC"

    `define adr_AsyncRead_StartDel_L                 5'd6
        `define reg_AsyncRead_StartDel_LA            "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[6][7:0]"
        `define reg_AsyncRead_StartDel_LB            "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[6][7:0]"
        `define reg_AsyncRead_StartDel_LC            "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[6][7:0]"
        `define loc_AsyncRead_StartDel_L             7:0
        `define func_AsyncRead_StartDel_LA           "Periphery.AsyncronousReadout.DelayA[7:0]"
        `define func_AsyncRead_StartDel_LB           "Periphery.AsyncronousReadout.DelayB[7:0]"
        `define func_AsyncRead_StartDel_LC           "Periphery.AsyncronousReadout.DelayC[7:0]"

    `define adr_AsyncRead_StartDel_H                 5'd7
        `define reg_AsyncRead_StartDel_HA            "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[7][7:0]"
        `define reg_AsyncRead_StartDel_HB            "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[7][7:0]"
        `define reg_AsyncRead_StartDel_HC            "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[7][7:0]"
        `define loc_AsyncRead_StartDel_H             5:0
        `define func_AsyncRead_StartDel_HA           "Periphery.AsyncronousReadout.DelayA[13:8]"
        `define func_AsyncRead_StartDel_HB           "Periphery.AsyncronousReadout.DelayB[13:8]"
        `define func_AsyncRead_StartDel_HC           "Periphery.AsyncronousReadout.DelayC[13:8]"
        `define loc_AsyncRead_StartDel_H_unused      7:6

    `define adr_LateralRX_sampling                   5'd8
        `define reg_LateralRX_samplingA              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[8][7:0]"
        `define reg_LateralRX_samplingB              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[8][7:0]"
        `define reg_LateralRX_samplingC              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[8][7:0]"
        `define loc_LateralRX_L_PhaseData            2:0
        `define func_LateralRX_L_PhaseDataA          "Periphery.Lateral_RX_Left.PhaseDataA[2:0]"
        `define func_LateralRX_L_PhaseDataB          "Periphery.Lateral_RX_Left.PhaseDataB[2:0]"
        `define func_LateralRX_L_PhaseDataC          "Periphery.Lateral_RX_Left.PhaseDataC[2:0]"
        `define loc_LateralRX_L_Edge320              3
        `define func_LateralRX_L_Edge320A            "Periphery.Lateral_RX_Left.Edge320A"
        `define func_LateralRX_L_Edge320B            "Periphery.Lateral_RX_Left.Edge320B"
        `define func_LateralRX_L_Edge320C            "Periphery.Lateral_RX_Left.Edge320C"
        `define loc_LateralRX_R_PhaseData            6:4
        `define func_LateralRX_R_PhaseDataA          "Periphery.Lateral_RX_Right.PhaseDataA[2:0]"
        `define func_LateralRX_R_PhaseDataB          "Periphery.Lateral_RX_Right.PhaseDataB[2:0]"
        `define func_LateralRX_R_PhaseDataC          "Periphery.Lateral_RX_Right.PhaseDataC[2:0]"
        `define loc_LateralRX_R_Edge320              7
        `define func_LateralRX_R_Edge320A            "Periphery.Lateral_RX_Right.Edge320A"
        `define func_LateralRX_R_Edge320B            "Periphery.Lateral_RX_Right.Edge320B"
        `define func_LateralRX_R_Edge320C            "Periphery.Lateral_RX_Right.Edge320C"

    `define adr_Shift_pattern_st_0                   5'd9
        `define reg_Shift_pattern_st_0A              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[9][7:0]"
        `define reg_Shift_pattern_st_0B              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[9][7:0]"
        `define reg_Shift_pattern_st_0C              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[9][7:0]"
        `define loc_Shift_pattern_st_0               7:0
        `define func_Shift_pattern_st_0A             "Periphery.PatternA[0]"
        `define func_Shift_pattern_st_0B             "Periphery.PatternB[0]"
        `define func_Shift_pattern_st_0C             "Periphery.PatternC[0]"

    `define adr_Shift_pattern_st_1                   5'd10
        `define reg_Shift_pattern_st_1A              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[10][7:0]"
        `define reg_Shift_pattern_st_1B              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[10][7:0]"
        `define reg_Shift_pattern_st_1C              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[10][7:0]"
        `define loc_Shift_pattern_st_1               7:0
        `define func_Shift_pattern_st_1A             "Periphery.PatternA[1]"
        `define func_Shift_pattern_st_1B             "Periphery.PatternB[1]"
        `define func_Shift_pattern_st_1C             "Periphery.PatternC[1]"

    `define adr_Shift_pattern_st_2                   5'd11
        `define reg_Shift_pattern_st_2A              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[11][7:0]"
        `define reg_Shift_pattern_st_2B              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[11][7:0]"
        `define reg_Shift_pattern_st_2C              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[11][7:0]"
        `define loc_Shift_pattern_st_2               7:0
        `define func_Shift_pattern_st_2A             "Periphery.PatternA[2]"
        `define func_Shift_pattern_st_2B             "Periphery.PatternB[2]"
        `define func_Shift_pattern_st_2C             "Periphery.PatternC[2]"

    `define adr_Shift_pattern_st_3                   5'd12
        `define reg_Shift_pattern_st_3A              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[12][7:0]"
        `define reg_Shift_pattern_st_3B              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[12][7:0]"
        `define reg_Shift_pattern_st_3C              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[12][7:0]"
        `define loc_Shift_pattern_st_3               7:0
        `define func_Shift_pattern_st_3A             "Periphery.PatternA[3]"
        `define func_Shift_pattern_st_3B             "Periphery.PatternB[3]"
        `define func_Shift_pattern_st_3C             "Periphery.PatternC[3]"

    `define adr_Shift_pattern_st_4                   5'd13
        `define reg_Shift_pattern_st_4A              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[13][7:0]"
        `define reg_Shift_pattern_st_4B              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[13][7:0]"
        `define reg_Shift_pattern_st_4C              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[13][7:0]"
        `define loc_Shift_pattern_st_4               7:0
        `define func_Shift_pattern_st_4A             "Periphery.PatternA[4]"
        `define func_Shift_pattern_st_4B             "Periphery.PatternB[4]"
        `define func_Shift_pattern_st_4C             "Periphery.PatternC[4]"

    `define adr_Shift_pattern_st_5                   5'd14
        `define reg_Shift_pattern_st_5A              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[14][7:0]"
        `define reg_Shift_pattern_st_5B              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[14][7:0]"
        `define reg_Shift_pattern_st_5C              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[14][7:0]"
        `define loc_Shift_pattern_st_5               7:0
        `define func_Shift_pattern_st_5A             "Periphery.PatternA[5]"
        `define func_Shift_pattern_st_5B             "Periphery.PatternB[5]"
        `define func_Shift_pattern_st_5C             "Periphery.PatternC[5]"

    `define adr_Shift_pattern_st_6                   5'd15
        `define reg_Shift_pattern_st_6A              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[15][7:0]"
        `define reg_Shift_pattern_st_6B              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[15][7:0]"
        `define reg_Shift_pattern_st_6C              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[15][7:0]"
        `define loc_Shift_pattern_st_6               7:0
        `define func_Shift_pattern_st_6A             "Periphery.PatternA[6]"
        `define func_Shift_pattern_st_6B             "Periphery.PatternB[6]"
        `define func_Shift_pattern_st_6C             "Periphery.PatternC[6]"

    `define adr_Shift_pattern_st_7                   5'd16
        `define reg_Shift_pattern_st_7A              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[16][7:0]"
        `define reg_Shift_pattern_st_7B              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[16][7:0]"
        `define reg_Shift_pattern_st_7C              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[16][7:0]"
        `define loc_Shift_pattern_st_7               7:0
        `define func_Shift_pattern_st_7A             "Periphery.PatternA[7]"
        `define func_Shift_pattern_st_7B             "Periphery.PatternB[7]"
        `define func_Shift_pattern_st_7C             "Periphery.PatternC[7]"

    `define adr_Shift_pattern_l1                     5'd17
        `define reg_Shift_pattern_l1A                "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[17][7:0]"
        `define reg_Shift_pattern_l1B                "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[17][7:0]"
        `define reg_Shift_pattern_l1C                "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[17][7:0]"
        `define loc_Shift_pattern_l1                 7:0
        `define func_Shift_pattern_l1A               "Periphery.PatternA[8]"
        `define func_Shift_pattern_l1B               "Periphery.PatternB[8]"
        `define func_Shift_pattern_l1C               "Periphery.PatternC[8]"

    `define adr_StripOffset_byte0                      5'd18
        `define reg_StripOffset_byte0_A                "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[18][7:0]"
        `define reg_StripOffset_byte0_B                "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[18][7:0]"
        `define reg_StripOffset_byte0_C                "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[18][7:0]"
        `define loc_StripOffset_byte0_all              7:0
        `define loc_StripOffset_0__b4                  7
        `define loc_StripOffset_0__b3                  6
        `define loc_StripOffset_0__b2                  5
        `define loc_StripOffset_0__b1                  4
        `define loc_StripOffset_0__b0                  3
        `define loc_StripOffset_1__b4                  2
        `define loc_StripOffset_1__b3                  1
        `define loc_StripOffset_1__b2                  0
        //`define func_StripOffset_0                   "Periphery.Trigger_data_handler.StripOffset.shift[0][4:0]"
        //`define func_StripOffset_1                   "Periphery.Trigger_data_handler.StripOffset.shift[1][4:0]"

    `define adr_StripOffset_byte1                      5'd19
        `define reg_StripOffset_byte1_A               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[19][7:0]"
        `define reg_StripOffset_byte1_B               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[19][7:0]"
        `define reg_StripOffset_byte1_C               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[19][7:0]"
        `define loc_StripOffset_byte1_all              7:0
        `define loc_StripOffset_1__b1                  7
        `define loc_StripOffset_1__b0                  6
        `define loc_StripOffset_2__b4                  5
        `define loc_StripOffset_2__b3                  4
        `define loc_StripOffset_2__b2                  3
        `define loc_StripOffset_2__b1                  2
        `define loc_StripOffset_2__b0                  1
        `define loc_StripOffset_3__b4                  0
        //`define func_StripOffset_2                   "Periphery.Trigger_data_handler.StripOffset.shift[2][4:0]"
        //`define func_StripOffset_3                   "Periphery.Trigger_data_handler.StripOffset.shift[3][4:0]"
        //`define func_StripOffset_3                   "Periphery.Trigger_data_handler.StripOffset.shift[3][4:0]"

    `define adr_StripOffset_byte2                      5'd20
        `define reg_StripOffset_byte2_A               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[20][7:0]"
        `define reg_StripOffset_byte2_B               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[20][7:0]"
        `define reg_StripOffset_byte2_C               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[20][7:0]"
        `define loc_StripOffset_byte2_all              7:0
        `define loc_StripOffset_3__b3                  7
        `define loc_StripOffset_3__b2                  6
        `define loc_StripOffset_3__b1                  5
        `define loc_StripOffset_3__b0                  4
        `define loc_StripOffset_4__b4                  3
        `define loc_StripOffset_4__b3                  2
        `define loc_StripOffset_4__b2                  1
        `define loc_StripOffset_4__b1                  0
        //`define func_StripOffset_4                   "Periphery.Trigger_data_handler.StripOffset.shift[4][4:0]"
        //`define func_StripOffset_5                   "Periphery.Trigger_data_handler.StripOffset.shift[5][4:0]"

    `define adr_StripOffset_byte3                      5'd21
        `define reg_StripOffset_byte3_A               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[21][7:0]"
        `define reg_StripOffset_byte3_B               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[21][7:0]"
        `define reg_StripOffset_byte3_C               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[21][7:0]"
        `define loc_StripOffset_byte3_all              7:0
        `define loc_StripOffset_4__b0                  7
        `define loc_StripOffset_5__b4                  6
        `define loc_StripOffset_5__b3                  5
        `define loc_StripOffset_5__b2                  4
        `define loc_StripOffset_5__b1                  3
        `define loc_StripOffset_5__b0                  2
        `define loc_StripOffset_unused__b1             1
        `define loc_StripOffset_unused__b0             0
        //`define func_StripOffset_4                   "Periphery.Trigger_data_handler.StripOffset.shift[4][4:0]"
        ///`define func_StripOffset_5                   "Periphery.Trigger_data_handler.StripOffset.shift[5][4:0]"

    `define adr_ClkTree_control                      5'd22
        `define reg_ClkTree_controlA                 "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[22][7:0]"
        `define reg_ClkTree_controlB                 "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[22][7:0]"
        `define reg_ClkTree_controlC                 "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[22][7:0]"
        `define loc_memory_sram_gating_enable        1:0
        `define func_memory_sram_gating_enableA      "Periphery.RawDataStore_CiclicMemory.memory_sram_gating_enableA[1:0]"
        `define func_memory_sram_gating_enableB      "Periphery.RawDataStore_CiclicMemory.memory_sram_gating_enableB[1:0]"
        `define func_memory_sram_gating_enableC      "Periphery.RawDataStore_CiclicMemory.memory_sram_gating_enableC[1:0]"
        `define loc_ClkTree_A                        3:2
        `define func_ClkTreeADisableA                "Periphery.Clk_manage.ClkTreeADisableA[1:0]"
        `define func_ClkTreeADisableB                "Periphery.Clk_manage.ClkTreeADisableB[1:0]"
        `define func_ClkTreeADisableC                "Periphery.Clk_manage.ClkTreeADisableC[1:0]"
        `define loc_ClkTree_B                        5:4
        `define func_ClkTreeBDisableA                "Periphery.Clk_manage.ClkTreeBDisableA[1:0]"
        `define func_ClkTreeBDisableB                "Periphery.Clk_manage.ClkTreeBDisableB[1:0]"
        `define func_ClkTreeBDisableC                "Periphery.Clk_manage.ClkTreeBDisableC[1:0]"
        `define loc_ClkTree_C                        7:6
        `define func_ClkTreeCDisableA                "Periphery.Clk_manage.ClkTreeCDisableA[1:0]"
        `define func_ClkTreeCDisableB                "Periphery.Clk_manage.ClkTreeCDisableB[1:0]"
        `define func_ClkTreeCDisableC                "Periphery.Clk_manage.ClkTreeCDisableC[1:0]"

    `define adr_ClkTreeMagicNumber                   5'd23
        `define reg_ClkTreeMagicNumberA              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[23][7:0]"
        `define reg_ClkTreeMagicNumberB              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[23][7:0]"
        `define reg_ClkTreeMagicNumberC              "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[23][7:0]"
        `define loc_ClkTreeMagicNumber               7:0
        `define func_ClkTreeMagicNumberA             "Periphery.Clk_manage.ClkTreeMagicNumberA[7:0]"
        `define func_ClkTreeMagicNumberB             "Periphery.Clk_manage.ClkTreeMagicNumberB[7:0]"
        `define func_ClkTreeMagicNumberC             "Periphery.Clk_manage.ClkTreeMagicNumberC[7:0]"

    `define adr_bist_memory_latch_ctrl               5'd24
        `define reg_bist_memory_latch_ctrlA          "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[24][7:0]"
        `define reg_bist_memory_latch_ctrlB          "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[24][7:0]"
        `define reg_bist_memory_latch_ctrlC          "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[24][7:0]"
        `define loc_bist_latch_enable_L              0
        `define func_bist_latch_enable_LA            "Periphery.RawDataStore_CiclicMemory.bist_latch_enable_LA"
        `define func_bist_latch_enable_LB            "Periphery.RawDataStore_CiclicMemory.bist_latch_enable_LB"
        `define func_bist_latch_enable_LC            "Periphery.RawDataStore_CiclicMemory.bist_latch_enable_LC"
        `define loc_bist_latch_enable_H              1
        `define func_bist_latch_enable_HA            "Periphery.RawDataStore_CiclicMemory.bist_latch_enable_HA"
        `define func_bist_latch_enable_HB            "Periphery.RawDataStore_CiclicMemory.bist_latch_enable_HB"
        `define func_bist_latch_enable_HC            "Periphery.RawDataStore_CiclicMemory.bist_latch_enable_HC"
        `define loc_sram_gating_ClrRst               7:2
        `define func_sram_gating_ClrRstA             "Periphery.RawDataStore_CiclicMemory.sram_gating_ClrRstA[5:0]"
        `define func_sram_gating_ClrRstB             "Periphery.RawDataStore_CiclicMemory.sram_gating_ClrRstB[5:0]"
        `define func_sram_gating_ClrRstC             "Periphery.RawDataStore_CiclicMemory.sram_gating_ClrRstC[5:0]"

    `define adr_bist_memory_sram_mode                5'd25
        `define reg_bist_memory_sram_modeA           "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[25][7:0]"
        `define reg_bist_memory_sram_modeB           "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[25][7:0]"
        `define reg_bist_memory_sram_modeC           "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[25][7:0]"
        `define loc_bist_memory_sram_mode_L          3:0
        `define func_bist_memory_sram_mode_LA        "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_mode_LA[3:0]"
        `define func_bist_memory_sram_mode_LB        "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_mode_LB[3:0]"
        `define func_bist_memory_sram_mode_LC        "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_mode_LC[3:0]"
        `define loc_bist_memory_sram_mode_H          7:4
        `define func_bist_memory_sram_mode_HA        "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_mode_HA[3:0]"
        `define func_bist_memory_sram_mode_HB        "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_mode_HB[3:0]"
        `define func_bist_memory_sram_mode_HC        "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_mode_HC[3:0]"

    `define adr_bist_memory_sram_start               5'd26
        `define reg_bist_memory_sram_startA          "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[26][7:0]"
        `define reg_bist_memory_sram_startB          "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[26][7:0]"
        `define reg_bist_memory_sram_startC          "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[26][7:0]"
        `define loc_bist_memory_sram_start_L         3:0
        `define func_bist_memory_sram_start_LA       "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_start_LA[3:0]"
        `define func_bist_memory_sram_start_LB       "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_start_LB[3:0]"
        `define func_bist_memory_sram_start_LC       "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_start_LC[3:0]"
        `define loc_bist_memory_sram_start_H         7:4
        `define func_bist_memory_sram_start_HA       "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_start_HA[3:0]"
        `define func_bist_memory_sram_start_HB       "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_start_HB[3:0]"
        `define func_bist_memory_sram_start_HC       "Periphery.RawDataStore_CiclicMemory.bist_memory_sram_start_HC[3:0]"

    `define adr_output_inv_ctrl_S                    5'd27
        `define reg_output_inv_ctrl_SA               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[27][7:0]"
        `define reg_output_inv_ctrl_SB               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[27][7:0]"
        `define reg_output_inv_ctrl_SC               "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[27][7:0]"
        `define loc_output_inv_ctrl_S_all            7:0
        `define func_output_inv_ctrl_SA              "Periphery.PeriWbInterface.output_inv_ctrl_SA[7:0]"
        `define func_output_inv_ctrl_SB              "Periphery.PeriWbInterface.output_inv_ctrl_SB[7:0]"
        `define func_output_inv_ctrl_SC              "Periphery.PeriWbInterface.output_inv_ctrl_SC[7:0]"
        `define Edge40_sample_Stub                   0
        `define func_Edge40_sample_Stub_A(N)         ($sformatf("Periphery.TrigDataSerGen[%1d].Trig_DataSerializer.Edge40A[7:0]",N))
        `define func_Edge40_sample_Stub_B(N)         ($sformatf("Periphery.TrigDataSerGen[%1d].Trig_DataSerializer.Edge40B[7:0]",N))
        `define func_Edge40_sample_Stub_C(N)         ($sformatf("Periphery.TrigDataSerGen[%1d].Trig_DataSerializer.Edge40C[7:0]",N))
        `define Edge40_sample_L1                     1
        `define func_Edge40_sample_L1_A              "Periphery.L1_Serializer_320.Edge40A[7:0]"
        `define func_Edge40_sample_L1_B              "Periphery.L1_Serializer_320.Edge40B[7:0]"
        `define func_Edge40_sample_L1_C              "Periphery.L1_Serializer_320.Edge40C[7:0]"
        `define Edge40_sample_Left_tx                2
        `define func_Edge40_sample_Left_tx_A         "Periphery.Lateral_Tx_Left.Edge40A[7:0]"
        `define func_Edge40_sample_Left_tx_B         "Periphery.Lateral_Tx_Left.Edge40B[7:0]"
        `define func_Edge40_sample_Left_tx_C         "Periphery.Lateral_Tx_Left.Edge40C[7:0]"
        `define Edge40_sample_Right_tx               3
        `define func_Edge40_sample_Right_tx_A        "Periphery.Lateral_Tx_Right.Edge40A[7:0]"
        `define func_Edge40_sample_Right_tx_B        "Periphery.Lateral_Tx_Right.Edge40B[7:0]"
        `define func_Edge40_sample_Right_tx_C        "Periphery.Lateral_Tx_Right.Edge40C[7:0]"
        `define Edge40_sample_Left_rx                4
        `define func_Edge40_sample_Left_rx_A         "Periphery.Lateral_RX_Left.Edge40A[7:0]"
        `define func_Edge40_sample_Left_rx_B         "Periphery.Lateral_RX_Left.Edge40B[7:0]"
        `define func_Edge40_sample_Left_rx_C         "Periphery.Lateral_RX_Left.Edge40C[7:0]"
        `define Edge40_sample_Right_rx               5
        `define func_Edge40_sample_Right_rx_A        "Periphery.Lateral_RX_Right.Edge40A[7:0]"
        `define func_Edge40_sample_Right_rx_B        "Periphery.Lateral_RX_Right.Edge40B[7:0]"
        `define func_Edge40_sample_Right_rx_C        "Periphery.Lateral_RX_Right.Edge40C[7:0]"
        `define loc6_inv_ctrl_S_unused               6
        `define loc7_inv_ctrl_S_unused               7

    `define adr_Config_HitDelay                      5'd28
        `define reg_Config_HitDelayA                 "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.register_o[28][7:0]"
        `define reg_Config_HitDelayB                 "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.register_o[28][7:0]"
        `define reg_Config_HitDelayC                 "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.register_o[28][7:0]"
        `define loc_Config_HitDelay                  7:0
        `define func_Config_HitDelayA                "Periphery.PeriWbInterface.Config_HitDelayA[7:0]"
        `define func_Config_HitDelayB                "Periphery.PeriWbInterface.Config_HitDelayB[7:0]"
        `define func_Config_HitDelayC                "Periphery.PeriWbInterface.Config_HitDelayC[7:0]"

    `define adr_SSA_Mask_blk0                        5'd29
        `define reg_SSA_Mask_blk0A                   "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.mask_o[7:0]"
        `define reg_SSA_Mask_blk0B                   "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.mask_o[7:0]"
        `define reg_SSA_Mask_blk0C                   "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.mask_o[7:0]"

    `define adr_SSA_Async_SEUcnt_blk0                5'd30
        `define reg_SSA_Async_SEUcnt_blk0A           "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.Async_SEUcnt[7:0]"
        `define reg_SSA_Async_SEUcnt_blk0B           "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.Async_SEUcnt[7:0]"
        `define reg_SSA_Async_SEUcnt_blk0C           "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.Async_SEUcnt[7:0]"

    `define adr_SSA_Sync_SEUcnt_blk0                 5'd31
        `define reg_SSA_Sync_SEUcnt_blk0A            "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instA.Sync_SEUcnt[7:0]"
        `define reg_SSA_Sync_SEUcnt_blk0B            "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instB.Sync_SEUcnt[7:0]"
        `define reg_SSA_Sync_SEUcnt_blk0C            "Periphery.PeriWbInterface.WbInterface_BLOCK0.WbInterface_instC.Sync_SEUcnt[7:0]"


`define BLK1 2'd1 // R/W register block

    `define adr_THDAC_L                              5'd0
        `define reg_THDAC_LA                         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[0][7:0]"
        `define reg_THDAC_LB                         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[0][7:0]"
        `define reg_THDAC_LC                         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[0][7:0]"
        `define loc_THDAC_L                          7:0
        `define func_THDAC_L                         "SSA_Bias.THDAC[7:0]"

    `define adr_THDAC_H                              5'd1
        `define reg_THDAC_HA                         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[1][7:0]"
        `define reg_THDAC_HB                         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[1][7:0]"
        `define reg_THDAC_HC                         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[1][7:0]"
        `define loc_THDAC_H                          7:0
        `define func_THDAC_H                         "SSA_Bias.THDACHIGH[7:0]"

    `define adr_CALDAC                               5'd2
        `define reg_CALDACA                          "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[2][7:0]"
        `define reg_CALDACB                          "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[2][7:0]"
        `define reg_CALDACC                          "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[2][7:0]"
        `define loc_CALDAC                           7:0
        `define func_CALDAC                          "SSA_Bias.CALDAC[7:0]"

    `define adr_Bias_TEST_lsb                        5'd3 //REGISTER UNUSED
        `define reg_Bias_TEST_lsbA                   "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[3][7:0]"
        `define reg_Bias_TEST_lsbB                   "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[3][7:0]"
        `define reg_Bias_TEST_lsbC                   "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[3][7:0]"
        `define loc_Bias_TEST_lsb                    7:0
        `define func_Bias_TEST_lsb                   "SSA_Bias.TEST[7:0]"

    `define adr_Bias_TEST_msb                        5'd4 //REGISTER UNUSED
        `define reg_Bias_TEST_msbA                   "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[4][7:0]"
        `define reg_Bias_TEST_msbB                   "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[4][7:0]"
        `define reg_Bias_TEST_msbC                   "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[4][7:0]"
        `define loc_Bias_TEST_msb                    3:0
        `define func_Bias_TEST_msb                   "SSA_Bias.TEST[11:8]"
        `define loc_Bias_TEST_msb_unused             7:4

    `define adr_Delay_line                           5'd5
        `define reg_Delay_lineA                      "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[5][7:0]"
        `define reg_Delay_lineB                      "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[5][7:0]"
        `define reg_Delay_lineC                      "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[5][7:0]"
        `define loc_DL_ctrl                          5:0
        `define func_DL_ctrl                         "SSA_Bias.DL_ctrl[5:0]"
        `define loc_Delay_line_unused                6
        `define loc_DL_en                            7
        `define func_DL_en                           "SSA_Bias.DL_en"

    `define adr_Bias_D5BFEED                         5'd6
        `define reg_Bias_D5BFEEDA                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[6][7:0]"
        `define reg_Bias_D5BFEEDB                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[6][7:0]"
        `define reg_Bias_D5BFEEDC                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[6][7:0]"
        `define loc_Bias_D5BFEED                     4:0
        `define func_Bias_D5BFEED                    "SSA_Bias.D5BFEED[4:0]"
        `define loc_Bias_D5BFEED_unused              7:5

    `define adr_Bias_D5PREAMP                        5'd7
        `define reg_Bias_D5PREAMPA                   "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[7][7:0]"
        `define reg_Bias_D5PREAMPB                   "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[7][7:0]"
        `define reg_Bias_D5PREAMPC                   "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[7][7:0]"
        `define loc_Bias_D5PREAMP                    4:0
        `define func_Bias_D5PREAMP                   "SSA_Bias.D5PREAMP[4:0]"
        `define loc_Bias_D5PREAMP_unused             7:5

    `define adr_Bias_D5TDR                           5'd8
        `define reg_Bias_D5TDRA                      "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[8][7:0]"
        `define reg_Bias_D5TDRB                      "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[8][7:0]"
        `define reg_Bias_D5TDRC                      "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[8][7:0]"
        `define loc_Bias_D5TDR                       4:0
        `define func_Bias_D5TDR                      "SSA_Bias.D5TDR[4:0]"
        `define loc_Bias_D5TDR_unused                7:5

    `define adr_Bias_D5ALLV                          5'd9
        `define reg_Bias_D5ALLVA                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[9][7:0]"
        `define reg_Bias_D5ALLVB                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[9][7:0]"
        `define reg_Bias_D5ALLVC                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[9][7:0]"
        `define loc_Bias_D5ALLV                      4:0
        `define func_Bias_D5ALLV                     "SSA_Bias.D5ALLV[4:0]"
        `define loc_Bias_D5ALLV_unused               7:5

    `define adr_Bias_D5ALLI                          5'd10
        `define reg_Bias_D5ALLIA                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[10][7:0]"
        `define reg_Bias_D5ALLIB                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[10][7:0]"
        `define reg_Bias_D5ALLIC                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[10][7:0]"
        `define loc_Bias_D5ALLI                      4:0
        `define func_Bias_D5ALLI                     "SSA_Bias.D5ALLI[4:0]"
        `define loc_Bias_D5ALLI_unused               7:5

    `define adr_Bias_D5DLLB                          5'd11
        `define reg_Bias_D5DLLBA                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[11][7:0]"
        `define reg_Bias_D5DLLBB                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[11][7:0]"
        `define reg_Bias_D5DLLBC                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[11][7:0]"
        `define loc_Bias_D5DLLB                      4:0
        `define func_Bias_D5DLLB                     "SSA_Bias.D5DLLB[4:0]"
        `define loc_Bias_D5DLLB_unused               7:5

    `define adr_Bias_D5DAC8                          5'd12
        `define reg_Bias_D5DAC8A                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[12][7:0]"
        `define reg_Bias_D5DAC8B                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[12][7:0]"
        `define reg_Bias_D5DAC8C                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[12][7:0]"
        `define loc_Bias_D5DAC8                      4:0
        `define func_Bias_D5DAC8                     "SSA_Bias.D5DAC8[4:0]"
        `define loc_Bias_D5DAC8_unused               7:5

    `define adr_SLVS_pad_current_Lateral             5'd13
        `define reg_SLVS_pad_current_LateralA        "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[13][7:0]"
        `define reg_SLVS_pad_current_LateralB        "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[13][7:0]"
        `define reg_SLVS_pad_current_LateralC        "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[13][7:0]"
        `define loc_SLVS_pad_current_Left            2:0
        `define func_SLVS_pad_currentLeft            "IO_ring.Left_o_iopad.B[2:0]"
        `define loc_SLVS_pad_current_Right           5:3
        `define func_SLVS_pad_currentRight           "IO_ring.Right_o_iopad.B[2:0]"
        `define loc_SLVS_pad_termination_lateral     7:6
        `define loc_SLVS_termination_Left            6
        `define func_SLVS_termination_Left           "IO_ring.Left_i_iopad.RT_EN"
        `define loc_SLVS_termination_Right           7
        `define func_SLVS_termination_Right          "IO_ring.Right_i_iopad.RT_EN"

    `define adr_SLVS_pad_current_Stub_0_1            5'd14
        `define reg_SLVS_pad_current_Stub_0_1A       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[14][7:0]"
        `define reg_SLVS_pad_current_Stub_0_1B       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[14][7:0]"
        `define reg_SLVS_pad_current_Stub_0_1C       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[14][7:0]"
        `define loc_SLVS_pad_current_Stub_0          2:0
        `define func_SLVS_pad_current_Stub_0         "IO_ring.Trig_Data_iopad_0.B[2:0]"
        `define loc_SLVS_pad_current_Stub_1          5:3
        `define func_SLVS_pad_current_Stub_1         "IO_ring.Trig_Data_iopad_1.B[2:0]"
        `define loc_SLVS_pad_current_Stub_0_1_unused 7:6

    `define adr_SLVS_pad_current_Stub_2_3            5'd15
        `define reg_SLVS_pad_current_Stub_2_3A       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[15][7:0]"
        `define reg_SLVS_pad_current_Stub_2_3B       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[15][7:0]"
        `define reg_SLVS_pad_current_Stub_2_3C       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[15][7:0]"
        `define loc_SLVS_pad_current_Stub_2          2:0
        `define func_SLVS_pad_current_Stub_2         "IO_ring.Trig_Data_iopad_2.B[2:0]"
        `define loc_SLVS_pad_current_Stub_3          5:3
        `define func_SLVS_pad_current_Stub_3         "IO_ring.Trig_Data_iopad_3.B[2:0]"
        `define loc_SLVS_pad_current_Stub_2_3_unused 7:6

    `define adr_SLVS_pad_current_Stub_4_5            5'd16
        `define reg_SLVS_pad_current_Stub_4_5A       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[16][7:0]"
        `define reg_SLVS_pad_current_Stub_4_5B       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[16][7:0]"
        `define reg_SLVS_pad_current_Stub_4_5C       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[16][7:0]"
        `define loc_SLVS_pad_current_Stub_4          2:0
        `define func_SLVS_pad_current_Stub_4         "IO_ring.Trig_Data_iopad_4.B[2:0]"
        `define loc_SLVS_pad_current_Stub_5          5:3
        `define func_SLVS_pad_current_Stub_5         "IO_ring.Trig_Data_iopad_5.B[2:0]"
        `define loc_SLVS_pad_current_Stub_4_5_unused 7:6

    `define adr_SLVS_pad_current_Stub_6_7            5'd17
        `define reg_SLVS_pad_current_Stub_6_7A       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[17][7:0]"
        `define reg_SLVS_pad_current_Stub_6_7B       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[17][7:0]"
        `define reg_SLVS_pad_current_Stub_6_7C       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[17][7:0]"
        `define loc_SLVS_pad_current_Stub_6          2:0
        `define func_SLVS_pad_current_Stub_6         "IO_ring.Trig_Data_iopad_6.B[2:0]"
        `define loc_SLVS_pad_current_Stub_7          5:3
        `define func_SLVS_pad_current_Stub_7         "IO_ring.Trig_Data_iopad_7.B[2:0]"
        `define loc_SLVS_pad_current_Stub_6_7_unused 7:6

    `define adr_SLVS_pad_current_Clk_T1              5'd18
        `define reg_SLVS_pad_current_Clk_T1A         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[18][7:0]"
        `define reg_SLVS_pad_current_Clk_T1B         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[18][7:0]"
        `define reg_SLVS_pad_current_Clk_T1C         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[18][7:0]"
        `define loc_SLVS_pad_current_Clk             2:0
        `define func_SLVS_pad_currentM               "IO_ring.Clk320_o_iopad.B[2:0]"
        `define loc_SLVS_pad_current_T1              5:3
        `define func_SLVS_pad_currentN               "IO_ring.T1_o_iopad.B[2:0]"
        `define loc_SLVS_pad_termination_clk_t1      7:6
        `define loc_SLVS_termination_clock           6
        `define func_SLVS_termination_clock          "IO_ring.Clk320_i_iopad.RT_EN"
        `define loc_SLVS_termination_T1              7
        `define func_SLVS_termination_T1             "IO_ring.T1_i_iopad.RT_EN"

    `define adr_SLVS_pad_current_L1                  5'd19
        `define reg_SLVS_pad_current_L1A             "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[19][7:0]"
        `define reg_SLVS_pad_current_L1B             "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[19][7:0]"
        `define reg_SLVS_pad_current_L1C             "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[19][7:0]"
        `define loc_SLVS_pad_current_L1              2:0
        `define func_SLVS_pad_currentH               "IO_ring.L1_data_iopad.B[2:0]"
        `define loc_SLVS_pad_current_L1_unused       7:3

    `define adr_Fuse_Mode                            5'd20
        `define reg_Fuse_ModeA                       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[20][7:0]"
        `define reg_Fuse_ModeB                       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[20][7:0]"
        `define reg_Fuse_ModeC                       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[20][7:0]"
        `define loc_Fuse_Mode                        7:0
        `define func_Fuse_ModeA                      "SSA_efuse.modeA[7:0]"
        `define func_Fuse_ModeB                      "SSA_efuse.modeB[7:0]"
        `define func_Fuse_ModeC                      "SSA_efuse.modeC[7:0]"

    `define adr_Fuse_Prog_b0                         5'd21
        `define reg_Fuse_Prog_b0A                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[21][7:0]"
        `define reg_Fuse_Prog_b0B                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[21][7:0]"
        `define reg_Fuse_Prog_b0C                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[21][7:0]"
        `define loc_Fuse_Prog_b0                     7:0
        `define func_Fuse_Prog_b0A                   "SSA_efuse.progA[7:0]"
        `define func_Fuse_Prog_b0B                   "SSA_efuse.progB[7:0]"
        `define func_Fuse_Prog_b0C                   "SSA_efuse.progC[7:0]"

    `define adr_Fuse_Prog_b1                         5'd22
        `define reg_Fuse_Prog_b1A                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[22][7:0]"
        `define reg_Fuse_Prog_b1B                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[22][7:0]"
        `define reg_Fuse_Prog_b1C                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[22][7:0]"
        `define loc_Fuse_Prog_b1                     7:0
        `define func_Fuse_Prog_b1A                   "SSA_efuse.progA[15:8]"
        `define func_Fuse_Prog_b1B                   "SSA_efuse.progB[15:8]"
        `define func_Fuse_Prog_b1C                   "SSA_efuse.progC[15:8]"

    `define adr_Fuse_Prog_b2                         5'd23
        `define reg_Fuse_Prog_b2A                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[23][7:0]"
        `define reg_Fuse_Prog_b2B                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[23][7:0]"
        `define reg_Fuse_Prog_b2C                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[23][7:0]"
        `define loc_Fuse_Prog_b2                     7:0
        `define func_Fuse_Prog_b2A                   "SSA_efuse.progA[23:16]"
        `define func_Fuse_Prog_b2B                   "SSA_efuse.progB[23:16]"
        `define func_Fuse_Prog_b2C                   "SSA_efuse.progC[23:16]"

    `define adr_Fuse_Prog_b3                         5'd24
        `define reg_Fuse_Prog_b3A                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[24][7:0]"
        `define reg_Fuse_Prog_b3B                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[24][7:0]"
        `define reg_Fuse_Prog_b3C                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[24][7:0]"
        `define loc_Fuse_Prog_b3                     7:0
        `define func_Fuse_Prog_b3A                   "SSA_efuse.progA[31:24]"
        `define func_Fuse_Prog_b3B                   "SSA_efuse.progB[31:24]"
        `define func_Fuse_Prog_b3C                   "SSA_efuse.progC[31:24]"

    `define adr_ADC_control                          5'd25
        `define reg_ADC_controlA                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[25][7:0]"
        `define reg_ADC_controlB                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[25][7:0]"
        `define reg_ADC_controlC                     "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[25][7:0]"
        `define loc_ADC_control_all                  7:0
        `define func_ADC_control_allA                "Periphery.ADC_controller.ADC_control_fromI2C[7:0]"
        `define func_ADC_control_allB                "Periphery.ADC_controller.ADC_control_fromI2C[7:0]"
        `define func_ADC_control_allC                "Periphery.ADC_controller.ADC_control_fromI2C[7:0]"
        `define loc_ADC_control_input_sel            4:0
        `define func_ADC_control_input_selA          "Periphery.ADC_controller.sel_inputA[4:0]"
        `define func_ADC_control_input_selB          "Periphery.ADC_controller.sel_inputB[4:0]"
        `define func_ADC_control_input_selC          "Periphery.ADC_controller.sel_inputC[4:0]"
        `define loc_ADC_control_soc                  5
        `define func_ADC_control_socA                "Periphery.ADC_controller.socA"
        `define func_ADC_control_socB                "Periphery.ADC_controller.socB"
        `define func_ADC_control_socC                "Periphery.ADC_controller.socC"
        `define loc_ADC_control_enable               6
        `define func_ADC_control_enableA             "Periphery.ADC_controller.enableA"
        `define func_ADC_control_enableB             "Periphery.ADC_controller.enableB"
        `define func_ADC_control_enableC             "Periphery.ADC_controller.enableC"
        `define loc_ADC_control_rst                  7
        `define func_ADC_control_rstA                "Periphery.ADC_controller.ADC_rstA"
        `define func_ADC_control_rstB                "Periphery.ADC_controller.ADC_rstB"
        `define func_ADC_control_rstC                "Periphery.ADC_controller.ADC_rstC"

    `define adr_ADC_trimming                         5'd26
        `define reg_ADC_trimmingA                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[26][7:0]"
        `define reg_ADC_trimmingB                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[26][7:0]"
        `define reg_ADC_trimmingC                    "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[26][7:0]"
        `define loc_ADC_trimming_all                 7:0
        `define func_ADC_trimming_allA               "Periphery.ADC_controller.ADC_trimming_fromI2C[6:0]"
        `define func_ADC_trimming_allB               "Periphery.ADC_controller.ADC_trimming_fromI2C[6:0]"
        `define func_ADC_trimming_allC               "Periphery.ADC_controller.ADC_trimming_fromI2C[6:0]"
        `define loc_ADC_trimming_trim_val            5:0
        `define func_ADC_trimming_trim_valA          "Periphery.ADC_controller.trimA[5:0]"
        `define func_ADC_trimming_trim_valB          "Periphery.ADC_controller.trimB[5:0]"
        `define func_ADC_trimming_trim_valC          "Periphery.ADC_controller.trimC[5:0]"
        `define loc_ADC_trimming_trim_sel            6
        `define func_ADC_trimming_trim_selA          "Periphery.ADC_controller.sel_trimA"
        `define func_ADC_trimming_trim_selB          "Periphery.ADC_controller.sel_trimB"
        `define func_ADC_trimming_trim_selC          "Periphery.ADC_controller.sel_trimC"
        `define loc_ADC_trimming_SW_en               7
        `define func_ADC_trimming_SW_enA             "Periphery.ADC_controller.SW_enA"
        `define func_ADC_trimming_SW_enB             "Periphery.ADC_controller.SW_enB"
        `define func_ADC_trimming_SW_enC             "Periphery.ADC_controller.SW_enC"

    `define adr_ADC_ref                              5'd27
        `define reg_ADC_refA                         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.register_o[27][7:0]"
        `define reg_ADC_refB                         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.register_o[27][7:0]"
        `define reg_ADC_refC                         "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.register_o[27][7:0]"
        `define loc_ADC_ref                          4:0
        `define func_ADC_ref                         "SSA_Bias.ADCREF[4:0]"
        `define loc_ADC_ref_unused                   7:5

    `define adr_blk1_unused_28                       5'd28

    `define adr_SSA_Mask_blk1                        5'd29
    `define reg_SSA_Mask_blk1A                       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.mask_o[7:0]"
    `define reg_SSA_Mask_blk1B                       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.mask_o[7:0]"
    `define reg_SSA_Mask_blk1C                       "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.mask_o[7:0]"

    `define adr_SSA_Async_SEUcnt_blk1                5'd30
    `define reg_SSA_Async_SEUcnt_blk1A               "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.Async_SEUcnt[7:0]"
    `define reg_SSA_Async_SEUcnt_blk1B               "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.Async_SEUcnt[7:0]"
    `define reg_SSA_Async_SEUcnt_blk1C               "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.Async_SEUcnt[7:0]"

    `define adr_SSA_Sync_SEUcnt_blk1                 5'd31
    `define reg_SSA_Sync_SEUcnt_blk1A                "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instA.Sync_SEUcnt[7:0]"
    `define reg_SSA_Sync_SEUcnt_blk1B                "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instB.Sync_SEUcnt[7:0]"
    `define reg_SSA_Sync_SEUcnt_blk1C                "Periphery.PeriWbInterface.WbInterface_BLOCK1.WbInterface_instC.Sync_SEUcnt[7:0]"

`define BLK2 2'd2 /// Read-only block
    `define adr_status_reg                       5'd0
    `define adr_CLuster_Overflow_Cnt_L           5'd1
    `define adr_CLuster_Overflow_Cnt_H           5'd2
    `define adr_L1_FIFO_Overflow_Cnt_L           5'd3
    `define adr_L1_FIFO_Overflow_Cnt_H           5'd4
    `define adr_Fuse_Value_b0                    5'd5
    `define adr_Fuse_Value_b1                    5'd6
    `define adr_Fuse_Value_b2                    5'd7
    `define adr_Fuse_Value_b3                    5'd8
    `define adr_bist_output                      5'd9
        `define loc_bist_latch_output_L             0  //Wait for output at 0
        `define loc_bist_latch_output_H             1  //Wait for output at 0
        `define loc_bist_memory_sram_done_L         2  //Wait for done at 1
        `define loc_bist_memory_sram_done_H         3  //Wait for done at 1
    `define adr_ADC_out_L                       5'd10
        `define loc_adr_ADC_out_7_0               7:0
    `define adr_ADC_out_H                       5'd11
        `define loc_adr_ADC_out_11_8              3:0
        `define loc_adr_ADC_out_EOC                 7
    `define adr_Ring_oscillator_out_locBR_T1_L  5'd12
    `define adr_Ring_oscillator_out_locBR_T1_H  5'd13
    `define adr_Ring_oscillator_out_locBR_T2_L  5'd14
    `define adr_Ring_oscillator_out_locBR_T2_H  5'd15
    `define adr_Ring_oscillator_out_locTR_T1_L  5'd16
    `define adr_Ring_oscillator_out_locTR_T1_H  5'd17
    `define adr_Ring_oscillator_out_locTR_T2_L  5'd18
    `define adr_Ring_oscillator_out_locTR_T2_H  5'd19
    `define adr_Ring_oscillator_out_locBC_T1_L  5'd20
    `define adr_Ring_oscillator_out_locBC_T1_H  5'd21
    `define adr_Ring_oscillator_out_locBC_T2_L  5'd22
    `define adr_Ring_oscillator_out_locBC_T2_H  5'd23
    `define adr_Ring_oscillator_out_locBL_T1_L  5'd24
    `define adr_Ring_oscillator_out_locBL_T1_H  5'd25
    `define adr_Ring_oscillator_out_locBL_T2_L  5'd26
    `define adr_Ring_oscillator_out_locBL_T2_H  5'd27

`define BLK3 2'd3 /// Read-only block
    `define adr_bist_memory_sram_output_L_0  5'd00   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_1  5'd01   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_2  5'd02   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_3  5'd03   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_4  5'd04   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_5  5'd05   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_6  5'd06   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_7  5'd07   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_8  5'd08   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_9  5'd09   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_A  5'd10   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_B  5'd11   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_C  5'd12   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_D  5'd13   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_E  5'd14   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_L_F  5'd15   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_0  5'd16   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_1  5'd17   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_2  5'd18   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_3  5'd19   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_4  5'd20   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_5  5'd21   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_6  5'd22   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_7  5'd23   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_8  5'd24   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_9  5'd25   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_A  5'd26   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_B  5'd27   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_C  5'd28   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_D  5'd29   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_E  5'd30   //Expecting all 0 if bist test is successful
    `define adr_bist_memory_sram_output_H_F  5'd31   //Expecting all 0 if bist test is successful

    //15 Strip Blocks with 8 strips each
    `define BLOCK0    4'd0
    `define BLOCK1    4'd1
    `define BLOCK2    4'd2
    `define BLOCK3    4'd3
    `define BLOCK4    4'd4
    `define BLOCK5    4'd5
    `define BLOCK6    4'd6
    `define BLOCK7    4'd7
    `define BLOCK8    4'd8
    `define BLOCK9    4'd9
    `define BLOCK10   4'd10
    `define BLOCK11   4'd11
    `define BLOCK12   4'd12
    `define BLOCK13   4'd13
    `define BLOCK14   4'd14
    `define BLOCK_ALL 4'd15

    `define STRIP0    4'd0
    `define STRIP1    4'd1
    `define STRIP2    4'd2
    `define STRIP3    4'd3
    `define STRIP4    4'd4
    `define STRIP5    4'd5
    `define STRIP6    4'd6
    `define STRIP7    4'd7

    // Strip configuration addresses
    `define adr_EnableFlags_Mode            4'd0
    `define reg_EnableFlags_ModeA           "SSA_WbInterfaceStripTMR.WbInterface_instA.register_o[0][6:0]"
    `define reg_EnableFlags_ModeB           "SSA_WbInterfaceStripTMR.WbInterface_instB.register_o[0][6:0]"
    `define reg_EnableFlags_ModeC           "SSA_WbInterfaceStripTMR.WbInterface_instC.register_o[0][6:0]"
    `define loc_PixelMask                   0
    `define func_PixelMaskA                 "StripCell.SSA_Strip_SamplingBlock.Strip_BR_Edge.En"
    `define func_PixelMaskB                 "StripCell.SSA_Strip_SamplingBlock.Strip_BR_Level.En"
    `define loc_SignalPolarity              1
    `define func_SignalPolarity             "StripCell.SSA_Strip_SamplingBlock.SignalPolarity"
    `define loc_EN_HitCounter               2
    `define func_EN_HitCounter              "StripCell.SSA_Strip_SamplingBlock.StripACounter.Enable"
    `define loc_EN_DigitalCalib             3
    `define func_EN_DigitalCalibA           "StripCell.SSA_Strip_SamplingBlock.DigitalCalibEn"
    `define func_EN_DigitalCalibB           "StripCell.SSA_Strip_SamplingBlock.StripCell_DigCal.DigCal"
    `define loc_EN_AnalogCalib              4
    `define func_EN_AnalogCalib1(N)          ($sformatf("SSA_StripCell_Generate[%1d].Analog_FE_Channel_X3.CALBIT[0]",N))
    `define func_EN_AnalogCalib2(N)         ($sformatf("SSA_StripCell_Generate[%1d].Analog_FE_Channel_X3.CALBIT[1]",N))
    `define func_EN_AnalogCalib3(N)         ($sformatf("SSA_StripCell_Generate[%1d].Analog_FE_Channel_X3.CALBIT[2]",N))
    `define loc_Mode_Trig0                  5
    `define loc_Mode_Trig1                  6
    `define func_Mode_Trig                  "StripCell.SSA_Strip_SamplingBlock.Mode[1:0]"

    `define adr_HipCut_FE_GainTrimming      4'd1
    `define reg_HipCut_FE_GainTrimmingA     "SSA_WbInterfaceStripTMR.WbInterface_instA.register_o[1][6:0]"
    `define reg_HipCut_FE_GainTrimmingB     "SSA_WbInterfaceStripTMR.WbInterface_instB.register_o[1][6:0]"
    `define reg_HipCut_FE_GainTrimmingC     "SSA_WbInterfaceStripTMR.WbInterface_instC.register_o[1][6:0]"
    `define loc_HipCut0                     0
    `define loc_HipCut2                     2
    `define func_HipCut                     "StripCell.SSA_Strip_SamplingBlock.HIP_suppression.HipLimit[2:0]"
    `define loc_FE_GainTrimming0            3
    `define loc_FE_GainTrimming3            6
    `define func_FE_GainTrimming1(N)         ($sformatf("SSA_StripCell_Generate[%1d].Analog_FE_Channel_X3.GPT[3:0]",N))
    `define func_FE_GainTrimming2(N)        ($sformatf("SSA_StripCell_Generate[%1d].Analog_FE_Channel_X3.GPT[7:4]",N))
    `define func_FE_GainTrimming3(N)        ($sformatf("SSA_StripCell_Generate[%1d].Analog_FE_Channel_X3.GPT[11:8]",N))

    `define adr_FE_ThresholdTrimming        4'd2
    `define reg_FE_ThresholdTrimmingA       "SSA_WbInterfaceStripTMR.WbInterface_instA.register_o[2][4:0]"
    `define reg_FE_ThresholdTrimmingB       "SSA_WbInterfaceStripTMR.WbInterface_instB.register_o[2][4:0]"
    `define reg_FE_ThresholdTrimmingC       "SSA_WbInterfaceStripTMR.WbInterface_instC.register_o[2][4:0]"
    `define func_FE_ThresholdTrimming1(N)   ($sformatf("SSA_StripCell_Generate[%1d].Analog_FE_Channel_X3.D[4:0]",N))
    `define func_FE_ThresholdTrimming2(N)   ($sformatf("SSA_StripCell_Generate[%1d].Analog_FE_Channel_X3.D[9:5]",N))
    `define func_FE_ThresholdTrimming3(N)   ($sformatf("SSA_StripCell_Generate[%1d].Analog_FE_Channel_X3.D[14:10]",N))

    `define adr_DigCalibPattern_L           4'd3
    `define reg_DigCalibPattern_L_A         "SSA_WbInterfaceStripTMR.WbInterface_instA.register_o[3][7:0]"
    `define reg_DigCalibPattern_L_B         "SSA_WbInterfaceStripTMR.WbInterface_instB.register_o[3][7:0]"
    `define reg_DigCalibPattern_L_C         "SSA_WbInterfaceStripTMR.WbInterface_instC.register_o[3][7:0]"
    `define func_DigCalibPattern_L          "StripCell.SSA_Strip_SamplingBlock.StripCell_DigCal.DigPattern_L[7:0]"

    `define adr_DigCalibPattern_H           4'd4
    `define reg_DigCalibPattern_H_A         "SSA_WbInterfaceStripTMR.WbInterface_instA.register_o[4][7:0]"
    `define reg_DigCalibPattern_H_B         "SSA_WbInterfaceStripTMR.WbInterface_instB.register_o[4][7:0]"
    `define reg_DigCalibPattern_H_C         "SSA_WbInterfaceStripTMR.WbInterface_instC.register_o[4][7:0]"
    `define func_DigCalibPattern_H          "StripCell.SSA_Strip_SamplingBlock.StripCell_DigCal.DigPattern_H[7:0]"

    `define adr_AC_ReadCounterLSB           4'd5
    `define reg_AC_ReadCounterLSB           "Readback Reg"
    `define func_AC_ReadCounterLSB(M,N)     ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%2d].SSA_StripCell_x8.SSA_StripCell_Generate[%1d].StripCell.SSA_Strip_SamplingBlock.AC_Counter[7:0]",M,N))

    `define adr_AC_ReadCounterMSB           4'd6
    `define reg_AC_ReadCounterMSB           "Readback Reg"
    `define func_AC_ReadCounterMSB(M,N)     ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%2d].SSA_StripCell_x8.SSA_StripCell_Generate[%1d].StripCell.SSA_Strip_SamplingBlock.AC_Counter[14:8]",M,N))

    // Block configuration addresses
    `define adr_Block_Mask                  4'b1101  //4'd13
    `define reg_Block_MaskA(N)              ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%1d].SSA_StripCell_x8.SSA_WbInterfaceBlock.MaskAVoted[7:0]",N))
    `define reg_Block_MaskB(N)              ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%1d].SSA_StripCell_x8.SSA_WbInterfaceBlock.MaskBVoted[7:0]",N))
    `define reg_Block_MaskC(N)              ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%1d].SSA_StripCell_x8.SSA_WbInterfaceBlock.MaskCVoted[7:0]",N))

    `define adr_Block_Async_SEUcnt          4'b1110  //4'd14
    `define reg_Block_Async_SEUcntA(N)      ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%1d].SSA_StripCell_x8.SSA_WbInterfaceBlock.Async_SEUcntA[7:0]",N))
    `define reg_Block_Async_SEUcntB(N)      ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%1d].SSA_StripCell_x8.SSA_WbInterfaceBlock.Async_SEUcntB[7:0]",N))
    `define reg_Block_Async_SEUcntC(N)      ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%1d].SSA_StripCell_x8.SSA_WbInterfaceBlock.Async_SEUcntC[7:0]",N))

    `define adr_Block_Sync_SEUcnt           4'b1111  //4'd15
    `define reg_Block_Sync_SEUcntA(N)       ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%1d].SSA_StripCell_x8.SSA_WbInterfaceBlock.Sync_SEUcntA[7:0]",N))
    `define reg_Block_Sync_SEUcntB(N)       ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%1d].SSA_StripCell_x8.SSA_WbInterfaceBlock.Sync_SEUcntB[7:0]",N))
    `define reg_Block_Sync_SEUcntC(N)       ($sformatf("DigitalFE.SSA_StripCell_x8_Generate[%1d].SSA_StripCell_x8.SSA_WbInterfaceBlock.Sync_SEUcntC[7:0]",N))

// Configuration PERI default values
//BLK 0 (DIGITAL)
//`define defaultVal_StripMask                 8'h00 //REGISTER NOT USED
`define defaultVal_Ring_oscillator_ctrl   8'h00
`define defaultVal_ReadoutMode               3'b000                  //SYNC MODE: 3'b000, ASYNC MODE: 3'b001
`define defaultVal_EdgeSel_T1                1'b1                    //1: posedge of T1 command, 0: negedge of T1 command
`define defaultVal_L1Offset                  9'd500                  //L1 raw data latency: all values from 2 to 511
`define defaultVal_memory_select             2'b00                   //MIP position MSB, Hit position LSB. If value '0' SRAM active, if value '1' latch active
`define defaultVal_ClusterCut                4'd5                    //0: everything pass, 1: only clusters with width 1, etc...until 7
`define defaultVal_CalPulse_duration         4'd1                    //Effect in analog front-end model, Calibration pulse length (from 0 to 15)
`define defaultVal_ClkTreeADisable           2'b01                   //If '10' and ClkTreeMagicNumber set to 8'h55, branch A of clock tree is disabled
`define defaultVal_ClkTreeBDisable           2'b01                   //If '10' and ClkTreeMagicNumber set to 8'h55, branch B of clock tree is disabled
`define defaultVal_ClkTreeCDisable           2'b01                   //If '10' and ClkTreeMagicNumber set to 8'h55, branch C of clock tree is disabled
`define defaultVal_memory_sram_gating_enable 2'b11                   //LSB Strip_hit SRAM, MSB MIP flag SRAM, Active low
`define defaultVal_ClkTreeMagicNumber        8'hAA                   //Has to be set to 8'h55 in order for clock disabling to be active
`define defaultVal_StripOffset               8'h00
`define defaultVal_Shift_pattern_st_0        8'b10000000
`define defaultVal_Shift_pattern_st_1        8'b10000000
`define defaultVal_Shift_pattern_st_2        8'b10000000
`define defaultVal_Shift_pattern_st_3        8'b10000000
`define defaultVal_Shift_pattern_st_4        8'b10000000
`define defaultVal_Shift_pattern_st_5        8'b10000000
`define defaultVal_Shift_pattern_st_6        8'b10000000
`define defaultVal_Shift_pattern_st_7        8'b10000000
`define defaultVal_Shift_pattern_st_l1       8'b10000000 //ascii "!"
`define defaultVal_DLL_value                 4'b0001                 //DLL value from 0 to 15
`define defaultVal_DLL_chargepump            2'b01                   //DLL current
`define defaultVal_DLL_bypass                1'b0                    //Bypass DLL if '1'
`define defaultVal_DLL_Enable                1'b1                    //Enable DLL if '1'
`define defaultVal_PhaseShiftClock           3'b0                    //Value from 0 to 7 for PhaseShift Clock
`define defaultVal_AsyncRead_StartDel        (14'd15360-14'd8-14'd6) //(120*16*8)-8 //Fixed delay to start to send out data in ASYNC MODE
`define defaultVal_LateralRX_L_PhaseData     3'd5
`define defaultVal_LateralRX_L_Edge320       1'b1
`define defaultVal_LateralRX_R_PhaseData     3'd5
`define defaultVal_LateralRX_R_Edge320       1'b1
`define defaultVal_bist_latch_enable_L       1'b0                    //If 1'b1 latch_L BIST enabled and start
`define defaultVal_bist_latch_enable_H       1'b0                    //If 1'b1 latch_H BIST enabled and start
`define defaultVal_sram_gating_ClrRst        6'd25
`define defaultVal_bist_memory_sram_mode_L   4'b0000                 //If 4'hF SRAM_L BIST mode enabled
`define defaultVal_bist_memory_sram_mode_H   4'b0000                 //If 4'hF SRAM_H BIST mode enabled
`define defaultVal_bist_memory_sram_start_L  4'b0000                 //If 4'hF SRAM_L BIST start
`define defaultVal_bist_memory_sram_start_H  4'b0000                 //If 4'hF SRAM_H BIST start
`define defaultVal_loc_output_inv_ctrl_S     8'h00                   //{1'b0,1'b0, Edge40_sample_Right_rx, Edge40_sample_Left_rx, Edge40_sample_Right_tx, Edge40_sample_Left_tx, Edge40_sample_L1, Edge40_sample_Stub}
`define defaultVal_Config_HitDelay           {1'b0, 2'b00, 2'b00, 3'b001}

//BLK 1 (ANALOG)
`define defaultVal_Bias_D5BFEED              5'd15                   //Effect in analog front-end model
`define defaultVal_Bias_D5PREAMP             5'd15                   //Effect in analog front-end model
`define defaultVal_Bias_D5TDR                5'd15                   //Effect in analog front-end model
`define defaultVal_Bias_D5ALLV               5'd15                   //Effect in analog front-end model
`define defaultVal_Bias_D5ALLI               5'd15                   //Effect in analog front-end model
`define defaultVal_Bias_D5DLLB               5'd15                   //Effect in analog front-end model
`define defaultVal_Bias_D5DAC8               5'd15                   //Effect in analog front-end model
`define defaultVal_THDAC_L                   8'd35                   //Effect in analog front-end model --> Low Threshold
`define defaultVal_THDAC_H                   8'd120                  //Effect in analog front-end model --> High Threshold
`define defaultVal_CALDAC                    8'd50                   //Effect in analog front-end model --> Calibration DAC
`define defaultVal_DL_en                     1'b0                    //Effect in analog front-end model, 0: Delay line disabled, 1: Delay line enabled
`define defaultVal_DL_ctrl                   6'b0                    //Effect in analog front-end model, delay line control (from 0 to 63)
`define defaultVal_Bias_TEST                 12'h000 //REGISTER UNUSED
`define defaultVal_SLVS_pad_current_Stub_0   3'b100                  //Effect in IO_RING: Value of current for TX pad for Trig0
`define defaultVal_SLVS_pad_current_Stub_1   3'b100                  //Effect in IO_RING: Value of current for TX pad for Trig1
`define defaultVal_SLVS_pad_current_Stub_2   3'b100                  //Effect in IO_RING: Value of current for TX pad for Trig2
`define defaultVal_SLVS_pad_current_Stub_3   3'b100                  //Effect in IO_RING: Value of current for TX pad for Trig3
`define defaultVal_SLVS_pad_current_Stub_4   3'b100                  //Effect in IO_RING: Value of current for TX pad for Trig4
`define defaultVal_SLVS_pad_current_Stub_5   3'b100                  //Effect in IO_RING: Value of current for TX pad for Trig5
`define defaultVal_SLVS_pad_current_Stub_6   3'b100                  //Effect in IO_RING: Value of current for TX pad for Trig6
`define defaultVal_SLVS_pad_current_Stub_7   3'b100                  //Effect in IO_RING: Value of current for TX pad for Trig7
`define defaultVal_SLVS_pad_current_L1       3'b100                  //Effect in IO_RING: Value of current for TX pad for L1
`define defaultVal_SLVS_pad_current_Clk      3'b100                  //Effect in IO_RING: Value of current for TX pad for MPA clk
`define defaultVal_SLVS_pad_current_T1       3'b100                  //Effect in IO_RING: Value of current for TX pad for MPA T1
`define defaultVal_SLVS_pad_termin_clk_t1    2'b00                   //Effect in IO_RING: Enable termination for clock and T1 if '11'
`define defaultVal_SLVS_pad_current_Right    3'b100                  //Effect in IO_RING: Value of current for TX pad for Lateral Right
`define defaultVal_SLVS_pad_current_Left     3'b100                  //Effect in IO_RING: Value of current for TX pad for Lateral Left
`define defaultVal_SLVS_pad_termin_lateral   2'b11                   //Enable termination for lateral communication if '11'
`define defaultVal_Fuse_Mode                 8'd0                    //Effect in Efuse: Control register to write/read efuse
`define defaultVal_Fuse_Prog                 32'd0                   //Effect in Efuse: Value to write in the Efuse
`define defaultVal_ADC_control               8'h00
`define defaultVal_ADC_trimming              {2'b00, 6'b100000}
`define defaultVal_ADC_ref                   5'h00

//Configuration STRIP default values
`define defaultVal_PixelMask                 1'b1                    //0: Mask strip, 1: Mask disabled
`define defaultVal_SignalPolarity            1'b0                    //0: , 1:
`define defaultVal_EN_HitCounter             1'b1                    //0: HitCounter disabled, 1:
`define defaultVal_EN_DigitalCalib           1'b0                    //0: Digital calibration disabled, 1: Digital calibration enabled
`define defaultVal_EN_AnalogCalib            1'b0                    //Effect in analog front-end model, 0: Analog calibration disabled, 1: Analog calibration enabled
`define defaultVal_StripReadoutMode          2'd0                    //Strip Readout mode??

`define defaultVal_HipCut                    3'd1                    //Hipcut value from 0 to 7
`define defaultVal_FE_GainTrimming           4'd0                    //Effect in analog front-end model

`define defaultVal_FE_ThresholdTrimming      5'd15                   //Effect in analog front-end model

`define defaultVal_DigPattern_L              8'hFF
`define defaultVal_DigPattern_H              8'hFF



/////////////////////////////////////////
////////////CONNECTIVITY ANALOG FE
/////////////////////////////////////////
`define con_Bias_D5BFEED_BFEDB(N,M)    ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.BFEDB",N,M))

`define con_Bias_D5PREAMP_IBPRE(N,M)   ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.IBPRE",N,M))

`define con_Bias_D5TDR_TDIREG(N,M)     ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.TDIREG",N,M))
`define con_Bias_D5TDR_TDREF(N,M)      ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.TDREF",N,M))

`define con_Bias_D5ALLV_BVCP(N,M)      ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.BVCP",N,M))
`define con_Bias_D5ALLV_BVCN(N,M)      ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.BVCN",N,M))
`define con_Bias_D5ALLV_VCDI(N,M)      ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.VCDI",N,M))

`define con_Bias_D5ALLI_IREGP(N,M)     ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.IREGP",N,M))
`define con_Bias_D5ALLI_IBPB(N,M)      ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.IBPB",N,M))
`define con_Bias_D5ALLI_IBCOMDI(N,M)   ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.IBCOMDI",N,M))
`define con_Bias_D5ALLI_IBCOMDIH(N,M)  ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.IBCOMDIH",N,M))
`define con_Bias_D5ALLI_BDIFBP(N,M)    ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.BDIFBP",N,M))
`define con_Bias_D5ALLI_BDIFBN(N,M)    ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.BDIFBN",N,M))
`define con_Bias_D5ALLI_BABBP(N,M)     ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.BABBP",N,M))
`define con_Bias_D5ALLI_BABBN(N,M)     ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.BABBN",N,M))

`define con_Bias_D5DAC8_VBAS(N,M)      ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.VBAS",N,M))

`define con_Bias_THDAC(N,M)            ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.VTLOW_mV",N,M))

`define con_Bias_THDACHIGH(N,M)        ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.VTHIGH_mV",N,M))

`define con_Bias_CALDAC(N,M)           ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.CALLINE_mV",N,M))

`define con_Bias_IBCOM(N,M)            ($sformatf("SSA_StripCell_Generate[%2d].Analog_FE_Channel_X3.Channel[%1d].Channel_i.IBCOM",N,M))


//`define defaultVal_BIAS_ThresholdDAC1        8'd0
//`define defaultVal_BIAS_ThresholdDAC2        8'd0
//`define defaultVal_BIAS_CalibrationDAC       8'd0
//`define defaultVal_Cal_Value                 8'b10001000
//`define defaultVal_DLL_Bias                  8'h0
//`define defaultVal_EdgeSel_Clk40des          1'b0
