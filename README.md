# 🚀 Browser Use Development Repository

这是一个独立的开发仓库，专门用于 Browser Use 项目的安全开发和实验。

## 📁 项目结构

```
browser-use-dev/
├── .git/                  # Git 版本控制
├── README.md             # 项目说明
├── CHANGELOG.md          # 变更日志
├── Dockerfile            # Docker 构建文件
├── docker-compose.yml    # Docker Compose 配置
├── requirements.txt      # Python 依赖
├── webui.py             # 主程序入口
├── supervisord.conf     # 进程管理配置
├── src/                 # 源代码目录
│   ├── agent/           # AI 代理相关代码
│   ├── browser/         # 浏览器控制代码
│   ├── controller/      # 控制器代码
│   ├── utils/           # 工具函数
│   └── webui/           # Web UI 相关代码
├── k8s/                 # Kubernetes 配置文件
│   ├── k8s-deployment.yaml
│   ├── browser-use-ingress.yaml
│   └── 其他 K8s 配置文件
├── docs/                # 文档和总结
│   ├── BEDROCK_PERMISSION_FIX_SUMMARY.md
│   ├── SAGEMAKER_PERMISSION_FIX_SUMMARY.md
│   └── 其他技术文档
├── backups/             # 重要状态备份
├── scripts/             # 部署和管理脚本
└── *.json              # 各种配置文件
```

## 🎯 开发目标

- ✅ 安全的版本控制环境
- ✅ 完整的回溯机制
- ✅ 清晰的开发历史
- ✅ 独立的实验空间

## 🔄 Git 工作流

### 分支策略
- **main**: 稳定版本，经过测试的代码
- **develop**: 开发版本，日常开发工作
- **feature/***: 具体功能开发分支
- **hotfix/***: 紧急修复分支

### 提交规范
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 🛡️ 回溯机制

### 多层次保护
1. **Commit 级别**: 每次重要更改自动提交
2. **Branch 级别**: 功能开发使用独立分支
3. **Tag 级别**: 重要里程碑创建标签
4. **Backup 级别**: 定期完整备份

### 快速回溯命令
```bash
# 查看提交历史
git log --oneline --graph

# 回到特定提交
git checkout <commit-hash>

# 回到特定标签
git checkout <tag-name>

# 创建新分支从特定点开始
git checkout -b new-branch <commit-hash>
```

## 🚀 快速开始

### 1. 克隆仓库
```bash
cd /Users/sssjwang/Documents/browser-use-dev
```

### 2. 创建开发分支
```bash
git checkout -b develop
```

### 3. 开始开发
```bash
# 进行代码修改
# ...

# 提交更改
git add .
git commit -m "feat: 添加新功能"
```

### 4. 部署测试
```bash
# 构建 Docker 镜像
docker build -t browser-use-dev .

# 部署到 Kubernetes
kubectl apply -f k8s/
```

## 📊 当前状态

- ✅ 项目结构已建立
- ✅ 源代码已复制
- ✅ Kubernetes 配置已迁移
- ✅ 文档已整理
- ✅ Git 仓库已初始化

## 🔧 维护说明

### 定期备份
- 每周创建完整项目备份
- 重要功能完成后创建 tag
- 保持 `backups/` 目录的备份文件

### 版本管理
- 遵循语义化版本控制 (Semantic Versioning)
- 主要版本: 不兼容的 API 修改
- 次要版本: 向下兼容的功能性新增
- 修订版本: 向下兼容的问题修正

---

**注意**: 这是一个独立的开发环境，可以安全地进行实验和修改，不会影响原始项目。
