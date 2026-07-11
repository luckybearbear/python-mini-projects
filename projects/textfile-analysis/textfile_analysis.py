# -*- coding: utf-8 -*-
# 声明文件编码为utf-8，防止中文乱码

# 导入系统模块：用来获取命令行输入的文件路径
import sys
# 导入计数工具：快速统计词语、字符出现次数
import collections
# 导入字符串工具：自带英文标点符号集合
import string
# 导入中文分词库：把中文句子切割成单个词语
import jieba

# 程序主函数，所有逻辑写在这里
def main():
    # sys.argv 是命令行传入的参数列表
    # sys.argv[0] = 当前脚本文件名
    # sys.argv[1] = 用户输入的txt文件路径
    # 程序要求必须传1个文件参数，总长度应为2
    if len(sys.argv) != 2:
        # 参数数量不对，打印使用教程并退出程序
        print(f"Usage: python {sys.argv[0]} file.txt")
        return

    # 取出用户传入的文件路径
    file_path = sys.argv[1]

    try:
        # 以只读模式打开文件，编码utf-8兼容中文
        with open(file_path, "r", encoding="utf-8") as f:
            # 一次性读取文件全部文本内容存入data
            data = f.read()
    except FileNotFoundError:
        # 如果文件不存在，捕获异常并提示
        print("文件不存在")
        # 直接结束函数，不再往下执行
        return

    # ===================== 文本清洗：去除所有中英文标点 =====================
    # string.punctuation：自带所有英文标点 !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
    # 手动补充常用中文标点
    punc = string.punctuation + "，。、；：？！‘’“”（）《》【】……——"
    # 创建翻译规则：把上面所有标点全部删除
    trans = str.maketrans("", "", punc)
    # 对原文执行清洗，得到无标点纯净文本
    pure_text = data.translate(trans)

    # ===================== jieba中文分词 =====================
    # lcut：精确模式分词，返回词语列表
    # 例："我爱Python编程" → ['我','爱','Python','编程']
    word_list = jieba.lcut(pure_text)

    # ===================== 过滤无效空白词语 =====================
    # 分词后可能产生空字符串、空格，全部过滤掉
    # w.strip() 去掉词语前后空格，为空就丢弃
    word_filtered = [w for w in word_list if w.strip()]

    # ===================== 词频统计 =====================
    # Counter：统计列表里每个词语出现多少次
    counter = collections.Counter(word_filtered)
    # most_common() 自动按出现次数从高到低排序，返回[(词语,次数),...]
    word_items = counter.most_common()

    # 总词汇量：把所有词语出现次数相加
    total_words = sum(cnt for _, cnt in word_items)
    # 不重复词汇：去重后词语总数量 = Counter长度
    unique_words = len(counter)

    # ===================== 打印统计结果 =====================
    print(f"总词汇量：{total_words}")
    print(f"不重复词汇数：{unique_words}")
    print("=====词频排行=====")
    # word_items[:5] 只取前5个高频词语
    for word, count in word_items[:5]:
        # 按 词语,次数 格式输出
        print(f"{word},{count}")

# 程序入口：直接运行本脚本时执行main函数
if __name__ == "__main__":
    main()