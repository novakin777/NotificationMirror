from pathlib import Path

handler = Path("wear/src/main/java/com/notifmirror/wear/NotificationHandler.kt")
s = handler.read_text()

anchor = '''    fun handleNotification(context: Context, messageEvent: MessageEvent) {\n'''
helper = '''    /**\n     * Pre-create per-app group summaries for apps previously seen by the watch.\n     * MiWearSysUI shows a separate HUN when a group summary is first created, but our\n     * testing showed that updating an already-existing summary with the same tag/id\n     * does not produce the extra HUN.\n     */\n    fun prewarmKnownSummaries(context: Context) {\n        val labels = context.getSharedPreferences("app_labels", Context.MODE_PRIVATE).all\n        if (labels.isEmpty()) return\n\n        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager\n        for ((packageName, rawLabel) in labels) {\n            val appLabel = rawLabel as? String ?: continue\n            if (packageName.isBlank() || appLabel.isBlank()) continue\n\n            val channelId = CHANNEL_PREFIX + packageName\n            val groupId = GROUP_PREFIX + packageName\n\n            if (nm.notificationChannelGroups.none { it.id == groupId }) {\n                nm.createNotificationChannelGroup(NotificationChannelGroup(groupId, appLabel))\n            }\n\n            if (nm.getNotificationChannel(channelId) == null) {\n                val channel = NotificationChannel(\n                    channelId,\n                    appLabel,\n                    NotificationManager.IMPORTANCE_HIGH\n                ).apply {\n                    description = "Mirrored notifications from $appLabel"\n                    enableVibration(false)\n                    setSound(\n                        RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION),\n                        AudioAttributes.Builder()\n                            .setUsage(AudioAttributes.USAGE_NOTIFICATION)\n                            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)\n                            .build()\n                    )\n                    this.group = groupId\n                }\n                nm.createNotificationChannel(channel)\n            }\n\n            val summaryId = (packageName.hashCode() and 0x7FFFFFFF)\n            val summary = NotificationCompat.Builder(context, channelId)\n                .setSmallIcon(R.drawable.ic_notification)\n                .setContentTitle(appLabel)\n                .setContentText("")\n                .setSubText(appLabel)\n                .setGroup(groupId)\n                .setGroupSummary(true)\n                .setAutoCancel(true)\n                .setOnlyAlertOnce(true)\n                .setSilent(true)\n                .setPriority(NotificationCompat.PRIORITY_MIN)\n                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)\n                .setShowWhen(false)\n                .build()\n\n            nm.notify(SUMMARY_TAG, summaryId, summary)\n            Log.d(TAG, "Prewarmed summary for $packageName id=$summaryId")\n        }\n    }\n\n'''
if anchor not in s:
    raise SystemExit("handleNotification anchor not found")
s = s.replace(anchor, helper + anchor, 1)
handler.write_text(s)

service = Path("wear/src/main/java/com/notifmirror/wear/PersistentListenerService.kt")
p = service.read_text()
old = '''        createNotificationChannel()\n        startForeground(NOTIFICATION_ID, buildNotification())\n'''
new = '''        createNotificationChannel()\n        startForeground(NOTIFICATION_ID, buildNotification())\n\n        // Pre-create summaries while the persistent watch service starts, before\n        // normal mirrored notifications arrive. Known packages come from the label\n        // cache populated by previous mirrored notifications.\n        NotificationHandler.prewarmKnownSummaries(this)\n'''
if old not in p:
    raise SystemExit("PersistentListenerService onCreate anchor not found")
p = p.replace(old, new, 1)
service.write_text(p)

receiver = Path("wear/src/main/java/com/notifmirror/wear/NotificationReceiverService.kt")
r = receiver.read_text()
class_anchor = '''    override fun onMessageReceived(messageEvent: MessageEvent) {\n'''
oncreate = '''    override fun onCreate() {\n        super.onCreate()\n        // Fallback in case the persistent listener was not running yet.\n        NotificationHandler.prewarmKnownSummaries(this)\n    }\n\n'''
if class_anchor not in r:
    raise SystemExit("NotificationReceiverService anchor not found")
r = r.replace(class_anchor, oncreate + class_anchor, 1)
receiver.write_text(r)

print("Applied HUN prewarmed-summary variant")
