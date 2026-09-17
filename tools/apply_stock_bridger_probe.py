from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)


mobile = Path("mobile/src/main/java/com/notifmirror/mobile/NotificationListener.kt")
s = mobile.read_text()

anchor = '''        // Check per-app keyword filters
        if (!settings.passesPerAppKeywordFilter(sbn.packageName, title, displayText)) {
            Log.d(TAG, "Notification filtered out by per-app keyword rules: $title (${sbn.packageName})")
            return
        }
'''

injected = anchor + '''
        // Xiaomi/WearServices stock bridger experiment.
        // Keep the normal /notification transport active in parallel.
        if (sbn.packageName == "org.telegram.messenger.web") {
            scope.launch {
                StockBridgerSender.sendTelegramPhoto(
                    context = this@NotificationListener,
                    sbn = sbn
                )
            }
        }
'''

s = replace_once(s, anchor, injected, "mobile per-app keyword filter")
mobile.write_text(s)

print("Stock bridger probe source changes applied")
