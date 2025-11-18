import SwiftUI

struct SettingsView: View {
    @State private var finnhubKey: String = ""
    @State private var useLLM: Bool = false
    @State private var llmProvider: String = "openai"
    @State private var llmKey: String = ""
    var body: some View {
        Form {
            Section("Data Source") {
                SecureField("Finnhub API Key", text: $finnhubKey)
            }
            Section("LLM") {
                Toggle("Enable LLM", isOn: $useLLM)
                Picker("Provider", selection: $llmProvider) {
                    Text("openai").tag("openai")
                    Text("deepseek").tag("deepseek")
                    Text("volcengine").tag("volcengine")
                }
                SecureField("API Key", text: $llmKey)
            }
        }
        .navigationTitle("Settings")
    }
}