"""Reusable velocity-ratio table parser and propeller-plane contour plotter.

Angle convention: 0 degrees is up; 90 degrees is right. All coordinates and
velocities are dimensionless. Interpolation is linear in (r/R, angle), with
no extrapolation beyond the measured domain.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
# Keep generated font/cache files within the project, including sandboxed runs.
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))


@dataclass
class WakeTable:
    angles_deg: np.ndarray
    radii_ratio: np.ndarray
    velocity_ratio: np.ndarray

    def __post_init__(self) -> None:
        self.angles_deg = np.asarray(self.angles_deg, dtype=float).copy()
        self.radii_ratio = np.asarray(self.radii_ratio, dtype=float).copy()
        self.velocity_ratio = np.asarray(self.velocity_ratio, dtype=float).copy()
        if self.angles_deg.ndim != 1 or self.radii_ratio.ndim != 1:
            raise ValueError("Açı ve yarıçap listeleri tek boyutlu olmalı.")
        if len(self.angles_deg) < 2 or len(self.radii_ratio) < 2:
            raise ValueError("En az iki açı satırı ve iki yarıçap sütunu gerekli.")
        expected = (len(self.angles_deg), len(self.radii_ratio))
        if self.velocity_ratio.shape != expected:
            raise ValueError(f"Hız tablosunun boyutu {expected} olmalı.")
        for values in (self.angles_deg, self.radii_ratio, self.velocity_ratio):
            if not np.all(np.isfinite(values)):
                raise ValueError("Boş hücre, NaN veya sonsuz değer kullanılamaz.")
        if np.any(np.diff(self.angles_deg) <= 0):
            raise ValueError("Açılar artan sırada ve tekrarsız olmalı.")
        if np.any(np.diff(self.radii_ratio) <= 0):
            raise ValueError("r/R değerleri artan sırada ve tekrarsız olmalı.")
        if self.angles_deg[0] < 0 or self.angles_deg[-1] > 360:
            raise ValueError("Açı aralığı 0–360 derece içinde olmalı.")
        if self.radii_ratio[0] < 0:
            raise ValueError("r/R negatif olamaz.")
        if self.radii_ratio[0] == 0 and not np.allclose(
            self.velocity_ratio[:, 0], self.velocity_ratio[0, 0], atol=1e-8, rtol=0
        ):
            raise ValueError("r/R=0 tek bir noktadır; bu sütundaki hızlar eşit olmalı.")
        if self.angles_deg[0] == 0 and self.angles_deg[-1] == 360:
            if not np.allclose(
                self.velocity_ratio[0], self.velocity_ratio[-1], atol=1e-8, rtol=0
            ):
                raise ValueError("0° ve 360° aynı konumdur; hız satırları eşit olmalı.")

    @property
    def wake_fraction(self) -> np.ndarray:
        return 1.0 - self.velocity_ratio


def parse_table(text: str) -> WakeTable:
    """Read CSV, semicolon CSV, tab-separated Excel paste, or whitespace text.

    The first row contains a label (possibly blank), followed by r/R values.
    Other rows contain an angle in degrees, followed by axial velocity ratios.
    Decimal commas are accepted with tabs, semicolons, or whitespace.
    """
    lines = [line for line in text.lstrip("\ufeff").splitlines() if line.strip()]
    if not lines:
        raise ValueError("Tablo boş. CSV açın veya tabloyu yapıştırın.")
    header = lines[0]
    delimiter = next((sep for sep in ("\t", ";") if sep in header), None)
    if delimiter is None and "," in header:
        # Distinguish decimal commas in a whitespace table from CSV separators.
        header_cells = header.split()
        whitespace_numbers = False
        if len(header_cells) >= 3:
            try:
                [float(cell.replace(",", ".")) for cell in header_cells[1:]]
                whitespace_numbers = True
            except ValueError:
                pass
        if not whitespace_numbers:
            delimiter = ","
    if delimiter:
        rows = list(csv.reader(lines, delimiter=delimiter))
    else:
        rows = [line.split() for line in lines]
    if len(rows[0]) < 3:
        raise ValueError("İlk satır 'angle_deg,0.2,0.3,...' biçiminde olmalı.")
    try:
        float(rows[0][0].strip().replace(",", "."))
    except ValueError:
        pass
    else:
        raise ValueError("İlk hücre bir başlık olmalı (angle_deg veya Angle).")

    def number(value: str, row: int, column: int) -> float:
        try:
            return float(value.strip().replace(",", "."))
        except ValueError as exc:
            raise ValueError(
                f"Satır {row}, sütun {column}: '{value}' geçerli bir sayı değil."
            ) from exc

    radii = [number(cell, 1, j + 2) for j, cell in enumerate(rows[0][1:])]
    angles, data = [], []
    for i, row in enumerate(rows[1:], start=2):
        if len(row) != len(radii) + 1:
            raise ValueError(
                f"Satır {i}: {len(radii) + 1} hücre bekleniyor, {len(row)} bulundu. "
                "Ondalık virgül kullanıyorsanız ayırıcı sekme veya noktalı virgül olmalı."
            )
        angles.append(number(row[0], i, 1))
        data.append([number(cell, i, j + 2) for j, cell in enumerate(row[1:])])
    return WakeTable(angles, radii, data)


def read_table(path: str | Path) -> WakeTable:
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1254")
    return parse_table(text)


def table_text(table: WakeTable, delimiter: str = ",") -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=delimiter, lineterminator="\n")
    writer.writerow(["angle_deg", *[format(v, ".12g") for v in table.radii_ratio]])
    for angle, row in zip(table.angles_deg, table.velocity_ratio):
        writer.writerow([format(angle, ".12g"), *[format(v, ".12g") for v in row]])
    return stream.getvalue()


def plotting_data(table: WakeTable, mirror: bool = False) -> tuple[np.ndarray, np.ndarray]:
    angles, values = table.angles_deg, table.velocity_ratio
    if mirror:
        if not (np.isclose(angles[0], 0) and np.isclose(angles[-1], 180)):
            raise ValueError("Simetrik tam disk için tablo tam olarak 0°–180° aralığında olmalı.")
        angles = np.concatenate([angles, 360 - angles[-2::-1]])
        values = np.concatenate([values, values[-2::-1]], axis=0)
    return angles, values


def interpolate_grid(
    table: WakeTable, mirror: bool = False, angular_samples: int = 361,
    radial_samples: int = 161,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return theta [degrees], r/R and q on a grid containing all source nodes."""
    angles, values = plotting_data(table, mirror)
    fine_angles = np.unique(np.r_[angles, np.linspace(angles[0], angles[-1], angular_samples)])
    fine_radii = np.unique(np.r_[table.radii_ratio, np.linspace(
        table.radii_ratio[0], table.radii_ratio[-1], radial_samples
    )])
    angular_values = np.column_stack([
        np.interp(fine_angles, angles, values[:, j]) for j in range(values.shape[1])
    ])
    grid = np.vstack([
        np.interp(fine_radii, table.radii_ratio, row) for row in angular_values
    ])
    return fine_angles, fine_radii, grid


def polar_coordinates(angles_deg: np.ndarray, radii: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    theta, radius = np.meshgrid(np.deg2rad(angles_deg), radii, indexing="ij")
    return radius * np.sin(theta), radius * np.cos(theta)


def draw_contour(
    figure, table: WakeTable, *, field: str = "velocity", mirror: bool = False,
    show_points: bool = True, bands: int = 10, title: str = "Pervane düzleminde iz alanı",
) -> None:
    from matplotlib.ticker import MaxNLocator

    if field not in ("velocity", "wake"):
        raise ValueError("Alan seçimi 'velocity' veya 'wake' olmalı.")
    if not 4 <= bands <= 30:
        raise ValueError("Renk bandı hedef sayısı 4–30 arasında olmalı.")
    angles, radii, q = interpolate_grid(table, mirror)
    values = q if field == "velocity" else 1.0 - q
    x, y = polar_coordinates(angles, radii)
    minimum, maximum = float(values.min()), float(values.max())
    constant = np.isclose(minimum, maximum, rtol=0, atol=1e-12)
    pad = max(0.05, abs(minimum) * 0.05) if constant else 0.0
    levels = MaxNLocator(nbins=bands).tick_values(minimum - pad, maximum + pad)
    figure.clear()
    figure.set_facecolor("#ffffff")
    ax = figure.add_axes([0.12, 0.20, 0.63, 0.66])
    ax.set_facecolor("#f5f7fa")
    contours = ax.contourf(x, y, values, levels=levels, cmap="turbo")
    if not constant:
        line_levels = levels[(levels > minimum) & (levels < maximum)]
        lines = ax.contour(x, y, values, levels=line_levels, colors="#172333", linewidths=0.55)
        ax.clabel(lines, inline=True, fontsize=8, fmt="%.2f")
    ax.plot(x[:, -1], y[:, -1], color="#172333", linewidth=1.1)
    if radii[0] > 0:
        ax.plot(x[:, 0], y[:, 0], color="#172333", linewidth=1.0)
    if angles[-1] - angles[0] < 360:
        for index in (0, -1):
            ax.plot(x[index], y[index], color="#172333", linewidth=1.0)
    source_angles, _ = plotting_data(table, mirror)
    if show_points:
        # Reflected nodes are explicitly shown with different markers.
        px, py = polar_coordinates(table.angles_deg, table.radii_ratio)
        ax.scatter(px, py, s=7, c="#172333", alpha=0.65, label="Verilen noktalar", zorder=4)
        if mirror:
            mx, my = polar_coordinates(360 - table.angles_deg[1:-1], table.radii_ratio)
            ax.scatter(mx, my, s=8, marker="x", c="#172333", alpha=0.5,
                       label="Simetri ile türetilen", zorder=4)
        handles, labels = ax.get_legend_handles_labels()
        figure.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.085),
                      fontsize=8, frameon=False, ncol=2)
    radius = radii[-1]
    for angle in np.arange(0, 360, 30):
        if source_angles[0] <= angle <= source_angles[-1]:
            rad = np.deg2rad(angle)
            ax.text(1.07 * radius * np.sin(rad), 1.07 * radius * np.cos(rad),
                    f"{angle}°", ha="center", va="center", fontsize=8, color="#475569")
    if source_angles[-1] <= 180:
        ax.set_xlim(-0.14 * radius, 1.17 * radius)
    else:
        ax.set_xlim(-1.19 * radius, 1.19 * radius)
    ax.set_ylim(-1.19 * radius, 1.19 * radius)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x/R  [-]", fontsize=10)
    ax.set_ylabel("y/R  [-]", fontsize=10)
    ax.tick_params(labelsize=9)
    ax.grid(alpha=0.12)
    label = r"Hız oranı $q = V_x/V_s$  [-]" if field == "velocity" else r"İz katsayısı $w = 1 - V_x/V_s$  [-]"
    color_ax = figure.add_axes([0.82, 0.23, 0.025, 0.56])
    bar = figure.colorbar(contours, cax=color_ax)
    bar.set_label(label, fontsize=10, labelpad=11)
    bar.ax.tick_params(labelsize=8)
    figure.suptitle(title, fontsize=15, fontweight="bold", x=0.49, y=0.96)
    subtitle = "Tam disk · merkez düzlemine göre simetri varsayımı" if mirror else "Verilen açısal alan"
    figure.text(0.49, 0.90, subtitle + " · 0° yukarı, 90° sağ", ha="center", fontsize=9, color="#475569")
    figure.text(0.5, 0.055,
                f"Min: {minimum:.3f}     Maks: {maximum:.3f}     "
                f"Girdi: {len(table.angles_deg)} açı × {len(table.radii_ratio)} yarıçap",
                ha="center", fontsize=9, color="#334155")
    inner_note = f"r/R < {radii[0]:g} için veri yok; iç bölge boş bırakıldı." if radii[0] > 0 else "Merkez verisi dahil."
    figure.text(0.5, 0.023, "(r/R, θ) düzleminde lineer interpolasyon. " + inner_note,
                ha="center", fontsize=8, color="#64748b")


def main() -> None:
    parser = argparse.ArgumentParser(description="İz tablosundan pervane düzlemi kontur grafiği.")
    parser.add_argument("--input", type=Path, help="CSV/TSV hız oranı tablosu")
    parser.add_argument("--output", type=Path, help="Çıktı PNG veya SVG yolu; verilmezse arayüz açılır")
    parser.add_argument("--field", choices=("velocity", "wake"), default="velocity")
    parser.add_argument("--full-disc", action="store_true", help="0–180° verisini simetri ile aynala")
    parser.add_argument("--hide-points", action="store_true")
    parser.add_argument("--bands", type=int, default=10)
    args = parser.parse_args()
    if args.output is None:
        from wake_app import run
        run(args.input)
        return
    if args.output.suffix.lower() not in (".png", ".svg"):
        parser.error("Çıktı uzantısı .png veya .svg olmalı.")
    if args.input is None:
        parser.error("Grafik kaydetmek için --input ile bir CSV/TSV tablosu belirtin.")
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    try:
        table = read_table(args.input)
        figure = Figure(figsize=(8.5, 8), dpi=110)
        FigureCanvasAgg(figure)
        draw_contour(figure, table, field=args.field, mirror=args.full_disc,
                     show_points=not args.hide_points, bands=args.bands)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(args.output, dpi=300, facecolor="white")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Hata: {exc}\n")
    print(f"Grafik kaydedildi: {args.output.resolve()}")


if __name__ == "__main__":
    main()

