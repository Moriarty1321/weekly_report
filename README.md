# 🔬 实验周报系统 (Experiment Weekly Report)

一个本地运行的实验记录与周报自动生成系统，专为科研/算法实验场景设计。支持 Markdown 图文混排记录，并集成 LLM 自动生成周报智能总结。

## ✨ 功能特性

- **Markdown 图文混排**：实验记录使用 Markdown 格式，文字与图片自由穿插，像写博客一样记录实验
- **图片管理**：上传图片后自动生成 Markdown 引用，粘贴到内容中即可
- **AI 智能周报**：调用 LLM 对本周实验进行总结、对比分析，并给出下周建议
- **历史记录浏览**：查看所有实验记录，支持 Markdown 渲染和图片预览
- **周报归档**：生成的周报保存为 Markdown 文件，支持在线预览和下载
- **纯本地运行**：数据存储在本地 SQLite，无需外部数据库服务

## 📁 项目结构

```
weekly_report/
├── app.py                  # Streamlit 主应用
├── config.py               # 配置文件（LLM API、路径等）
├── models.py               # 数据模型（SQLAlchemy + SQLite）
├── report_generator.py     # 周报生成器（含 LLM 再创作）
├── requirements.txt        # Python 依赖
├── README.md
├── data/
│   ├── experiments.db      # SQLite 数据库（自动创建）
│   └── images/             # 上传的实验图片
└── reports/                # 生成的周报文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 LLM API

通过环境变量设置你的 LLM API 信息（支持 Anthropic 兼容接口）：

**Linux / macOS：**

```bash
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://your-api-endpoint"
export LLM_MODEL="your-model-name"
```

**Windows PowerShell：**

```powershell
$env:LLM_API_KEY = "your-api-key"
$env:LLM_BASE_URL = "https://your-api-endpoint"
$env:LLM_MODEL = "your-model-name"
```

也可以直接编辑 `config.py` 中的默认值（注意不要将真实密钥提交到版本库）。

### 3. 启动应用

```bash
streamlit run app.py --server.headless true
```

浏览器访问 `http://localhost:8501` 即可使用。

## 📖 使用说明

### 新增实验记录

1. 在左侧导航选择 **📝 新增实验**
2. **上传图片**：先上传实验相关的图片（截图、曲线图等），系统会生成对应的 Markdown 图片引用
3. **编写内容**：在 Markdown 编辑框中自由编写实验记录，将图片引用粘贴到合适的位置
4. 填写实验名称和标签，点击保存

Markdown 内容示例：

```markdown
## 实验目的
测试不同学习率对 agent 表现的影响。

## 实验参数
| 参数 | 值 |
|------|-----|
| learning_rate | 3e-4 |
| batch_size | 64 |

## 实验过程
训练 100 epoch 后，loss 曲线如下：

![loss曲线](xxxxxxxx_loss.png)

## 结论
lr=3e-4 效果最优，成功率达 87.3%。
```

### 生成周报

1. 在左侧导航选择 **📊 生成周报**
2. 选择目标日期（默认为今天，系统会生成该日期所在周的周报）
3. 点击 **🚀 生成周报**，系统将：
   - 汇总该周所有实验记录
   - 调用 LLM 生成智能总结（本周总结、实验对比、下周建议）
   - 将原始实验记录（含图片）附在详情部分
4. 支持在线预览和下载 Markdown 文件

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | [Streamlit](https://streamlit.io/) |
| 数据库 | SQLite + [SQLAlchemy](https://www.sqlalchemy.org/) |
| HTTP 客户端 | [httpx](https://www.python-httpx.org/) |
| LLM API | Anthropic 兼容接口 |

## 📝 License

MIT
