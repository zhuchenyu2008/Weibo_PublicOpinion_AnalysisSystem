# LLM 接入配置统一说明

> 适用于 2024-09 之后的提交：`feat: unify openai-compatible llm configuration`

本次重构针对多 Agent 的大模型接入方式进行了“统一为 OpenAI 兼容格式”的整理。该整理 **不会改变默认模型、默认 API 地址或既有的调用逻辑**，仅增加了更灵活的配置能力，确保在不同部署环境下能够通过同一套代码对接 DeepSeek、OpenAI、Kimi、Gemini 以及硅基流动的 Qwen3 服务。

## 1. 变更概览

| 模块 | 调整内容 | 对原有流程的影响 |
| --- | --- | --- |
| `config.py` | 新增 `DEFAULT_LLM_PROVIDER`、`*_MODEL`、`*_API_BASE` 等字段，保留旧的 API Key 常量，并为 Bocha 搜索保留旧常量 `BOCHA_Web_Search_API_KEY` | 默认值与旧版本完全一致，不填新字段也可继续使用原配置 |
| 各 Engine (`InsightEngine/`, `MediaEngine/`, `QueryEngine/`) | 统一通过对应的 `utils/config.py` 读取模型、Base URL、Key | 仍然可以只配置 API Key；未填写的 Base URL/Model 自动回退到旧值 |
| LLM 封装 (`llms/*.py`) | 使用官方 `openai` SDK 构造 OpenAI 兼容客户端，支持自定义 Base URL | 原有接口 `invoke(...)`、`get_model_info()` 保持不变；不需要改动业务调用代码 |
| Forum Host & 关键词优化等 Qwen3 工具 | 切换到 OpenAI 兼容客户端，并支持通过环境变量覆写 Base URL/模型 | 仍使用硅基流动的 Qwen3 模型，默认模型名与 Base URL 未改变 |

## 2. 兼容性保证

1. **默认常量未改动**：
   - DeepSeek 默认模型仍是 `deepseek-chat`，Base URL 仍是 `https://api.deepseek.com`。
   - OpenAI 默认模型仍是 `gpt-4o-mini`，Base URL 仍是 `https://api.openai.com/v1`。
   - Kimi 默认模型仍是 `kimi-k2-0711-preview`。
   - Gemini 默认 Base URL 继续指向 `https://www.chataiapi.com/v1`。
   - Qwen3 论坛主持与关键词工具仍默认指向硅基流动 `https://api.siliconflow.cn/v1`。

2. **环境变量优先级保留**：所有封装都按如下顺序解析配置：
   1. 显式传入的参数
   2. 对应的环境变量（例如 `OPENAI_API_KEY`、`DEEPSEEK_API_BASE`）
   3. `config.py` 中的常量默认值

3. **旧字段别名保留**：
   - `config.py` 中保留 `BOCHA_Web_Search_API_KEY` 以兼容旧代码。
   - 工程内未新增新的必填字段；缺省情况下会自动回退到旧常量。

4. **调用方式未变化**：
   - `BaseLLM.invoke(...)` 的签名和返回值保持不变。
   - 论坛主持人、关键词优化器、Topic Extractor 的入口函数未做行为改动，仅替换为统一客户端。

## 3. 如何自定义 API 地址与模型

在 `config.py` 中新增的字段是可选项，用于覆盖默认值：

```python
# 例如：切换 DeepSeek 到自建代理
DEEPSEEK_API_KEY = "your_deepseek_key"
DEEPSEEK_MODEL = "deepseek-reasoner"
DEEPSEEK_API_BASE = "https://your-proxy.example.com/v1"
```

也可以通过环境变量临时覆盖：

```bash
export DEEPSEEK_API_BASE="https://internal-proxy.example.com/v1"
export OPENAI_MODEL="gpt-4.1-mini"
```

不设置则沿用默认值，与旧版本保持一致。

## 4. 验证方法

1. **代码级验证**：`python -m compileall ForumEngine InsightEngine MediaEngine QueryEngine ReportEngine MindSpider/BroadTopicExtraction`
   - 该命令已在提交中执行，确保语法无误。

2. **手动冒烟**：任选一个 Engine（如 `QueryEngine`）执行原有流程：

   ```python
   from QueryEngine.llms.openai_llm import OpenAILLM
   llm = OpenAILLM()
   print(llm.get_model_info())
   ```

   若未配置 Key 会提示原有错误信息；配置完成后返回的 `model`、`api_base` 即为最终使用的参数，便于验证覆盖顺序。

## 5. 常见问题

- **是否需要修改已有业务代码？** 不需要，所有调用层接口保持不变。
- **能否继续使用旧版 `config.py`？** 可以，旧字段名全部保留，如果不关心模型/地址切换可以忽略新增字段。
- **是否影响已有任务队列或调度脚本？** 不影响，所有导入路径与类名保持一致。

如需进一步确认，可对照本说明逐项比对您部署环境中的配置；若遇到异常，请提供配置与调用日志以便排查。
