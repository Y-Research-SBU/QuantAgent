import Foundation

final class IndicatorEngine {
    func sma(_ values: [Double], period: Int) -> [Double] {
        guard period > 0, values.count >= period else { return [] }
        var out: [Double] = []
        var sum = values[0..<period].reduce(0, +)
        out.append(sum / Double(period))
        var i = period
        while i < values.count {
            sum += values[i]
            sum -= values[i - period]
            out.append(sum / Double(period))
            i += 1
        }
        return out
    }
    func ema(_ values: [Double], period: Int) -> [Double] {
        guard period > 0, !values.isEmpty else { return [] }
        let k = 2.0 / (Double(period) + 1.0)
        var out: [Double] = []
        var prev = values[0]
        out.append(prev)
        for i in 1..<values.count {
            let v = values[i] * k + prev * (1.0 - k)
            out.append(v)
            prev = v
        }
        return out
    }
    func rsi(_ closes: [Double], period: Int) -> [Double] {
        guard period > 0, closes.count > period else { return [] }
        var gains: [Double] = []
        var losses: [Double] = []
        for i in 1..<closes.count {
            let diff = closes[i] - closes[i - 1]
            gains.append(max(0, diff))
            losses.append(max(0, -diff))
        }
        let avgGain = sma(gains, period: period)
        let avgLoss = sma(losses, period: period)
        let n = min(avgGain.count, avgLoss.count)
        guard n > 0 else { return [] }
        var out: [Double] = []
        for i in 0..<n {
            let ag = avgGain[i]
            let al = avgLoss[i]
            if al == 0 { out.append(100) } else {
                let rs = ag / al
                out.append(100 - (100 / (1 + rs)))
            }
        }
        return out
    }
    func macd(_ closes: [Double], fast: Int = 12, slow: Int = 26, signal: Int = 9) -> (macd: [Double], signal: [Double], hist: [Double]) {
        let emaFast = ema(closes, period: fast)
        let emaSlow = ema(closes, period: slow)
        let n = min(emaFast.count, emaSlow.count)
        guard n > 0 else { return ([], [], []) }
        var diff: [Double] = []
        for i in 0..<n { diff.append(emaFast[i + (emaFast.count - n)] - emaSlow[i + (emaSlow.count - n)]) }
        let sig = ema(diff, period: signal)
        let m = min(diff.count, sig.count)
        var hist: [Double] = []
        for i in 0..<m { hist.append(diff[i + (diff.count - m)] - sig[i + (sig.count - m)]) }
        return (diff, sig, hist)
    }
    func bollinger(_ closes: [Double], period: Int = 20, mult: Double = 2.0) -> (mid: [Double], upper: [Double], lower: [Double]) {
        guard period > 0, closes.count >= period else { return ([], [], []) }
        var mids = sma(closes, period: period)
        var uppers: [Double] = []
        var lowers: [Double] = []
        let start = closes.count - mids.count
        for i in 0..<mids.count {
            let window = Array(closes[(start + i - period + 1)...(start + i)])
            let mean = mids[i]
            let variance = window.map { ($0 - mean) * ($0 - mean) }.reduce(0, +) / Double(window.count)
            let std = sqrt(variance)
            uppers.append(mean + mult * std)
            lowers.append(mean - mult * std)
        }
        return (mids, uppers, lowers)
    }
    func linearRegressionSlope(_ values: [Double], period: Int) -> [Double] {
        guard period > 1, values.count >= period else { return [] }
        var out: [Double] = []
        let xs = (0..<period).map { Double($0) }
        let xMean = xs.reduce(0, +) / Double(period)
        let xVar = xs.map { ($0 - xMean) * ($0 - xMean) }.reduce(0, +)
        var i = 0
        while i + period <= values.count {
            let window = Array(values[i..<(i + period)])
            let yMean = window.reduce(0, +) / Double(period)
            let cov = zip(xs, window).map { ($0 - xMean) * ($1 - yMean) }.reduce(0, +)
            out.append(cov / xVar)
            i += 1
        }
        return out
    }
}