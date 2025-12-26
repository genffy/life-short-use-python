#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据文件创建日期自动分类文件的工具

支持按 YYYY/MM/DD 格式将文件分类到目标目录
DD 文件夹支持备注，如 "25-周末旅行"
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_file_creation_time(file_path: Path) -> Optional[datetime]:
    """
    获取文件的创建时间

    在 macOS 上使用 st_birthtime
    在其他系统上尝试使用 st_ctime

    Args:
        file_path: 文件路径

    Returns:
        文件创建时间的 datetime 对象，如果获取失败则返回 None
    """
    try:
        stat_info = os.stat(file_path)
        # macOS 使用 st_birthtime 获取创建时间
        if hasattr(stat_info, 'st_birthtime'):
            timestamp = stat_info.st_birthtime
        else:
            # 其他系统使用 st_ctime
            timestamp = stat_info.st_ctime
        return datetime.fromtimestamp(timestamp)
    except (OSError, IOError) as e:
        logger.warning(f"无法获取文件 {file_path} 的创建时间: {e}")
        return None


def find_or_create_day_folder(month_dir: Path, day: int) -> Path:
    """
    在月份目录中查找或创建日期文件夹

    支持的格式：
    - DD（纯数字，如 "25"）
    - DD-备注（如 "25-周末旅行"）

    Args:
        month_dir: 月份目录路径
        day: 日期（1-31）

    Returns:
        日期文件夹路径
    """
    day_str = f"{day:02d}"

    # 先尝试查找已存在的匹配文件夹
    if month_dir.exists():
        for item in month_dir.iterdir():
            if item.is_dir():
                # 提取文件夹名中的日期部分
                match = re.match(r'^(\d{1,2})', item.name)
                if match:
                    existing_day = int(match.group(1))
                    if existing_day == day:
                        logger.debug(f"找到已存在的日期文件夹: {item.name}")
                        return item

    # 没有找到，返回新文件夹路径
    new_folder = month_dir / day_str
    return new_folder


def resolve_conflict(target_path: Path) -> Path:
    """
    解决目标路径文件名冲突

    如果目标文件已存在，在文件名后添加数字后缀

    Args:
        target_path: 原始目标路径

    Returns:
        解决冲突后的路径
    """
    if not target_path.exists():
        return target_path

    base = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent
    counter = 1

    while True:
        new_name = f"{base}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def scan_directory(source_dir: Path, extensions: Optional[tuple] = None) -> List[Path]:
    """
    扫描目录获取所有文件

    Args:
        source_dir: 源目录
        extensions: 可选的文件扩展名过滤，如 ('.jpg', '.png', '.heic')

    Returns:
        文件路径列表
    """
    files = []

    if not source_dir.exists():
        logger.error(f"源目录不存在: {source_dir}")
        return files

    if not source_dir.is_dir():
        logger.error(f"源路径不是目录: {source_dir}")
        return files

    logger.info(f"开始扫描目录: {source_dir}")

    for item in source_dir.rglob('*'):
        if item.is_file():
            if extensions is None or item.suffix.lower() in extensions:
                files.append(item)

    logger.info(f"找到 {len(files)} 个文件")
    return files


def classify_files(
    source_dir: Path,
    target_dir: Path,
    extensions: Optional[tuple] = None,
    dry_run: bool = False,
    copy: bool = False,
    skip_existing: bool = False
) -> Dict:
    """
    分类文件到目标目录（按 YYYY/MM/DD 结构）

    Args:
        source_dir: 源目录
        target_dir: 目标目录
        extensions: 文件扩展名过滤
        dry_run: 预览模式，不实际移动/复制文件
        copy: 复制而非移动文件
        skip_existing: 跳过已存在的文件

    Returns:
        统计信息字典
    """
    # 扫描源目录
    files = scan_directory(source_dir, extensions)

    stats = {
        'total': len(files),
        'processed': 0,
        'skipped': 0,
        'failed': 0,
        'folders_created': 0,
        'errors': []
    }

    for file_path in files:
        # 获取创建时间
        creation_time = get_file_creation_time(file_path)
        if creation_time is None:
            stats['skipped'] += 1
            continue

        # 生成年月目录路径
        year = creation_time.strftime('%Y')
        month = creation_time.strftime('%m')
        month_dir = target_dir / year / month

        # 查找或创建日期文件夹
        day_folder = find_or_create_day_folder(month_dir, creation_time.day)

        # 目标路径
        target_path = day_folder / file_path.name

        # 检查是否是同一个位置
        if file_path == target_path:
            logger.debug(f"文件已在正确位置: {file_path}")
            stats['skipped'] += 1
            continue

        # 检查目标文件是否已存在
        if target_path.exists():
            if skip_existing:
                logger.debug(f"文件已存在，跳过: {target_path}")
                stats['skipped'] += 1
                continue
            else:
                target_path = resolve_conflict(target_path)

        # 创建目录
        if not dry_run:
            # 创建日期文件夹（如果不存在）
            if not day_folder.exists():
                day_folder.mkdir(parents=True, exist_ok=True)
                stats['folders_created'] += 1

        # 执行操作
        action = "复制" if copy else "移动"
        mode_str = "[预览] " if dry_run else ""

        logger.info(f"{mode_str}{action}: {file_path} -> {target_path}")

        if not dry_run:
            try:
                if copy:
                    shutil.copy2(file_path, target_path)
                else:
                    shutil.move(str(file_path), str(target_path))
                stats['processed'] += 1
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                stats['failed'] += 1
                stats['errors'].append(str(file_path))
        else:
            stats['processed'] += 1
            # 预览模式下也统计需要创建的文件夹
            if not day_folder.exists():
                stats['folders_created'] += 1

    return stats


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数

    支持的格式：
    1. 位置参数：python classify_image.py <source_dir> <target_dir>
    2. 完整参数：python classify_image.py --source /path/to/source --target /path/to/target ...
    """
    parser = argparse.ArgumentParser(
        description='根据文件创建日期自动分类文件（YYYY/MM/DD 结构）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预览模式（推荐先运行）
  python classify_image.py /Volumes/SD\ Card/DCIM ~/Pictures/Photos --dry-run

  # 移动文件
  python classify_image.py ~/Downloads/Photos ~/Pictures/Photos

  # 只处理图片文件
  python classify_image.py ~/Downloads/Photos ~/Pictures/Photos --extensions .jpg .png .heic

  # 复制而非移动
  python classify_image.py ~/Downloads/Photos ~/Pictures/Photos --copy

  # 跳过已存在的文件
  python classify_image.py ~/Downloads/Photos ~/Pictures/Photos --skip-existing
        """
    )

    parser.add_argument(
        'source',
        nargs='?',
        help='源目录路径'
    )

    parser.add_argument(
        'target',
        nargs='?',
        help='目标目录路径'
    )

    parser.add_argument(
        '--source-dir',
        type=str,
        help='源目录路径（与位置参数二选一）'
    )

    parser.add_argument(
        '--target-dir',
        type=str,
        help='目标目录路径（与位置参数二选一）'
    )

    parser.add_argument(
        '--extensions',
        nargs='+',
        default=None,
        help='要处理的文件扩展名（如 .jpg .png .heic），默认处理所有文件'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际移动/复制文件'
    )

    parser.add_argument(
        '--copy',
        action='store_true',
        help='复制文件而非移动'
    )

    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='跳过目标目录中已存在的文件'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 获取源目录和目标目录
    source_dir = Path(args.source or args.source_dir)
    target_dir = Path(args.target or args.target_dir)

    # 验证参数
    if not source_dir or not target_dir:
        logger.error("必须指定源目录和目标目录")
        logger.error("使用 --help 查看帮助信息")
        sys.exit(1)

    # 转换为绝对路径，支持 ~ 和外接硬盘
    source_dir = source_dir.expanduser().resolve()
    target_dir = target_dir.expanduser().resolve()

    # 验证源目录
    if not source_dir.exists():
        logger.error(f"源目录不存在: {source_dir}")
        sys.exit(1)

    # 处理扩展名参数
    extensions = None
    if args.extensions:
        extensions = tuple(ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions)
        logger.info(f"只处理以下扩展名的文件: {', '.join(extensions)}")

    # 显示配置
    logger.info("=" * 50)
    logger.info("文件分类工具 (YYYY/MM/DD)")
    logger.info("=" * 50)
    logger.info(f"源目录: {source_dir}")
    logger.info(f"目标目录: {target_dir}")
    logger.info(f"模式: {'预览' if args.dry_run else '执行'}")
    logger.info(f"操作: {'复制' if args.copy else '移动'}")
    if args.skip_existing:
        logger.info(f"已存在文件: 跳过")
    logger.info("=" * 50)

    # 确认执行（非预览模式）
    if not args.dry_run:
        response = input(f"确定要{'复制' if args.copy else '移动'}文件吗？(y/N): ")
        if response.lower() != 'y':
            logger.info("操作已取消")
            sys.exit(0)

    # 执行分类
    stats = classify_files(
        source_dir=source_dir,
        target_dir=target_dir,
        extensions=extensions,
        dry_run=args.dry_run,
        copy=args.copy,
        skip_existing=args.skip_existing
    )

    # 显示统计
    logger.info("=" * 50)
    logger.info("统计信息")
    logger.info("=" * 50)
    logger.info(f"总文件数: {stats['total']}")
    logger.info(f"已处理: {stats['processed']}")
    logger.info(f"已跳过: {stats['skipped']}")
    logger.info(f"失败: {stats['failed']}")
    logger.info(f"创建的文件夹: {stats['folders_created']}")

    if stats['errors']:
        logger.warning("失败的文件:")
        for error in stats['errors']:
            logger.warning(f"  - {error}")

    logger.info("=" * 50)

    if args.dry_run:
        logger.info("预览模式完成，去掉 --dry-run 参数实际执行")


if __name__ == '__main__':
    main()
