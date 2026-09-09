from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)


main = Path("mobile/src/main/java/com/notifmirror/mobile/MainActivity.kt")
s = main.read_text()

# Reuse the existing IMAGE enum so we don't introduce exhaustive-when compile failures.
s = replace_once(
    s,
    '        IMAGE("With Image", "Notification with an attached picture (BigPictureStyle)")\n',
    '        IMAGE("HUN Group Selection Probe", "4 grouped child/summary tests for MiWear HUN selection")\n',
    "rename IMAGE probe type",
)

s = replace_once(
    s,
    '''                    TestNotifType.IMAGE -> {\n                        countRow.visibility = View.GONE\n                        delayRow.visibility = View.GONE\n                        titleInput.setText("Photo Shared")\n                        textInput.setText("Check out this picture!")\n                    }\n''',
    '''                    TestNotifType.IMAGE -> {\n                        countRow.visibility = View.GONE\n                        delayRow.visibility = View.GONE\n                        titleInput.setText("HUN GROUP PROBE")\n                        textInput.setText("Child BigPicture vs text summary")\n                    }\n''',
    "IMAGE probe UI",
)

s = replace_once(
    s,
    '''                    if (index < testMessages.size - 1 && testMessages.size > 1) {\n                        kotlinx.coroutines.delay(delayMs)\n                    }\n''',
    '''                    if (index < testMessages.size - 1 && testMessages.size > 1) {\n                        val effectiveDelay = if (type == TestNotifType.IMAGE) 10000L else delayMs\n                        kotlinx.coroutines.delay(effectiveDelay)\n                    }\n''',
    "probe delay",
)

old_image_case = '''            TestNotifType.IMAGE -> {\n                listOf(buildBaseTestJson(packageName, title, text, "_image").apply {\n                    // Generate a small colored gradient test image as base64\n                    val bmp = android.graphics.Bitmap.createBitmap(200, 150, android.graphics.Bitmap.Config.ARGB_8888)\n                    val canvas = android.graphics.Canvas(bmp)\n                    val paint = android.graphics.Paint()\n                    val gradient = android.graphics.LinearGradient(\n                        0f, 0f, 200f, 150f,\n                        intArrayOf(0xFF6200EE.toInt(), 0xFF03DAC5.toInt(), 0xFFBB86FC.toInt()),\n                        null, android.graphics.Shader.TileMode.CLAMP\n                    )\n                    paint.shader = gradient\n                    canvas.drawRect(0f, 0f, 200f, 150f, paint)\n                    val textPaint = android.graphics.Paint().apply {\n                        color = android.graphics.Color.WHITE\n                        textSize = 40f\n                        textAlign = android.graphics.Paint.Align.CENTER\n                        isAntiAlias = true\n                        typeface = android.graphics.Typeface.DEFAULT_BOLD\n                    }\n                    canvas.drawText("TEST", 100f, 85f, textPaint)\n                    val stream = java.io.ByteArrayOutputStream()\n                    bmp.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, stream)\n                    bmp.recycle()\n                    put("picture", android.util.Base64.encodeToString(stream.toByteArray(), android.util.Base64.NO_WRAP))\n                })\n            }\n'''

new_image_case = '''            TestNotifType.IMAGE -> {\n                fun probePicture(label: String): String {\n                    val bmp = android.graphics.Bitmap.createBitmap(320, 200, android.graphics.Bitmap.Config.ARGB_8888)\n                    val canvas = android.graphics.Canvas(bmp)\n                    canvas.drawColor(0xFF1565C0.toInt())\n                    val p = android.graphics.Paint().apply {\n                        color = android.graphics.Color.WHITE\n                        textSize = 34f\n                        textAlign = android.graphics.Paint.Align.CENTER\n                        isAntiAlias = true\n                        typeface = android.graphics.Typeface.DEFAULT_BOLD\n                    }\n                    canvas.drawText(label, 160f, 115f, p)\n                    val out = java.io.ByteArrayOutputStream()\n                    bmp.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out)\n                    bmp.recycle()\n                    return android.util.Base64.encodeToString(out.toByteArray(), android.util.Base64.NO_WRAP)\n                }\n\n                fun groupProbe(variant: String, picLabel: String) =\n                    buildBaseTestJson(packageName, "CHILD_$variant", "CHILD_TEXT_$variant", "_hun_group_$variant").apply {\n                        put("hunGroupProbe", true)\n                        put("hunGroupVariant", variant)\n                        put("picture", probePicture(picLabel))\n                        put("notifPriority", 2)\n                        put("showOpenButton", false)\n                        put("showMuteButton", false)\n                        put("showSnoozeButton", false)\n                    }\n\n                listOf(\n                    groupProbe("BASE", "PIC_BASE"),\n                    groupProbe("CHILDREN", "PIC_CHILDREN"),\n                    groupProbe("SILENTLOW", "PIC_SILENTLOW"),\n                    groupProbe("SUMMARY", "PIC_SUMMARY")\n                )\n            }\n'''

s = replace_once(s, old_image_case, new_image_case, "replace IMAGE with group-selection probe")
main.write_text(s)

wear = Path("wear/src/main/java/com/notifmirror/wear/NotificationHandler.kt")
w = wear.read_text()

w = replace_once(
    w,
    '''            val pictureBase64 = json.optString("picture", "")\n            val appLabel = json.optString("appLabel", "")\n''',
    '''            val pictureBase64 = json.optString("picture", "")\n            val appLabel = json.optString("appLabel", "")\n            val hunGroupProbe = json.optBoolean("hunGroupProbe", false)\n            val hunGroupVariant = json.optString("hunGroupVariant", "")\n''',
    "read group probe metadata",
)

w = replace_once(
    w,
    '''                isMessagingStyle = isMessagingStyle,\n                notifTag = notifTag, shortcutId = shortcutId\n            )\n''',
    '''                isMessagingStyle = isMessagingStyle,\n                notifTag = notifTag, shortcutId = shortcutId,\n                hunGroupProbe = hunGroupProbe, hunGroupVariant = hunGroupVariant\n            )\n''',
    "pass group probe metadata",
)

w = replace_once(
    w,
    '''        isMessagingStyle: Boolean = false,\n        notifTag: String = "",\n        shortcutId: String = ""\n    ) {\n''',
    '''        isMessagingStyle: Boolean = false,\n        notifTag: String = "",\n        shortcutId: String = "",\n        hunGroupProbe: Boolean = false,\n        hunGroupVariant: String = ""\n    ) {\n''',
    "group probe args",
)

builder_anchor = '''            .setOnlyAlertOnce(silentUpdate)\n            .setSilent(isSilent || vibrateOnly || silentUpdate || alertMode == 1 || alertMode == 2)\n\n'''
probe_renderer = builder_anchor + '''        if (hunGroupProbe) {\n            val probeGroup = "hun_probe_group_$hunGroupVariant"\n            builder.setPriority(NotificationCompat.PRIORITY_MAX)\n                .setCategory(NotificationCompat.CATEGORY_MESSAGE)\n                .setContentTitle("CHILD_$hunGroupVariant")\n                .setContentText("CHILD_TEXT_$hunGroupVariant")\n                .setTicker("CHILD_TICKER_$hunGroupVariant")\n                .setGroup(probeGroup)\n                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)\n\n            when (hunGroupVariant) {\n                "CHILDREN", "SILENTLOW" -> builder.setGroupAlertBehavior(NotificationCompat.GROUP_ALERT_CHILDREN)\n                "SUMMARY" -> builder.setGroupAlertBehavior(NotificationCompat.GROUP_ALERT_SUMMARY)\n            }\n\n            if (pictureBitmap != null) {\n                builder.setStyle(\n                    NotificationCompat.BigPictureStyle()\n                        .bigPicture(pictureBitmap)\n                        .setBigContentTitle("CHILD_$hunGroupVariant")\n                        .setSummaryText("CHILD_PIC_$hunGroupVariant")\n                )\n            }\n        }\n\n'''
w = replace_once(w, builder_anchor, probe_renderer, "group probe child renderer")

# Keep the normal style code from overriding the probe's BigPictureStyle.
w = replace_once(
    w,
    '''        if (!hideContent && pictureBitmap != null) {\n''',
    '''        if (!hunGroupProbe && !hideContent && pictureBitmap != null) {\n''',
    "disable normal picture style during group probe",
)
w = replace_once(
    w,
    '''        } else if (!hideContent && conversationHistory.isNotEmpty()) {\n''',
    '''        } else if (!hunGroupProbe && !hideContent && conversationHistory.isNotEmpty()) {\n''',
    "disable normal messaging style during group probe",
)
w = replace_once(
    w,
    '''        } else if (!hideContent && text.length > bigTextThreshold) {\n''',
    '''        } else if (!hunGroupProbe && !hideContent && text.length > bigTextThreshold) {\n''',
    "disable normal bigtext during group probe",
)

summary_anchor = '''        // Create/update summary notification for the per-app group.\n        // Uses a tag ("summary") to prevent ID collision with regular notification IDs.\n'''
custom_summary = '''        if (hunGroupProbe) {\n            val probeGroup = "hun_probe_group_$hunGroupVariant"\n            val probeSummary = NotificationCompat.Builder(context, channelId)\n                .setSmallIcon(R.drawable.ic_notification)\n                .setContentTitle("SUMMARY_$hunGroupVariant")\n                .setContentText("SUMMARY_TEXT_$hunGroupVariant")\n                .setTicker("SUMMARY_TICKER_$hunGroupVariant")\n                .setCategory(NotificationCompat.CATEGORY_MESSAGE)\n                .setGroup(probeGroup)\n                .setGroupSummary(true)\n                .setAutoCancel(true)\n                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)\n                .setPriority(NotificationCompat.PRIORITY_MAX)\n\n            when (hunGroupVariant) {\n                "CHILDREN" -> probeSummary.setGroupAlertBehavior(NotificationCompat.GROUP_ALERT_CHILDREN)\n                "SILENTLOW" -> probeSummary\n                    .setGroupAlertBehavior(NotificationCompat.GROUP_ALERT_CHILDREN)\n                    .setPriority(NotificationCompat.PRIORITY_MIN)\n                    .setSilent(true)\n                    .setOnlyAlertOnce(true)\n                "SUMMARY" -> probeSummary.setGroupAlertBehavior(NotificationCompat.GROUP_ALERT_SUMMARY)\n            }\n\n            val probeSummaryId = ("hun_probe_summary_" + hunGroupVariant).hashCode()\n            nm.notify(SUMMARY_TAG, probeSummaryId, probeSummary.build())\n            Log.d(TAG, "HUN group probe posted: variant=$hunGroupVariant child=$notifId summary=$probeSummaryId")\n            return\n        }\n\n'''
w = replace_once(w, summary_anchor, custom_summary + summary_anchor, "custom group probe summary")

wear.write_text(w)
print("HUN group selection probe applied")
