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
| `.nojekyll` | 告诉 GitHub Pages 不要用 Jekyll 处理，加快部署 |
| `LICENSE` | 开源协议（MIT），见下文「开源许可」 |

> 样式集中定义在 `style.css` 顶部的 `:root` 变量里，改那几个颜色变量就能整体换风格。

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
