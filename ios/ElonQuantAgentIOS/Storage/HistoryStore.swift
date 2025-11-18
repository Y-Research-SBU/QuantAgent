import Foundation

final class HistoryStore {
    static let shared = HistoryStore()
    private let queue = DispatchQueue(label: "HistoryStoreQueue")
    private var records: [HistoryRecord] = []
    private var url: URL {
        let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        return dir.appendingPathComponent("elonquant_history.json")
    }
    func load() {
        queue.sync {
            if let data = try? Data(contentsOf: url) {
                if let decoded = try? JSONDecoder().decode([HistoryRecord].self, from: data) {
                    records = decoded
                }
            }
        }
    }
    func all() -> [HistoryRecord] { queue.sync { records } }
    func save(record: HistoryRecord) {
        queue.sync {
            records.insert(record, at: 0)
            if let data = try? JSONEncoder().encode(records) {
                try? data.write(to: url)
            }
        }
    }
    func delete(id: UUID) {
        queue.sync {
            records.removeAll { $0.id == id }
            if let data = try? JSONEncoder().encode(records) {
                try? data.write(to: url)
            }
        }
    }
    func clear() {
        queue.sync {
            records.removeAll()
            try? FileManager.default.removeItem(at: url)
        }
    }
}