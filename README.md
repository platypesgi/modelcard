# modelcard

**给模型写一张说得清来源的说明卡。**

`modelcard` —— 生成模型说明卡模板，把来源、适用范围与已知限制写成必须填的字段。

- 零依赖，Python 3.10+ 标准库即可运行
- 单文件，`modelcard.py` 拷走就能用
- 不联网、不写文件

<!-- ipos:install -->
## 安装

零依赖，Python 3.10+ 即可：

```bash
pip install platypesgi-modelcard
```

装完直接用命令名调用：

```bash
modelcard --help
```

也可以不用安装，直接把 `modelcard.py` 拷走用——它只依赖标准库。

## 为什么需要它

模型卡工具多给一个空模板；modelcard 把「不知道」也做成合法答案，并记录每个结论的来源。

它遵守下面几条自己定的规矩：

1. **「不知道」是合法答案**。宁可让卡片半空，也不填满无法核对的漂亮话。
2. **来源是必填字段**。每个结论要么给来源，要么明确写「不知道」。
3. **指标要写版本**。同名指标在不同评测里未必指同一件事。

## 用法

```bash
python modelcard.py --model gpt-4o --use-case "客户问答" --out card.md
python modelcard.py --init --out card.md
```

加 `--json` 可以拿到机器可读的结果，便于接到流水线里。

## 已知局限

- 「说得清」靠占位符与套话模式识别，判断不了内容真伪。
- 不生成实验，也不跑评测，只审计你写好的卡片。
- 「不知道」被当作合法答案，不追求把字段填满。

## 跑测试

```bash
python test_modelcard.py
```

测试用独立的断言与临时数据，不污染工作目录。

## 来源与参考

- Python 标准库文档：<https://docs.python.org/3/>
- GitHub 仓库：<https://github.com/platypesgi/modelcard>

---

## 关于作者

platypesgi 做模型文档的来源标注相关的问题。这个工具先替你回答一个具体问题，再谈别的。

- 个人主页：<https://platypesgi.github.io>
- 仓库：<https://github.com/platypesgi/modelcard>

## 许可

MIT，见 [LICENSE](LICENSE)。
