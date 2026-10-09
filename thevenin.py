"""
② 验证戴维南定理 —— PySpice 仿真

含源二端网络（自己定的参数，注意 node 名不能用 Python 关键字）：

        ┌──[ R1 = 1 kΩ ]──┬──── a  (输出端口)
        │                 │
     V1=12V            [ R2 = 3 kΩ ]
        │                 │
        └─────────────────┴──── b  (地)

手算（先用节点法求 V_oc，再用叠加法求 R_th）：
    ① 开路电压 V_oc：a、b 开路，没有电流流出，a 点就是 R1/R2 分压
         V_oc = V1 · R2/(R1+R2) = 12 × 3/4 = 9 V

    ② 短路电流 I_sc：把 a、b 短接，R2 被短路去掉，回路里只剩 V1 和 R1
         I_sc = V1/R1 = 12/1000 = 12 mA

    ③ 等效内阻 R_th
         方法一：R_th = V_oc/I_sc = 9 / 0.012 = 750 Ω
         方法二：电压源置零(短路)后从端口看进去 = R1 ∥ R2 = 1k∥3k = 750 Ω

    ④ 戴维南等效电路：V_th = 9 V 串联 R_th = 750 Ω
       接负载 R_L 时：V_L = V_th · R_L/(R_th+R_L)

仿真验证（四步）：
    1) 端口开路     → 量 V_oc
    2) 端口短路     → 量 I_sc
    3) 外接电压源 1V 灌 1A 电流  → 量端口电压，直接得到 R_th（外加激励法）
    4) 原网络 vs 戴维南等效电路，分别接 1kΩ / 2kΩ / 10kΩ 负载，
       比较负载电压和电流（应该完全一样）

运行： python thevenin.py
"""

import numpy as np
import matplotlib.pyplot as plt

from common import (init_backend, make_circuit, run, transient, val, branch,
                    save, table, rel_err, u_V, u_A, u_Ohm)

# ---------------- 电路参数（自己定的） ----------------
V1 = 12.0          # V
R1 = 1_000.0       # Ω
R2 = 3_000.0       # Ω
LOAD_LIST = [1_000.0, 2_000.0, 10_000.0]     # 要验证的负载电阻

# ---------------- 手算 ----------------
V_oc_hand = V1 * R2 / (R1 + R2)
I_sc_hand = V1 / R1
R_th_hand = V_oc_hand / I_sc_hand
R_th_hand2 = R1 * R2 / (R1 + R2)            # 另一种算法，用来互相校验

print("=" * 68)
print("② 验证戴维南定理")
print("=" * 68)
print(f"手算：V_oc = V1·R2/(R1+R2) = {V1:.0f} × {R2:.0f}/({R1:.0f}+{R2:.0f}) = {V_oc_hand:.3f} V")
print(f"手算：I_sc = V1/R1             = {V1:.0f}/{R1:.0f} = {I_sc_hand*1e3:.3f} mA")
print(f"手算：R_th = V_oc/I_sc         = {R_th_hand:.2f} Ω")
print(f"      另一种算法 R1∥R2        = {R_th_hand2:.2f} Ω  （两者一致，说明手算没错）")


# =====================================================================
# 1. 原始含源二端网络
#    节点名：n_a = 端口 a，n_mid = R1 和 R2 之间（其实和 n_a 同点，
#    为了标出端口，这里让 R1 接到中间节点，R2 从中间节点到地）
# =====================================================================
def build_original(load=None, short=False, inject_current=None):
    """
    load           : 端口接的负载电阻（None = 开路）
    short          : True 表示端口短路。方法：串一个 0V 电压源当"电流表"，
                     再接地 —— SPICE 不允许 0Ω 电阻，而且 0V 电源正好能
                     直接读出短路电流（这是 SPICE 里测电流的标准技巧）。
    inject_current : 往端口灌电流的外加源（用于量 R_th）
    """
    c = make_circuit("Thevenin original network")
    c.V("1", "n_v1", c.gnd, V1 @ u_V)          # 12V 电压源
    c.R("1", "n_v1", "n_a", R1 @ u_Ohm)        # R1
    c.R("2", "n_a", c.gnd, R2 @ u_Ohm)         # R2

    if load is not None:
        c.R("load", "n_a", c.gnd, load @ u_Ohm)
    if short:
        c.V("short", "n_a", "n_gnd2", 0 @ u_V)     # 0V 电源 = 理想电流表
        c.R("short", "n_gnd2", c.gnd, 1e-9 @ u_Ohm)  # 1nΩ 把 n_gnd2 拉到地电位
    if inject_current is not None:
        # 电流源从地流向端口 → 端口被灌入电流
        c.I("probe", c.gnd, "n_a", inject_current @ u_A)
    return c


init_backend()
print("\n原始网络网表（开路状态）：")
print(build_original())

# =====================================================================
# 2. 仿真一：端口开路 → V_oc
# =====================================================================
print("[1/4] 端口开路，测 V_oc ……")
a, _ = run(build_original(), analysis="op")
V_oc_sim = float(val(a, "n_a"))

# =====================================================================
# 3. 仿真二：端口短路 → I_sc
#    通过短接支路的电流，方向是 n_a → 地
# =====================================================================
print("[2/4] 端口短路，测 I_sc ……")
a, _ = run(build_original(short=True), analysis="op")
# 支路电流的键名就是元件的小写名，比如 Vshort → 'vshort'
I_sc_sim = abs(float(branch(a, "vshort")))      # 单位 A

# =====================================================================
# 4. 仿真三：外加激励法测 R_th
#    把内部电压源置零（短路），从端口灌入 1A 电流，量端口电压
#    → R_th = V_端口 / 1A
# =====================================================================
print("[3/4] 外加 1A 激励，直接测 R_th ……")
c_zero = make_circuit("Thevenin Rth by external source")
c_zero.V("1", "n_v1", c_zero.gnd, 0 @ u_V)       # 内部电源置零 = 短路
c_zero.R("1", "n_v1", "n_a", R1 @ u_Ohm)
c_zero.R("2", "n_a", c_zero.gnd, R2 @ u_Ohm)
c_zero.I("probe", c_zero.gnd, "n_a", 1 @ u_A)
a, _ = run(c_zero, analysis="op")
R_th_sim = float(val(a, "n_a")) / 1.0            # V / 1A

# =====================================================================
# 5. 仿真四：原网络 vs 戴维南等效电路，接不同负载
# =====================================================================
print("[4/4] 原网络 vs 等效电路，接负载对比 ……")


def build_equivalent(load):
    """戴维南等效电路：V_th 串联 R_th，再接负载。"""
    c = make_circuit("Thevenin equivalent")
    c.V("th", "n_th", c.gnd, V_oc_hand @ u_V)
    c.R("th", "n_th", "n_a", R_th_hand @ u_Ohm)
    c.R("load", "n_a", c.gnd, load @ u_Ohm)
    return c


rows = []
for RL in LOAD_LIST:
    # 原网络
    a1, _ = run(build_original(load=RL), analysis="op")
    v_orig = float(val(a1, "n_a"))
    i_orig = v_orig / RL

    # 等效电路
    a2, _ = run(build_equivalent(RL), analysis="op")
    v_eq = float(val(a2, "n_a"))
    i_eq = v_eq / RL

    # 手算理论值
    v_hand = V_oc_hand * RL / (R_th_hand + RL)

    rows.append((RL, v_hand, v_orig, v_eq, i_orig))

# =====================================================================
# 6. 画图：负载电压随负载电阻变化的曲线（原网络 vs 等效电路）
# =====================================================================
RL_sweep = np.logspace(np.log10(50), np.log10(100000), 60)
v_hand_curve = V_oc_hand * RL_sweep / (R_th_hand + RL_sweep)

v_orig_curve, v_eq_curve = [], []
for RL in RL_sweep:
    a1, _ = run(build_original(load=float(RL)), analysis="op")
    v_orig_curve.append(float(val(a1, "n_a")))
    a2, _ = run(build_equivalent(float(RL)), analysis="op")
    v_eq_curve.append(float(val(a2, "n_a")))

fig, ax = plt.subplots(figsize=(9, 4.4))
ax.semilogx(RL_sweep, v_hand_curve, "-", color="tab:blue", lw=2.4, label="手算 V_L = V_oc·R_L/(R_th+R_L)")
ax.semilogx(RL_sweep, v_orig_curve, "--", color="tab:red", lw=1.6, label="仿真：原始含源二端网络")
ax.semilogx(RL_sweep, v_eq_curve, ":", color="tab:green", lw=3.0, label="仿真：戴维南等效电路")
ax.axhline(V_oc_hand, color="gray", ls="-.", lw=1.0)
ax.annotate(f"开路时 V_L → V_oc = {V_oc_hand:.0f} V", xy=(60, V_oc_hand),
            xytext=(70, V_oc_hand - 1.6), color="gray", fontsize=10,
            arrowprops=dict(arrowstyle="->", color="gray"))
for RL in LOAD_LIST:
    ax.plot([RL], [V_oc_hand * RL / (R_th_hand + RL)], "o", color="black", ms=5)
ax.set_xlabel("负载电阻 R_L (Ω)")
ax.set_ylabel("负载电压 V_L (V)")
ax.set_title("② 戴维南定理验证：原网络与等效电路的负载特性完全重合")
ax.grid(alpha=0.3, which="both")
ax.legend(loc="lower right", fontsize=9)
save(fig, "thevenin_load_curve.png")

# 另外画一张等效电路示意图（用文字块说明，方便贴 README）
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.axis("off")
ax.text(0.02, 0.80, "原始含源二端网络", fontsize=12, weight="bold")
ax.text(0.02, 0.55, f"V1 = {V1:.0f} V\nR1 = {R1/1000:.1f} kΩ\nR2 = {R2/1000:.1f} kΩ",
        fontsize=11, va="top")
ax.text(0.30, 0.80, "戴维南等效电路", fontsize=12, weight="bold")
ax.text(0.30, 0.55, f"V_th = V_oc = {V_oc_hand:.2f} V\nR_th = {R_th_hand:.0f} Ω\n( = R1∥R2 )",
        fontsize=11, va="top")
ax.text(0.62, 0.80, "三个关键量（手算）", fontsize=12, weight="bold")
ax.text(0.62, 0.55, f"V_oc = {V_oc_hand:.3f} V\nI_sc = {I_sc_hand*1e3:.3f} mA\n"
                    f"R_th = V_oc/I_sc = {R_th_hand:.0f} Ω",
        fontsize=11, va="top")
save(fig, "thevenin_summary.png")

# =====================================================================
# 7. 对比表
# =====================================================================
print("\n【② 戴维南定理 · 手算 vs 仿真】")
table(
    [
        ("开路电压 V_oc", f"{V_oc_hand:.3f} V", f"{V_oc_sim:.3f} V", rel_err(V_oc_hand, V_oc_sim)),
        ("短路电流 I_sc", f"{I_sc_hand*1e3:.3f} mA", f"{I_sc_sim*1e3:.3f} mA", rel_err(I_sc_hand, I_sc_sim)),
        ("等效内阻 R_th", f"{R_th_hand:.2f} Ω", f"{R_th_sim:.2f} Ω", rel_err(R_th_hand, R_th_sim)),
    ],
    ["项目", "手算值", "仿真值", "误差(%)"],
)

print("\n【② 接不同负载：原网络 vs 等效电路 vs 手算】")
table(
    [(f"R_L = {int(r[0])} Ω", f"{r[1]:.4f} V", f"{r[2]:.4f} V", f"{r[3]:.4f} V", f"{r[4]*1e3:.4f} mA")
     for r in rows],
    ["负载", "手算 V_L", "原网络 V_L", "等效电路 V_L", "负载电流"],
)

print("""
结论：
  1) 开路电压、短路电流两次独立仿真得到的比值 V_oc/I_sc = R_th，
     与"电压源置零后从端口看进去的电阻"R1∥R2 完全一致 → 戴维南定理成立。
  2) 外加 1A 激励测端口电压，直接得到 R_th（外加激励法），结果同样一致。
  3) 把原网络换成"V_th 串联 R_th"后，接任意负载的电压/电流都与原网络相同
     （图上两条曲线完全重合）→ 等效电路对外特性等价，验证完成。
""")
