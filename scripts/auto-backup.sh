#!/bin/bash

# 🔄 自动备份脚本
# 用于在重要更改前自动创建备份和提交

set -e

# 配置
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="backup_${TIMESTAMP}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在正确的目录
check_directory() {
    if [[ ! -f "README.md" ]] || [[ ! -d ".git" ]]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
}

# 创建备份目录
create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        log_info "创建备份目录: $BACKUP_DIR"
    fi
}

# 检查 Git 状态
check_git_status() {
    if git diff --quiet && git diff --staged --quiet; then
        log_warning "没有检测到文件更改"
        return 1
    fi
    return 0
}

# 显示当前状态
show_status() {
    log_info "当前 Git 状态:"
    git status --short
    echo
}

# 创建完整备份
create_full_backup() {
    local backup_path="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    
    log_info "创建完整项目备份..."
    
    # 排除不需要备份的文件
    tar --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='tmp' \
        --exclude='*.log' \
        --exclude='backups' \
        -czf "$backup_path" .
    
    log_success "备份已创建: $backup_path"
}

# Git 提交
git_commit() {
    local commit_message="$1"
    
    if [[ -z "$commit_message" ]]; then
        commit_message="auto-backup: ${TIMESTAMP}"
    fi
    
    log_info "添加所有更改到 Git..."
    git add .
    
    log_info "创建 Git 提交..."
    git commit -m "$commit_message"
    
    local commit_hash=$(git rev-parse --short HEAD)
    log_success "Git 提交已创建: $commit_hash"
}

# 创建 Git 标签
create_git_tag() {
    local tag_name="backup-${TIMESTAMP}"
    local tag_message="自动备份标签 - ${TIMESTAMP}"
    
    log_info "创建 Git 标签..."
    git tag -a "$tag_name" -m "$tag_message"
    
    log_success "Git 标签已创建: $tag_name"
}

# 清理旧备份
cleanup_old_backups() {
    local keep_count=10
    
    log_info "清理旧备份文件 (保留最新 $keep_count 个)..."
    
    cd "$BACKUP_DIR"
    ls -t backup_*.tar.gz 2>/dev/null | tail -n +$((keep_count + 1)) | xargs -r rm -f
    cd ..
    
    log_success "旧备份清理完成"
}

# 显示备份信息
show_backup_info() {
    echo
    log_info "备份完成信息:"
    echo "  - 时间戳: $TIMESTAMP"
    echo "  - 备份文件: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    echo "  - Git 提交: $(git rev-parse --short HEAD)"
    echo "  - Git 标签: backup-${TIMESTAMP}"
    echo
}

# 主函数
main() {
    log_info "🔄 开始自动备份流程..."
    echo
    
    # 检查环境
    check_directory
    create_backup_dir
    
    # 检查是否有更改
    if ! check_git_status; then
        log_warning "没有需要备份的更改，退出"
        exit 0
    fi
    
    # 显示当前状态
    show_status
    
    # 获取提交信息
    local commit_message="$1"
    if [[ -z "$commit_message" ]]; then
        echo -n "请输入提交信息 (回车使用默认): "
        read user_input
        if [[ -n "$user_input" ]]; then
            commit_message="$user_input"
        fi
    fi
    
    # 执行备份流程
    create_full_backup
    git_commit "$commit_message"
    create_git_tag
    cleanup_old_backups
    
    # 显示结果
    show_backup_info
    log_success "🎉 自动备份完成！"
}

# 帮助信息
show_help() {
    echo "用法: $0 [提交信息]"
    echo
    echo "选项:"
    echo "  -h, --help    显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0                           # 交互式输入提交信息"
    echo "  $0 \"feat: 添加新功能\"        # 直接指定提交信息"
    echo
}

# 处理命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$1"
        ;;
esac
