import SwiftUI

struct HomeView: View {
    @State private var asset: Asset = Asset.defaults.first!
    @State private var timeframe: Timeframe = .h1
    @State private var startDate: Date = Calendar.current.date(byAdding: .day, value: -30, to: Date()) ?? Date()
    @State private var endDate: Date = Date()
    @State private var generateCharts: Bool = true
    @State private var strategy: String = "high_frequency"
    @State private var isLoading: Bool = false
    @State private var result: AnalysisResult?
    @State private var errorText: String?
    var body: some View {
        NavigationStack {
            Form {
                Picker("Asset", selection: $asset) {
                    ForEach(Asset.defaults) { a in Text(a.displayName).tag(a) }
                }
                Picker("Timeframe", selection: $timeframe) {
                    ForEach(Timeframe.allCases) { t in Text(t.rawValue).tag(t) }
                }
                DatePicker("Start", selection: $startDate, displayedComponents: [.date])
                DatePicker("End", selection: $endDate, displayedComponents: [.date])
                Toggle("Generate Charts", isOn: $generateCharts)
                Picker("Strategy", selection: $strategy) {
                    Text("high_frequency").tag("high_frequency")
                    Text("trend").tag("trend")
                    Text("swing").tag("swing")
                }
                if let result = result {
                    NavigationLink(destination: ResultView(result: result)) { Text("View Result") }
                }
                if let errorText = errorText { Text(errorText).foregroundColor(.red) }
                Button(action: analyze) { Text(isLoading ? "Analyzing..." : "Analyze") }.disabled(isLoading)
            }
            .navigationTitle("ElonQuantAgent")
            .toolbar {
                NavigationLink(destination: HistoryView()) { Image(systemName: "clock") }
                NavigationLink(destination: SettingsView()) { Image(systemName: "gearshape") }
            }
        }
    }
    private func analyze() {
        isLoading = true
        errorText = nil
        let api = MarketAPI()
        api.fetchOHLCV(asset: asset, timeframe: timeframe, start: startDate, end: endDate) { res in
            DispatchQueue.main.async {
                switch res {
                case .failure(let err):
                    errorText = err.localizedDescription
                    isLoading = false
                case .success(let ohlcv):
                    let closes = ohlcv.map { $0.close }
                    let ind = IndicatorEngine()
                    let rsi = ind.rsi(closes, period: 14)
                    let macdRes = ind.macd(closes)
                    let slope = ind.linearRegressionSlope(closes, period: 20)
                    let pat = PatternEngine()
                    let engulf = pat.detectEngulfing(ohlcv)
                    let hammer = pat.detectHammer(ohlcv)
                    let decEng = DecisionEngine()
                    let dec = decEng.decide(assetName: asset.displayName, timeframe: timeframe.rawValue, closes: closes, signals: .init(rsi: rsi, macd: macdRes.macd, macdSignal: macdRes.signal, slope: slope, engulfing: engulf, hammer: hammer))
                    let tech = "RSI: \(rsi.last ?? 0), MACD: \(macdRes.macd.last ?? 0)"
                    let patt = "Engulfing: \(engulf.suffix(3).contains(true)), Hammer: \(hammer.suffix(3).contains(true))"
                    let trend = "Slope: \(slope.last ?? 0)"
                    let resObj = AnalysisResult(assetName: asset.displayName, timeframe: timeframe.rawValue, dataLength: ohlcv.count, technicalIndicators: tech, patternAnalysis: patt, trendAnalysis: trend, finalDecision: dec)
                    result = resObj
                    let req = AnalysisRequest(asset: asset, timeframe: timeframe, startDate: startDate, endDate: endDate, generateCharts: generateCharts, tradingStrategy: strategy)
                    let record = HistoryRecord(id: UUID(), createdAt: Date(), request: req, result: resObj)
                    HistoryStore.shared.save(record: record)
                    isLoading = false
                }
            }
        }
    }
}