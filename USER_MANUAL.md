# Wake Contour User Manual

## Install on Windows

1. Install Python 3.10 or later with Tcl/Tk support. Wake Contour was tested with Python 3.12.
2. Extract the project ZIP and double-click `Baslat.cmd` in the extracted folder.
3. Keep your internet connection active on the first launch so the launcher can install NumPy and Matplotlib. After setup, plotting works offline.

## Create and save a contour

1. Click **CSV / TSV aç** to open a data file, or paste a table copied from Excel into the editor.
2. Select **Hız oranı** for the axial velocity ratio `Vx/Vs` or **İz katsayısı** for the wake fraction `w = 1 − Vx/Vs`.
3. Click **Grafiği çiz / güncelle** to draw or update the contour. For data spanning 0° to 180°, use the **Tam disk** option to mirror the supplied half about the centre plane.
4. Click **PNG / SVG kaydet** to export the plot. The app also saves the input table as `.input.csv` and the plot settings as `.settings.json` alongside the image. Use **CSV kaydet** to save an edited table separately.

## Example input

```csv
angle_deg,0.3,0.7,1.0
0,0.32,0.43,0.48
90,0.67,0.85,0.96
180,0.58,0.76,0.91
```

The first column contains angles in degrees. The remaining headers are dimensionless radii `r/R`, and the cells contain axial velocity ratios. Enter angles and radii in ascending order. In the plot, 0° points up and 90° points right.

Press **F1** for the built-in Turkish help.
