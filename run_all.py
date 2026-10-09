"""
run_all.py —— 一键跑完三个电路，并把所有输出（含对比表）保存成 运行结果.md

用法：
    python run_all.py

它做的事：
    1) 依次运行 rc_filter.py / thevenin.py / nmos_amplifier.py / schematic.py
    2) 把三个脚本的控制台输出原样收集起来
    3) 写成 运行结果.md（可以直接复制进 README 的「仿真数据」一节）

为什么要有这个文件：
    README 里要附「手算 vs 仿真」对比表。表格是脚本算出来的，
    跑一次这个脚本就能拿到最新、最准确的数据，不用手动抄。
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = ["schematic.py", "rc_filter.py", "thevenin.py", "nmos_amplifier.py"]
OUT = HERE / "运行结果.md"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    blocks = [
        "# PySpice 三电路 · 运行结果（手算 vs 仿真）\n",
        f"> 由 `run_all.py` 自动生成，时间：{datetime.now():%Y-%m-%d %H:%M:%S}\n",
        "> 环境：Windows + Python 3.14 + PySpice 1.5 + ngspice 34（shared 模式）\n",
    ]

    for script in SCRIPTS:
        print(f"===== 运行 {script} =====")
        proc = subprocess.run([sys.executable, str(HERE / script)],
                              cwd=HERE, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        blocks.append(f"\n## `{script}`\n")
        if proc.returncode != 0:
            blocks.append(f"**运行失败（exit {proc.returncode}）**\n")
            print(proc.stderr[-2000:])
        blocks.append("```text\n" + (proc.stdout or "").strip() + "\n```\n")
        if proc.stderr.strip():
            blocks.append("```text\n[stderr]\n" + proc.stderr.strip()[-3000:] + "\n```\n")
        print(f"  exit={proc.returncode}, 输出 {len(proc.stdout)} 字符")

    OUT.write_text("\n".join(blocks), encoding="utf-8")
    print(f"\n已写入 {OUT}")


if __name__ == "__main__":
    main()
