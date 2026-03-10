import ArgumentParser
import Foundation

struct Clipboard: ParsableCommand {
    static let configuration = CommandConfiguration(
        abstract: "Read or write the system clipboard. Writes are scoped and approval-gated."
    )

    @Argument(help: "Action: read | write")
    var action: String

    @Argument(help: "Text to write (for write action)")
    var text: String?

    @Option(name: .long, help: "Content type: text | image (default: text)")
    var type: String = "text"

    @Option(name: .long, help: "File path for image read/write")
    var file: String?

    @Option(name: .long, help: "Approval contract id for clipboard writes")
    var approval: String?

    @Flag(name: .long, help: "Output JSON")
    var json = false

    func run() throws {
        switch action.lowercased() {
        case "read":
            switch type.lowercased() {
            case "text":
                let content = ClipboardControl.readText()
                if json {
                    let escaped = (content ?? "").replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: "\\n")
                    print("{\"action\":\"read\",\"type\":\"text\",\"content\":\"\(escaped)\",\"ok\":true}")
                } else {
                    print(content ?? "(clipboard empty)")
                }
            case "image":
                let path = try ClipboardControl.readImage(saveTo: file)
                print(json ? "{\"action\":\"read\",\"type\":\"image\",\"file\":\"\(path)\",\"ok\":true}" : "Saved clipboard image to \(path)")
            default:
                throw ValidationError("Type must be: text, image")
            }
        case "write":
            guard let approval else { throw ValidationError("write requires --approval") }
            switch type.lowercased() {
            case "text":
                guard let text = text else { throw ValidationError("Provide text to write") }
                try ApprovalControl.validate(approval, action: "steer.clipboard.write-text", target: "clipboard:text")
                ClipboardControl.writeText(text)
                if json {
                    let escaped = text.replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: "\\n")
                    print("{\"action\":\"write\",\"type\":\"text\",\"content\":\"\(escaped)\",\"approval\":\"\(approval)\",\"ok\":true}")
                } else {
                    print("Copied to clipboard: \"\(text.prefix(80))\(text.count > 80 ? "..." : "")\"")
                }
            case "image":
                guard let file = file else { throw ValidationError("Provide --file path for image write") }
                try ApprovalControl.validate(approval, action: "steer.clipboard.write-image", target: "clipboard:image")
                try ClipboardControl.writeImage(fromPath: file)
                print(json ? "{\"action\":\"write\",\"type\":\"image\",\"file\":\"\(file)\",\"approval\":\"\(approval)\",\"ok\":true}" : "Copied image to clipboard from \(file)")
            default:
                throw ValidationError("Type must be: text, image")
            }
        default:
            throw ValidationError("Action must be: read, write")
        }
    }
}
