# -*- coding: utf-8 -*-
import csv
import hashlib
import os
import argparse
from typing import Dict, List, Tuple

# ===================== 常量统一管理 =====================
LOG_FILE_NAME = "duplicate_log.csv"
CSV_HEADER = ["原始文件路径", "重复删除文件路径"]
SKIP_SUFFIX = (".py", ".csv")
DEFAULT_CHUNK_SIZE = 4096

# Windows终端开启彩色与UTF8
if os.name == "nt":
    os.system("chcp 65001 >nul")
    os.system("reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1")

# 颜色内联常量（不定义函数，满足你之前需求）
COLOR_ERR = "\033[31m"
COLOR_WARN = "\033[33m"
COLOR_INFO = "\033[34m"
COLOR_SUCC = "\033[32m"
COLOR_GRAY = "\033[90m"
COLOR_RESET = "\033[0m"


def get_file_md5(file_path: str, chunk_size: int) -> str:
    """分块计算文件MD5哈希值"""
    md5_obj = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            md5_obj.update(chunk)
    return md5_obj.hexdigest()


def scan_dir(target_dir: str, recursive: bool, chunk_size: int) -> List[Tuple[str, int]]:
    """扫描目录，返回(文件路径, 文件大小)列表，过滤空文件、指定后缀"""
    file_list = []
    for entry in os.scandir(target_dir):
        if entry.is_dir(follow_symlinks=False):
            if recursive:
                file_list.extend(scan_dir(entry.path, recursive, chunk_size))
            continue
        # 过滤空文件、指定后缀
        file_size = entry.stat().st_size
        if file_size == 0 or entry.path.endswith(SKIP_SUFFIX):
            continue
        file_list.append((entry.path, file_size))
    return file_list


def main():
    parser = argparse.ArgumentParser(
        description="重复文件清理工具：扫描目录，删除内容完全一样的重复文件",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("target_dir", help="待扫描的目标文件夹路径")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="预览模式，只展示重复项，不会真实删除文件",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="递归扫描所有子文件夹内文件"
    )
    parser.add_argument(
        "--log-path",
        default=LOG_FILE_NAME,
        help=f"自定义日志CSV输出路径，默认：{LOG_FILE_NAME}"
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"文件读取分块大小，默认 {DEFAULT_CHUNK_SIZE}"
    )
    parser.add_argument("-v", "--version", action="version", version="Duplicate Remover v1.0")
    args = parser.parse_args()

    target_dir = args.target_dir
    preview_mode = args.preview
    recursive = args.recursive
    log_path = args.log_path
    chunk_size = args.chunk

    # 校验目录合法性
    if not os.path.isdir(target_dir):
        print(f"{COLOR_ERR}[✖] 错误：传入的路径不是有效文件夹 {COLOR_RESET}")
        return

    # key:文件大小, value: {md5: 原始文件路径}
    size_group_map: Dict[int, Dict[str, str]] = {}
    log_rows: List[List[str]] = []
    del_count = 0

    print(f"{COLOR_GRAY}============================================={COLOR_RESET}")
    print(f"{COLOR_INFO}[ℹ] 开始扫描目录：{target_dir} {'(递归模式)' if recursive else ''}{COLOR_RESET}")

    all_files = scan_dir(target_dir, recursive, chunk_size)
    print(f"{COLOR_INFO}[ℹ] 共读取待校验文件：{len(all_files)} 个{COLOR_RESET}")

    for full_path, file_size in all_files:
        try:
            # 按文件大小分组，大小不同直接跳过哈希计算，提速
            if file_size not in size_group_map:
                size_group_map[file_size] = {}
            md5_map = size_group_map[file_size]

            md5_val = get_file_md5(full_path, chunk_size)
            if md5_val not in md5_map:
                md5_map[md5_val] = full_path
            else:
                original_file = md5_map[md5_val]
                log_rows.append([original_file, full_path])
                del_count += 1
                if preview_mode:
                    print(f"{COLOR_INFO}[ℹ]【预览】原件：{original_file} 待删副本：{full_path}{COLOR_RESET}")
                else:
                    os.remove(full_path)
                    print(f"{COLOR_SUCC}[✔]【已删除】副本：{full_path} 保留原件：{original_file}{COLOR_RESET}")
        except PermissionError:
            print(f"{COLOR_ERR}[✖] 权限不足，无法读取：{full_path}{COLOR_RESET}")
        except OSError as e:
            print(f"{COLOR_ERR}[✖] 文件访问异常 {full_path}: {str(e)}{COLOR_RESET}")

    # 写入CSV日志，捕获写入异常
    try:
        with open(log_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
            writer.writerows(log_rows)
        print(f"\n{COLOR_SUCC}[✔] 重复记录已导出至 {log_path}{COLOR_RESET}")
    except IOError as e:
        print(f"\n{COLOR_ERR}[✖] 日志文件写入失败：{str(e)}{COLOR_RESET}")

    # 汇总输出
    print(f"{COLOR_GRAY}============================================={COLOR_RESET}")
    print(f"{COLOR_INFO}[ℹ] 唯一文件数量：{sum(len(md5s) for md5s in size_group_map.values())}{COLOR_RESET}")
    print(f"{COLOR_INFO}[ℹ] 检测到重复文件总数：{del_count}{COLOR_RESET}")
    if preview_mode:
        print(f"{COLOR_WARN}[⚠] 当前为预览模式，未执行真实删除操作{COLOR_RESET}")
    print(f"{COLOR_GRAY}============================================={COLOR_RESET}")


if __name__ == "__main__":
    main()