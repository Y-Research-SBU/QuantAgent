import Foundation

final class MarketAPI {
    struct Config {
        var finnhubKey: String?
    }
    private let config: Config
    init(config: Config = Config()) {
        self.config = config
    }
    func fetchOHLCV(asset: Asset, timeframe: Timeframe, start: Date, end: Date, completion: @escaping (Result<[OHLCV], Error>) -> Void) {
        if let key = config.finnhubKey, !key.isEmpty {
            let res = resolution(for: timeframe)
            let from = Int(start.timeIntervalSince1970)
            let to = Int(end.timeIntervalSince1970)
            let symbol = asset.id
            var comps = URLComponents(string: "https://finnhub.io/api/v1/stock/candle")!
            comps.queryItems = [
                URLQueryItem(name: "symbol", value: symbol),
                URLQueryItem(name: "resolution", value: res),
                URLQueryItem(name: "from", value: String(from)),
                URLQueryItem(name: "to", value: String(to)),
                URLQueryItem(name: "token", value: key)
            ]
            let url = comps.url!
            URLSession.shared.dataTask(with: url) { data, _, error in
                if error != nil { self.fallback(asset: asset, start: start, end: end, completion: completion) ; return }
                guard let data = data else { self.fallback(asset: asset, start: start, end: end, completion: completion) ; return }
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any], (json["s"] as? String) == "ok" {
                    guard let t = json["t"] as? [Int], let o = json["o"] as? [Double], let h = json["h"] as? [Double], let l = json["l"] as? [Double], let c = json["c"] as? [Double], let v = json["v"] as? [Double] else { self.fallback(asset: asset, start: start, end: end, completion: completion) ; return }
                    var arr: [OHLCV] = []
                    let n = [t.count, o.count, h.count, l.count, c.count, v.count].min() ?? 0
                    for i in 0..<n {
                        arr.append(OHLCV(datetime: Date(timeIntervalSince1970: TimeInterval(t[i])), open: o[i], high: h[i], low: l[i], close: c[i], volume: v[i]))
                    }
                    completion(.success(arr))
                } else {
                    self.fallback(asset: asset, start: start, end: end, completion: completion)
                }
            }.resume()
            return
        }
        let calendar = Calendar.current
        var dates: [Date] = []
        var d = start
        while d <= end {
            if let weekday = calendar.dateComponents([.weekday], from: d).weekday, weekday >= 2 && weekday <= 6 {
                dates.append(d)
            }
            d = calendar.date(byAdding: .day, value: 1, to: d) ?? d.addingTimeInterval(86400)
        }
        if dates.isEmpty {
            completion(.success([]))
            return
        }
        var rng = SeededGenerator(seed: asset.id.hashValue)
        var last = Double(abs(asset.id.hashValue % 200) + 50)
        var points: [OHLCV] = []
        for date in dates {
            let ret = Double.random(in: -0.02...0.02, using: &rng)
            let price = max(1.0, last * (1.0 + ret))
            let vol = Double(Int.random(in: 1_000_000...10_000_000, using: &rng))
            let high = price * (1.0 + Double.random(in: 0.0...0.01, using: &rng))
            let low = price * (1.0 - Double.random(in: 0.0...0.01, using: &rng))
            let open = last
            let close = price
            points.append(OHLCV(datetime: date, open: open, high: high, low: low, close: close, volume: vol))
            last = price
        }
        completion(.success(points))
    }

    private func resolution(for timeframe: Timeframe) -> String {
        switch timeframe {
        case .m1: return "1"
        case .m5: return "5"
        case .m15: return "15"
        case .m30: return "30"
        case .h1: return "60"
        case .h4: return "240"
        case .d1: return "D"
        case .w1: return "W"
        case .M1: return "M"
        }
    }

    private func fallback(asset: Asset, start: Date, end: Date, completion: @escaping (Result<[OHLCV], Error>) -> Void) {
        let calendar = Calendar.current
        var dates: [Date] = []
        var d = start
        while d <= end {
            if let weekday = calendar.dateComponents([.weekday], from: d).weekday, weekday >= 2 && weekday <= 6 {
                dates.append(d)
            }
            d = calendar.date(byAdding: .day, value: 1, to: d) ?? d.addingTimeInterval(86400)
        }
        var rng = SeededGenerator(seed: asset.id.hashValue)
        var last = Double(abs(asset.id.hashValue % 200) + 50)
        var points: [OHLCV] = []
        for date in dates {
            let ret = Double.random(in: -0.02...0.02, using: &rng)
            let price = max(1.0, last * (1.0 + ret))
            let vol = Double(Int.random(in: 1_000_000...10_000_000, using: &rng))
            let high = price * (1.0 + Double.random(in: 0.0...0.01, using: &rng))
            let low = price * (1.0 - Double.random(in: 0.0...0.01, using: &rng))
            let open = last
            let close = price
            points.append(OHLCV(datetime: date, open: open, high: high, low: low, close: close, volume: vol))
            last = price
        }
        completion(.success(points))
    }
}

struct SeededGenerator: RandomNumberGenerator {
    private var state: UInt64
    init(seed: Int) { self.state = UInt64(bitPattern: Int64(seed)) ^ 0x9E3779B97F4A7C15 }
    mutating func next() -> UInt64 {
        state &+= 0x9E3779B97F4A7C15
        var z = state
        z = (z ^ (z >> 30)) &* 0xBF58476D1CE4E5B9
        z = (z ^ (z >> 27)) &* 0x94D049BB133111EB
        return z ^ (z >> 31)
    }
}