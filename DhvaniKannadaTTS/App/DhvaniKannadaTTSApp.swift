import SwiftUI

@main
struct DhvaniKannadaTTSApp: App {
    var body: some Scene {
        WindowGroup {
            MainTTSView()
                .preferredColorScheme(nil) // Respects system Light/Dark mode
        }
    }
}
