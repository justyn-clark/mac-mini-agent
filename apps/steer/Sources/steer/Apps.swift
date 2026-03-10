import ArgumentParser
import Foundation

struct Apps: ParsableCommand {
    static let configuration = CommandConfiguration(
        abstract: "List running apps, inspect state, or perform tightly-scoped app actions."
    )

    @Argument(help: "Action: list | launch | activate | hide | unhide | quit | force-quit")
    var action: String = "list"

    @Argument(help: "App name (for non-list actions)")
    var name: String?

    @Option(name: .long, help: "Approval contract id for stronger actions like quit/force-quit")
    var approval: String?

    @Flag(name: .long, help: "Output JSON")
    var json = false

    func run() throws {
        switch action.lowercased() {
        case "list":
            let apps = AppControl.list()
            if json {
                let enc = JSONEncoder()
                enc.outputFormatting = .prettyPrinted
                if let d = try? enc.encode(apps) { print(String(data: d, encoding: .utf8) ?? "[]") }
            } else {
                for a in apps {
                    let star = a.isActive ? " *" : ""
                    print("  \(a.name.padding(toLength: 25, withPad: " ", startingAt: 0)) pid:\(a.pid)\(star)")
                }
            }
        case "launch":
            guard let name = name else { throw ValidationError("Provide app name") }
            try AppControl.launch(name)
            print(json ? "{\"action\":\"launch\",\"app\":\"\(name)\",\"ok\":true}" : "Launched \(name)")
        case "activate", "focus":
            guard let name = name else { throw ValidationError("Provide app name") }
            try AppControl.activate(name)
            print(json ? "{\"action\":\"activate\",\"app\":\"\(name)\",\"ok\":true}" : "Activated \(name)")
        case "hide":
            guard let name = name else { throw ValidationError("Provide app name") }
            try AppControl.hide(name)
            print(json ? "{\"action\":\"hide\",\"app\":\"\(name)\",\"ok\":true}" : "Hid \(name)")
        case "unhide":
            guard let name = name else { throw ValidationError("Provide app name") }
            try AppControl.unhide(name)
            print(json ? "{\"action\":\"unhide\",\"app\":\"\(name)\",\"ok\":true}" : "Unhid \(name)")
        case "quit":
            guard let name = name else { throw ValidationError("Provide app name") }
            guard let approval else { throw ValidationError("quit requires --approval") }
            try ApprovalControl.validate(approval, action: "steer.apps.quit", target: "app:\(name)")
            try AppControl.quit(name)
            print(json ? "{\"action\":\"quit\",\"app\":\"\(name)\",\"approval\":\"\(approval)\",\"ok\":true}" : "Quit \(name)")
        case "force-quit":
            guard let name = name else { throw ValidationError("Provide app name") }
            guard let approval else { throw ValidationError("force-quit requires --approval") }
            try ApprovalControl.validate(approval, action: "steer.apps.force-quit", target: "app:\(name)")
            try AppControl.quit(name, force: true)
            print(json ? "{\"action\":\"force-quit\",\"app\":\"\(name)\",\"approval\":\"\(approval)\",\"ok\":true}" : "Force-quit \(name)")
        default:
            throw ValidationError("Action must be: list, launch, activate, hide, unhide, quit, force-quit")
        }
    }
}
