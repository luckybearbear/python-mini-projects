1. 脚本包含以下功能：
- 下载并解析正确的 OPML 文件。
- 并发抓取订阅源，筛选最近 24 小时的文章。
- 按论文、工具、产业、资讯分类。
- 生成中文 Markdown 日报，保留文章标题、原文链接和 RSS 摘要。
- 去重，并单独记录无法获取的订阅源及没有有效发布时间的条目。
- 保存日报到指定目录。

2. 在 Windows 本机运行
先下载脚本，打开 PowerShell，进入脚本所在目录，执行：
```shell
python -m pip install feedparser
```
3. 然后运行：
```shell
python .\ai_rss_daily.py
```

默认输出目录是：
D:\devloper\project\myselfProject\kb\📥 Inbox
成功运行后，会生成类似这样的文件：
2026-10-15-AI日报.md
如果需要指定其他 OPML 文件或输出目录，也可以运行：
python .\ai_rss_daily.py `
  --opml-url "https://raw.githubusercontent.com/xiangyugongzuoliu/awesome-rss-feeds/main/feeds/ai-blogs-cn.opml" `
  --output-dir "D:\devloper\project\myselfProject\kb\📥 Inbox"

4. 异常处理
### SSLError: [ASN1: NOT_ENOUGH_DATA] not enough data (_ssl.c:4040)
```shell
conda activate data_env
conda update openssl ca-certificates certifi
```