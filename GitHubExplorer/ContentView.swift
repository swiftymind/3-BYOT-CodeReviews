import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = UserSearchViewModel(
        gitHubService: GitHubService()
    )

    var body: some View {
        Text("Hello World!")
    }
}

#Preview {
    ContentView()
}
