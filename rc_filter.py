"""
① RC 低通滤波器 —— PySpice 仿真

电路：
    Vin ──[ R ]──┬── Vout
                 │
                [C]
                 │
                GND

    元件参数（自己定的）：
        R = 1.6 kΩ
        C = 100 nF

手算：
    τ  = R·C = 1600 × 100e-9 = 1.6e-4 s = 160 μs
    fc = 1/(2πRC) = 1/(2π × 1.6e-4) ≈ 994.7 Hz

仿真内容：
    1) 瞬态：输入 0~1V、500Hz 方波，看电容充放电（从波形反推 τ）
    2) 交流：1Hz~1MHz 扫频，画波特图，找 -3dB 点 → 就是 fc
    3) 打印「手算 vs 仿真」对比表

运行： python rc_filter.py
"""

import numpy as np
import matplotlib.pyplot as plt

from common import (init_backend, make_circuit, run, transient, val, gain_db,
                    save, table, rel_err, u_V, u_Ohm, u_F, u_Hz, u_MHz, u_us)

# ---------------- 元件参数（想改就改这里） ----------------
R = 1_600.0        # Ω
C = 100e-9         # F
V_HIGH = 1.0       # 方波高电平 V
# 方波频率选两个：
#   F_LOW  = 100Hz：半周期 5ms ≫ 5τ(0.8ms)，电容能充到稳态 → 用它反推 τ
#   F_HIGH = 2kHz ：半周期 0.25ms ≈ 1.5τ，电容来不及充满 → 用它看"滤波"效果
F_LOW = 100.0
F_HIGH = 2000.0
T_END_MS = 4.0     # 仿真总时长 4ms

# ---------------- 手算 ----------------
tau_hand = R * C
fc_hand = 1.0 / (2 * np.pi * R * C)
print("=" * 68)
print("① RC 低通滤波器")
print("=" * 68)
print(f"手算：τ  = R·C      = {R:.0f} × {C:.2e} = {tau_hand:.3e} s = {tau_hand*1e6:.1f} μs")
print(f"手算：fc = 1/(2πRC) = {fc_hand:.2f} Hz")


# =====================================================================
# 1. 建立电路
#    注意：节点名不要用 in / out / lambda 这类 Python 关键字，PySpice 会报
#    "Node name 'in' is a Python keyword"，所以这里用 n_in / n_out。
# =====================================================================
def build_circuit(f_square):
    c = make_circuit("RC low-pass filter")
    half_us = 1e6 / (2 * f_square)          # 半个周期，单位 μs
    c.PulseVoltageSource(
        "input", "n_in", c.gnd,
        initial_value=0 @ u_V,
        pulsed_value=V_HIGH @ u_V,
        delay_time=0 @ u_us,
        rise_time=0.001 @ u_us,             # 1ns 上升沿，近似理想方波
        fall_time=0.001 @ u_us,
        pulse_width=half_us @ u_us,
        period=1e6 / f_square @ u_us,
    )
    c.R(1, "n_in", "n_out", R @ u_Ohm)
    c.C(1, "n_out", c.gnd, C @ u_F)
    return c


init_backend()
print("\n生成的 SPICE 网表（100Hz 方波那一路）：")
print(build_circuit(F_LOW))

# =====================================================================
# 2. 仿真一：瞬态
#    (a) 100Hz 方波 → 半周期足够长，电容充到稳态，用它反推 τ
#    (b) 2kHz  方波 → 半周期和 τ 同量级，输出被"削"成小三角波，体现低通
# =====================================================================
print("\n[1/2] 瞬态仿真：方波输入 ……")


def run_square(f_square):
    _t, _v = transient(run(build_circuit(f_square), analysis="transient",
                           step_time=1 @ u_us, end_time=T_END_MS * 1000 @ u_us),
                       ["n_in", "n_out"], 1 @ u_us)
    return _t, _v["n_in"], _v["n_out"]


t, v_in, v_out = run_square(F_LOW)                 # 时间单位：秒
_, v_in_fast, v_out_fast = run_square(F_HIGH)


# 从仿真波形反推 τ：
# 每个半周期里电容是"从某个起点做指数充/放电"，任意取两个时刻 t1<t2：
#   (V(t2)-V∞) / (V(t1)-V∞) = exp(-(t2-t1)/τ)
#   → τ = (t2-t1) / ln( (V(t1)-V∞)/(V(t2)-V∞) )
# 这个方法不需要"从 0 开始"，比读 0.632·Vin 那个点稳得多。
def tau_from_decay(tt, vv, i0, i1, v_inf):
    y1, y2 = vv[i0] - v_inf, vv[i1] - v_inf
    if abs(y1) < 1e-12 or abs(y2) < 1e-12 or y1 * y2 <= 0:
        return None
    return float((tt[i1] - tt[i0]) / np.log(y1 / y2))


# 100Hz 方波：第 1 个下降沿在 5ms，但我们只仿到 4ms，所以用第 1 个上升沿的充电段
idx = np.nonzero((t > 0.1e-3) & (t < 2.4e-3))[0]        # 上升后 0.1ms ~ 2.4ms
tau_rise = tau_from_decay(t, v_out, idx[0], idx[len(idx) // 2], V_HIGH)
tau_sim = tau_rise

# 稳态值与纹波（100Hz 时电容能充满，基本等于方波幅度；
#                 2kHz 时来不及充满，纹波变小 = 滤波效果）
# 稳态值（100Hz 时电容能充满，4ms 时已经稳定在 V_HIGH 附近）
v_ss_high = float(np.mean(v_out[(t > 3.0e-3) & (t < 4.0e-3)]))
# 2kHz 时的输出纹波：远小于方波幅度，说明高频被滤掉
tt_f, vv_f = t, v_out_fast
ripple_fast = float(vv_f[tt_f > 3e-3].max() - vv_f[tt_f > 3e-3].min())

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.6))
ax1.plot(t * 1e3, v_in, "--", color="tab:gray", lw=1.2, label="输入 Vin（100Hz 方波）")
ax1.plot(t * 1e3, v_out, color="tab:blue", lw=1.8, label="输出 Vout（电容两端）")
ax1.axhline(0.632 * V_HIGH, color="tab:red", ls=":", lw=1.0)
ax1.annotate(f"充到 0.632·Vin 用时 1τ ≈ {tau_sim*1e6:.0f} μs\n（手算 τ = {tau_hand*1e6:.0f} μs）",
             xy=(tau_sim * 1e3, 0.632 * V_HIGH), xytext=(0.75, 0.42),
             arrowprops=dict(arrowstyle="->", color="tab:red"), color="tab:red", fontsize=10)
ax1.set_xlabel("时间 (ms)")
ax1.set_ylabel("电压 (V)")
ax1.set_title("① RC 低通滤波器：方波输入的瞬态响应（用它测时间常数 τ=RC）")
ax1.grid(alpha=0.3)
ax1.legend(loc="upper right", fontsize=9)

ax2.plot(t * 1e3, v_in_fast, "--", color="tab:gray", lw=1.2, label="输入 Vin（2kHz 方波）")
ax2.plot(t * 1e3, v_out_fast, color="tab:green", lw=1.8, label="输出 Vout（被滤成小三角波）")
ax2.annotate(f"幅度被衰减：输入 1V 方波 → 输出只有 {ripple_fast*1e3:.0f} mV",
             xy=(2.02, 0.20), xytext=(2.12, 0.50),
             arrowprops=dict(arrowstyle="->", color="tab:red"), color="tab:red", fontsize=10)
ax2.set_xlabel("时间 (ms)")
ax2.set_ylabel("电压 (V)")
ax2.set_title("同为 RC 电路，输入频率 2kHz（2 倍 f_c）时输出被明显衰减")
ax2.grid(alpha=0.3)
ax2.legend(loc="upper left", fontsize=9)
save(fig, "rc_transient.png")

# =====================================================================
# 3. 仿真二：交流扫频（波特图）
# =====================================================================
print("\n[2/2] 交流扫描：画波特图 ……")
circuit_ac = make_circuit("RC low-pass filter ac")
circuit_ac.SinusoidalVoltageSource("input", "n_in", circuit_ac.gnd, amplitude=1 @ u_V)
circuit_ac.R(1, "n_in", "n_out", R @ u_Ohm)
circuit_ac.C(1, "n_out", circuit_ac.gnd, C @ u_F)

analysis_ac, _ = run(circuit_ac, analysis="ac", variation="dec",
                     number_of_points=200,
                     start_frequency=1 @ u_Hz, stop_frequency=1 @ u_MHz)

freq = np.array(analysis_ac.frequency)
mag_db = gain_db(analysis_ac, "n_out", "n_in")
phase = np.angle(val(analysis_ac, "n_out"), deg=True)

# 找 -3dB 点：幅度第一次跌破 -3.0103 dB 的频率
idx = int(np.argmax(mag_db <= -3.0103))
fc_sim = float(freq[idx])
phase_at_fc = float(np.interp(np.log10(fc_sim), np.log10(freq), phase))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.6), sharex=True)
ax1.semilogx(freq, mag_db, color="tab:blue", lw=1.8)
ax1.axhline(-3.0103, color="tab:red", ls=":", lw=1.2)
ax1.axvline(fc_sim, color="tab:red", ls=":", lw=1.2)
ax1.plot([fc_sim], [-3.0103], "o", color="tab:red")
ax1.annotate(f"fc(仿真) = {fc_sim:.1f} Hz\nfc(手算) = {fc_hand:.1f} Hz",
             xy=(fc_sim, -3.0103), xytext=(fc_sim * 2.2, -12),
             arrowprops=dict(arrowstyle="->", color="tab:red"), color="tab:red", fontsize=10)
ax1.set_ylabel("幅度 (dB)")
ax1.set_title("① RC 低通滤波器：波特图（幅度 + 相位）")
ax1.grid(alpha=0.3, which="both")

ax2.semilogx(freq, phase, color="tab:green", lw=1.8)
ax2.axvline(fc_sim, color="tab:red", ls=":", lw=1.2)
ax2.axhline(-45, color="tab:red", ls=":", lw=1.2)
ax2.plot([fc_sim], [phase_at_fc], "o", color="tab:red")
ax2.annotate(f"fc 处相位 {phase_at_fc:.1f}°（理论 -45°）",
             xy=(fc_sim, phase_at_fc), xytext=(fc_sim * 2.2, -20),
             arrowprops=dict(arrowstyle="->", color="tab:red"), color="tab:red", fontsize=10)
ax2.set_xlabel("频率 (Hz)")
ax2.set_ylabel("相位 (°)")
ax2.grid(alpha=0.3, which="both")
save(fig, "rc_bode.png")

# =====================================================================
# 4. 对比表
# =====================================================================
print("\n【① RC 低通滤波器 · 手算 vs 仿真】")
table(
    [
        ("时间常数 τ", f"{tau_hand*1e6:.1f} μs", f"{tau_sim*1e6:.1f} μs", rel_err(tau_hand, tau_sim)),
        ("截止频率 fc", f"{fc_hand:.1f} Hz", f"{fc_sim:.1f} Hz", rel_err(fc_hand, fc_sim)),
        ("fc 处相位", "-45.0 °", f"{phase_at_fc:.1f} °", rel_err(45.0, abs(phase_at_fc))),
        ("稳态高电平(100Hz)", f"{V_HIGH:.3f} V", f"{v_ss_high:.3f} V", rel_err(V_HIGH, v_ss_high)),
        ("2kHz 输出纹波(峰峰)", "-", f"{ripple_fast*1000:.2f} mV", "-"),
    ],
    ["项目", "手算值", "仿真值", "误差(%)"],
)

print(f"""
结论：
  1) 瞬态（100Hz 方波）：半周期 5ms 远大于 5τ，电容能充到稳态；
     从充电曲线反推的 τ ≈ {tau_sim*1e6:.1f} μs，与手算 τ = RC = {tau_hand*1e6:.1f} μs 一致
     → 时间常数公式验证通过。
  2) 交流：幅度在 fc 处跌到 -3.01 dB，仿真 fc = {fc_sim:.1f} Hz，
     手算 fc = {fc_hand:.1f} Hz，误差 {rel_err(fc_hand, fc_sim)}%；
     fc 处相位 ≈ -45° → 截止频率公式 fc = 1/(2πRC) 验证通过。
  3) 滤波效果：把输入换成 2kHz（2 倍 fc），输出幅度只有 {ripple_fast*1e3:.0f} mV
     （输入是 1V 方波），波形被磨成小三角波
     → 直观说明"频率越高、衰减越大"的低通特性。
""")
