import SwiftUI

struct ChatView: View {
    @Environment(AppSettings.self) private var settings
    @State private var viewModel = ChatViewModel()
    @State private var showSettings = false
    @FocusState private var inputFocused: Bool
    @Namespace private var bottomAnchor

    var body: some View {
        VStack(spacing: 0) {
            // Status bar
            statusBar

            Divider()

            // Message list
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        if viewModel.messages.isEmpty {
                            emptyState
                        }

                        ForEach(viewModel.messages) { msg in
                            MessageBubble(message: msg)
                                .padding(.horizontal, 12)
                        }

                        if viewModel.isLoading {
                            TypingIndicator()
                                .padding(.horizontal, 12)
                        }

                        Color.clear
                            .frame(height: 1)
                            .id("bottom")
                    }
                    .padding(.vertical, 12)
                }
                .onChange(of: viewModel.messages.count) { _, _ in
                    withAnimation { proxy.scrollTo("bottom", anchor: .bottom) }
                }
                .onChange(of: viewModel.isLoading) { _, _ in
                    withAnimation { proxy.scrollTo("bottom", anchor: .bottom) }
                }
            }

            // Error banner
            if let error = viewModel.errorMessage {
                errorBanner(error)
            }

            Divider()

            // Input bar
            inputBar
        }
        .navigationTitle("Local Agent")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button {
                    showSettings = true
                } label: {
                    Image(systemName: "gearshape")
                }
            }

            ToolbarItem(placement: .automatic) {
                Button {
                    viewModel.clearConversation()
                } label: {
                    Image(systemName: "square.and.pencil")
                }
                .disabled(viewModel.messages.isEmpty)
            }
        }
        .sheet(isPresented: $showSettings) {
            NavigationStack {
                SettingsView()
                    .toolbar {
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Done") { showSettings = false }
                        }
                    }
            }
        }
        .task {
            await viewModel.checkConnection(settings: settings)
        }
    }

    // MARK: - Sub-views

    private var statusBar: some View {
        HStack(spacing: 6) {
            Circle()
                .frame(width: 7, height: 7)
                .foregroundStyle(viewModel.connectionStatus.isConnected ? .green : .red)

            Text(viewModel.connectionStatus.isConnected
                 ? viewModel.connectionStatus.label
                 : "Not connected — start python api.py")
                .font(.caption)
                .foregroundStyle(.secondary)

            Spacer()

            if !viewModel.availableTools.isEmpty {
                Text("\(viewModel.availableTools.count) tools")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
        .background(.bar)
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "cpu.fill")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)

            Text("Local Agent")
                .font(.title2.bold())

            Text("Ask me about your emails, calendar,\nLinkedIn, or anything on the web.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)

            if !viewModel.connectionStatus.isConnected {
                Label("Server offline — run python api.py", systemImage: "exclamationmark.triangle")
                    .font(.caption)
                    .foregroundStyle(.orange)
                    .padding(.top, 4)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 80)
    }

    private var inputBar: some View {
        HStack(alignment: .bottom, spacing: 10) {
            TextField("Message", text: Binding(
                get: { viewModel.inputText },
                set: { viewModel.inputText = $0 }
            ), axis: .vertical)
            .lineLimit(1...6)
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(.secondary.opacity(0.1), in: RoundedRectangle(cornerRadius: 20))
            .focused($inputFocused)
            .onSubmit {
                #if os(macOS)
                sendMessage()
                #endif
            }
            #if os(macOS)
            .onKeyPress(.return) {
                if NSApp.currentEvent?.modifierFlags.contains(.shift) == true {
                    return .ignored
                }
                sendMessage()
                return .handled
            }
            #endif

            Button(action: sendMessage) {
                Image(systemName: viewModel.isLoading ? "stop.circle.fill" : "arrow.up.circle.fill")
                    .font(.system(size: 30))
                    .foregroundStyle(canSend ? .blue : .secondary)
            }
            .buttonStyle(.plain)
            .disabled(!canSend)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(.bar)
    }

    private var canSend: Bool {
        !viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !viewModel.isLoading
            && viewModel.connectionStatus.isConnected
    }

    private func sendMessage() {
        guard canSend else { return }
        Task { await viewModel.sendMessage(settings: settings) }
    }

    private func errorBanner(_ msg: String) -> some View {
        HStack {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.red)
            Text(msg)
                .font(.caption)
            Spacer()
            Button { viewModel.errorMessage = nil } label: {
                Image(systemName: "xmark.circle.fill")
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 8)
        .background(.red.opacity(0.1))
    }
}
