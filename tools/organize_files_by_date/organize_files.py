#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件整理工具 - 按日期整理文件到 YYYY/MM/DD-备注 结构

支持子命令：
  classify    - 从源目录分类整理文件到目标目录
  reorganize  - 在已有 YYYY/MM 结构下，将 MM 层文件移动到 DD 层
  find-dups   - 查找重复文件（xxx_N.ext 格式）
"""

import os
import re
import json
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any
from fnmatch import fnmatch
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# 公共模块
# =============================================================================

def get_file_time(file_path: Path, use_mtime: bool = False) -> Optional[datetime]:
    """
    获取文件的时间戳

    在 macOS 上使用 st_birthtime 获取创建时间
    在其他系统上尝试使用 st_ctime
    可选择使用修改时间 (mtime)

    Args:
        file_path: 文件路径
        use_mtime: 使用修改时间而非创建时间

    Returns:
        文件时间的 datetime 对象，如果获取失败则返回 None
    """
    try:
        stat_info = os.stat(file_path)
        if use_mtime:
            timestamp = stat_info.st_mtime
        elif hasattr(stat_info, 'st_birthtime'):
            # macOS 使用 st_birthtime 获取创建时间
            timestamp = stat_info.st_birthtime
        else:
            # 其他系统使用 st_ctime
            timestamp = stat_info.st_ctime
        return datetime.fromtimestamp(timestamp)
    except (OSError, IOError) as e:
        logger.warning(f"无法获取文件 {file_path} 的时间: {e}")
        return None


def find_day_folder(month_dir: Path, day: int) -> Path:
    """
    在月份目录中查找或获取日期文件夹路径

    支持的格式：
    - DD（纯数字，如 "25"）
    - DD-备注（如 "25-周末旅行"）

    Args:
        month_dir: 月份目录路径
        day: 日期（1-31）

    Returns:
        日期文件夹路径（可能不存在）
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
    return month_dir / day_str


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


def matches_exclude_patterns(file_path: Path, patterns: List[str]) -> bool:
    """
    检查文件路径是否匹配排除规则

    Args:
        file_path: 文件路径
        patterns: glob 模式列表

    Returns:
        是否匹配（匹配则应该排除）
    """
    for pattern in patterns:
        # 检查完整路径
        if fnmatch(str(file_path), pattern):
            return True
        # 检查文件名
        if fnmatch(file_path.name, pattern):
            return True
        # 检查相对于当前目录的路径
        try:
            if fnmatch(str(file_path.relative_to(Path.cwd())), pattern):
                return True
        except ValueError:
            pass
    return False


def scan_directory(
    source_dir: Path,
    extensions: Optional[tuple] = None,
    exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """
    扫描目录获取所有文件

    Args:
        source_dir: 源目录
        extensions: 可选的文件扩展名过滤，如 ('.jpg', '.png', '.heic')
        exclude_patterns: 排除规则列表（glob 模式）

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

    exclude = exclude_patterns or []

    for item in source_dir.rglob('*'):
        if item.is_file():
            # 检查排除规则
            if exclude and matches_exclude_patterns(item, exclude):
                logger.debug(f"排除文件: {item}")
                continue

            # 检查扩展名
            if extensions is None or item.suffix.lower() in extensions:
                files.append(item)

    logger.info(f"找到 {len(files)} 个文件")
    return files


def generate_report(
    report_data: Dict[str, Any],
    output_path: Path
) -> bool:
    """
    生成操作报告

    Args:
        report_data: 报告数据
        output_path: 输出路径

    Returns:
        是否成功
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        logger.info(f"报告已生成: {output_path}")
        return True
    except Exception as e:
        logger.error(f"生成报告失败: {e}")
        return False


# =============================================================================
# classify 子命令
# =============================================================================

def cmd_classify(args: argparse.Namespace) -> int:
    """
    分类整理命令 - 从源目录分类文件到目标目录

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    source_dir = Path(args.source).expanduser().resolve()
    target_dir = Path(args.target).expanduser().resolve()

    # 验证源目录
    if not source_dir.exists():
        logger.error(f"源目录不存在: {source_dir}")
        return 1

    # 处理扩展名参数
    extensions = None
    if args.extensions:
        extensions = tuple(ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions)
        logger.info(f"只处理以下扩展名的文件: {', '.join(extensions)}")

    # 处理排除规则
    exclude_patterns = args.exclude or []
    if exclude_patterns:
        logger.info(f"排除规则: {', '.join(exclude_patterns)}")

    # 显示配置
    logger.info("=" * 50)
    logger.info("文件分类 (YYYY/MM/DD)")
    logger.info("=" * 50)
    logger.info(f"源目录: {source_dir}")
    logger.info(f"目标目录: {target_dir}")
    logger.info(f"模式: {'预览' if args.dry_run else '执行'}")
    logger.info(f"操作: {'复制' if args.copy else '移动'}")
    if args.skip_existing:
        logger.info(f"已存在文件: 跳过")
    if args.use_mtime:
        logger.info(f"使用时间: 修改时间")
    logger.info("=" * 50)

    # 确认执行
    if not args.dry_run:
        response = input(f"确定要{'复制' if args.copy else '移动'}文件吗？(y/N): ")
        if response.lower() != 'y':
            logger.info("操作已取消")
            return 0

    # 扫描源目录
    files = scan_directory(source_dir, extensions, exclude_patterns)

    stats = {
        'total': len(files),
        'processed': 0,
        'skipped': 0,
        'failed': 0,
        'folders_created': 0,
        'errors': []
    }
    operations = []

    for file_path in files:
        # 获取文件时间
        file_time = get_file_time(file_path, use_mtime=args.use_mtime)
        if file_time is None:
            stats['skipped'] += 1
            continue

        # 生成年月目录路径
        year = file_time.strftime('%Y')
        month = file_time.strftime('%m')
        month_dir = target_dir / year / month

        # 查找日期文件夹
        day_folder = find_day_folder(month_dir, file_time.day)

        # 目标路径
        target_path = day_folder / file_path.name

        # 记录操作
        operation = {
            'source': str(file_path),
            'target': str(target_path),
            'action': 'copy' if args.copy else 'move',
            'status': 'pending'
        }

        # 检查是否是同一个位置
        if file_path == target_path:
            logger.debug(f"文件已在正确位置: {file_path}")
            stats['skipped'] += 1
            operation['status'] = 'skipped'
            operations.append(operation)
            continue

        # 检查目标文件是否已存在
        if target_path.exists():
            if args.skip_existing:
                logger.debug(f"文件已存在，跳过: {target_path}")
                stats['skipped'] += 1
                operation['status'] = 'skipped'
                operations.append(operation)
                continue
            else:
                target_path = resolve_conflict(target_path)
                operation['target'] = str(target_path)

        # 创建目录
        if not args.dry_run:
            if not day_folder.exists():
                day_folder.mkdir(parents=True, exist_ok=True)
                stats['folders_created'] += 1

        # 执行操作
        action = "复制" if args.copy else "移动"
        mode_str = "[预览] " if args.dry_run else ""
        logger.info(f"{mode_str}{action}: {file_path} -> {target_path}")

        if not args.dry_run:
            try:
                if args.copy:
                    shutil.copy2(file_path, target_path)
                else:
                    shutil.move(str(file_path), str(target_path))
                stats['processed'] += 1
                operation['status'] = 'success'
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                stats['failed'] += 1
                stats['errors'].append({'file': str(file_path), 'error': str(e)})
                operation['status'] = 'failed'
                operation['error'] = str(e)
        else:
            stats['processed'] += 1
            operation['status'] = 'success'
            # 预览模式下也统计需要创建的文件夹
            if not day_folder.exists():
                stats['folders_created'] += 1

        operations.append(operation)

    # 生成报告
    if args.report:
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'command': 'classify',
            'source_dir': str(source_dir),
            'target_dir': str(target_dir),
            'options': {
                'extensions': list(extensions) if extensions else None,
                'exclude': exclude_patterns,
                'copy': args.copy,
                'skip_existing': args.skip_existing,
                'use_mtime': args.use_mtime
            },
            'stats': stats,
            'operations': operations
        }
        generate_report(report_data, Path(args.report))

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
            logger.warning(f"  - {error['file']}: {error['error']}")

    logger.info("=" * 50)

    if args.dry_run:
        logger.info("预览模式完成，去掉 --dry-run 参数实际执行")

    return 0 if stats['failed'] == 0 else 1


# =============================================================================
# reorganize 子命令
# =============================================================================

def get_month_dirs(root_dir: Path) -> List[Path]:
    """
    获取所有月份目录

    Args:
        root_dir: 根目录

    Returns:
        月份目录列表
    """
    month_dirs = []

    for year_dir in root_dir.iterdir():
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue

        for item in year_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                month = int(item.name)
                if 1 <= month <= 12:
                    month_dirs.append(item)

    return month_dirs


def scan_month_files(month_dir: Path) -> List[Path]:
    """
    扫描月份目录下的所有文件（不包括子目录中的文件）

    Args:
        month_dir: 月份目录

    Returns:
        文件路径列表
    """
    files = []

    if not month_dir.exists():
        return files

    for item in month_dir.iterdir():
        if item.is_file():
            files.append(item)

    return files


def cmd_reorganize(args: argparse.Namespace) -> int:
    """
    二次整理命令 - 在 YYYY/MM 结构下，将 MM 层文件移动到 DD 层

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    root_dir = Path(args.root).expanduser().resolve()

    # 验证根目录
    if not root_dir.exists():
        logger.error(f"根目录不存在: {root_dir}")
        return 1

    if not root_dir.is_dir():
        logger.error(f"根路径不是目录: {root_dir}")
        return 1

    # 显示配置
    logger.info("=" * 50)
    logger.info("月份文件二次整理 (MM -> DD)")
    logger.info("=" * 50)
    logger.info(f"根目录: {root_dir}")
    logger.info(f"模式: {'预览' if args.dry_run else '执行'}")
    logger.info(f"创建缺失文件夹: {'否' if args.no_create_folders else '是'}")
    logger.info("=" * 50)

    # 确认执行
    if not args.dry_run:
        response = input("确定要移动文件吗？(y/N): ")
        if response.lower() != 'y':
            logger.info("操作已取消")
            return 0

    month_dirs = get_month_dirs(root_dir)

    stats = {
        'total': 0,
        'processed': 0,
        'skipped': 0,
        'failed': 0,
        'folders_created': 0,
        'errors': []
    }
    operations = []

    for month_dir in month_dirs:
        logger.info(f"处理目录: {month_dir}")

        # 扫描该月份目录下的文件
        files = scan_month_files(month_dir)

        for file_path in files:
            stats['total'] += 1

            # 获取创建时间
            creation_time = get_file_time(file_path)
            if creation_time is None:
                stats['skipped'] += 1
                continue

            # 验证文件的创建日期是否与目录匹配
            expected_year = int(month_dir.parent.name)
            expected_month = int(month_dir.name)

            if creation_time.year != expected_year or creation_time.month != expected_month:
                logger.debug(
                    f"文件日期 {creation_time.strftime('%Y-%m-%d')} 与目录 "
                    f"{expected_year}-{expected_month:02d} 不匹配"
                )

            day = creation_time.day

            # 查找日期文件夹
            day_folder = find_day_folder(month_dir, day)

            # 如果文件夹不存在且需要创建
            if not day_folder.exists():
                if not args.no_create_folders:
                    logger.info(f"{'[预览] ' if args.dry_run else ''}创建日期文件夹: {day_folder}")
                    if not args.dry_run:
                        day_folder.mkdir(parents=True, exist_ok=True)
                    stats['folders_created'] += 1
                else:
                    logger.warning(f"日期文件夹不存在且跳过创建: {day_folder}")
                    stats['skipped'] += 1
                    continue

            # 目标路径
            target_path = day_folder / file_path.name

            # 记录操作
            operation = {
                'source': str(file_path),
                'target': str(target_path),
                'action': 'move',
                'status': 'pending'
            }

            # 检查是否是同一个位置
            if file_path == target_path:
                logger.debug(f"文件已在正确位置: {file_path}")
                stats['skipped'] += 1
                operation['status'] = 'skipped'
                operations.append(operation)
                continue

            # 处理文件名冲突
            if target_path.exists():
                target_path = resolve_conflict(target_path)
                operation['target'] = str(target_path)

            # 显示操作
            mode_str = "[预览] " if args.dry_run else ""
            logger.info(f"{mode_str}移动: {file_path} -> {target_path}")

            # 执行移动
            if not args.dry_run:
                try:
                    shutil.move(str(file_path), str(target_path))
                    stats['processed'] += 1
                    operation['status'] = 'success'
                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {e}")
                    stats['failed'] += 1
                    stats['errors'].append({'file': str(file_path), 'error': str(e)})
                    operation['status'] = 'failed'
                    operation['error'] = str(e)
            else:
                stats['processed'] += 1
                operation['status'] = 'success'

            operations.append(operation)

    # 生成报告
    if args.report:
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'command': 'reorganize',
            'root_dir': str(root_dir),
            'options': {
                'no_create_folders': args.no_create_folders
            },
            'stats': stats,
            'operations': operations
        }
        generate_report(report_data, Path(args.report))

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
            logger.warning(f"  - {error['file']}: {error['error']}")

    logger.info("=" * 50)

    if args.dry_run:
        logger.info("预览模式完成，去掉 --dry-run 参数实际执行")

    return 0 if stats['failed'] == 0 else 1


# =============================================================================
# find-dups 子命令
# =============================================================================

def is_duplicate_name(filename: str) -> Tuple[bool, str, int, str]:
    """
    检查文件名是否符合 xxx_N.yyy 格式（N 为数字）

    Args:
        filename: 文件名

    Returns:
        (是否匹配, 原始文件名, 数字后缀, 扩展名)
    """
    match = re.match(r'^(.+?)_(\d+)(\.[^.]+)$', filename)
    if match:
        base_name = match.group(1)
        number = int(match.group(2))
        ext = match.group(3)
        if base_name and number > 0:
            return True, base_name, number, ext
    return False, '', 0, ''


def find_duplicates_in_dir(
    directory: Path,
    extensions: Optional[tuple] = None,
    verbose: bool = False
) -> List[Tuple[Path, Path, int]]:
    """
    在目录中查找所有重复文件

    Args:
        directory: 要扫描的目录
        extensions: 可选的扩展名过滤
        verbose: 是否显示详细调试信息

    Returns:
        列表，每项为 (重复文件路径, 原始文件路径, 数字后缀)
    """
    duplicates = []

    if not directory.exists() or not directory.is_dir():
        logger.warning(f"目录不存在或不是目录: {directory}")
        return duplicates

    # 按目录分组处理
    dirs_to_files: Dict[Path, List[str]] = {}

    for item in directory.rglob('*'):
        if item.is_file():
            # 扩展名过滤
            if extensions is not None and item.suffix.lower() not in extensions:
                continue

            parent_dir = item.parent
            if parent_dir not in dirs_to_files:
                dirs_to_files[parent_dir] = []
            dirs_to_files[parent_dir].append(item.name)

    # 检查每个目录中的文件
    for dir_path, filenames in dirs_to_files.items():
        if verbose:
            logger.debug(f"目录 {dir_path}: {len(filenames)} 个文件")

        # 构建当前目录的文件集合（完整文件名）
        files_set = set(filenames)

        # 检查每个文件是否是重复文件
        for filename in filenames:
            is_dup, base_name, number, ext = is_duplicate_name(filename)
            if is_dup:
                # 检查原始文件是否存在于同一目录
                original_filename = f"{base_name}{ext}"
                if original_filename in files_set:
                    dup_file = dir_path / filename
                    orig_file = dir_path / original_filename
                    duplicates.append((dup_file, orig_file, number))
                    if verbose:
                        logger.debug(f"  重复: {filename} -> 原始: {original_filename}")

    return duplicates


def group_duplicates(
    duplicates: List[Tuple[Path, Path, int]]
) -> Dict[Path, List[Tuple[Path, int]]]:
    """
    将重复文件按原始文件分组

    Args:
        duplicates: 重复文件列表

    Returns:
        分组字典，key 为原始文件路径，value 为重复文件列表
    """
    groups: Dict[Path, List[Tuple[Path, int]]] = {}

    for dup_file, orig_file, number in duplicates:
        if orig_file not in groups:
            groups[orig_file] = []
        groups[orig_file].append((dup_file, number))

    # 对每组内的重复文件按数字排序
    for orig_file in groups:
        groups[orig_file].sort(key=lambda x: x[1])

    return groups


def print_duplicates(groups: Dict[Path, List[Tuple[Path, int]]], show_size: bool = False):
    """
    打印重复文件信息

    Args:
        groups: 分组的重复文件
        show_size: 是否显示文件大小
    """
    if not groups:
        logger.info("未找到重复文件")
        return

    total_files = sum(len(files) for files in groups.values())
    total_groups = len(groups)

    logger.info("=" * 60)
    logger.info(f"找到 {total_groups} 个原始文件，共 {total_files} 个重复文件")
    logger.info("=" * 60)

    for orig_file, dup_list in sorted(groups.items()):
        logger.info(f"\n原始文件: {orig_file}")

        if show_size and orig_file.exists():
            size = orig_file.stat().st_size
            logger.info(f"  大小: {size:,} 字节")

        for dup_file, number in dup_list:
            size_str = ""
            if show_size and dup_file.exists():
                size = dup_file.stat().st_size
                size_str = f" ({size:,} 字节)"
            logger.info(f"  └─ {dup_file.name} [后缀: _{number}]{size_str}")


def cmd_find_dups(args: argparse.Namespace) -> int:
    """
    查找重复文件命令

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    directory = Path(args.directory).expanduser().resolve()

    # 验证目录
    if not directory.exists():
        logger.error(f"目录不存在: {directory}")
        return 1

    if not directory.is_dir():
        logger.error(f"路径不是目录: {directory}")
        return 1

    # 处理扩展名参数
    extensions = None
    if args.extensions:
        extensions = tuple(ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions)

    # 显示配置
    logger.info("=" * 60)
    logger.info("重复文件查找工具")
    logger.info("=" * 60)
    logger.info(f"目录: {directory}")
    if extensions:
        logger.info(f"扩展名过滤: {', '.join(extensions)}")
    logger.info("=" * 60)

    # 查找重复文件
    all_duplicates = find_duplicates_in_dir(directory, extensions, verbose=args.verbose)

    # 分组并显示
    groups = group_duplicates(all_duplicates)
    print_duplicates(groups, show_size=args.show_size)

    stats = {
        'total': len(all_duplicates),
        'deleted': 0,
        'failed': 0,
        'errors': []
    }
    operations = []

    # 删除操作
    if args.delete:
        dry_run = args.dry_run and not args.no_dry_run

        if dry_run:
            logger.info("\n" + "=" * 60)
            logger.info("预览模式：使用 --no-dry-run 实际删除文件")
            logger.info("=" * 60)
        else:
            logger.info("\n" + "=" * 60)
            response = input("确定要删除这些重复文件吗？(y/N): ")
            if response.lower() != 'y':
                logger.info("操作已取消")
                return 0
            logger.info("=" * 60)

        for dup_file, orig_file, number in all_duplicates:
            if not dup_file.exists():
                logger.debug(f"文件不存在，跳过: {dup_file}")
                continue

            operation = {
                'file': str(dup_file),
                'original_file': str(orig_file),
                'action': 'delete',
                'status': 'pending'
            }

            mode_str = "[预览] " if dry_run else ""
            logger.info(f"{mode_str}删除: {dup_file}")

            if not dry_run:
                try:
                    dup_file.unlink()
                    stats['deleted'] += 1
                    operation['status'] = 'success'
                except Exception as e:
                    logger.error(f"删除失败 {dup_file}: {e}")
                    stats['failed'] += 1
                    stats['errors'].append({'file': str(dup_file), 'error': str(e)})
                    operation['status'] = 'failed'
                    operation['error'] = str(e)
            else:
                stats['deleted'] += 1
                operation['status'] = 'success'

            operations.append(operation)

        # 显示统计
        logger.info("\n" + "=" * 60)
        logger.info("统计信息")
        logger.info("=" * 60)
        logger.info(f"总计: {stats['total']}")
        logger.info(f"已删除: {stats['deleted']}")
        logger.info(f"失败: {stats['failed']}")

        if stats['errors']:
            logger.warning("失败的文件:")
            for error in stats['errors']:
                logger.warning(f"  - {error['file']}: {error['error']}")

        logger.info("=" * 60)

        # 生成报告
        if args.report:
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'command': 'find-dups',
                'directory': str(directory),
                'options': {
                    'extensions': list(extensions) if extensions else None,
                    'delete': args.delete
                },
                'stats': stats,
                'operations': operations
            }
            generate_report(report_data, Path(args.report))

        return 0 if stats['failed'] == 0 else 1

    return 0


# =============================================================================
# 主入口
# =============================================================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='文件整理工具 - 按日期整理文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分类整理（预览）
  python organize_files.py classify ~/Downloads ~/Pictures/Organized --dry-run

  # 分类整理（只处理图片，排除临时文件）
  python organize_files.py classify ~/Downloads ~/Pictures/Organized \\
      --extensions .jpg .png .heic --exclude "*/tmp/*" --exclude "*.tmp"

  # 分类整理（生成报告）
  python organize_files.py classify ~/Downloads ~/Pictures/Organized --report report.json

  # 二次整理
  python organize_files.py reorganize ~/Pictures/Organized --dry-run

  # 查找重复文件
  python organize_files.py find-dups ~/Pictures/Organized
        """
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出'
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # =========================================================================
    # classify 子命令
    # =========================================================================
    classify_parser = subparsers.add_parser(
        'classify',
        help='从源目录分类整理文件到目标目录 (YYYY/MM/DD 结构)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用
  python organize_files.py classify ~/Downloads ~/Pictures/Organized

  # 只处理图片文件
  python organize_files.py classify ~/Downloads ~/Pictures/Organized --extensions .jpg .png .heic

  # 排除临时文件
  python organize_files.py classify ~/Downloads ~/Pictures/Organized --exclude "*/tmp/*" --exclude "*.tmp"

  # 复制而非移动
  python organize_files.py classify ~/Downloads ~/Pictures/Organized --copy

  # 跳过已存在的文件
  python organize_files.py classify ~/Downloads ~/Pictures/Organized --skip-existing

  # 使用修改时间而非创建时间
  python organize_files.py classify ~/Downloads ~/Pictures/Organized --use-mtime

  # 生成报告
  python organize_files.py classify ~/Downloads ~/Pictures/Organized --report report.json
        """
    )

    classify_parser.add_argument(
        'source',
        help='源目录路径'
    )

    classify_parser.add_argument(
        'target',
        help='目标目录路径'
    )

    classify_parser.add_argument(
        '--extensions',
        nargs='+',
        default=None,
        help='要处理的文件扩展名（如 .jpg .png .heic），默认处理所有文件'
    )

    classify_parser.add_argument(
        '--exclude',
        action='append',
        default=None,
        help='排除规则（glob 模式，可多次使用，如 "*/tmp/*" 或 "*.tmp"）'
    )

    classify_parser.add_argument(
        '--copy',
        action='store_true',
        help='复制文件而非移动'
    )

    classify_parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='跳过目标目录中已存在的文件'
    )

    classify_parser.add_argument(
        '--use-mtime',
        action='store_true',
        help='使用修改时间而非创建时间进行分类'
    )

    classify_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际移动/复制文件'
    )

    classify_parser.add_argument(
        '--report',
        type=str,
        help='生成操作报告文件（JSON 格式）'
    )

    # =========================================================================
    # reorganize 子命令
    # =========================================================================
    reorganize_parser = subparsers.add_parser(
        'reorganize',
        help='在已有 YYYY/MM 结构下，将 MM 层文件移动到 DD 层',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预览模式
  python organize_files.py reorganize ~/Pictures/Organized --dry-run

  # 执行整理
  python organize_files.py reorganize ~/Pictures/Organized

  # 不创建缺失的日期文件夹
  python organize_files.py reorganize ~/Pictures/Organized --no-create-folders
        """
    )

    reorganize_parser.add_argument(
        'root',
        help='根目录路径（YYYY/MM 结构的顶层目录）'
    )

    reorganize_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际移动文件'
    )

    reorganize_parser.add_argument(
        '--no-create-folders',
        action='store_true',
        help='不创建缺失的日期文件夹，只移动到已存在的文件夹'
    )

    reorganize_parser.add_argument(
        '--report',
        type=str,
        help='生成操作报告文件（JSON 格式）'
    )

    # =========================================================================
    # find-dups 子命令
    # =========================================================================
    find_dups_parser = subparsers.add_parser(
        'find-dups',
        help='查找重复文件（xxx_N.ext 格式）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查找并列出重复文件
  python organize_files.py find-dups ~/Pictures/Organized

  # 显示文件大小
  python organize_files.py find-dups ~/Pictures/Organized --show-size

  # 只查找特定扩展名
  python organize_files.py find-dups ~/Pictures/Organized --extensions .jpg .png

  # 预览删除重复文件
  python organize_files.py find-dups ~/Pictures/Organized --delete --dry-run

  # 删除重复文件
  python organize_files.py find-dups ~/Pictures/Organized --delete --no-dry-run
        """
    )

    find_dups_parser.add_argument(
        'directory',
        help='要扫描的目录路径'
    )

    find_dups_parser.add_argument(
        '--show-size',
        action='store_true',
        help='显示文件大小'
    )

    find_dups_parser.add_argument(
        '--delete',
        action='store_true',
        help='删除重复文件（需配合 --no-dry-run 使用）'
    )

    find_dups_parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='预览模式，不实际删除文件（默认启用）'
    )

    find_dups_parser.add_argument(
        '--no-dry-run',
        action='store_true',
        help='实际执行删除操作'
    )

    find_dups_parser.add_argument(
        '--extensions',
        nargs='+',
        default=None,
        help='只查找特定扩展名的文件（如 .jpg .png）'
    )

    find_dups_parser.add_argument(
        '--report',
        type=str,
        help='生成操作报告文件（JSON 格式）'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 路由到子命令
    if args.command == 'classify':
        return cmd_classify(args)
    elif args.command == 'reorganize':
        return cmd_reorganize(args)
    elif args.command == 'find-dups':
        return cmd_find_dups(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
