import Foundation

struct FinalDecision: Codable, Hashable {
    let decision: String
    let riskRewardRatio: String
    let forecastHorizon: String
    let justification: String
}

struct AnalysisResult: Codable {
    let assetName: String
    let timeframe: String
    let dataLength: Int
    let technicalIndicators: String
    let patternAnalysis: String
    let trendAnalysis: String
    let finalDecision: FinalDecision
}