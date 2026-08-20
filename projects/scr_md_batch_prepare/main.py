"""
脚本名称：scr_md_batch_prepare.py
用途：批量预处理 Markdown，适配 Obsidian Supercharged Repetition 闪卡插件
功能：
1. 移除文档开头 --- 包裹的 YAML FrontMatter
2. 在 ### 三级标题下方插入 ? 作为问答分隔
3. 每个问答单元末尾添加 ---，并且上下保留空行分隔闪卡
4. 递归遍历文件夹全部 md，输出 xxx_out.md，不覆盖原文件
"""
import re
import os

def process_single_md(file_path: str, output_suffix: str = "_out"):
    """处理单个md文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 移除开头 --- 包裹的 frontmatter
    frontmatter_pattern = re.compile(r"^---[\s\S]*?---\n", re.MULTILINE)
    content = frontmatter_pattern.sub("", content)

    # 按 ### 三级标题分割
    parts = re.split(r"(### .+)", content)
    result_lines = []

    for part in parts:
        part = part.rstrip("\n")
        if part.startswith("### "):
            result_lines.append(part)
            result_lines.append("?")
        else:
            if part.strip():
                result_lines.append(part.strip("\n"))
                # --- 上下增加空行
                result_lines.append("")
                result_lines.append("---")
                result_lines.append("")

    final_text = "\n".join(result_lines)
    # 清理连续过多空行（避免出现多行空白）
    final_text = re.sub(r"\n{4,}", "\n\n", final_text)

    # 生成输出文件名
    dirname, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    out_filename = f"{name}{output_suffix}{ext}"
    out_path = os.path.join(dirname, out_filename)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"✅ 已处理：{file_path} -> {out_path}")


def batch_process_md(folder_path: str):
    """批量递归遍历文件夹所有md"""
    if not os.path.isdir(folder_path):
        print(f"❌ 目录不存在：{folder_path}")
        return

    md_files = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(".md"):
                md_files.append(os.path.join(root, f))

    if not md_files:
        print("⚠️ 当前目录未找到任何 .md 文件")
        return

    print(f"📂 一共找到 {len(md_files)} 个md文件，开始处理...\n")
    for md_file in md_files:
        process_single_md(md_file)
    print("\n🎉 全部文件处理完成！")


if __name__ == "__main__":
    # ===================== 配置这里 =====================
    TARGET_FOLDER = "./md_docs"
    # ====================================================
    batch_process_md(TARGET_FOLDER)