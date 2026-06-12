import SwiftUI

struct ToolCallCard: View {
    let record: ToolCallRecord
    @State private var isExpanded = false

    private var iconName: String {
        switch record.name {
        case let n where n.contains("email"): return "envelope"
        case let n where n.contains("calendar"): return "calendar"
        case let n where n.contains("linkedin"): return "person.2"
        case let n where n.contains("web"), let n where n.contains("search"): return "magnifyingglass"
        default: return "wrench.and.screwdriver"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Button {
                withAnimation(.spring(duration: 0.25)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: iconName)
                        .font(.caption)
                        .foregroundStyle(.orange)

                    Text(record.name)
                        .font(.caption.monospaced())
                        .foregroundStyle(.primary)

                    if !record.arguments.isEmpty {
                        Text("(\(record.arguments))")
                            .font(.caption.monospaced())
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }

                    Spacer()

                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 7)
            }
            .buttonStyle(.plain)

            if isExpanded {
                Divider()
                    .padding(.horizontal, 10)

                ScrollView {
                    Text(record.result)
                        .font(.caption.monospaced())
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(10)
                }
                .frame(maxHeight: 200)
            }
        }
        .background(.orange.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(.orange.opacity(0.25), lineWidth: 1)
        )
    }
}
