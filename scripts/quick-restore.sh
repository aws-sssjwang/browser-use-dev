#!/bin/bash

# 🔙 快速回溯脚本
# 用于快速回到之前的版本或状态

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_highlight() {
    echo -e "${CYAN}[HIGHLIGHT]${NC} $1"
}

# 检查是否在正确的目录
check_directory() {
    if [[ ! -f "README.md" ]] || [[ ! -d ".git" ]]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
}

# 显示最近的提交
show_recent_commits() {
    log_info "最近的 10 个提交:"
    echo
    git log --oneline --graph -10 --color=always
    echo
}

# 显示所有标签
show_tags() {
    log_info "可用的标签:"
    echo
    git tag -l --sort=-version:refname | head -20
    echo
}

# 显示当前状态
show_current_status() {
    log_info "当前状态:"
    echo "  - 分支: $(git branch --show-current)"
    echo "  - 提交: $(git rev-parse --short HEAD) - $(git log -1 --pretty=format:'%s')"
    echo "  - 工作目录状态:"
    
    if git diff --quiet && git diff --staged --quiet; then
        echo "    ✅ 工作目录干净"
    else
        echo "    ⚠️  有未提交的更改"
        git status --short | sed 's/^/    /'
    fi
    echo
}

# 检查工作目录状态
check_working_directory() {
    if ! git diff --quiet || ! git diff --staged --quiet; then
        log_warning "工作目录有未提交的更改"
        echo
        git status --short
        echo
        
        echo -n "是否要先保存当前更改? (y/N): "
        read -r response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            log_info "保存当前更改..."
            git stash push -m "临时保存 - $(date '+%Y-%m-%d %H:%M:%S')"
            log_success "更改已保存到 stash"
        else
            log_warning "将丢弃未提交的更改"
            echo -n "确认继续? (y/N): "
            read -r confirm
            if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
                log_info "操作已取消"
                exit 0
            fi
        fi
    fi
}

# 回到特定提交
restore_to_commit() {
    local commit_hash="$1"
    
    if [[ -z "$commit_hash" ]]; then
        log_error "请提供提交哈希"
        return 1
    fi
    
    # 验证提交是否存在
    if ! git cat-file -e "$commit_hash" 2>/dev/null; then
        log_error "提交 $commit_hash 不存在"
        return 1
    fi
    
    log_info "回到提交: $commit_hash"
    
    # 显示提交信息
    echo
    log_highlight "提交信息:"
    git show --no-patch --pretty=format:"  提交: %H%n  作者: %an <%ae>%n  日期: %ad%n  信息: %s%n" "$commit_hash"
    echo
    
    echo -n "确认回到此提交? (y/N): "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git checkout "$commit_hash"
        log_success "已回到提交: $commit_hash"
        
        echo
        log_warning "注意: 您现在处于 'detached HEAD' 状态"
        log_info "如果要在此基础上继续开发，请创建新分支:"
        log_info "  git checkout -b new-branch-name"
    else
        log_info "操作已取消"
    fi
}

# 回到特定标签
restore_to_tag() {
    local tag_name="$1"
    
    if [[ -z "$tag_name" ]]; then
        log_error "请提供标签名称"
        return 1
    fi
    
    # 验证标签是否存在
    if ! git tag -l | grep -q "^${tag_name}$"; then
        log_error "标签 $tag_name 不存在"
        return 1
    fi
    
    log_info "回到标签: $tag_name"
    
    # 显示标签信息
    echo
    log_highlight "标签信息:"
    git show --no-patch --pretty=format:"  标签: %D%n  提交: %H%n  作者: %an <%ae>%n  日期: %ad%n  信息: %s%n" "$tag_name"
    echo
    
    echo -n "确认回到此标签? (y/N): "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git checkout "$tag_name"
        log_success "已回到标签: $tag_name"
        
        echo
        log_warning "注意: 您现在处于 'detached HEAD' 状态"
        log_info "如果要在此基础上继续开发，请创建新分支:"
        log_info "  git checkout -b new-branch-name"
    else
        log_info "操作已取消"
    fi
}

# 回到特定分支
restore_to_branch() {
    local branch_name="$1"
    
    if [[ -z "$branch_name" ]]; then
        log_error "请提供分支名称"
        return 1
    fi
    
    # 验证分支是否存在
    if ! git branch -a | grep -q "\\b${branch_name}\\b"; then
        log_error "分支 $branch_name 不存在"
        return 1
    fi
    
    log_info "切换到分支: $branch_name"
    git checkout "$branch_name"
    log_success "已切换到分支: $branch_name"
}

# 从备份文件恢复
restore_from_backup() {
    local backup_dir="./backups"
    
    if [[ ! -d "$backup_dir" ]]; then
        log_error "备份目录不存在: $backup_dir"
        return 1
    fi
    
    log_info "可用的备份文件:"
    echo
    
    local backups=($(ls -t "$backup_dir"/backup_*.tar.gz 2>/dev/null || true))
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        log_warning "没有找到备份文件"
        return 1
    fi
    
    for i in "${!backups[@]}"; do
        local backup_file="${backups[$i]}"
        local backup_name=$(basename "$backup_file" .tar.gz)
        local backup_date=$(echo "$backup_name" | sed 's/backup_//' | sed 's/_/ /')
        echo "  $((i+1)). $backup_name ($backup_date)"
    done
    
    echo
    echo -n "选择要恢复的备份 (1-${#backups[@]}): "
    read -r choice
    
    if [[ ! "$choice" =~ ^[0-9]+$ ]] || [[ "$choice" -lt 1 ]] || [[ "$choice" -gt ${#backups[@]} ]]; then
        log_error "无效的选择"
        return 1
    fi
    
    local selected_backup="${backups[$((choice-1))]}"
    log_warning "警告: 这将覆盖当前的所有文件!"
    echo -n "确认从备份恢复? (y/N): "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "从备份恢复: $(basename "$selected_backup")"
        
        # 创建临时目录
        local temp_dir=$(mktemp -d)
        
        # 解压备份
        tar -xzf "$selected_backup" -C "$temp_dir"
        
        # 保留 .git 目录
        if [[ -d ".git" ]]; then
            cp -r .git "$temp_dir/"
        fi
        
        # 替换文件
        rm -rf ./*
        cp -r "$temp_dir"/* .
        cp -r "$temp_dir"/.* . 2>/dev/null || true
        
        # 清理临时目录
        rm -rf "$temp_dir"
        
        log_success "备份恢复完成"
    else
        log_info "操作已取消"
    fi
}

# 显示 stash 列表
show_stash() {
    log_info "Stash 列表:"
    echo
    
    if git stash list | grep -q .; then
        git stash list --color=always
    else
        log_warning "没有保存的 stash"
    fi
    echo
}

# 从 stash 恢复
restore_from_stash() {
    if ! git stash list | grep -q .; then
        log_warning "没有保存的 stash"
        return 1
    fi
    
    show_stash
    
    echo -n "输入要恢复的 stash 编号 (0 为最新): "
    read -r stash_num
    
    if [[ ! "$stash_num" =~ ^[0-9]+$ ]]; then
        log_error "无效的 stash 编号"
        return 1
    fi
    
    log_info "恢复 stash@{$stash_num}..."
    git stash pop "stash@{$stash_num}"
    log_success "Stash 恢复完成"
}

# 交互式菜单
interactive_menu() {
    while true; do
        echo
        log_highlight "🔙 快速回溯菜单"
        echo
        echo "1. 显示最近提交"
        echo "2. 回到特定提交"
        echo "3. 显示标签列表"
        echo "4. 回到特定标签"
        echo "5. 切换到分支"
        echo "6. 从备份文件恢复"
        echo "7. 显示 stash 列表"
        echo "8. 从 stash 恢复"
        echo "9. 显示当前状态"
        echo "0. 退出"
        echo
        echo -n "请选择操作 (0-9): "
        read -r choice
        
        case "$choice" in
            1)
                show_recent_commits
                ;;
            2)
                echo -n "输入提交哈希: "
                read -r commit_hash
                if [[ -n "$commit_hash" ]]; then
                    check_working_directory
                    restore_to_commit "$commit_hash"
                fi
                ;;
            3)
                show_tags
                ;;
            4)
                echo -n "输入标签名称: "
                read -r tag_name
                if [[ -n "$tag_name" ]]; then
                    check_working_directory
                    restore_to_tag "$tag_name"
                fi
                ;;
            5)
                echo -n "输入分支名称: "
                read -r branch_name
                if [[ -n "$branch_name" ]]; then
                    check_working_directory
                    restore_to_branch "$branch_name"
                fi
                ;;
            6)
                check_working_directory
                restore_from_backup
                ;;
            7)
                show_stash
                ;;
            8)
                restore_from_stash
                ;;
            9)
                show_current_status
                ;;
            0)
                log_info "退出"
                break
                ;;
            *)
                log_error "无效的选择"
                ;;
        esac
    done
}

# 帮助信息
show_help() {
    echo "用法: $0 [选项] [参数]"
    echo
    echo "选项:"
    echo "  -c, --commit <hash>    回到特定提交"
    echo "  -t, --tag <name>       回到特定标签"
    echo "  -b, --branch <name>    切换到特定分支"
    echo "  -s, --stash [num]      从 stash 恢复"
    echo "  -f, --backup           从备份文件恢复"
    echo "  -i, --interactive      交互式菜单"
    echo "  -h, --help             显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 -i                  # 交互式菜单"
    echo "  $0 -c abc1234          # 回到提交 abc1234"
    echo "  $0 -t v1.0.0           # 回到标签 v1.0.0"
    echo "  $0 -b develop          # 切换到 develop 分支"
    echo "  $0 -s 0                # 恢复最新的 stash"
    echo
}

# 主函数
main() {
    check_directory
    
    case "${1:-}" in
        -c|--commit)
            if [[ -n "$2" ]]; then
                check_working_directory
                restore_to_commit "$2"
            else
                log_error "请提供提交哈希"
                exit 1
            fi
            ;;
        -t|--tag)
            if [[ -n "$2" ]]; then
                check_working_directory
                restore_to_tag "$2"
            else
                log_error "请提供标签名称"
                exit 1
            fi
            ;;
        -b|--branch)
            if [[ -n "$2" ]]; then
                check_working_directory
                restore_to_branch "$2"
            else
                log_error "请提供分支名称"
                exit 1
            fi
            ;;
        -s|--stash)
            restore_from_stash
            ;;
        -f|--backup)
            check_working_directory
            restore_from_backup
            ;;
        -i|--interactive|"")
            interactive_menu
            ;;
        -h|--help)
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
