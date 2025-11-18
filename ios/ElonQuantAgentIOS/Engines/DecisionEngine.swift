import Foundation

final class DecisionEngine {
    struct Signals {
        let rsi: [Double]
        let macd: [Double]
        let macdSignal: [Double]
        let slope: [Double]
        let engulfing: [Bool]
        let hammer: [Bool]
    }
    func decide(assetName: String, timeframe: String, closes: [Double], signals: Signals) -> FinalDecision {
        let n = closes.count
        let lastRSI = signals.rsi.last ?? 50
        let lastMACD = signals.macd.last ?? 0
        let lastSignal = signals.macdSignal.last ?? 0
        let lastSlope = signals.slope.last ?? 0
        let recentEngulf = signals.engulfing.suffix(3).contains(true)
        let recentHammer = signals.hammer.suffix(3).contains(true)
        var decision = "HOLD"
        if lastRSI < 30 && lastMACD > lastSignal && lastSlope > 0 { decision = "BUY" }
        if lastRSI > 70 && lastMACD < lastSignal && lastSlope < 0 { decision = "SELL" }
        if recentEngulf && lastSlope > 0 { decision = "BUY" }
        if recentHammer && lastSlope < 0 { decision = "SELL" }
        let rr = decision == "BUY" ? "2:1" : decision == "SELL" ? "1.5:1" : "1:1"
        let horizon = timeframe
        let justification = "Signals combined"
        return FinalDecision(decision: decision, riskRewardRatio: rr, forecastHorizon: horizon, justification: justification)
    }
}