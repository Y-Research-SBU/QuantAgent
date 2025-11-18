import Foundation

struct AnalysisRequest: Codable {
    let asset: Asset
    let timeframe: Timeframe
    let startDate: Date
    let endDate: Date
    let generateCharts: Bool
    let tradingStrategy: String
}