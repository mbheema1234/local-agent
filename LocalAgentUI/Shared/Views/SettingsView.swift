import SwiftUI

struct SettingsView: View {
    @Environment(AppSettings.self) private var settings
    @State private var draftURL: String = ""
    @State private var healthResult: String? = nil
    @State private var isTesting = false

    var body: some View {
        @Bindable var settings = settings

        Form {
            Section("Server") {
                LabeledContent("URL") {
                    TextField("http://127.0.0.1:8765", text: $settings.serverURL)
                        #if os(iOS)
                        .keyboardType(.URL)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                        #endif
                }

                HStack {
                    Button(isTesting ? "Testing…" : "Test Connection") {
                        Task { await testConnection() }
                    }
                    .disabled(isTesting)

                    if let result = healthResult {
                        Text(result)
                            .font(.caption)
                            .foregroundStyle(result.hasPrefix("✓") ? .green : .red)
                    }
                }
            }

            Section("Note") {
                Text("Start the Python server on your Mac/PC:\n  python api.py\n\nTo connect from iPhone, use your machine's local IP instead of 127.0.0.1 and run:\n  python api.py --host 0.0.0.0")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Settings")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .frame(minWidth: 340, minHeight: 280)
        .onAppear { draftURL = settings.serverURL }
    }

    private func testConnection() async {
        isTesting = true
        healthResult = nil
        do {
            let health = try await AgentService.shared.checkHealth(settings: settings)
            healthResult = "✓ Connected · \(health.tools.count) tools"
        } catch {
            healthResult = "✗ \(error.localizedDescription)"
        }
        isTesting = false
    }
}
