# 安装指南

## 📋 系统要求

### 最低配置
- **Python**: 3.9 或更高版本
- **内存**: 4GB RAM
- **存储**: 1GB 可用空间
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### 推荐配置
- **Python**: 3.9+
- **内存**: 8GB+ RAM
- **存储**: 5GB+ 可用空间
- **操作系统**: Windows 11, macOS 12+, Ubuntu 20.04+

## 🚀 快速安装

### 1. 克隆项目
```bash
git clone <repository-url>
cd langgraph-learning
```

### 2. 创建虚拟环境
```bash
# 使用 venv
python -m venv langgraph-env

# 激活虚拟环境
# Windows
langgraph-env\Scripts\activate

# macOS/Linux
source langgraph-env/bin/activate

# 使用 conda (可选)
conda create -n langgraph-env python=3.9
conda activate langgraph-env
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
项目已预配置硅基流动API密钥，无需额外配置：
```bash
# .env 文件已包含：
OPENAI_API_KEY=sk-kodzewuwqkxlypmgegdjdgvhwntqfegmcamipvcoylribmss
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
```

### 5. 验证安装
```bash
python 01-basics/hello_world.py
```

## 🔧 详细配置

### Python 版本管理

#### 使用 pyenv (推荐)
```bash
# 安装 pyenv
# macOS
brew install pyenv

# Linux
curl https://pyenv.run | bash

# 安装 Python 3.9+
pyenv install 3.9.16
pyenv global 3.9.16
```

#### Windows 用户
- 从 python.org 下载安装包
- 确保添加到 PATH
- 使用 Windows Terminal 更好

### IDE 配置

#### VS Code
1. 安装 Python 扩展
2. 选择虚拟环境解释器
3. 安装推荐扩展：
   - Python
   - Pylance
   - Python Docstring Generator
   - GitLens

#### PyCharm
1. 打开项目
2. 设置 Python 解释器为虚拟环境
3. 启用代码检查
4. 配置代码格式化

### 可选依赖

#### 开发工具
```bash
pip install black flake8 mypy pytest
```

#### Jupyter 支持
```bash
pip install jupyter notebook ipykernel
```

#### 数据分析工具
```bash
pip install pandas matplotlib seaborn
```

## 🐛 常见问题

### Q: Python 版本不兼容
```bash
# 检查 Python 版本
python --version

# 如果版本过低，请升级 Python 或使用 pyenv
```

### Q: 依赖安装失败
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### Q: 环境变量问题
```bash
# 检查 .env 文件是否存在
ls -la .env

# 手动设置环境变量
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.siliconflow.cn/v1"
```

### Q: Windows 下路径问题
```bash
# 使用 PowerShell 而非 CMD
# 或使用 Git Bash
```

## 🧪 测试安装

### 基础测试
```bash
# 测试基础模块
python 01-basics/hello_world.py

# 测试配置
python -c "from utils import Config; print('配置正常')"
```

### 进阶测试
```bash
# 测试中级模块
python 02-intermediate/conditional_routing.py

# 测试高级模块
python 03-advanced/memory_system.py
```

### 性能测试
```bash
# 运行性能基准
python utils/benchmark.py
```

## 📦 项目结构

```
langgraph-learning/
├── 01-basics/           # 基础概念
│   ├── hello_world.py   # Hello World示例
│   ├── state_management.py # 状态管理
│   ├── nodes_edges.py   # 节点和边
│   └── README.md
├── 02-intermediate/     # 中级示例
│   ├── conditional_routing.py # 条件路由
│   ├── human_in_loop.py # 人工干预
│   ├── parallel_execution.py # 并行执行
│   └── README.md
├── 03-advanced/         # 高级应用
│   ├── memory_system.py # 记忆系统
│   ├── error_handling.py # 错误处理
│   ├── custom_tools.py  # 自定义工具
│   └── README.md
├── 04-real-world/       # 实际案例
│   ├── chatbot/         # 智能对话系统
│   ├── workflow/        # 工作流自动化
│   └── README.md
├── 05-exercises/        # 练习题目
│   ├── basic_challenges.py
│   ├── advanced_problems.py
│   ├── real_projects.py
│   └── README.md
├── utils/               # 工具函数
│   ├── config.py
│   └── __init__.py
├── docs/               # 文档
│   └── LEARNING_GUIDE.md
├── requirements.txt    # 依赖列表
├── .env               # 环境变量
├── README.md          # 项目说明
└── INSTALLATION.md    # 安装指南
```

## 🔒 安全注意事项

### API 密钥安全
- 不要将 `.env` 文件提交到版本控制
- 定期更换 API 密钥
- 使用环境变量管理敏感信息

### 代码安全
- 定期更新依赖包
- 使用虚拟环境隔离项目
- 运行前检查代码安全性

## 📞 技术支持

如果在安装过程中遇到问题：

1. 检查系统要求是否满足
2. 查看常见问题部分
3. 搜索项目 Issues
4. 提交新的 Issue

## 🚀 开始学习

安装完成后，请查看 [学习指南](docs/LEARNING_GUIDE.md) 开始你的 LangGraph 学习之旅！

---

**祝你学习愉快！** 🎉