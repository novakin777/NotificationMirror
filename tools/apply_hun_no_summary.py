from pathlib import Path

p = Path("wear/src/main/java/com/notifmirror/wear/NotificationHandler.kt")
s = p.read_text()
old = '''        // Create/update summary notification for the per-app group.\n        // Uses a tag ("summary") to prevent ID collision with regular notification IDs.\n        val summaryId = (packageName.hashCode() and 0x7FFFFFFF)\n        val summaryBuilder = NotificationCompat.Builder(context, channelId)\n            .setSmallIcon(R.drawable.ic_notification)\n            .setContentTitle(appLabel)\n            .setContentText(title)\n            .setSubText(appLabel)\n            .setGroup(groupId)\n            .setGroupSummary(true)\n            .setAutoCancel(true)\n            .setSilent(true)\n            .setStyle(NotificationCompat.InboxStyle()\n                .setSummaryText(appLabel))\n        nm.notify(SUMMARY_TAG, summaryId, summaryBuilder.build())\n'''
new = '''        // MiWearSysUI treats creation/update of the per-app group summary as a separate\n        // heads-up StreamItem. On Xiaomi Watch 5 this produces a second HUN that hides\n        // the real child notification (including its BigPictureStyle image).\n        // Keep only the child notification; WearOS can display it directly.\n'''
if old not in s:
    raise SystemExit("summary block anchor not found")
p.write_text(s.replace(old, new, 1))
print("Applied HUN no-summary fix")
