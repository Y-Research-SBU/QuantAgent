import Foundation

struct Asset: Identifiable, Hashable, Codable {
    let id: String
    let displayName: String
}

extension Asset {
    static let defaults: [Asset] = [
        Asset(id: "SPX", displayName: "S&P 500"),
        Asset(id: "BTC", displayName: "Bitcoin"),
        Asset(id: "AAPL", displayName: "Apple"),
        Asset(id: "TSLA", displayName: "Tesla"),
        Asset(id: "QQQ", displayName: "Invesco QQQ"),
        Asset(id: "GC", displayName: "Gold")
    ]
}