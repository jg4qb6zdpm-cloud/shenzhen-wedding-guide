# 维护工具

本目录只服务于文档维护。**读者不需要运行这里的任何脚本**；直接打开根目录的
[深圳备婚指南.md](../深圳备婚指南.md) 或 [docs/](../docs/README.md) 即可。

| 脚本 | 作用 | 输出 |
|---|---|---|
| [`build_master_md.py`](build_master_md.py) | 按 `docs/manifest.json` 拼装单文件版 | 根目录 `深圳备婚指南.md` |
| [`check_markdown.py`](check_markdown.py) | 校验表格、标题、章节结构、链接、版本 | 失败时退出码 1 |

## 环境

- Python 3.10 及以上
- 无第三方依赖

## 常用命令

在项目根目录执行：

```powershell
python tools/build_master_md.py
python tools/check_markdown.py
```

先构建，再校验。校验失败时逐条修复，不要跳过。

## manifest 是唯一元数据源

`docs/manifest.json` 同时决定：

- 单文件版的标题、副标题、版本、资料截止日、适用对象；
- 章节顺序与收录范围；
- 构建时的锚点命名（`ch00`–`ch09`、`appendix-a`–`appendix-e`）。

新增、删除或重命名章节时，必须同步修改 `files` 数组，否则校验会失败。

## 构建做了什么

1. 读取 manifest 元数据，生成封面与文档信息。
2. 解析每章的一级标题，生成“全书目录”。
3. 剥离各章的 `<!-- nav:start -->…<!-- nav:end -->` 阅读导航，避免单文件里出现断链。
4. 为每章注入 `<a id="…"></a>` 锚点，供目录跳转。
5. 按 manifest 顺序拼接，写入根目录 `深圳备婚指南.md`。

> 不要手工编辑 `深圳备婚指南.md`。它每次构建都会被覆盖，改动请落在 `docs/` 源文件。
