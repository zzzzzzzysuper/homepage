"""
schematic.py —— 画出三个电路的电路图 / 等效模型（存成 png，便于插进 README）

说明：任务书要求"电路图自己画"（手绘拍照也行）。这个脚本用 matplotlib 帮你
画一份规范的程序化电路图，可以：
  · 直接插进 README（比手绘整齐，评审看着舒服）
  · 当参照物，照着它手绘再拍照
  · 作为"直流通路图"和"小信号等效模型图"（题目明确要求画这两个）

运行： python schematic.py
产出： figures/sch_rc.png / sch_thevenin.png / sch_thevenin_equiv.png
       figures/sch_nmos.png / sch_nmos_dc_path.png / sch_nmos_small_signal.png
"""

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Circle, FancyArrow

_avail = {f.name for f in font_manager.fontManager.ttflist}
for _n in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC"):
    if _n in _avail:
        plt.rcParams["font.sans-serif"] = [_n]
        break
plt.rcParams["axes.unicode_minus"] = False

FIG = Path(__file__).resolve().parent / "figures"
FIG.mkdir(exist_ok=True)
LW = 1.7
C_WIRE = "black"
C_EL = "tab:blue"
C_TXT = "black"


# ---------------------------------------------------------------------
# 基础图元
# ---------------------------------------------------------------------
def new_ax(xlim=(0, 10), ylim=(0, 7), title=""):
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    return fig, ax


def wire(ax, *pts, lw=LW, color=C_WIRE):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, "-", color=color, lw=lw, solid_capstyle="round", zorder=1)


def dot(ax, x, y):
    ax.plot([x], [y], "o", color=C_WIRE, ms=4.5, zorder=3)


def label(ax, x, y, text, ha="center", va="center", size=10, color=C_TXT, weight="normal"):
    ax.text(x, y, text, ha=ha, va=va, fontsize=size, color=color, weight=weight, zorder=4)


def resistor(ax, x, y, name, vertical=True, length=2.0, width=0.55, name_dx=0.75):
    """画一个电阻（矩形符号），返回两端坐标。"""
    if vertical:
        ax.add_patch(Rectangle((x - width / 2, y - length / 2), width, length,
                               fill=True, facecolor="white", edgecolor=C_EL,
                               lw=LW, zorder=2))
        label(ax, x + name_dx, y, name, ha="left")
        return (x, y - length / 2), (x, y + length / 2)
    else:
        ax.add_patch(Rectangle((x - length / 2, y - width / 2), length, width,
                               fill=True, facecolor="white", edgecolor=C_EL,
                               lw=LW, zorder=2))
        label(ax, x, y + width / 2 + 0.28, name)
        return (x - length / 2, y), (x + length / 2, y)


def capacitor(ax, x, y, name, vertical=True, gap=0.28, plate=0.9, name_dx=1.0):
    """画一个电容（两块平行板）。"""
    if vertical:
        for dy in (-gap / 2, gap / 2):
            ax.plot([x - plate / 2, x + plate / 2], [y + dy, y + dy],
                    "-", color=C_EL, lw=LW + 0.6, zorder=2)
        label(ax, x + name_dx, y, name, ha="left")
        return (x, y - gap / 2 - 0.35), (x, y + gap / 2 + 0.35)
    else:
        for dx in (-gap / 2, gap / 2):
            ax.plot([x + dx, x + dx], [y - plate / 2, y + plate / 2],
                    "-", color=C_EL, lw=LW + 0.6, zorder=2)
        label(ax, x, y + plate / 2 + 0.35, name)
        return (x - gap / 2 - 0.35, y), (x + gap / 2 + 0.35, y)


def vsource(ax, x, y, name, r=0.5, plus_top=True):
    """画电压源（圆圈 + 正负号）。"""
    ax.add_patch(Circle((x, y), r, fill=True, facecolor="white", edgecolor=C_EL, lw=LW, zorder=2))
    label(ax, x, y + 0.22, "+", size=11)
    label(ax, x, y - 0.22, "−", size=11)
    label(ax, x - 0.85, y, name, ha="right")
    return (x, y - r), (x, y + r)


def ground(ax, x, y):
    for i, w in enumerate((0.55, 0.36, 0.18)):
        ax.plot([x - w / 2, x + w / 2], [y + i * 0.14, y + i * 0.14],
                "-", color=C_WIRE, lw=LW, zorder=2)


def isource(ax, x, y, name, r=0.5, direction="up"):
    ax.add_patch(Circle((x, y), r, fill=True, facecolor="white", edgecolor=C_EL, lw=LW, zorder=2))
    ax.annotate("", xy=(x, y + 0.32), xytext=(x, y - 0.32),
                arrowprops=dict(arrowstyle="->", color=C_EL, lw=1.6))
    label(ax, x - 0.85, y, name, ha="right")
    return (x, y - r), (x, y + r)


def nmos(ax, x, y, label_name="M1", with_bulk_to_gnd=False, gnd_y=None):
    """
    画 NMOS 符号（栅极在左，漏极在上，源极在下）。
    返回：gate 端点、drain 端点、source 端点
    """
    # 栅极竖线
    ax.plot([x - 0.25, x - 0.25], [y - 0.9, y + 0.9], "-", color=C_EL, lw=LW + 0.8, zorder=2)
    # 沟道竖线（三段）
    for dy in (0.62, 0.0, -0.62):
        ax.plot([x + 0.05, x + 0.05], [y + dy - 0.28, y + dy + 0.28],
                "-", color=C_EL, lw=LW + 0.8, zorder=2)
    # 漏极、源极引出
    ax.plot([x + 0.05, x + 0.9], [y + 0.62, y + 0.62], "-", color=C_EL, lw=LW, zorder=2)
    ax.plot([x + 0.05, x + 0.9], [y - 0.62, y - 0.62], "-", color=C_EL, lw=LW, zorder=2)
    ax.plot([x + 0.9, x + 0.9], [y + 0.62, y + 1.4], "-", color=C_EL, lw=LW, zorder=2)
    ax.plot([x + 0.9, x + 0.9], [y - 0.62, y - 1.4], "-", color=C_EL, lw=LW, zorder=2)
    # 衬底箭头
    ax.annotate("", xy=(x + 0.05, y + 0.72), xytext=(x + 0.5, y + 0.72),
                arrowprops=dict(arrowstyle="->", color=C_EL, lw=1.3))
    # 栅极引出
    ax.plot([x - 0.25, x - 1.1], [y, y], "-", color=C_EL, lw=LW, zorder=2)
    label(ax, x + 1.15, y + 0.3, label_name, ha="left")
    return (x - 1.1, y), (x + 0.9, y + 1.4), (x + 0.9, y - 1.4)


def save(fig, name):
    p = FIG / name
    fig.tight_layout()
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"  [图] {p}")


# =====================================================================
# ① RC 低通滤波器
# =====================================================================
def draw_rc():
    fig, ax = new_ax((0, 10), (0, 6.5), "① RC 低通滤波器 电路图")
    y_top = 4.6
    y_bot = 1.0

    vsource(ax, 1.2, (y_top + y_bot) / 2, "Vin\n方波 1V/2kHz")
    wire(ax, (1.2, (y_top + y_bot) / 2 + 0.5), (1.2, y_top), (3.0, y_top))
    r_a, r_b = resistor(ax, 4.0, y_top, "R = 1.6 kΩ", vertical=False, name_dx=0)
    wire(ax, (3.0, y_top), r_a)
    wire(ax, r_b, (7.4, y_top))
    dot(ax, 7.4, y_top)
    wire(ax, (7.4, y_top), (7.4, y_top - 1.2))
    c_a, c_b = capacitor(ax, 7.4, y_top - 1.7, "C = 100 nF", vertical=True, name_dx=0.9)
    wire(ax, (7.4, y_top - 1.2), c_a)
    wire(ax, c_b, (7.4, y_bot))
    wire(ax, (7.4, y_bot), (1.2, y_bot))
    wire(ax, (1.2, y_bot), (1.2, (y_top + y_bot) / 2 - 0.5))
    ground(ax, 4.2, y_bot - 0.45)
    wire(ax, (4.2, y_bot), (4.2, y_bot - 0.45))
    # 输出端子
    wire(ax, (7.4, y_top), (9.0, y_top))
    label(ax, 9.35, y_top, "Vout", ha="left")
    label(ax, 8.2, y_top + 0.45, "低通：f_c = 1/(2πRC) ≈ 995 Hz", size=9.5, color="tab:red")
    save(fig, "sch_rc.png")


# =====================================================================
# ② 戴维南：原始网络 + 等效电路
# =====================================================================
def draw_thevenin():
    fig, ax = new_ax((0, 10), (0, 7), "② 含源二端网络（端口 a-b）")
    y_top, y_bot = 5.4, 1.2
    # 电压源 V1 + R1 串联
    vsource(ax, 1.4, (y_top + y_bot) / 2, "V1 = 12 V")
    wire(ax, (1.4, (y_top + y_bot) / 2 + 0.5), (1.4, y_top), (3.2, y_top))
    r_a, r_b = resistor(ax, 4.2, y_top, "R1 = 1 kΩ", vertical=False, name_dx=0)
    wire(ax, (3.2, y_top), r_a)
    wire(ax, r_b, (6.6, y_top))
    dot(ax, 6.6, y_top)
    # R2 到地
    wire(ax, (6.6, y_top), (6.6, y_top - 1.0))
    r2a, r2b = resistor(ax, 6.6, y_top - 1.9, "R2 = 3 kΩ", vertical=True, name_dx=0.75)
    wire(ax, (6.6, y_top - 1.0), r2a)
    wire(ax, r2b, (6.6, y_bot))
    # 地
    wire(ax, (6.6, y_bot), (1.4, y_bot))
    wire(ax, (1.4, y_bot), (1.4, (y_top + y_bot) / 2 - 0.5))
    ground(ax, 4.0, y_bot - 0.45)
    wire(ax, (4.0, y_bot), (4.0, y_bot - 0.45))
    # 端口 a、b
    wire(ax, (6.6, y_top), (8.6, y_top))
    dot(ax, 8.6, y_top)
    label(ax, 8.95, y_top, "a", ha="left", size=12, weight="bold")
    wire(ax, (8.6, y_bot), (8.6, y_top), lw=1.2, color="tab:gray")
    ax.plot([8.6], [y_bot], "o", color="tab:gray", ms=4.5)
    label(ax, 8.95, y_bot, "b", ha="left", size=12, weight="bold")
    label(ax, 8.6, (y_top + y_bot) / 2, "端口\n(开路测 V_oc\n短路测 I_sc)", size=9.5, color="tab:red")
    save(fig, "sch_thevenin.png")

    # 等效电路
    fig, ax = new_ax((0, 10), (0, 6.5), "② 戴维南等效电路")
    y_top, y_bot = 4.6, 1.2
    vsource(ax, 1.5, (y_top + y_bot) / 2, "V_th = 9 V")
    wire(ax, (1.5, (y_top + y_bot) / 2 + 0.5), (1.5, y_top), (3.0, y_top))
    r_a, r_b = resistor(ax, 4.0, y_top, "R_th = 750 Ω", vertical=False, name_dx=0)
    wire(ax, (3.0, y_top), r_a)
    wire(ax, r_b, (7.0, y_top))
    dot(ax, 7.0, y_top)
    # 负载
    wire(ax, (7.0, y_top), (7.0, y_top - 1.0))
    ra, rb = resistor(ax, 7.0, y_top - 1.9, "R_L", vertical=True, name_dx=0.75)
    wire(ax, (7.0, y_top - 1.0), ra)
    wire(ax, rb, (7.0, y_bot))
    wire(ax, (7.0, y_bot), (1.5, y_bot))
    wire(ax, (1.5, y_bot), (1.5, (y_top + y_bot) / 2 - 0.5))
    ground(ax, 4.2, y_bot - 0.45)
    wire(ax, (4.2, y_bot), (4.2, y_bot - 0.45))
    label(ax, 8.2, y_top, "端口 a", ha="left", size=10)
    label(ax, 8.2, y_bot, "端口 b", ha="left", size=10)
    save(fig, "sch_thevenin_equiv.png")


# =====================================================================
# ③ NMOS 共源放大电路（完整电路 + 直流通路 + 小信号模型）
# =====================================================================
def draw_nmos_full():
    fig, ax = new_ax((0, 11), (0, 8), "③ NMOS 共源级放大电路（题目参数）")
    x_rail = 1.6
    x_gate = 4.2
    x_drain = 6.8
    y_vdd, y_gate, y_gnd = 7.0, 4.2, 1.0

    # VDD 电源轨
    wire(ax, (x_rail, y_vdd), (x_drain, y_vdd))
    label(ax, x_rail + 0.4, y_vdd + 0.42, "VDD = 5 V", ha="left", size=11, weight="bold")
    ground(ax, x_rail, y_gnd - 0.5)
    wire(ax, (x_rail, y_gnd), (x_rail, y_gnd - 0.5))

    # Rd
    wire(ax, (x_drain, y_vdd), (x_drain, y_vdd - 0.8))
    rda, rdb = resistor(ax, x_drain, y_vdd - 1.8, "Rd = 2 kΩ", vertical=True, name_dx=0.75)
    wire(ax, (x_drain, y_vdd - 0.8), rda)

    # MOS
    wire(ax, rdb, (x_drain, 4.2))
    g, d, s = nmos(ax, x_gate + 1.2, y_gate, "")
    wire(ax, (x_drain, 4.2), d)
    wire(ax, s, (s[0], y_gnd))
    wire(ax, (s[0], y_gnd), (x_rail, y_gnd))
    # 器件参数标注放在管子左下方，避免和输出线重叠
    label(ax, x_gate + 2.05, y_gate - 2.0,
          "NMOS\nK = 0.8 mA/V²\nV_th = 1 V\nλ = 0.02 /V",
          ha="left", va="top", size=9.5)

    # 栅极 → 分压
    wire(ax, g, (x_gate, y_gate))
    dot(ax, x_gate, y_gate)
    # Rg1 到 VDD
    wire(ax, (x_gate, y_gate), (x_gate, y_gate + 0.8))
    r1a, r1b = resistor(ax, x_gate, y_gate + 1.8, "Rg1 = 60 kΩ", vertical=True, name_dx=-2.1)
    wire(ax, (x_gate, y_gate + 0.8), r1a)
    wire(ax, r1b, (x_gate, y_vdd))
    wire(ax, (x_gate, y_vdd), (x_rail, y_vdd))
    # Rg2 到地
    wire(ax, (x_gate, y_gate), (x_gate, y_gate - 0.8))
    r2a, r2b = resistor(ax, x_gate, y_gate - 1.8, "Rg2 = 40 kΩ", vertical=True, name_dx=-2.1)
    wire(ax, (x_gate, y_gate - 0.8), r2a)
    wire(ax, r2b, (x_gate, y_gnd))
    wire(ax, (x_gate, y_gnd), (x_rail, y_gnd))

    # 输入 + 耦合电容
    vsource(ax, 0.9, y_gate, "Vi\n10mV\n1kHz", r=0.55)
    wire(ax, (0.9, y_gate + 0.55), (0.9, y_gate), (1.9, y_gate))
    ca, cb = capacitor(ax, 2.5, y_gate, "Cb1\n(足够大)", vertical=False, name_dx=0)
    wire(ax, (1.9, y_gate), ca)
    wire(ax, cb, (x_gate, y_gate))
    wire(ax, (0.9, y_gate - 0.55), (0.9, y_gnd), (x_rail, y_gnd))

    # 输出
    dot(ax, x_drain, 4.2)
    wire(ax, (x_drain, 4.2), (9.6, 4.2))
    label(ax, 9.9, 4.2, "Vout", ha="left", size=11)
    label(ax, 9.9, 5.0, "输出与输入反相\n(Av < 0)", ha="left", size=9.5, color="tab:red")
    save(fig, "sch_nmos.png")


def draw_nmos_dc_path():
    fig, ax = new_ax((0, 10), (0, 7), "③ NMOS 直流通路（Cb1 视为开路，输入信号断开）")
    x_rail, x_gate, x_drain = 1.8, 4.4, 7.0
    y_vdd, y_gate, y_gnd = 6.0, 3.6, 1.0

    wire(ax, (x_rail, y_vdd), (x_drain, y_vdd))
    label(ax, x_rail + 0.3, y_vdd + 0.4, "VDD = 5 V", ha="left", size=11, weight="bold")
    ground(ax, x_rail, y_gnd - 0.5)
    wire(ax, (x_rail, y_gnd), (x_rail, y_gnd - 0.5))

    wire(ax, (x_drain, y_vdd), (x_drain, y_vdd - 0.7))
    rda, rdb = resistor(ax, x_drain, y_vdd - 1.7, "Rd = 2 kΩ", vertical=True, name_dx=0.75)
    wire(ax, (x_drain, y_vdd - 0.7), rda)
    wire(ax, rdb, (x_drain, y_gate))

    g, d, s = nmos(ax, x_gate + 1.1, y_gate, "NMOS")
    wire(ax, (x_drain, y_gate), d)
    wire(ax, s, (s[0], y_gnd), (x_rail, y_gnd))

    wire(ax, g, (x_gate, y_gate))
    dot(ax, x_gate, y_gate)
    wire(ax, (x_gate, y_gate), (x_gate, y_gate + 0.7))
    r1a, r1b = resistor(ax, x_gate, y_gate + 1.7, "Rg1 = 60 kΩ", vertical=True, name_dx=-2.1)
    wire(ax, (x_gate, y_gate + 0.7), r1a)
    wire(ax, r1b, (x_gate, y_vdd), (x_rail, y_vdd))
    wire(ax, (x_gate, y_gate), (x_gate, y_gate - 0.7))
    r2a, r2b = resistor(ax, x_gate, y_gate - 1.7, "Rg2 = 40 kΩ", vertical=True, name_dx=-2.1)
    wire(ax, (x_gate, y_gate - 0.7), r2a)
    wire(ax, r2b, (x_gate, y_gnd), (x_rail, y_gnd))
    label(ax, 8.6, y_gate, "I_D = 0.853 mA\nV_GS = 2.00 V\nV_DS = 3.29 V",
          ha="left", size=10, color="tab:red")
    save(fig, "sch_nmos_dc_path.png")


def draw_nmos_small_signal():
    """小信号等效模型：输入侧 Rg1∥Rg2，输出侧 gm·V_gs、ro、Rd 三条支路并联。"""
    fig, ax = new_ax((0, 12), (0, 7), "③ 小信号等效模型（三种元件都从输出节点接到地 → 并联）")
    y_top, y_bot = 5.2, 1.6            # 输出节点母线 / 地线
    x_in = 2.2                          # 输入节点
    x_rg = 1.4                          # Rg1∥Rg2 支路
    x_gm, x_ro, x_rd = 5.6, 7.6, 9.4    # 三条输出侧支路

    # ---- 输入侧：Vi 与 Rg1∥Rg2 ----
    wire(ax, (x_in, y_bot), (x_in, y_top - 1.0))
    dot(ax, x_in, y_top - 1.0)
    label(ax, x_in - 0.2, (y_top - 1.0 + y_bot) / 2 - 0.3, "Vi\n(小信号)", ha="right", size=10)
    # Rg1∥Rg2：接在栅极与地之间
    wire(ax, (x_in, y_top - 1.0), (x_rg, y_top - 1.0))
    wire(ax, (x_rg, y_top - 1.0), (x_rg, y_top - 0.3))
    rga, rgb = resistor(ax, x_rg, y_top + 0.7, "Rg1∥Rg2\n= 24 kΩ", vertical=True, name_dx=-0.8)
    wire(ax, (x_rg, y_top - 0.3), rga)
    wire(ax, rgb, (x_rg, y_bot))
    dot(ax, x_rg, y_bot)
    wire(ax, (x_rg, y_bot), (x_in, y_bot))
    # 栅极 → 输出母线之间的 V_gs 标注（栅极就是输入节点）
    wire(ax, (x_in, y_top - 1.0), (x_gm - 1.5, y_top - 1.0))
    dot(ax, x_gm - 1.5, y_top - 1.0)
    wire(ax, (x_gm - 1.5, y_top - 1.0), (x_gm - 1.5, y_top - 0.2))
    ax.annotate("", xy=(x_in + 0.45, y_top - 1.0), xytext=(x_in + 0.45, y_bot),
                arrowprops=dict(arrowstyle="<->", color="tab:red", lw=1.4))
    label(ax, x_in + 0.65, (y_top - 1.0 + y_bot) / 2, "V_gs", ha="left", size=10.5, color="tab:red")

    # ---- 输出母线 ----
    wire(ax, (x_gm - 1.5, y_top - 0.2), (x_gm - 1.5, y_top))
    wire(ax, (x_gm - 1.5, y_top), (x_rd + 0.8, y_top))
    dot(ax, x_gm - 1.5, y_top)
    label(ax, x_rd + 0.85, y_top, "Vout", ha="left", size=11)

    # ---- 支路 1：gm·V_gs 电流源（漏→源，箭头向下） ----
    wire(ax, (x_gm, y_top), (x_gm, y_top - 0.5))
    ax.add_patch(Circle((x_gm, y_top - 1.1), 0.6, fill=True, facecolor="white",
                        edgecolor=C_EL, lw=LW, zorder=2))
    ax.annotate("", xy=(x_gm, y_top - 0.5), xytext=(x_gm, y_top - 1.7),
                arrowprops=dict(arrowstyle="->", color=C_EL, lw=1.7))
    label(ax, x_gm, y_top - 2.1, "gm·V_gs", ha="center", size=10.5)
    label(ax, x_gm, y_top - 2.45, "= 1.705 mS·V_gs", ha="center", size=9, color="tab:gray")
    wire(ax, (x_gm, y_top - 1.7), (x_gm, y_bot))
    dot(ax, x_gm, y_bot)

    # ---- 支路 2：ro ----
    wire(ax, (x_ro, y_top), (x_ro, y_top - 0.5))
    roa, rob = resistor(ax, x_ro, y_top - 1.4, "ro = 58.6 kΩ", vertical=True, name_dx=0.8)
    wire(ax, (x_ro, y_top - 0.5), roa)
    wire(ax, rob, (x_ro, y_bot))
    dot(ax, x_ro, y_bot)

    # ---- 支路 3：Rd ----
    wire(ax, (x_rd, y_top), (x_rd, y_top - 0.5))
    rda, rdb = resistor(ax, x_rd, y_top - 1.4, "Rd = 2 kΩ", vertical=True, name_dx=0.8)
    wire(ax, (x_rd, y_top - 0.5), rda)
    wire(ax, rdb, (x_rd, y_bot))
    dot(ax, x_rd, y_bot)

    # ---- 地线 ----
    wire(ax, (x_rg, y_bot), (x_rd, y_bot))
    ground(ax, 6.5, y_bot - 0.5)
    wire(ax, (6.5, y_bot), (6.5, y_bot - 0.5))

    label(ax, 7.5, 0.7, "Av = -gm·(Rd ∥ ro) = -1.705 mS × 1.934 kΩ ≈ -3.30",
          size=10.5, color="tab:red")
    save(fig, "sch_nmos_small_signal.png")


if __name__ == "__main__":
    print("生成电路图 ……")
    draw_rc()
    draw_thevenin()
    draw_nmos_full()
    draw_nmos_dc_path()
    draw_nmos_small_signal()
    print("完成。图片都在 figures/ 目录，可直接插入 README。")
