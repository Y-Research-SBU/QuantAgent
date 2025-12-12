## 目标
- 当输入是美股代码（US equity ticker）时，优先使用 `akshare` 获取价格数据；
- 对非美股资产（指数、期货、外汇、加密货币、A/H 股等），优先使用 `yfinance`；
- 保持统一的输出列结构：`Datetime/Open/High/Low/Close/Volume`，与现有分析逻辑兼容。

## 代码位置
- 核心路由与抓取：`web_interface_new.py:578` 的 `WebTradingAnalyzer.fetch_market_data`
- akshare 抓取：`web_interface_new.py:172` 的 `MultiSourceDataFetcher.fetch_akshare_data`
- finnhub 抓取：`web_interface_new.py:404` 的 `MultiSourceDataFetcher.fetch_finnhub_data`
- 符号与周期映射：`web_interface_new.py:519` 的 `symbol_mapping`，`web_interface_new.py:553` 的 `timeframe_mapping`
- 美股/港股/A股检测参考：`coze_akshare_plugin.py:78` 的 `_detect_market`
- 现有 yfinance 实现（旧接口可复用）：`web_interface.py:75` 与 `web_interface.py:131`

## 实现步骤
1. 添加美股检测辅助方法
- 复用现有检测逻辑：调用 `coze_akshare_plugin.py:78` 的 `_detect_market(symbol)`；当返回 `us` 时视为美股。
- 若不引入跨模块依赖，则在 `web_interface_new.py` 内新增轻量检测：`^[A-Z]{1,5}$`、支持常见美股符号（字母 1–5 位）。

2. 新增 `yfinance` 抓取方法（新接口）
- 在 `MultiSourceDataFetcher` 中新增 `fetch_yfinance_data_with_datetime(symbol: str, interval: str, start_datetime: datetime, end_datetime: datetime) -> pd.DataFrame`，实现参考 `web_interface.py:131–199`：
  - 使用 `yf.download(tickers=..., start=..., end=..., interval=...)`；
  - 处理 `MultiIndex` 列、重置索引、重命名列到统一格式；
  - 返回只含所需列并确保 `Datetime` 为 `datetime` 类型。
- 或保留同签名的 `fetch_yfinance_data(...)` 并在 `fetch_market_data` 里转换日期为字符串（参考 `web_interface.py:75–129`）。

3. 改造数据源路由（核心变更）
- 修改 `WebTradingAnalyzer.fetch_market_data`（`web_interface_new.py:578–603`）：
  - 检测 `symbol` 是否为美股：
    - 是美股：按 `symbol_mapping['akshare']` 与 `timeframe_mapping['akshare']` 调用 `fetch_akshare_data(...)`；
    - 失败回退到 `yfinance`：使用 `symbol_mapping['yfinance']` 与 `timeframe_mapping['yfinance']` 调用新建的 `fetch_yfinance_data_with_datetime(...)`。
  - 非美股：直接按 `yfinance` 路由；
    - 如 `yfinance` 返回空，可选回退到 `akshare`（当为 `cn/hk` 数字代码时更可能成功）。
- 移除当前默认的 `akshare → finnhub` 回退链，改为条件分支路由（满足你的指令）。如需保留 `finnhub` 作为第三级兜底，可在两条分支末尾追加（可选）。

4. 保持映射与周期一致
- 使用既有映射：`web_interface_new.py:519` 的 `symbol_mapping['yfinance']`（如 `SPX → ^GSPC`、`CL → CL=F`、`VIX → ^VIX`），以及 `web_interface_new.py:553` 的 `timeframe_mapping['yfinance']`。
- 对美股使用 `akshare` 时，符号基本直接用输入（已有 `fetch_akshare_data` 的美股分支）。

## 验证方案
- 示例用例：
  - 美股：`AAPL`、`MSFT`、`NVDA`（应走 `akshare`，失败时走 `yfinance`）。
  - 指数/期货：`SPX`、`VIX`、`CL`（应走 `yfinance`，映射到 `^GSPC`、`^VIX`、`CL=F`）。
  - A股/港股：`000300`、`510300`、`hk00700`/`700`（应走 `yfinance` 优先，必要时回退 `akshare`）。
- 校验输出列与时间范围：确保返回包含 `Datetime/Open/High/Low/Close/Volume`，并在 `run_analysis` 中不报缺列错误（`web_interface_new.py:617–627`）。

## 风险与处理
- 美股符号的特殊字符（如 `BRK.B`）在 `akshare` 支持有限：这类符号可能直接走 `yfinance`；检测规则可扩展为更严格或白名单。
- `yfinance` 部分资产可能速率限制或空返回：保留针对 `cn/hk` 的回退到 `akshare` 以提升鲁棒性。
- `.env` 中的默认数据源注释无需改动；当前代码未使用 `DATA_SOURCE` 环境变量，路由为硬编码逻辑变更。

## 交付内容
- 新增 `MultiSourceDataFetcher.fetch_yfinance_data_with_datetime` 方法；
- 调整 `WebTradingAnalyzer.fetch_market_data` 的路由逻辑与回退顺序；
- 复用/轻量实现美股检测；
- 不改动分析管线和输出格式。