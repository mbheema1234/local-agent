import Foundation

enum AgentServiceError: LocalizedError {
    case notConfigured
    case serverUnreachable
    case badResponse(String)

    var errorDescription: String? {
        switch self {
        case .notConfigured: return "Server URL not configured. Open Settings."
        case .serverUnreachable: return "Cannot reach the agent server. Is it running?"
        case .badResponse(let msg): return "Server error: \(msg)"
        }
    }
}

@MainActor
final class AgentService: ObservableObject {
    static let shared = AgentService()

    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }()

    private let encoder: JSONEncoder = {
        let e = JSONEncoder()
        return e
    }()

    func baseURL(from settings: AppSettings) -> URL? {
        URL(string: settings.serverURL)
    }

    func sendMessage(_ text: String, history: [Message], settings: AppSettings) async throws -> ChatResponse {
        guard let base = baseURL(from: settings) else { throw AgentServiceError.notConfigured }
        let url = base.appendingPathComponent("chat")

        let historyPayload = history.map { msg in
            HistoryMessage(role: msg.role.rawValue, content: msg.content)
        }
        let body = ChatRequest(message: text, history: historyPayload)

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 120
        request.httpBody = try encoder.encode(body)

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw AgentServiceError.serverUnreachable
        }

        guard let http = response as? HTTPURLResponse else {
            throw AgentServiceError.serverUnreachable
        }
        guard http.statusCode == 200 else {
            let detail = String(data: data, encoding: .utf8) ?? "unknown"
            throw AgentServiceError.badResponse("HTTP \(http.statusCode): \(detail)")
        }

        do {
            return try decoder.decode(ChatResponse.self, from: data)
        } catch {
            throw AgentServiceError.badResponse(error.localizedDescription)
        }
    }

    func checkHealth(settings: AppSettings) async throws -> HealthResponse {
        guard let base = baseURL(from: settings) else { throw AgentServiceError.notConfigured }
        let url = base.appendingPathComponent("health")
        var request = URLRequest(url: url)
        request.timeoutInterval = 5
        let (data, _): (Data, URLResponse)
        do {
            (data, _) = try await URLSession.shared.data(for: request)
        } catch {
            throw AgentServiceError.serverUnreachable
        }
        return try decoder.decode(HealthResponse.self, from: data)
    }
}
