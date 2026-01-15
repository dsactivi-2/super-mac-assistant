# Super Mac Assistant - Accessibility IDs

This document lists all UI elements with their accessibility identifiers for automated testing and VoiceOver support.

## OTOP Standard Format

```
supermac.menubar.{section}.{element}
```

## Menu Bar App IDs

| ID                                   | Element              | Keyboard Shortcut | Description                        |
| ------------------------------------ | -------------------- | ----------------- | ---------------------------------- |
| `supermac.menubar.status.display`    | Status Text          | -                 | Shows current status (Ready/Error) |
| `supermac.menubar.agent.supervisor`  | Switch to Supervisor | ⌘1                | Activate Supervisor mode           |
| `supermac.menubar.agent.assistant`   | Switch to Assistant  | ⌘2                | Activate Assistant mode            |
| `supermac.menubar.agent.current`     | Current Agent        | -                 | Displays active agent name         |
| `supermac.menubar.action.screenshot` | Take Screenshot      | ⌘S                | Capture screen to Desktop          |
| `supermac.menubar.action.status`     | Check Status         | ⌘C                | Show detailed status notification  |
| `supermac.menubar.backend.status`    | Backend Status       | -                 | Shows connection status            |
| `supermac.menubar.backend.reconnect` | Reconnect            | ⌘R                | Attempt backend reconnection       |
| `supermac.menubar.slack.toggle`      | Notifications Toggle | ⌘N                | Enable/disable Slack notifications |
| `supermac.menubar.app.quit`          | Quit                 | ⌘Q                | Exit the application               |

## Menu Structure

```
🤖 (Menu Bar Icon)
├── Status: Ready                    [supermac.menubar.status.display]
├── ─────────────
├── --- Agent ---
│   ├── Current: SUPERVISOR          [supermac.menubar.agent.current]
│   ├── Switch to Supervisor  ⌘1     [supermac.menubar.agent.supervisor]
│   └── Switch to Assistant   ⌘2     [supermac.menubar.agent.assistant]
├── ─────────────
├── --- Quick Actions ---
│   ├── Take Screenshot       ⌘S     [supermac.menubar.action.screenshot]
│   └── Check Status          ⌘C     [supermac.menubar.action.status]
├── ─────────────
├── --- Backend ---
│   ├── Backend: Connected           [supermac.menubar.backend.status]
│   └── Reconnect             ⌘R     [supermac.menubar.backend.reconnect]
├── ─────────────
├── --- Slack ---
│   └── Notifications: On     ⌘N     [supermac.menubar.slack.toggle]
├── ─────────────
└── Quit Super Mac Assistant  ⌘Q     [supermac.menubar.app.quit]
```

## UI Automation with AppleScript

Example: Click a menu item via AppleScript

```applescript
tell application "System Events"
    tell process "Python"
        -- Click menu bar item
        click menu bar item 1 of menu bar 2
        delay 0.5
        -- Click "Take Screenshot"
        click menu item "Take Screenshot" of menu 1 of menu bar item 1 of menu bar 2
    end tell
end tell
```

## VoiceOver Support

All menu items are automatically accessible via VoiceOver. Navigate using:

- **VO + M**: Open menu bar
- **VO + Arrow Keys**: Navigate menu items
- **VO + Space**: Activate item

## Testing with XCTest (Swift/Obj-C)

For macOS UI tests:

```swift
let app = XCUIApplication()
app.menuBars.statusItems["Super Mac Assistant"].click()
app.menuItems["Take Screenshot"].click()
```

---

**OTOP Compliance**: ✅ All interactive elements have unique identifiers following the `supermac.menubar.{section}.{element}` pattern.
