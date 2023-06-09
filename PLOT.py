from plotter import *
import argparse
def PLOT():
    print("test")
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("-t", "--tag", dest = "tag", default = "", help="tag to label output")
    args = parser.parse_args()

    # MaPSA ID
    mapsaid='HPK-35494-033L'



    # IV Scan Plots
    draw_IVScan(mapsaid, args.tag)


    # 2D Summary Plots

    allkeys = ["pixelalive","mask_test","PostTrim_THR_THR_RMS", "PostTrim_THR_THR_Mean", "PostTrim_CAL_CAL_RMS","PostTrim_CAL_CAL_Mean","BumpBonding_Noise_BadBump","BumpBonding_BadBumpMap"]

    summary_plots(mapsaid, bases=allkeys, note=args.tag)



    # THR S-curves 1D
    for i in range(1,17):
        chipid=str(i)
        draw_1D(mapsaid,chipid, keys=["PostTrim_THR_THR_RMS"], note=args.tag)
        draw_1D(mapsaid,chipid, keys=["PostTrim_THR_THR_Mean"], note=args.tag)

    # CAL S-curves 1D
    for i in range(1,17):
        chipid=str(i)
        draw_1D(mapsaid,chipid, keys=["PostTrim_CAL_CAL_RMS"], note=args.tag)
        draw_1D(mapsaid,chipid, keys=["PostTrim_CAL_CAL_Mean"], note=args.tag)


    # Draw S-Curves
    for i in range(1,17):
        chipid=str(i)
        draw_SCurve(mapsaid, chipid, "PreTrim_THR_THR",args.tag)

        draw_SCurve(mapsaid, chipid, "PreTrim_CAL_CAL",args.tag)

        draw_SCurve(mapsaid, chipid, "PostTrim_THR_THR",args.tag)

        draw_SCurve(mapsaid, chipid, "PostTrim_CAL_CAL",args.tag)
print("test")
PLOT()