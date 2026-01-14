# Desktop Notifications Feature

## Overview

The DeepTempo AI SOC platform now includes full support for browser/desktop notifications, allowing users to receive real-time alerts for critical security events even when the application is running in the background.

## Features

### Notification Service

The notification system is implemented using the Web Notifications API and provides:

- **Browser notification support detection**
- **Permission request handling**
- **Configurable notification preferences**
- **Multiple notification types** for different security events
- **Auto-close timers** for non-critical notifications
- **Click-to-focus** behavior to bring the app to the foreground

### Notification Types

#### 1. New Security Findings
- **Trigger**: When new high or critical severity findings are detected
- **Behavior**: 
  - Critical/High severity: Requires user interaction to dismiss
  - Medium/Low severity: No desktop notification (in-app only)
- **Content**: Finding ID, title, severity level, and description

#### 2. Investigation Completion
- **Trigger**: When an AI-powered investigation chat completes analysis
- **Behavior**: Requires user interaction to dismiss
- **Content**: Investigation title, completion summary, and finding ID
- **Why Important**: User-initiated deep analysis that typically takes time to complete

#### 3. Case Updates
- **Trigger**: When case details are modified or status changes
- **Behavior**: High/Critical priority cases require interaction
- **Content**: Case title, status, priority, and update message

#### 4. Case Resolution
- **Trigger**: When a case is marked as resolved
- **Behavior**: Auto-dismiss after 10 seconds
- **Content**: Case title and resolution confirmation

#### 5. Report Generation
- **Trigger**: When PDF report generation completes (success or failure)
- **Behavior**: Auto-dismiss after 10 seconds
- **Content**: 
  - Success: Case title and filename
  - Failure: Error message
- **Why Important**: User-initiated export that can take time for large cases

#### 6. Timesketch Export
- **Trigger**: When timeline export to Timesketch completes (success or failure)
- **Behavior**: Auto-dismiss after 10 seconds
- **Content**:
  - Success: Number of events exported and timeline name
  - Failure: Error message
- **Why Important**: Long-running operation that processes and exports forensic data

#### 7. MCP Server Status Changes
- **Trigger**: When MCP server operations fail or encounter errors
- **Behavior**: Requires user interaction for errors
- **Content**: Server name, status, and error details
- **Why Important**: Critical infrastructure issues that affect AI capabilities
- **Includes**:
  - Individual server start/stop failures
  - Bulk server operation failures (start all/stop all)

#### 8. Generic Notifications
- **Trigger**: System events, configuration changes, or custom alerts
- **Behavior**: Configurable based on severity
- **Content**: Custom title and message

## Configuration

### Enabling Desktop Notifications

1. Navigate to **Settings** → **General** tab
2. Toggle **"Show desktop notifications"** switch
3. Grant browser permission when prompted
4. Click **"Send Test Notification"** to verify it's working

### Browser Permissions

The notification system requires browser permission to display desktop notifications:

- **Supported Browsers**: Chrome, Firefox, Edge, Safari (desktop versions)
- **Permission Request**: Automatic when enabling notifications
- **Permission Status**: Displayed in Settings → General tab

### Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome 22+ | ✅ Full | Best experience |
| Firefox 22+ | ✅ Full | Best experience |
| Edge 14+ | ✅ Full | Best experience |
| Safari 7+ | ✅ Full | May require permission in system preferences |
| Mobile Browsers | ⚠️ Limited | Varies by OS and browser |

## Implementation Details

### Architecture

```
NotificationService (Singleton)
    ↓
NotificationContext (React Context)
    ↓
Components (FindingsTable, CaseDetailDialog, etc.)
```

### Key Files

- **`frontend/src/services/notifications.ts`**: Core notification service with singleton pattern
- **`frontend/src/contexts/NotificationContext.tsx`**: React context provider for app-wide notification state
- **`frontend/src/pages/Settings.tsx`**: User interface for notification configuration and MCP server notifications
- **`frontend/src/components/findings/FindingsTable.tsx`**: Finding notification triggers
- **`frontend/src/components/cases/CaseDetailDialog.tsx`**: Case update, resolution, and report generation notifications
- **`frontend/src/components/claude/ClaudeDrawer.tsx`**: Investigation completion notifications
- **`frontend/src/components/timesketch/ExportToTimesketchDialog.tsx`**: Timesketch export notifications

### Notification Service API

```typescript
// Get singleton instance
const notificationService = NotificationService.getInstance()

// Check browser support
notificationService.isSupported(): boolean

// Request permission
await notificationService.requestPermission(): Promise<boolean>

// Enable/disable notifications
notificationService.setEnabled(true|false): void

// Show custom notification
await notificationService.show(title, {
  body: 'message',
  icon: '/path/to/icon.png',
  tag: 'unique-id',
  requireInteraction: false,
  silent: false,
  onClick: () => { /* callback */ }
})

// Specialized notification methods
notificationService.notifyNewFinding({ finding_id, title, severity, description })
notificationService.notifyCaseUpdate({ case_id, title, status, priority, message })
notificationService.notifyInvestigationComplete({ title, summary })
notificationService.notifyMcpServerStatus({ name, status, error })
notificationService.notifyGeneric(title, message, { severity, requireInteraction })
```

### React Context Hook

```typescript
import { useNotifications } from '../contexts/NotificationContext'

function MyComponent() {
  const { 
    notificationsEnabled,      // Current state
    setNotificationsEnabled,   // Enable/disable
    permissionGranted,         // Permission status
    requestPermission          // Request permission
  } = useNotifications()
  
  // Use in component logic
}
```

## User Experience

### First-Time Setup

1. User navigates to Settings → General
2. User enables "Show desktop notifications"
3. Browser displays permission prompt
4. User grants permission
5. Test notification is automatically sent
6. User can verify notifications are working

### Permission Denied

If the user denies notification permission:

- The checkbox automatically reverts to disabled
- A warning message is displayed
- User must manually enable notifications in browser settings to retry

### Notification Interaction

- **Click**: Brings the application window to focus and closes the notification
- **Close**: Dismisses the notification without action
- **Auto-dismiss**: Non-critical notifications close after 10 seconds

## Privacy & Security

- **No external servers**: Notifications are generated client-side using the browser's native API
- **No tracking**: Notification interactions are not tracked or logged
- **User control**: Users can disable notifications at any time
- **Browser-level privacy**: Subject to browser privacy and security policies

## Testing

### Manual Testing

1. **Enable Notifications**
   - Settings → General → Enable "Show desktop notifications"
   - Click "Send Test Notification" button
   - Verify notification appears on desktop

2. **Test Finding Notifications**
   - Navigate to Findings page
   - Click Refresh to load findings
   - New high/critical findings should trigger notifications

3. **Test Investigation Notifications**
   - Open a finding
   - Click "Investigate" to start AI analysis
   - Wait for investigation to complete
   - Verify notification appears when analysis finishes

4. **Test Case Notifications**
   - Open a case
   - Update case details (priority, status, etc.)
   - Click Save
   - Verify notification appears
   - Mark case as resolved
   - Verify resolution notification appears

5. **Test Report Generation**
   - Open a case
   - Click "Generate PDF Report"
   - Wait for generation to complete
   - Verify notification with filename appears

6. **Test Timesketch Export**
   - Navigate to Findings or Cases
   - Click "Export to Timesketch"
   - Complete export dialog
   - Wait for export to complete
   - Verify notification with event count appears

7. **Test MCP Server Notifications**
   - Settings → MCP Servers tab
   - Try to start/stop a server
   - If operation fails, verify error notification
   - Click "Start All" or "Stop All"
   - Verify bulk operation notifications

### Browser Developer Tools

```javascript
// Check notification support
'Notification' in window

// Check permission status
Notification.permission  // "granted", "denied", or "default"

// Manually trigger test notification
new Notification("Test", { body: "Testing notifications" })
```

## Troubleshooting

### Notifications Not Appearing

1. **Check browser support**: Ensure your browser supports the Notifications API
2. **Check permissions**: 
   - Chrome: Settings → Privacy and Security → Site Settings → Notifications
   - Firefox: Preferences → Privacy & Security → Permissions → Notifications
   - Safari: Preferences → Websites → Notifications
3. **Check system settings**: 
   - macOS: System Preferences → Notifications
   - Windows: Settings → System → Notifications
4. **Check Do Not Disturb**: Disable system-level Do Not Disturb mode
5. **Try different browser**: Test in another browser to isolate the issue

### Notifications Disabled in Settings

- Browser permission was denied
- Navigate to browser notification settings and allow notifications for the site
- Return to Settings → General and re-enable notifications

### Notifications Appearing After Disable

- Clear browser cache and cookies
- Reload the application
- Verify the setting is saved correctly

## Future Enhancements

Potential improvements for future releases:

- **Notification preferences per event type** (e.g., only critical findings)
- **Quiet hours** configuration
- **Sound notifications** with custom alert sounds
- **Notification history** panel in the UI
- **Desktop notification actions** (e.g., "View Finding", "Acknowledge")
- **Push notifications** for mobile devices
- **Notification batching** to prevent notification spam
- **Web Push API** integration for notifications when app is closed

## Related Documentation

- [Settings Configuration](./SETTINGS_CONFIGURATION_UPDATE.md)
- [React Chat Features](./react-chat-features.md)
- [Navigation Guide](./navigation-guide.md)

