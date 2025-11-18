import SwiftUI

struct ResultView: View {
    let result: AnalysisResult
    var body: some View {
        List {
            Section("Asset") { Text(result.assetName) }
            Section("Timeframe") { Text(result.timeframe) }
            Section("Indicators") { Text(result.technicalIndicators) }
            Section("Pattern") { Text(result.patternAnalysis) }
            Section("Trend") { Text(result.trendAnalysis) }
            Section("Decision") {
                Text(result.finalDecision.decision)
                Text(result.finalDecision.riskRewardRatio)
                Text(result.finalDecision.forecastHorizon)
                Text(result.finalDecision.justification)
            }
        }
        .navigationTitle("Result")
    }
}