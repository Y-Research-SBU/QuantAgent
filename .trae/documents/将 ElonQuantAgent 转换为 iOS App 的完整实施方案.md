## 项目目标
- 构建纯原生 SwiftUI iOS 应用，分析流程在端侧运行，不依赖现有 Flask/后端 API。
- 保留核心能力：行情数据获取、技术指标与形态/趋势分析、结果生成与历史持久化、图表展示、可选 LLM 增强。

## 技术路线
- 前端框架：SwiftUI + Combine。
- 数据层：URLSession 直接调用公共行情 API（如 Finnhub、Yahoo 非官方端点或替代源），端侧统一处理为 OHLCV。
- 指标与分析：Swift 实现 SMA/EMA/RSI/MACD/Bollinger、线性回归趋势、基础形态识别（吞噬/锤子/顶部/突破等）。
- 图表：Apple Swift Charts（iOS 16+），支持多轴与叠加；低版本采用第三方折线图库。
- 持久化：Core Data（或 SQLite via GRDB）存储历史记录与缓存数据。
- LLM（可选）：若需文本分析增强，App 侧直接调用厂商 API（OpenAI/DeepSeek/火山方舟），Keychain 管理密钥；如需完全离线，后续引入轻量 on-device LLM（llama.cpp/MLC LLM）。

## 端侧分析管线设计
- 数据获取
  - 资产映射与时间框架（对齐现有：`1m/5m/15m/30m/1h/4h/1d/1w/1M`）。
  - 数据源优先级：Finnhub（需 Key）→ Yahoo/其他免费源；统一为 `[Datetime, Open, High, Low, Close, Volume]`。
- 指标计算
  - 基础：SMA/EMA、RSI、MACD、布林带、ATR。
  - 趋势：移动均线交叉、线性回归斜率、ADX（可选）。
- 形态检测
  - K 线形态：吞没、锤子、射击之星、三连阴/阳；区间突破/回撤模式。
- 决策引擎
  - 规则集：依据指标组合与形态信号生成 `BUY/SELL/HOLD`，并计算简版风险收益比、预测周期。
  - 可插拔策略（高频/趋势/波段）。
- 结果结构（对齐现有）：`technical_indicators`、`pattern_analysis`、`trend_analysis`、`final_decision`、图表引用。

## SwiftUI 模块划分
- Core
  - `MarketAPI`：封装数据源调用、节流与重试（Combine）。
  - `IndicatorEngine`：指标计算与形态识别。
  - `DecisionEngine`：规则决策，支持策略切换。
- Models
  - `Asset`、`Timeframe`、`OHLCV`、`AnalysisRequest`、`AnalysisResult`、`HistoryRecord`。
- Storage
  - `HistoryStore`（Core Data）：保存分析参数、摘要、详情、图表快照路径。
- Views
  - Home：资产/时间框架/日期范围/策略选择，触发分析。
  - Result：文本与图表展示，支持保存与分享。
  - History：列表/详情/删除与清理。
  - Settings：数据源 Key（Keychain）、策略默认值、外观设置。

## 安全与合规
- Keychain 存储第三方数据源/LLM 密钥；不将密钥回传至任何自建服务。
- ATS：仅允许 HTTPS；如需特殊域名，最小化例外配置。
- 隐私政策：说明仅端侧计算与外部 API 调用的范围与目的。

## 兼容性与性能
- 支持 iOS 16+（Swift Charts）；iOS 14–15 使用替代图表库。
- 指标计算在后台线程执行（GCD/OperationQueue），UI 响应流畅。
- 数据量大时分页/抽样绘制，避免阻塞主线程。

## 测试与验证
- 单元测试：指标计算（边界与精度）、形态识别、决策逻辑。
- 集成测试：数据源连通与回退、历史持久化、Keychain 读写。
- UI 测试：核心路径与异常兜底（弱网/断网）。

## 迭代计划
- W1（原型）：完成数据源封装、SMA/EMA/RSI/MACD、基础 UI；生成结果与图表。
- W2（完善）：形态检测、决策引擎、历史持久化、设置页与 Keychain；测试覆盖。
- W3（增强）：Swift Charts 交互、策略高级参数、可选 LLM 增强与完全离线模型探索。

## 交付物
- Xcode 项目（SwiftUI 原生），含模块化代码与测试。
- 指南文档：资产支持、时间框架映射、策略说明与扩展接口。
- 构建与签名配置、上架所需素材（图标/截图）。

## 需要确认
- 首批支持的资产与数据源（是否接入付费源，如 Finnhub）。
- 是否需要完全离线（不调用任何 LLM 或数据 API），或允许仅数据 API 在线、分析离线。
- 最低 iOS 版本与图表库选择（Swift Charts vs 第三方）。

确认后我将按照此方案开始实现原生端侧分析与界面，不再依赖现有后端 API。