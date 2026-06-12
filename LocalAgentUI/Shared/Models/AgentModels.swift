import Foundation

// MARK: - Domain models

enum MessageRole: String, Codable {
    case user, assistant
}

struct ToolCallRecord: Identifiable, Codable, Hashable {
    var id = UUID()
    let name: String
    let arguments: String
    let result: String
}

struct Message: Identifiable, Codable {
    var id = UUID()
    let role: MessageRole
    let content: String
    var toolCalls: [ToolCallRecord] = []
    let timestamp: Date

    init(role: MessageRole, content: String, toolCalls: [ToolCallRecord] = []) {
        self.role = role
        self.content = content
        self.toolCalls = toolCalls
        self.timestamp = Date()
    }
}

// MARK: - API wire types

struct ChatRequest: Encodable {
    let message: String
    let history: [HistoryMessage]
}

struct HistoryMessage: Encodable {
    let role: String
    let content: String
}

struct ChatResponse: Decodable {
    let response: String
    let toolCalls: [ToolCallResponse]

    enum CodingKeys: String, CodingKey {
        case response
        case toolCalls = "tool_calls"
    }
}

struct ToolCallResponse: Decodable {
    let name: String
    let arguments: String
    let result: String
}

struct HealthResponse: Decodable {
    let status: String
    let model: String
    let tools: [String]
}
