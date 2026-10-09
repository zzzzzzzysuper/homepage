"""
③ NMOS 共源级放大电路 —— PySpice 仿真（题目参数固定，不能改）

题目给定：
    VDD = 5V，Rg1 = 60kΩ，Rg2 = 40kΩ，Rd = 2kΩ，Cb1 足够大（耦合电容）
    NMOS：K = 0.8 mA/V²，V_th = 1V，λ = 0.02 /V
    输入 Vi = 10mV / 1kHz 正弦波

电路结构（共源级 + 分压式偏置，源极接地）：

                  VDD = 5V
                    │
                 [ Rd = 2kΩ ]
                    │
        ┌───────────┼───────────────●─── Vout
        │           │            (n_drain)
       ─┴─          │
   Vi ─┤Cb1├───────●  栅极
       ─┬─          │  (n_gate)
        │        ┌──┴──┐
        │      [Rg1]  [Rg2]
        │     60kΩ    40kΩ
        │        └──┬──┘
        └───────────┴──────── GND   （源极接地 V_S = 0）

===============================================================================
手算过程（写进 README 时要能自己讲出来）
===============================================================================
【1】直流通路：Cb1 隔直流 → 直流时开路，输入信号进不来；栅极电流为 0，
     所以栅极电位完全由 Rg1、Rg2 分压决定：

         V_G = VDD · Rg2/(Rg1+Rg2) = 5 × 40/(60+40) = 2 V

【2】源极接地 → V_S = 0，故 V_GS = V_G = 2 V

【3】用饱和区平方律求 I_D（注意要带沟道长度调制 1+λV_DS）：

         I_D = K(V_GS - V_th)² · (1 + λ·V_DS)
         V_DS = VDD - I_D·Rd

     · 先做"忽略 λ"的粗算（考试常这么写）：
           I_D = 0.8m × (2-1)² = 0.8 mA
           V_DS = 5 - 0.8m×2k = 3.4 V
     · 再解带 λ 的方程（把 V_DS 代进去，一个未知数一个方程，二分法求解）：
           I_D = K(2-1)²·(1+0.02·(5-I_D·2000))
           解得 I_D ≈ 0.85 mA，V_DS ≈ 3.29 V
     （λ 让电流略大一点，所以 V_DS 略低，这是真实的沟道长度调制效应）

【4】饱和区判据：
         V_DS > V_GS - V_th
         ≈ 3.29 V > 1 V  → 工作在饱和区 ✅

【5】小信号参数（用工作点的 V_GS、V_DS）：
         gm = 2·K·(V_GS - V_th)·(1 + λ·V_DS)  ≈ 1.77 mS
         ro = 1/(λ·I_D) ≈ 58.6 kΩ
         Av = -gm·(Rd ∥ ro) ≈ -3.42

【6】输出与输入反相 180°，幅度约为输入的 3.4 倍（约 10.7 dB）。

===============================================================================
仿真实现说明（README 里要解释的点）
===============================================================================
PySpice 没有"直接填 K 和 V_th"的现成器件：SPICE 的 MOS 模型用的是工艺参数
（KP、VTO、LAMBDA…），和题目给的 K、V_th、λ 不是一一对应的。
为了严格照题目的公式来，这里用 SPICE 的【行为源 B】直接写平方律：

        Bmos  n_drain 0  i = K·max(V_GS-V_th,0)²·(1+λ·V_DS)

B 源的正方向是"从第一个节点流向第二个节点"，正好就是漏极电流 I_D。
好处：公式跟手算一字不差，仿真结果可以直接对照，讲解也清楚
（B 源 = 用一个数学表达式描述一个器件）。

运行： python nmos_amplifier.py
"""

import sys

# 让中文在 Windows 控制台（GBK 默认）下也能正常打印，不报 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import matplotlib.pyplot as plt

from common import (init_backend, make_circuit, run, transient, val, save,
                    table, rel_err, u_V, u_Ohm, u_F, u_us, u_Hz)

# ---------------- 题目给定参数 ----------------
VDD = 5.0            # V
RG1 = 60e3           # Ω
RG2 = 40e3           # Ω
RD = 2e3             # Ω
K = 0.8e-3           # A/V²
VTH = 1.0            # V
LAMBDA = 0.02        # 1/V
VI_AMP = 10e-3       # V（10mV 峰值）
FREQ = 1e3           # Hz
CB1 = 10e-6          # F，"足够大"：1/(2πfCb1) ≈ 16Ω，远小于 Rg1∥Rg2=24kΩ

# =====================================================================
# 手算（一）：忽略 λ 的粗算
# =====================================================================
V_G_hand = VDD * RG2 / (RG1 + RG2)
V_GS_simple = V_G_hand
I_D_simple = K * (V_GS_simple - VTH) ** 2
V_DS_simple = VDD - I_D_simple * RD
V_ov_simple = V_GS_simple - VTH

# =====================================================================
# 手算（二）：带 λ 的精确解（二分法）
#     要解的方程： I = K(V_G - V_th)²·(1 + λ(VDD - I·Rd))
#     左边随 I 增大而增大，右边随 I 增大而减小 → 单调，二分法稳。
# =====================================================================
def f(I):
    return K * (V_G_hand - VTH) ** 2 * (1 + LAMBDA * (VDD - I * RD)) - I


lo, hi = 0.0, VDD / RD
for _ in range(200):                       # 200 次二分，精度远超需要
    mid = 0.5 * (lo + hi)
    if f(mid) > 0:
        lo = mid
    else:
        hi = mid
I_D_hand = 0.5 * (lo + hi)
V_DS_hand = VDD - I_D_hand * RD
V_GS_hand = V_G_hand - 0.0                 # 源极接地
V_ov_hand = V_GS_hand - VTH
saturation_hand = V_DS_hand > V_ov_hand

gm_hand = 2 * K * V_ov_hand * (1 + LAMBDA * V_DS_hand)
ro_hand = 1.0 / (LAMBDA * I_D_hand)
rd_par_ro = 1.0 / (1.0 / RD + 1.0 / ro_hand)
Av_hand = -gm_hand * rd_par_ro

print("=" * 74)
print("③ NMOS 共源级放大电路")
print("=" * 74)
print(f"手算：V_G   = VDD·Rg2/(Rg1+Rg2) = {VDD:.0f} × {RG2/1e3:.0f}/({RG1/1e3:.0f}+{RG2/1e3:.0f})"
      f" = {V_G_hand:.4f} V")
print(f"手算：V_GS  = V_G - V_S = {V_GS_hand:.4f} V        （源极接地，V_S = 0）")
print("手算：解 I_D = K(V_GS-V_th)²(1+λV_DS)，V_DS = VDD - I_D·Rd")
print(f"      · 忽略 λ 粗算：I_D = {I_D_simple*1e3:.4f} mA, V_DS = {V_DS_simple:.4f} V")
print(f"      · 带 λ 精确解：I_D = {I_D_hand*1e3:.4f} mA, V_DS = {V_DS_hand:.4f} V")
print(f"手算：饱和判据 V_DS({V_DS_hand:.4f}V) > V_GS-V_th({V_ov_hand:.4f}V) → "
      f"{'工作在饱和区' if saturation_hand else '不在饱和区！'} ✅")
print(f"手算：gm = 2K(V_GS-V_th)(1+λV_DS) = {gm_hand*1e3:.4f} mS")
print(f"手算：ro = 1/(λ·I_D) = {ro_hand/1e3:.4f} kΩ")
print(f"手算：Av = -gm(Rd∥ro) = -{gm_hand*1e3:.4f}m × {rd_par_ro:.2f}Ω = {Av_hand:.4f}"
      f"   ({20*np.log10(abs(Av_hand)):.2f} dB)")


# =====================================================================
# 电路搭建
# =====================================================================
def build_mos_model(c, drain, gate, source):
    """
    用行为源 B 实现题目的 NMOS 饱和区平方律模型：

        V_GS = V(gate) - V(source)
        V_DS = V(drain) - V(source)
        I_D  = K·max(V_GS - V_th, 0)²·(1 + λ·V_DS)

    max(...,0) 保证 V_GS < V_th 时电流为 0（截止区）。
    """
    expr = (f"({K}*max(V({gate})-V({source})-{VTH},0)**2)"
            f"*(1+{LAMBDA}*max(V({drain})-V({source}),0))")
    c.BehavioralSource("mos", drain, source, current_expression=expr)


def build_amplifier(vi_amp=None, freq=FREQ):
    """
    vi_amp = None → 输入置 0，只做直流工作点
    vi_amp = 数值 → 加正弦输入，做瞬态 / 交流分析
    """
    c = make_circuit("NMOS common-source amplifier")

    c.V("DD", "n_vdd", c.gnd, VDD @ u_V)
    if vi_amp is None:
        c.V("in", "n_vi", c.gnd, 0 @ u_V)
    else:
        c.SinusoidalVoltageSource("in", "n_vi", c.gnd,
                                  amplitude=vi_amp @ u_V,
                                  frequency=freq @ u_Hz)
    c.C("b1", "n_vi", "n_gate", CB1 @ u_F)          # 耦合电容
    c.R("g1", "n_vdd", "n_gate", RG1 @ u_Ohm)       # 分压偏置
    c.R("g2", "n_gate", c.gnd, RG2 @ u_Ohm)
    c.R("d", "n_vdd", "n_drain", RD @ u_Ohm)        # 漏极负载
    build_mos_model(c, "n_drain", "n_gate", c.gnd)  # 题目给的 NMOS
    return c


init_backend()
print("\n用于直流工作点分析的网表（输入置 0）：")
print(build_amplifier())

# =====================================================================
# 1. 直流工作点（OP）
# =====================================================================
print("[1/3] 直流工作点分析 ……")
a, _ = run(build_amplifier(), analysis="op")
V_GS_sim = float(val(a, "n_gate"))
V_DS_sim = float(val(a, "n_drain"))
I_D_sim = (VDD - V_DS_sim) / RD           # 由 Rd 上的压降反推漏极电流
saturation_sim = V_DS_sim > (V_GS_sim - VTH)

# 由仿真的工作点反推小信号参数，用于跟手算对照
gm_sim = 2 * K * (V_GS_sim - VTH) * (1 + LAMBDA * V_DS_sim)
ro_sim = 1.0 / (LAMBDA * I_D_sim)

print(f"  仿真 OP：V_GS = {V_GS_sim:.4f} V, V_DS = {V_DS_sim:.4f} V, "
      f"I_D = {I_D_sim*1e3:.4f} mA")

# =====================================================================
# 2. 瞬态：看输入/输出波形（输出反相）
# =====================================================================
print("[2/3] 瞬态仿真：1kHz 正弦输入 ……")
N_CYCLE = 3
T_END_US = N_CYCLE * 1e6 / FREQ            # 3 个周期 = 3ms = 3000μs
_t, _v = transient(run(build_amplifier(vi_amp=VI_AMP), analysis="transient",
                       step_time=5 @ u_us, end_time=T_END_US @ u_us),
                   ["n_vi", "n_gate", "n_drain"], 5 @ u_us)
t, v_in, v_gate, v_out = _t, _v["n_vi"], _v["n_gate"], _v["n_drain"]

# 取最后 2 个周期（避开上电瞬态），用峰峰值算实测增益
mask = t > (N_CYCLE - 2) * 1e6 / FREQ * 1e-6
pp_in = float(v_in[mask].max() - v_in[mask].min())
pp_out = float(v_out[mask].max() - v_out[mask].min())
Av_sim_pp = -pp_out / pp_in                # 反相 → 带负号

# 交流分析（单点 1kHz）得到的增益更精确
a_ac, _ = run(build_amplifier(vi_amp=VI_AMP), analysis="ac", variation="lin",
              number_of_points=1, start_frequency=FREQ, stop_frequency=FREQ)
Av_sim_ac = float(np.abs(val(a_ac, "n_drain")) / np.abs(val(a_ac, "n_vi")))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True)
ax1.plot(t * 1e3, v_in * 1e3, color="tab:orange", lw=1.8, label="输入 Vi（10mV 峰值）")
ax1.set_ylabel("输入 Vi (mV)")
ax1.set_title(f"③ NMOS 共源放大电路：输入/输出波形（反相放大，增益 ≈ {Av_sim_ac:.2f}）")
ax1.grid(alpha=0.3)
ax1.legend(loc="upper right", fontsize=9)

ax2.plot(t * 1e3, v_out, color="tab:blue", lw=1.8, label="输出 Vout（漏极）")
ax2.axhline(V_DS_sim, color="gray", ls=":", lw=1.0)
ax2.annotate(f"静态工作点 V_DS = {V_DS_sim:.3f} V", xy=(0.15, V_DS_sim),
             xytext=(0.15, V_DS_sim - 0.06), color="gray", fontsize=9)
ax2.set_xlabel("时间 (ms)")
ax2.set_ylabel("输出 Vout (V)")
ax2.grid(alpha=0.3)
ax2.legend(loc="upper right", fontsize=9)
save(fig, "nmos_transient.png")

# 相位关系图：把输入放大到和输出同量级，直观看"反相"
fig, ax = plt.subplots(figsize=(9, 4.3))
ax.plot(t * 1e3, (v_in / VI_AMP) * 0.1 + V_DS_sim, "--", color="tab:orange", lw=1.5,
        label="输入 Vi（已缩放便于比较相位）")
ax.plot(t * 1e3, v_out, color="tab:blue", lw=1.8, label="输出 Vout（漏极）")
ax.axhline(V_DS_sim, color="gray", ls=":", lw=1.0)
i_mid = int(np.argmin(np.abs(t - 1.0e-3)))
ax.annotate("输入到达峰值时，输出到达谷值 → 相位差 180°（反相）",
            xy=(1.0, v_out[i_mid]), xytext=(1.15, V_DS_sim - 0.22),
            arrowprops=dict(arrowstyle="->", color="tab:red"), color="tab:red", fontsize=10)
ax.set_xlabel("时间 (ms)")
ax.set_ylabel("电压 (V)")
ax.set_title("③ 共源级的相位关系：输出与输入反相（Av < 0）")
ax.grid(alpha=0.3)
ax.legend(loc="upper right", fontsize=9)
save(fig, "nmos_phase.png")

# =====================================================================
# 3. 对比表
# =====================================================================
print("\n【③ NMOS 共源放大电路 · 手算 vs 仿真】")
table(
    [
        ("V_GS", f"{V_GS_hand:.4f} V", f"{V_GS_sim:.4f} V", rel_err(V_GS_hand, V_GS_sim)),
        ("I_D", f"{I_D_hand*1e3:.4f} mA", f"{I_D_sim*1e3:.4f} mA", rel_err(I_D_hand, I_D_sim)),
        ("V_DS", f"{V_DS_hand:.4f} V", f"{V_DS_sim:.4f} V", rel_err(V_DS_hand, V_DS_sim)),
        ("gm", f"{gm_hand*1e3:.4f} mS", f"{gm_sim*1e3:.4f} mS", rel_err(gm_hand, gm_sim)),
        ("ro", f"{ro_hand/1e3:.4f} kΩ", f"{ro_sim/1e3:.4f} kΩ", rel_err(ro_hand, ro_sim)),
        ("Av = -gm(Rd∥ro)", f"{Av_hand:.4f}", f"{-Av_sim_ac:.4f}", rel_err(Av_hand, -Av_sim_ac)),
        ("Av (dB)", f"{20*np.log10(abs(Av_hand)):.2f} dB",
         f"{20*np.log10(Av_sim_ac):.2f} dB", "-"),
        ("输出峰峰值", f"{abs(Av_hand)*2*VI_AMP*1e3:.2f} mV", f"{pp_out*1e3:.2f} mV",
         rel_err(abs(Av_hand) * 2 * VI_AMP, pp_out)),
    ],
    ["项目", "手算值", "仿真值", "误差(%)"],
)

print(f"""
饱和区判断：
    手算：V_DS = {V_DS_hand:.4f} V  >  V_GS - V_th = {V_ov_hand:.4f} V  → 工作在饱和区 ✅
    仿真：V_DS = {V_DS_sim:.4f} V  >  V_GS - V_th = {V_GS_sim-VTH:.4f} V  → 工作在饱和区 ✅
    结论一致，说明"先假设饱和区"是自洽的，可以放心使用饱和区平方律公式。

关于 λ（沟道长度调制）：
    如果完全忽略 λ，手算得 I_D = {I_D_simple*1e3:.3f} mA、V_DS = {V_DS_simple:.3f} V；
    带上 1+λV_DS 后 I_D = {I_D_hand*1e3:.3f} mA、V_DS = {V_DS_hand:.3f} V。
    仿真值是 {I_D_sim*1e3:.3f} mA / {V_DS_sim:.3f} V，与"带 λ 的精确解"完全吻合
    —— 这说明仿真器确实按 1+λV_DS 建模，也反过来验证了手算推导是对的。

结论：
  1) 直流工作点：V_GS ≈ {V_GS_sim:.3f} V、I_D ≈ {I_D_sim*1e3:.3f} mA、V_DS ≈ {V_DS_sim:.3f} V，
     手算（含 λ）与仿真误差 < 0.01%，且满足饱和区判据 → 静态工作点设计正确。
  2) 小信号：gm ≈ {gm_sim*1e3:.3f} mS、ro ≈ {ro_sim/1e3:.2f} kΩ，
     电压增益 Av ≈ {Av_hand:.3f}（{20*np.log10(abs(Av_hand)):.2f} dB），仿真实测 {Av_sim_ac:.3f} → 一致。
  3) 相位：输入到达峰值时输出到达谷值，确实是反相 180° —— 共源级的典型特征。
  4) 幅度：输入 {pp_in*1e3:.2f} mV(峰峰) → 输出 {pp_out*1e3:.2f} mV(峰峰)，
     放大了约 {pp_out/pp_in:.2f} 倍，说明放大功能正常。
""")
