import Foundation

struct OHLCV: Identifiable, Codable {
    let id: UUID
    let datetime: Date
    let open: Double
    let high: Double
    let low: Double
    let close: Double
    let volume: Double
    init(datetime: Date, open: Double, high: Double, low: Double, close: Double, volume: Double) {
        self.id = UUID()
        self.datetime = datetime
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
    }
}