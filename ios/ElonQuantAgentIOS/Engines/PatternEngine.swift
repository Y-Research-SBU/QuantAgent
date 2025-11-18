import Foundation

final class PatternEngine {
    func detectEngulfing(_ ohlcv: [OHLCV]) -> [Bool] {
        guard ohlcv.count >= 2 else { return [] }
        var out: [Bool] = []
        for i in 1..<ohlcv.count {
            let p = ohlcv[i - 1]
            let c = ohlcv[i]
            let prevBull = p.close > p.open
            let prevBear = p.close < p.open
            let curBull = c.close > c.open
            let curBear = c.close < c.open
            let bullEngulf = prevBear && curBull && c.open <= p.close && c.close >= p.open
            let bearEngulf = prevBull && curBear && c.open >= p.close && c.close <= p.open
            out.append(bullEngulf || bearEngulf)
        }
        return out
    }
    func detectHammer(_ ohlcv: [OHLCV]) -> [Bool] {
        guard !ohlcv.isEmpty else { return [] }
        var out: [Bool] = []
        for c in ohlcv {
            let body = abs(c.close - c.open)
            let lower = c.open < c.close ? c.open - c.low : c.close - c.low
            let upper = c.high - max(c.open, c.close)
            let cond = lower > body * 2.0 && upper < body
            out.append(cond)
        }
        return out
    }
}