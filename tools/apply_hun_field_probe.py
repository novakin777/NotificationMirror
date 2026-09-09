from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)

main = Path("mobile/src/main/java/com/notifmirror/mobile/MainActivity.kt")
s = main.read_text()

s = replace_once(s,
'        IMAGE("With Image", "Notification with an attached picture (BigPictureStyle)")\n',
'        IMAGE("HUN Summary Prewarm Probe", "Pre-create summary, then child BigPicture, then update same summary")\n',
"rename IMAGE")

s = replace_once(s,
'''                    TestNotifType.IMAGE -> {\n                        countRow.visibility = View.GONE\n                        delayRow.visibility = View.GONE\n                        titleInput.setText("Photo Shared")\n                        textInput.setText("Check out this picture!")\n                    }\n''',
'''                    TestNotifType.IMAGE -> {\n                        countRow.visibility = View.GONE\n                        delayRow.visibility = View.GONE\n                        titleInput.setText("HUN PREWARM PROBE")\n                        textInput.setText("Summary prewarm -> child -> summary update")\n                    }\n''',
"IMAGE UI")

s = replace_once(s,
'''                    if (index < testMessages.size - 1 && testMessages.size > 1) {\n                        kotlinx.coroutines.delay(delayMs)\n                    }\n''',
'''                    if (index < testMessages.size - 1 && testMessages.size > 1) {\n                        val effectiveDelay = if (type == TestNotifType.IMAGE) {\n                            if (index == 0) 10000L else 3000L\n                        } else delayMs\n                        kotlinx.coroutines.delay(effectiveDelay)\n                    }\n''',
"probe delays")

old_image = '''            TestNotifType.IMAGE -> {\n                listOf(buildBaseTestJson(packageName, title, text, "_image").apply {\n                    // Generate a small colored gradient test image as base64\n                    val bmp = android.graphics.Bitmap.createBitmap(200, 150, android.graphics.Bitmap.Config.ARGB_8888)\n                    val canvas = android.graphics.Canvas(bmp)\n                    val paint = android.graphics.Paint()\n                    val gradient = android.graphics.LinearGradient(\n                        0f, 0f, 200f, 150f,\n                        intArrayOf(0xFF6200EE.toInt(), 0xFF03DAC5.toInt(), 0xFFBB86FC.toInt()),\n                        null, android.graphics.Shader.TileMode.CLAMP\n                    )\n                    paint.shader = gradient\n                    canvas.drawRect(0f, 0f, 200f, 150f, paint)\n                    val textPaint = android.graphics.Paint().apply {\n                        color = android.graphics.Color.WHITE\n                        textSize = 40f\n                        textAlign = android.graphics.Paint.Align.CENTER\n                        isAntiAlias = true\n                        typeface = android.graphics.Typeface.DEFAULT_BOLD\n                    }\n                    canvas.drawText("TEST", 100f, 85f, textPaint)\n                    val stream = java.io.ByteArrayOutputStream()\n                    bmp.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, stream)\n                    bmp.recycle()\n                    put("picture", android.util.Base64.encodeToString(stream.toByteArray(), android.util.Base64.NO_WRAP))\n                })\n            }\n'''

new_image = '''            TestNotifType.IMAGE -> {\n                fun probePicture(): String {\n                    val bmp = android.graphics.Bitmap.createBitmap(320, 200, android.graphics.Bitmap.Config.ARGB_8888)\n                    val canvas = android.graphics.Canvas(bmp)\n                    canvas.drawColor(0xFF1565C0.toInt())\n                    val p = android.graphics.Paint().apply {\n                        color = android.graphics.Color.WHITE\n                        textSize = 34f\n                        textAlign = android.graphics.Paint.Align.CENTER\n                        isAntiAlias = true\n                        typeface = android.graphics.Typeface.DEFAULT_BOLD\n                    }\n                    canvas.drawText("PIC_PREWARM_CHILD", 160f, 115f, p)\n                    val out = java.io.ByteArrayOutputStream()\n                    bmp.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out)\n                    bmp.recycle()\n                    return android.util.Base64.encodeToString(out.toByteArray(), android.util.Base64.NO_WRAP)\n                }\n                val prewarm = buildBaseTestJson(packageName, "PREWARM_SUMMARY", "PREWARM_SUMMARY_TEXT", "_hun_prewarm_summary").apply {\n                    put("hunPrewarmProbe", true); put("hunPrewarmStage", "PREWARM")\n                    put("notifPriority", 2); put("showOpenButton", false); put("showMuteButton", false); put("showSnoozeButton", false)\n                }\n                val child = buildBaseTestJson(packageName, "CHILD_PREWARM", "CHILD_TEXT_PREWARM", "_hun_prewarm_child").apply {\n                    put("hunPrewarmProbe", true); put("hunPrewarmStage", "CHILD")\n                    put("picture", probePicture()); put("notifPriority", 2)\n                    put("showOpenButton", false); put("showMuteButton", false); put("showSnoozeButton", false)\n                }\n                val update = buildBaseTestJson(packageName, "UPDATED_SUMMARY", "UPDATED_SUMMARY_TEXT", "_hun_prewarm_update").apply {\n                    put("hunPrewarmProbe", true); put("hunPrewarmStage", "UPDATE")\n                    put("notifPriority", 2); put("showOpenButton", false); put("showMuteButton", false); put("showSnoozeButton", false)\n                }\n                listOf(prewarm, child, update)\n            }\n'''
s = replace_once(s, old_image, new_image, "IMAGE sequence")
main.write_text(s)

wear = Path("wear/src/main/java/com/notifmirror/wear/NotificationHandler.kt")
w = wear.read_text()

w = replace_once(w,
'''            val pictureBase64 = json.optString("picture", "")\n            val appLabel = json.optString("appLabel", "")\n''',
'''            val pictureBase64 = json.optString("picture", "")\n            val appLabel = json.optString("appLabel", "")\n            val hunPrewarmProbe = json.optBoolean("hunPrewarmProbe", false)\n            val hunPrewarmStage = json.optString("hunPrewarmStage", "")\n''',
"read prewarm metadata")

w = replace_once(w,
'''                isMessagingStyle = isMessagingStyle,\n                notifTag = notifTag, shortcutId = shortcutId\n            )\n''',
'''                isMessagingStyle = isMessagingStyle,\n                notifTag = notifTag, shortcutId = shortcutId,\n                hunPrewarmProbe = hunPrewarmProbe, hunPrewarmStage = hunPrewarmStage\n            )\n''',
"pass prewarm metadata")

w = replace_once(w,
'''        isMessagingStyle: Boolean = false,\n        notifTag: String = "",\n        shortcutId: String = ""\n    ) {\n''',
'''        isMessagingStyle: Boolean = false,\n        notifTag: String = "",\n        shortcutId: String = "",\n        hunPrewarmProbe: Boolean = false,\n        hunPrewarmStage: String = ""\n    ) {\n''',
"prewarm args")

builder_anchor = '''            .setOnlyAlertOnce(silentUpdate)\n            .setSilent(isSilent || vibrateOnly || silentUpdate || alertMode == 1 || alertMode == 2)\n\n'''
w = replace_once(w, builder_anchor, builder_anchor + '''        if (hunPrewarmProbe) {\n            builder.setGroup("hun_prewarm_group")\n                .setPriority(NotificationCompat.PRIORITY_MAX)\n                .setCategory(NotificationCompat.CATEGORY_MESSAGE)\n                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)\n            if (hunPrewarmStage == "CHILD") {\n                builder.setContentTitle("CHILD_PREWARM")\n                    .setContentText("CHILD_TEXT_PREWARM")\n                    .setGroupAlertBehavior(NotificationCompat.GROUP_ALERT_CHILDREN)\n            }\n        }\n\n''', "prewarm child group")

notify_anchor = '''        nm.notify(notifId, builder.build())\n\n'''
pre_notify = '''        if (hunPrewarmProbe && (hunPrewarmStage == "PREWARM" || hunPrewarmStage == "UPDATE")) {\n            val summaryId = "hun_prewarm_summary_fixed".hashCode()\n            val isUpdateStage = hunPrewarmStage == "UPDATE"\n            val summary = NotificationCompat.Builder(context, channelId)\n                .setSmallIcon(R.drawable.ic_notification)\n                .setContentTitle(if (isUpdateStage) "UPDATED_SUMMARY" else "PREWARM_SUMMARY")\n                .setContentText(if (isUpdateStage) "UPDATED_SUMMARY_TEXT" else "PREWARM_SUMMARY_TEXT")\n                .setTicker(if (isUpdateStage) "UPDATED_SUMMARY_TICKER" else "PREWARM_SUMMARY_TICKER")\n                .setCategory(NotificationCompat.CATEGORY_MESSAGE)\n                .setGroup("hun_prewarm_group")\n                .setGroupSummary(true)\n                .setGroupAlertBehavior(NotificationCompat.GROUP_ALERT_CHILDREN)\n                .setPriority(NotificationCompat.PRIORITY_MIN)\n                .setSilent(true)\n                .setOnlyAlertOnce(true)\n                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)\n                .build()\n            nm.notify(SUMMARY_TAG, summaryId, summary)\n            Log.d(TAG, "HUN prewarm probe summary stage=$hunPrewarmStage id=$summaryId")\n            return\n        }\n\n'''
w = replace_once(w, notify_anchor, pre_notify + notify_anchor, "prewarm/update summary intercept")

summary_anchor = '''        // Create/update summary notification for the per-app group.\n        // Uses a tag ("summary") to prevent ID collision with regular notification IDs.\n'''
w = replace_once(w, summary_anchor, '''        if (hunPrewarmProbe && hunPrewarmStage == "CHILD") {\n            Log.d(TAG, "HUN prewarm probe child posted without summary update id=$notifId")\n            return\n        }\n\n''' + summary_anchor, "suppress summary after child")

wear.write_text(w)
print("HUN summary prewarm probe applied")
