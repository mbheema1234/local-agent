import Foundation
import Observation

@Observable
final class ChatViewModel {
    var messages: [Message] = []
    var inputText: String = ""
    var isLoading: Bool = false
    var errorMessage: String? = nil
    var availableTools: [String] = []
    var connectionStatus: ConnectionStatus = .unknown

    enum ConnectionStatus {
        case unknown, connected(String), disconnected(String)

        var label: String {
            switch self {
            case .unknown: return "—"
            case .connected(let model): return model
            case .disconnected: return "Offline"
            }
        }

        var isConnected: Bool {
            if case .connected = self { return true }
            return false
        }
    }

    private let service = AgentService.shared

    // Build history from current messages (user/assistant pairs only)
    private func currentHistory() -> [Message] {
        messages
    }

    func sendMessage(settings: AppSettings) async {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isLoading else { return }

        inputText = ""
        errorMessage = nil

        let userMsg = Message(role: .user, content: text)
        messages.append(userMsg)
        isLoading = true

        defer { isLoading = false }

        do {
            let response = try await service.sendMessage(text, history: currentHistory().dropLast(), settings: settings)
            let toolCalls = response.toolCalls.map { tc in
                ToolCallRecord(name: tc.name, arguments: tc.arguments, result: tc.result)
            }
            let assistantMsg = Message(role: .assistant, content: response.response, toolCalls: toolCalls)
            messages.append(assistantMsg)
        } catch {
            errorMessage = error.localizedDescription
            messages.removeLast() // remove the user message on failure
            inputText = text      // restore what they typed
        }
    }

    func checkConnection(settings: AppSettings) async {
        do {
            let health = try await service.checkHealth(settings: settings)
            connectionStatus = .connected(health.model)
            availableTools = health.tools
        } catch {
            connectionStatus = .disconnected(error.localizedDescription)
        }
    }

    func clearConversation() {
        messages = []
        errorMessage = nil
    }
}
