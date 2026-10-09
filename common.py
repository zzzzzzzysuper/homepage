"""
common.py —— 三个电路共用的开头（装环境、运行仿真、画图）

小白说明：
  这个文件不是给你直接运行的，是被另外三个 .py 文件 import 的。
  它干三件事：
    1) 告诉 PySpice 用哪种 ngspice 后端（Windows 上默认用 shared 模式，即 dll）
    2) 提供一个 run(...) 函数：把电路跑一次仿真
    3) 提供 solve/ac/trans 三个快捷函数，以及画图保存的工具
"""

from pathlib import Path
import numpy as np

# ---- matplotlib：只用来画图存 png，不弹窗（避免在没屏幕的环境里卡住）----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 让图里的中文能正常显示（Windows 自带微软雅黑）
_available = {f.name for f in font_manager.fontManager.ttflist}
for _name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC"):
    if _name in _available:
        plt.rcParams["font.sans-serif"] = [_name]
        break
plt.rcParams["axes.unicode_minus"] = False      # 负号正常显示
plt.rcParams["font.size"] = 11
plt.rcParams["figure.dpi"] = 130

# ---- PySpice ----
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import (u_V, u_A, u_Ohm, u_F, u_H,
                          u_s, u_ms, u_us, u_ns,
                          u_Hz, u_kHz, u_MHz)
from PySpice.Spice.NgSpice.Shared import NgSpiceShared

# 图片统一存到脚本同目录的 figures/
FIG_DIR = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(exist_ok=True)


# =====================================================================
# 1. 后端设置
# =====================================================================
def init_backend(verbose=False):
    """
    Windows 上 PySpice 默认走 ngspice 的共享库（dll）。
    注意：ngspice 的 dll 默认会把日志打到标准输出，这里把日志压掉，
    只保留真正的错误，免得刷屏。如果你要看 ngspice 的原始输出，
    把 verbose 改成 True。
    """
    def send_char(char, *_):
        if verbose:
            print(char, end="", flush=True)

    def send_stat(*args):
        if verbose:
            print("ngspice:", *args)

    NgSpiceShared.LOGGER_LINE = send_char
    NgSpiceShared.LOGGER_STAT = send_stat


def make_circuit(title):
    """新建一个电路。title 会出现在生成的网表第一行。"""
    return Circuit(title)


def run(circuit, **kwargs):
    """
    用 ngspice 跑一次仿真，返回 (analysis, simulator)。
    用法：
        analysis, sim = run(circuit, analysis="op")
        analysis, sim = run(circuit, analysis="transient", step_time=1@u_ms, end_time=10@u_ms)
        analysis, sim = run(circuit, analysis="ac", variation="decade", number_of_points=100,
                            start_frequency=1@u_Hz, stop_frequency=1@u_MHz)
    """
    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    # ngspice 是共享库，仿真数据存在全局区；不清掉上一次的结果，
    # 连续跑多次时可能读到串台的波形（踩过坑）。所以每次都先 reset。
    reset(simulator)
    if kwargs.get("analysis") == "op":
        analysis = simulator.operating_point()
    elif kwargs.get("analysis") == "transient":
        kwargs.pop("analysis")
        analysis = simulator.transient(**kwargs)
    elif kwargs.get("analysis") == "ac":
        kwargs.pop("analysis")
        analysis = simulator.ac(**kwargs)
    else:
        raise ValueError("analysis 只能是 'op' / 'transient' / 'ac'")
    # 关键：把 simulator 挂在 analysis 上，防止它被垃圾回收。
    # PySpice 的 simulator 析构时会清掉 ngspice 的共享数据，
    # 如果没人引用它，读波形时就会只剩几个残点（踩过这个坑）。
    analysis._dsh_simulator = simulator
    return analysis, simulator


def reset(simulator):
    """
    连跑多次仿真时，先重置上一次的分析结果，
    否则 ngspice 会警告 "doAnalyses: iteration ... " 或结果串台。
    """
    try:
        simulator.reset_analysis()
    except Exception:
        pass


# =====================================================================
# 1.5 瞬态波形：均匀时间轴
# =====================================================================
def to_seconds(value):
    """
    把 PySpice 的单位对象换成"秒"的纯数字。

    踩坑记录：
        x = 1@u_us          # 这是一个 PeriodValue
        float(x)  -> 1e-06  # 已经是秒了
        x.value   -> 1       # 只是数字部分
    所以不能再乘 x.scale，否则会变成 1e-12。
    """
    if hasattr(value, "value"):
        return float(value.value) * float(getattr(value, "scale", 1))
    return float(value)


# ngspice 的瞬态分析是"变步长"的：拐点附近点很密（1e-11 级），
# 平稳段点很稀。直接拿 analysis.time 数组去查表会很别扭，
# 所以用 ngspice 自带的 linearize 命令，把它插值到均匀时间轴。
def transient(run_result, nodes, step_time):
    """
    参数：
        run_result = run(...) 的返回值（analysis, simulator）
        nodes      = 要取的节点名列表，比如 ['n_in', 'n_out']
        step_time  = 想要的时间步长（带单位的量，如 1@u_s）
    返回：
        (t, {节点名: 数组})
    """
    analysis, simulator = run_result
    from scipy.interpolate import interp1d

    # 注意顺序：先取节点波形，再取时间轴。
    # ngspice 是共享库、数据放在全局区，PySpice 的封装会惰性去读；
    # 先读节点数据能保证后面读到的 time 和它们是同一次仿真的结果。
    ys = {node: val(analysis, node) for node in nodes}
    t = np.array(analysis.time)
    if t.size < 10 or t[-1] <= t[0]:
        raise RuntimeError(
            f"瞬态数据异常：只读到 {t.size} 个时间点（t: {t[:5]} ... {t[-1] if t.size else '空'}）。\n"
            f"  节点数据长度：{ {k: len(v) for k, v in ys.items()} }\n"
            "  通常是因为 ngspice 全局数据被上一次仿真覆盖，重跑一次即可。")
    step = to_seconds(step_time)
    t_uni = np.arange(t[0], t[-1] + step / 2, step)
    out = {node: interp1d(t, ys[node], kind="linear")(t_uni) for node in nodes}
    return t_uni, out


# =====================================================================
# 2. 取值小工具
# =====================================================================
def val(analysis, node):
    """
    取某个节点的值（直流/瞬态/交流都能用）。
    - 直流时返回一个数
    - 瞬态/交流时返回 numpy 数组
    """
    return np.array(analysis[node]).squeeze()


def branch(analysis, name):
    """取支路电流，比如 branch(a, 'Vinput') 取输入源的电流。"""
    return np.array(analysis.branches[name]).squeeze()


def amplitude(analysis, node):
    """交流分析里取某个节点的幅度（峰值）。"""
    return float(np.abs(val(analysis, node)).max())


def gain_db(analysis, out_node, in_node):
    """交流分析里算 20*log10(|Vout|/|Vin|)，返回数组，单位 dB。"""
    out = np.abs(val(analysis, out_node))
    inp = np.abs(val(analysis, in_node))
    return 20.0 * np.log10(out / inp + 1e-30)


# =====================================================================
# 3. 画图小工具
# =====================================================================
def save(fig, filename):
    """保存图片到 figures/ 并打印路径。"""
    path = FIG_DIR / filename
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  [图] 已保存 -> {path}")
    return path


def table(rows, headers):
    """
    打印一张等宽的对比表。rows 是 [(项目, 手算值, 仿真值, 误差%), ...]
    误差%（相对手算）留空就写 '-'。
    """
    widths = [max(len(str(r[i])) for r in [headers] + rows) + 2 for i in range(len(headers))]
    line = "-" * (sum(widths) + len(headers) + 1)
    print(line)
    print("|" + "|".join(str(h).center(widths[i]) for i, h in enumerate(headers)) + "|")
    print(line)
    for r in rows:
        print("|" + "|".join(str(c).center(widths[i]) for i, c in enumerate(r)) + "|")
    print(line)


def rel_err(hand, sim):
    """相对误差（%）。手算为 0 时返回 '-'。"""
    if hand == 0:
        return "-"
    return f"{abs(sim - hand) / abs(hand) * 100:.2f}"
