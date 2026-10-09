# 个人主页 · Personal Homepage

纯静态个人主页，使用 HTML/CSS 手写，无框架、无外部依赖，托管在 **GitHub Pages**（免费）。

在线地址格式：`https://<你的用户名>.github.io/<仓库名>/`

---

## 仓库内容

| 文件 | 说明 |
| --- | --- |
| `index.html` | 主页结构：自我介绍、兴趣、技能、项目、联系方式 |
| `style.css` | 全部样式：配色、排版、响应式、深色模式、打印样式 |
| `resume.pdf` | 个人简介 PDF，可直接下载（页面上「下载个人简介 PDF」按钮） |
| `snake/index.html` | 小游戏：贪吃蛇**基础版**（WASD · 50×50 格 · 自撞弹 GAME OVER · 深浅主题） |
| `snake/README.html` | 贪吃蛇**开发文档**（README 的网页版）：实现过程、验证方法、给 AI 的提示词记录 |
| `snake/README.md` | 开发文档的 Markdown 原文（在 GitHub 上会被自动渲染） |
| `snake/img/` | 开发文档里引用的验证截图（主题、GAME OVER、AI 托管与通关） |
| `snake-ai/index.html` | 小游戏：贪吃蛇 **AI 托管版**（在基础版之上加了 AI 自动游玩） |
| `rc_filter.py` | 进阶挑战 ①：RC 低通滤波器（PySpice 仿真 + 手算对比） |
| `thevenin.py` | 进阶挑战 ②：戴维南定理验证（开路/短路/外加激励/接负载） |
| `nmos_amplifier.py` | 进阶挑战 ③：NMOS 共源放大电路（直流工作点 + 小信号 + 反相波形） |
| `common.py` | 上面三个脚本共用的模块（初始化 ngspice、跑仿真、画图、打印对比表） |
| `schematic.py` | 用程序画电路图、直流通路图、小信号等效模型图 |
| `run_all.py` | 一键跑完三个电路并汇总输出 |
| `pyspice-report.md` | PySpice 三电路的**汇总报告**：手算推导 + 波形 + 「理论值 vs 仿真值」对比表 |
| `运行结果.md` | 三个脚本的真实运行输出（对比表原文） |
| `00_先看这个_总步骤.md` | PySpice 环境安装步骤与交付清单 |
| `figures/` | 上述电路的波形图与电路图（12 张 PNG） |
| `.nojekyll` | 告诉 GitHub Pages 不要用 Jekyll 处理，加快部署 |
| `LICENSE` | 开源协议（MIT），见下文「开源许可」 |

> 样式集中定义在 `style.css` 顶部的 `:root` 变量里，改那几个颜色变量就能整体换风格。

---

## 仓库里的两个在线小游戏

| 版本 | 在线地址 |
| --- | --- |
| 贪吃蛇 · 基础版 | <https://zzzzzzzysuper.github.io/homepage/snake/> |
| 贪吃蛇 · AI 托管版 | <https://zzzzzzzysuper.github.io/homepage/snake-ai/> |
| 直接看 AI 自己玩 | <https://zzzzzzzysuper.github.io/homepage/snake-ai/?demo=ai> |
| 开发文档（README） | <https://zzzzzzzysuper.github.io/homepage/snake/README.html> |

两个游戏都是**纯前端单文件**（HTML/CSS/JavaScript 全部内联在一个 `index.html` 里），不依赖任何框架、
不请求任何外部资源，把文件下载下来双击也能直接玩：

- **基础版**：`W/A/S/D` 控制上/下/左/右，吃食物 +10 分并加长，每 5 个加速一档；蛇头撞到自己身体（或撞墙）
  弹出 `GAME OVER`；深色 / 浅色两套配色一键切换，刷新后保留所选主题。
- **AI 托管版**：多一个「🤖 AI 托管」按钮，程序自己控制蛇去找食物、绕开自己和墙，连续吃满 15 个食物弹出
  「AI 通关」，全程无需人工操作。

开发文档（`snake/README.html`）里写了三件事：**阶段一**（核心玩法）、**阶段二**（主题切换）、
**阶段三**（AI 自动托管）分别是怎么实现、怎么验证的，以及给 AI 的关键提示词原文和每轮迭代记录。

> 这两份游戏页面与开发文档都是由本地项目 `snake-game/` 里的 `publish_homepage.mjs`、`publish_readme.mjs`
> 生成后复制进本仓库的；改了游戏本体后重跑脚本即可同步。

---

## 进阶挑战：PySpice 三个电路仿真

大一考核「进阶挑战」路线 A —— 用 **PySpice**（底层调用 ngspice）做完三个电路：

| # | 电路 | 做了什么 |
| --- | --- | --- |
| ① | RC 低通滤波器 | 方波瞬态响应（测 τ=RC）+ 波特图（测 f_c=1/2πRC）|
| ② | 戴维南定理验证 | 4 组独立仿真：端口开路测 V_oc、短路测 I_sc、外加激励测 R_th、等效电路接负载对比 |
| ③ | NMOS 共源放大电路 | 直流工作点（V_GS/I_D/V_DS + 饱和区判断）+ 小信号 gm/Av + 反相输出波形 |

每个电路都交了：**电路图 + 手算公式与步骤 + PySpice 跑出的波形/数值 + 「理论值 vs 仿真值」对比表**。

完整报告（含全部推导、12 张图和对比表）见 **[`pyspice-report.md`](pyspice-report.md)**，
三个脚本的真实运行输出见 [`运行结果.md`](运行结果.md)，环境安装步骤见 [`00_先看这个_总步骤.md`](00_先看这个_总步骤.md)。

几个值得一提的点：

- **③ 的 NMOS 用 SPICE 行为源实现题目的平方律公式**，而不是套用 SPICE 自带的 MOS 模型
  （自带模型带 1/2 和 W/L 系数，与题目给的 K 定义不一致，直接用会差 2 倍）；
- 手算 ③ 时把**沟道长度调制 (1+λV_DS)** 也解了进去，因此手算与仿真对到小数点后 4 位
  （V_GS 2.0000 V、I_D 0.8527 mA、V_DS 3.2946 V、gm 1.7054 mS、Av ≈ −3.30）；
- 过程中记录了两次「手算与仿真不一致」的排查：τ 的测量方法用错前提、以及手算漏掉 λ 项，
  都在报告里写清了原因和修法。

运行方式（Windows 需先单独装 ngspice 的动态库）：

```bash
pip install PySpice
pyspice-post-installation --install-ngspice-dll
python rc_filter.py        # ①
python thevenin.py         # ②
python nmos_amplifier.py   # ③
```

---

## 本地预览

直接双击 `index.html` 即可。或者起一个本地服务器（推荐，路径行为与线上一致）：

```bash
python -m http.server 8000
# 然后打开 http://localhost:8000
```

---

## 部署到 GitHub Pages

### 1. 在 GitHub 上新建仓库

打开 <https://github.com/new>，仓库名例如 `homepage`，
**不要**勾选 "Add a README file"（保持空仓库，避免推送冲突）。

### 2. 关联远程仓库并推送

把下面的 `你的用户名` 和 `homepage` 换成你自己的：

```bash
git remote add origin https://github.com/你的用户名/homepage.git
git push -u origin main
```

首次推送会弹出浏览器让你登录 GitHub 授权（Git Credential Manager），
授权一次之后就不需要再输了。

### 3. 开启 GitHub Pages

1. 打开仓库页面 → **Settings**（设置）
2. 左侧菜单 → **Pages**
3. **Source** 选 `Deploy from a branch`
4. **Branch** 选 `main`，目录选 `/ (root)`，点 **Save**
5. 等 1–2 分钟，刷新页面，顶部会出现绿色提示和网址：

```
https://你的用户名.github.io/homepage/
```

---

## 修改成你自己的内容

1. **改文字**：编辑 `index.html`，把「待填写」等占位内容替换成你自己的信息
   （真实姓名、专业年级、兴趣、联系方式）。
2. **改颜色**：编辑 `style.css` 顶部的 `:root { --accent: ...; }` 等变量。
3. **换头像**：`index.html` 里的 `<div class="avatar">曾</div>` 可以换成
   `<img class="avatar" src="avatar.jpg" alt="头像">`（图片放进仓库根目录）。
4. **换简历**：把你的 PDF 命名为 `resume.pdf` 覆盖本目录的文件即可。
   （如果文件名要用中文，记得同步修改 `index.html` 里两处 `href="resume.pdf"`。）
5. **推送更新**：

```bash
git add -A
git commit -m "更新个人主页内容"
git push
```

GitHub Pages 会在 1 分钟左右自动重新部署。

---

## 开源许可

本项目使用 **MIT 协议**（见 [`LICENSE`](LICENSE)）。

选它的理由：MIT 是最宽松、最常见的开源协议之一 —— 别人可以自由使用、修改、再发布甚至商用我的代码，
只要保留版权声明和协议原文即可；对我来说，个人主页这种小项目没有商业保护的需求，
用最简单的协议把"可以随便拿去改"讲清楚，比用限制更多的协议（如 GPL）更合适。

## 关于 Git 分支与合并（一句话）

**分支**就是从主线分出去的一条平行开发线，在上面改动不影响主线；**合并**就是把分支上的改动并回主线。

## 开发说明

本仓库使用 Git 管理，提交历史记录了从"套用模板"到"改成真实个人信息"的逐步修改过程。
提交信息尽量写清每次改了什么、为什么改。

---

## 常见问题

**打开网址是 404？** 检查仓库 Settings → Pages 里的分支是不是 `main`、目录是不是 `/ (root)`；
再确认仓库根目录下确实有 `index.html`（文件名全小写）。

**页面样式没生效？** 确认 `style.css` 和 `index.html` 在同一层目录，并且文件名大小写一致
（GitHub Pages 的服务器区分大小写，Windows 本地不区分）。

**想用自己的域名？** 在仓库根目录加一个名为 `CNAME` 的文件，内容写你的域名，
然后在域名服务商处把 DNS 指向 GitHub Pages 的地址。
