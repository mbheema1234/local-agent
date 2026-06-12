import SwiftUI

@Observable
final class AppSettings {
    var serverURL: String {
        didSet { UserDefaults.standard.set(serverURL, forKey: "serverURL") }
    }

    init() {
        self.serverURL = UserDefaults.standard.string(forKey: "serverURL") ?? "http://127.0.0.1:8765"
    }
}

@main
struct LocalAgentApp: App {
    @State private var settings = AppSettings()

    var body: some Scene {
        WindowGroup {
            NavigationStack {
                ChatView()
            }
            .environment(settings)
        }
        #if os(macOS)
        .windowStyle(.titleBar)
        .windowToolbarStyle(.unified(showsTitle: true))
        .defaultSize(width: 700, height: 700)

        Settings {
            NavigationStack {
                SettingsView()
            }
            .environment(settings)
        }
        #endif
    }
}
