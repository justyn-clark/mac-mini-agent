import ArgumentParser
import Foundation

struct Hotkey: ParsableCommand {
    static let configuration = CommandConfiguration(
        abstract: "Press a key combination: cmd+s, ctrl+c, return, escape, etc. High-risk combos require approval."
    )

    @Argument(help: "Key combo: cmd+s, cmd+shift+n, return, escape, tab, etc.")
    var combo: String

    @Option(name: .long, help: "Approval contract id for stronger combos like cmd+q")
    var approval: String?

    @Flag(name: .long, help: "Output JSON")
    var json = false

    func run() throws {
        let normalized = combo.lowercased()
        if ["cmd+q", "cmd+w", "cmd+shift+q"].contains(normalized) {
            guard let approval else { throw ValidationError("\(combo) requires --approval") }
            try ApprovalControl.validate(approval, action: "steer.hotkey", target: "combo:\(normalized)")
        }

        Keyboard.hotkey(combo)

        if json {
            if let approval {
                print("{\"action\":\"hotkey\",\"combo\":\"\(combo)\",\"approval\":\"\(approval)\",\"ok\":true}")
            } else {
                print("{\"action\":\"hotkey\",\"combo\":\"\(combo)\",\"ok\":true}")
            }
        } else {
            print("Pressed \(combo)")
        }
    }
}
