import SwiftUI

struct MessageBubble: View {
    let message: Message

    private var isUser: Bool { message.role == .user }

    var body: some View {
        VStack(alignment: isUser ? .trailing : .leading, spacing: 6) {
            HStack(alignment: .bottom, spacing: 8) {
                if isUser { Spacer(minLength: 48) }

                if !isUser {
                    Image(systemName: "cpu")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .frame(width: 24, height: 24)
                        .background(.secondary.opacity(0.12), in: Circle())
                        .padding(.bottom, 2)
                }

                Text(message.content)
                    .textSelection(.enabled)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        isUser
                            ? AnyShapeStyle(.blue)
                            : AnyShapeStyle(.secondary.opacity(0.15))
                    )
                    .foregroundStyle(isUser ? .white : .primary)
                    .clipShape(
                        .rect(
                            topLeadingRadius: isUser ? 18 : 4,
                            bottomLeadingRadius: 18,
                            bottomTrailingRadius: isUser ? 4 : 18,
                            topTrailingRadius: 18
                        )
                    )

                if isUser {
                    Image(systemName: "person.circle.fill")
                        .font(.caption)
                        .foregroundStyle(.blue)
                        .frame(width: 24, height: 24)
                        .padding(.bottom, 2)
                }

                if !isUser { Spacer(minLength: 48) }
            }

            if !message.toolCalls.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(message.toolCalls) { tc in
                        ToolCallCard(record: tc)
                    }
                }
                .padding(.leading, 32)
                .padding(.trailing, 48)
            }
        }
    }
}

struct TypingIndicator: View {
    @State private var phase = 0

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            Image(systemName: "cpu")
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(width: 24, height: 24)
                .background(.secondary.opacity(0.12), in: Circle())

            HStack(spacing: 4) {
                ForEach(0..<3) { i in
                    Circle()
                        .frame(width: 7, height: 7)
                        .foregroundStyle(.secondary)
                        .opacity(phase == i ? 1 : 0.3)
                        .animation(.easeInOut(duration: 0.4).repeatForever().delay(Double(i) * 0.15), value: phase)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(.secondary.opacity(0.15), in: RoundedRectangle(cornerRadius: 18))

            Spacer(minLength: 48)
        }
        .onAppear {
            withAnimation { phase = 1 }
        }
    }
}
