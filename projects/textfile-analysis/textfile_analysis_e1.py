# -*- coding: utf-8 -*-
# 定义文件编码，解决中文乱码
import sys
import collections
import string
import jieba
import re

def main():
    # 校验命令行参数，必须传入1个txt文件路径
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} file.txt")
        return
    file_path = sys.argv[1]

    # 内置中文停用词列表，可自行扩充
    stop_words = {"的", "了", "是", "我", "你", "他", "她", "它", "有", "和", "在", "不", "都", "就", "而", "及", "与", "之", "也"}

    try:
        # 读取完整文本
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read()
    except FileNotFoundError:
        print("文件不存在，请检查路径！")
        return
    except Exception as e:
        print(f"读取文件失败：{e}")
        return

    # 1. 准备所有中英文标点，批量删除
    all_punc = string.punctuation + "，。、；：？！‘’“”（）《》【】……——"
    del_punc = str.maketrans("", "", all_punc)
    pure_text = data.translate(del_punc)

    # 2. jieba精确分词
    raw_word_list = jieba.lcut(pure_text)

    # 3. 过滤：空字符 + 停用词
    word_filtered = []
    chinese_char_total = 0   # 纯汉字总数量
    english_word_total = 0   # 英文单词总数量
    # 正则匹配汉字、英文字母
    re_chinese = re.compile(r'[\u4e00-\u9fff]')
    re_english = re.compile(r'^[a-zA-Z]+$')

    for word in raw_word_list:
        word_strip = word.strip()
        # 跳过空字符串、停用词
        if not word_strip or word_strip in stop_words:
            continue
        word_filtered.append(word_strip)

        # 分别统计汉字、英文单词
        if re_chinese.fullmatch(word_strip):
            chinese_char_total += 1
        elif re_english.fullmatch(word_strip):
            english_word_total += 1

    # 4. 词频统计、自动降序
    word_counter = collections.Counter(word_filtered)
    all_word_items = word_counter.most_common()
    total_words = sum(cnt for _, cnt in all_word_items)
    unique_words = len(word_counter)

    # 5. 控制台打印汇总信息
    print("==========文本统计汇总==========")
    print(f"过滤停用词后总词汇量：{total_words}")
    print(f"不重复独立词汇数：{unique_words}")
    print(f"纯汉字词语总数：{chinese_char_total}")
    print(f"纯英文单词总数：{english_word_total}")
    print("\n==========TOP5高频词汇==========")
    for word, count in all_word_items[:5]:
        print(f"{word},{count}")

    # 6. 全部词频写入 word_result.txt
    try:
        with open("word_result.txt", "w", encoding="utf-8") as out_file:
            out_file.write("词语,出现次数\n")
            for word, count in all_word_items:
                out_file.write(f"{word},{count}\n")
        print("\n全部词频已完整导出至 word_result.txt")
    except Exception as e:
        print(f"写入结果文件失败：{e}")

if __name__ == "__main__":
    main()