import SwiftUI

struct HistoryView: View {
    @State private var records: [HistoryRecord] = []
    var body: some View {
        List {
            ForEach(records) { r in
                NavigationLink(destination: ResultView(result: r.result)) {
                    VStack(alignment: .leading) {
                        Text(r.request.asset.displayName)
                        Text(r.createdAt.formatted()).font(.caption).foregroundColor(.secondary)
                    }
                }
            }
            .onDelete(perform: delete)
        }
        .navigationTitle("History")
        .toolbar {
            Button(action: clear) { Text("Clear") }
        }
        .onAppear {
            HistoryStore.shared.load()
            records = HistoryStore.shared.all()
        }
    }
    private func delete(at offsets: IndexSet) {
        for i in offsets { HistoryStore.shared.delete(id: records[i].id) }
        records = HistoryStore.shared.all()
    }
    private func clear() {
        HistoryStore.shared.clear()
        records = []
    }
}