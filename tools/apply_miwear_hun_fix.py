from pathlib import Path

wear = Path("wear/src/main/java/com/notifmirror/wear/NotificationHandler.kt")
w = wear.read_text()

old = '''            builder.setContentTitle(peekTitle)
            builder.setContentText(peekText)
            builder.setTicker(peekText)

            if (pictureBitmap != null) {
'''
new = '''            builder.setContentTitle(peekTitle)
            builder.setContentText(peekText)
            builder.setTicker(peekText)

            // Xiaomi MiWearSysUI HUN uses Notification.subText as its visible
            // secondary text when the HUN layout provides that TextView. It only
            // falls back to contentText for the alternate layout. Put the latest
            // message body in BOTH fields for mirrored MessagingStyle notifications.
            // The original app identity remains available through the per-app
            // notification channel/group.
            if (isMessagingStyle && peekText.isNotEmpty()) {
                builder.setSubText(peekText)
            }

            if (pictureBitmap != null) {
'''

if old not in w:
    raise SystemExit("anchor not found: HUN subText insertion")
w = w.replace(old, new, 1)
wear.write_text(w)
print("MiWear HUN content-field patch applied")
