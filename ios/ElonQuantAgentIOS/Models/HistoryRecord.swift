import Foundation

struct HistoryRecord: Identifiable, Codable {
    let id: UUID
    let createdAt: Date
    let request: AnalysisRequest
    let result: AnalysisResult
}