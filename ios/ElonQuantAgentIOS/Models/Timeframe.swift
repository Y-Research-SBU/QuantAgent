import Foundation

enum Timeframe: String, CaseIterable, Codable, Identifiable {
    case m1 = "1m"
    case m5 = "5m"
    case m15 = "15m"
    case m30 = "30m"
    case h1 = "1h"
    case h4 = "4h"
    case d1 = "1d"
    case w1 = "1w"
    case M1 = "1M"
    var id: String { rawValue }
}