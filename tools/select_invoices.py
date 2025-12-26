#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票选择工具：根据指定金额从 todo 文件夹中选择发票并移动到 doing 文件夹

## 目录结构规范

工作目录需包含以下子目录：

    work_dir/
    ├── todo/          # 待处理发票文件夹（放入待报销的发票 PDF）
    ├── doing/         # 处理中发票文件夹（脚本自动将选中的发票移动到此）
    └── done/          # 已完成发票文件夹（报销完成后手动移动）

## 文件命名规范

发票 PDF 文件名必须以金额开头（纯数字），例如：

    - 100_公司名称_2024-01-01.pdf
    - 500_某发票.pdf
    - 1234.pdf

金额将从文件名开头的数字中提取。

## 使用方法

在代码目录运行，通过 --work-dir 参数指定工作目录：

    cd ~/workspace/github/life-short-use-python/tools/
    python select_invoices.py --work-dir ~/Document/invoice/ 1000

## 参数说明

    --work-dir: 工作目录路径（必需），需包含 todo/doing/done 子目录
    目标金额:   需要凑齐的总金额（必需，整数）
    --yes, -y:  自动确认，不询问（可选）

## 示例

    # 选择总额 >= 1000 的发票
    python select_invoices.py --work-dir ~/Document/invoice/ 1000

    # 自动确认，不询问
    python select_invoices.py --work-dir ~/Document/invoice/ 1000 --yes
"""

import argparse
import os
import shutil
import re
import sys
from pathlib import Path


def parse_amount_from_filename(filename):
    """从文件名中提取金额（文件名开头的数字）"""
    match = re.match(r'^(\d+)', filename)
    if match:
        return int(match.group(1))
    return None


def validate_work_dir(work_dir):
    """验证工作目录的合法性，确保包含必需的子目录"""
    work_dir = os.path.expanduser(work_dir)
    work_dir = os.path.abspath(work_dir)

    if not os.path.exists(work_dir):
        print(f"错误: 工作目录不存在: {work_dir}")
        sys.exit(1)

    if not os.path.isdir(work_dir):
        print(f"错误: 指定路径不是目录: {work_dir}")
        sys.exit(1)

    # 检查必需的子目录
    required_subdirs = ['todo', 'doing', 'done']
    missing_dirs = []

    for subdir in required_subdirs:
        subdir_path = os.path.join(work_dir, subdir)
        if not os.path.exists(subdir_path):
            missing_dirs.append(subdir)

    if missing_dirs:
        print(f"错误: 工作目录缺少以下子目录: {', '.join(missing_dirs)}")
        print(f"请在 {work_dir} 下创建以下目录:")
        for d in missing_dirs:
            print(f"  mkdir {os.path.join(work_dir, d)}")
        sys.exit(1)

    return work_dir


def select_invoices(todo_dir, target_amount):
    """选择发票，使得总金额 >= target_amount"""
    invoices = []
    
    # 扫描 todo 文件夹中的所有 PDF 文件
    for filename in os.listdir(todo_dir):
        if filename.endswith('.pdf'):
            amount = parse_amount_from_filename(filename)
            if amount is not None:
                invoices.append({
                    'filename': filename,
                    'amount': amount,
                    'path': os.path.join(todo_dir, filename)
                })
    
    if not invoices:
        print("未找到符合条件的发票文件")
        return [], 0
    
    # 按金额排序（从大到小）
    invoices.sort(key=lambda x: x['amount'], reverse=True)
    
    # 贪心算法：优先选择金额大的发票，直到满足条件
    selected = []
    total = 0
    
    # 从大到小选择，直到总金额 >= 目标金额
    for invoice in invoices:
        if total < target_amount:
            selected.append(invoice)
            total += invoice['amount']
        else:
            break
    
    # 如果所有发票加起来都不够，返回所有发票
    if total < target_amount:
        print(f"警告: 所有发票总金额 {total} 小于目标金额 {target_amount}")
    
    return selected, total


def move_invoices(selected_invoices, todo_dir, doing_dir):
    """将选中的发票移动到 doing 文件夹"""
    # 确保 doing 文件夹存在
    os.makedirs(doing_dir, exist_ok=True)
    
    moved_files = []
    for invoice in selected_invoices:
        src = invoice['path']
        dst = os.path.join(doing_dir, invoice['filename'])
        
        try:
            shutil.move(src, dst)
            moved_files.append(invoice['filename'])
            print(f"已移动: {invoice['filename']} (金额: {invoice['amount']})")
        except Exception as e:
            print(f"移动失败 {invoice['filename']}: {e}")
    
    return moved_files


def main():
    parser = argparse.ArgumentParser(
        description='发票选择工具：根据指定金额从 todo 文件夹中选择发票并移动到 doing 文件夹',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python select_invoices.py --work-dir ~/Document/invoice/ 1000
  python select_invoices.py --work-dir ~/Document/invoice/ 1000 --yes
        """
    )
    parser.add_argument(
        '--work-dir',
        required=True,
        help='工作目录路径，需包含 todo/doing/done 子目录'
    )
    parser.add_argument(
        'amount',
        type=int,
        help='目标金额（整数）'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='自动确认，不询问'
    )

    args = parser.parse_args()

    # 验证工作目录
    work_dir = validate_work_dir(args.work_dir)
    todo_dir = os.path.join(work_dir, 'todo')
    doing_dir = os.path.join(work_dir, 'doing')

    print(f"目标金额: {args.amount}")
    print(f"工作目录: {work_dir}")
    print(f"扫描文件夹: {todo_dir}")
    print("-" * 50)

    # 选择发票
    selected, total = select_invoices(todo_dir, args.amount)

    if not selected:
        print("未找到足够的发票")
        sys.exit(1)

    print(f"\n选中 {len(selected)} 张发票，总金额: {total}")
    print("\n选中的发票:")
    for invoice in selected:
        print(f"  - {invoice['filename']} (金额: {invoice['amount']})")

    # 确认移动
    if args.yes:
        confirm = 'y'
    else:
        print(f"\n是否将这些发票移动到 doing 文件夹? (y/n): ", end='')
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n操作已取消")
            sys.exit(0)

    if confirm == 'y':
        moved = move_invoices(selected, todo_dir, doing_dir)
        print(f"\n成功移动 {len(moved)} 张发票到 doing 文件夹")
    else:
        print("操作已取消")


if __name__ == '__main__':
    main()

