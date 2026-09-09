from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)

main = Path("mobile/src/main/java/com/notifmirror/mobile/MainActivity.kt")
s = main.read_text()

s = replace_once(s,
'''        IMAGE("With Image", "Notification with an attached picture (BigPictureStyle)")\n''',
'''        IMAGE("With Image", "Notification with an attached picture (BigPictureStyle)"),\n        HUN_FIELD_PROBE("HUN Field Probe", "3 diagnostic HUNs: text fields, BigPicture, MessagingStyle")\n''',
"enum")

s = replace_once(s,
'''                    TestNotifType.IMAGE -> {\n                        countRow.visibility = View.GONE\n                        delayRow.visibility = View.GONE\n                        titleInput.setText("Photo Shared")\n                        textInput.setText("Check out this picture!")\n                    }\n''',
'''                    TestNotifType.IMAGE -> {\n                        countRow.visibility = View.GONE\n                        delayRow.visibility = View.GONE\n                        titleInput.setText("Photo Shared")\n                        textInput.setText("Check out this picture!")\n                    }\n                    TestNotifType.HUN_FIELD_PROBE -> {\n                        countRow.visibility = View.GONE\n                        delayRow.visibility = View.GONE\n                        titleInput.setText("HUN PROBE")\n                        textInput.setText("Field mapping diagnostic")\n                    }\n''',
"ui")

s = replace_once(s,
'''                    if (index < testMessages.size - 1 && testMessages.size > 1) {\n                        kotlinx.coroutines.delay(delayMs)\n                    }\n''',
'''                    if (index < testMessages.size - 1 && testMessages.size > 1) {\n                        val effectiveDelay = if (type == TestNotifType.HUN_FIELD_PROBE) 8000L else delayMs\n                        kotlinx.coroutines.delay(effectiveDelay)\n                    }\n''',
"delay")

progress_anchor = '''            TestNotifType.PROGRESS -> {\n'''
probe_case = '''            TestNotifType.HUN_FIELD_PROBE -> {\n                fun probePicture(label: String): String {\n                    val bmp = android.graphics.Bitmap.createBitmap(320, 200, android.graphics.Bitmap.Config.ARGB_8888)\n                    val canvas = android.graphics.Canvas(bmp)\n                    canvas.drawColor(0xFF1565C0.toInt())\n                    val p = android.graphics.Paint().apply {\n                        color = android.graphics.Color.WHITE\n                        textSize = 42f\n                        textAlign = android.graphics.Paint.Align.CENTER\n                        isAntiAlias = true\n                        typeface = android.graphics.Typeface.DEFAULT_BOLD\n                    }\n                    canvas.drawText(label, 160f, 115f, p)\n                    val out = java.io.ByteArrayOutputStream()\n                    bmp.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out)\n                    bmp.recycle()\n                    return android.util.Base64.encodeToString(out.toByteArray(), android.util.Base64.NO_WRAP)\n                }\n\n                val basic = buildBaseTestJson(packageName, "TITLE_A", "TEXT_B", "_hun_basic").apply {\n                    put("hunProbe", true); put("hunProbeVariant", "basic")\n                    put("subText", "SUB_C"); put("notifPriority", 2)\n                    put("showOpenButton", false); put("showMuteButton", false); put("showSnoozeButton", false)\n                }\n                val picture = buildBaseTestJson(packageName, "PIC_TITLE_A", "PIC_TEXT_B", "_hun_picture").apply {\n                    put("hunProbe", true); put("hunProbeVariant", "picture")\n                    put("subText", "PIC_SUB_C"); put("picture", probePicture("BIGPIC_P")); put("notifPriority", 2)\n                    put("showOpenButton", false); put("showMuteButton", false); put("showSnoozeButton", false)\n                }\n                val msgs = JSONArray().apply {\n                    put(JSONObject().apply { put("sender", "SENDER_M"); put("text", "MESSAGE_M1") })\n                    put(JSONObject().apply { put("sender", "SENDER_N"); put("text", "MESSAGE_M2") })\n                }\n                val messaging = buildBaseTestJson(packageName, "MSG_TITLE_A", "MSG_TEXT_B", "_hun_msg").apply {\n                    put("hunProbe", true); put("hunProbeVariant", "messaging")\n                    put("subText", "MSG_SUB_C"); put("isMessagingStyle", true); put("conversationTitle", "CONV_H")\n                    put("conversationMessages", msgs); put("notifPriority", 2)\n                    put("showOpenButton", false); put("showMuteButton", false); put("showSnoozeButton", false)\n                }\n                listOf(basic, picture, messaging)\n            }\n\n'''
s = replace_once(s, progress_anchor, probe_case + progress_anchor, "build probe")
main.write_text(s)

wear = Path("wear/src/main/java/com/notifmirror/wear/NotificationHandler.kt")
w = wear.read_text()

w = replace_once(w,
'''            val pictureBase64 = json.optString("picture", "")\n            val appLabel = json.optString("appLabel", "")\n''',
'''            val pictureBase64 = json.optString("picture", "")\n            val appLabel = json.optString("appLabel", "")\n            val hunProbe = json.optBoolean("hunProbe", false)\n            val hunProbeVariant = json.optString("hunProbeVariant", "")\n''',
"read metadata")

w = replace_once(w,
'''                isMessagingStyle = isMessagingStyle,\n                notifTag = notifTag, shortcutId = shortcutId\n            )\n''',
'''                isMessagingStyle = isMessagingStyle,\n                notifTag = notifTag, shortcutId = shortcutId,\n                hunProbe = hunProbe, hunProbeVariant = hunProbeVariant\n            )\n''',
"pass metadata")

w = replace_once(w,
'''        isMessagingStyle: Boolean = false,\n        notifTag: String = "",\n        shortcutId: String = ""\n    ) {\n''',
'''        isMessagingStyle: Boolean = false,\n        notifTag: String = "",\n        shortcutId: String = "",\n        hunProbe: Boolean = false,\n        hunProbeVariant: String = ""\n    ) {\n''',
"args")

builder_anchor = '''            .setOnlyAlertOnce(silentUpdate)\n            .setSilent(isSilent || vibrateOnly || silentUpdate || alertMode == 1 || alertMode == 2)\n\n'''
probe_renderer = builder_anchor + '''        if (hunProbe) {\n            builder.setPriority(NotificationCompat.PRIORITY_MAX)\n                .setCategory(NotificationCompat.CATEGORY_MESSAGE)\n                .setContentTitle(if (hunProbeVariant == "picture") "PIC_TITLE_A" else if (hunProbeVariant == "messaging") "MSG_TITLE_A" else "TITLE_A")\n                .setContentText(if (hunProbeVariant == "picture") "PIC_TEXT_B" else if (hunProbeVariant == "messaging") "MSG_TEXT_B" else "TEXT_B")\n                .setSubText(if (hunProbeVariant == "picture") "PIC_SUB_C" else if (hunProbeVariant == "messaging") "MSG_SUB_C" else "SUB_C")\n                .setTicker(if (hunProbeVariant == "picture") "PIC_TICKER_G" else if (hunProbeVariant == "messaging") "MSG_TICKER_G" else "TICKER_G")\n                .setGroup(null)\n\n            when (hunProbeVariant) {\n                "picture" -> if (pictureBitmap != null) {\n                    builder.setLargeIcon(iconBitmap)\n                    builder.setStyle(NotificationCompat.BigPictureStyle()\n                        .bigPicture(pictureBitmap)\n                        .setBigContentTitle("PIC_BIGTITLE_E")\n                        .setSummaryText("PIC_SUMMARY_D"))\n                }\n                "messaging" -> {\n                    val user = Person.Builder().setName("USER_U").build()\n                    val st = NotificationCompat.MessagingStyle(user).setConversationTitle("CONV_H").setGroupConversation(true)\n                    st.addMessage(NotificationCompat.MessagingStyle.Message("MESSAGE_M1", System.currentTimeMillis()-1000L, Person.Builder().setName("SENDER_M").build()))\n                    st.addMessage(NotificationCompat.MessagingStyle.Message("MESSAGE_M2", System.currentTimeMillis(), Person.Builder().setName("SENDER_N").build()))\n                    builder.setStyle(st)\n                }\n                else -> builder.setStyle(NotificationCompat.BigTextStyle()\n                    .setBigContentTitle("BIGTITLE_E")\n                    .bigText("BIGTEXT_F")\n                    .setSummaryText("SUMMARY_D"))\n            }\n        }\n\n'''
w = replace_once(w, builder_anchor, probe_renderer, "renderer")

w = replace_once(w,
'''        if (!hideContent && pictureBitmap != null) {\n''',
'''        if (!hunProbe && !hideContent && pictureBitmap != null) {\n''',
"picture override")
w = replace_once(w,
'''        } else if (!hideContent && conversationHistory.isNotEmpty()) {\n''',
'''        } else if (!hunProbe && !hideContent && conversationHistory.isNotEmpty()) {\n''',
"msg override")
w = replace_once(w,
'''        } else if (!hideContent && text.length > bigTextThreshold) {\n''',
'''        } else if (!hunProbe && !hideContent && text.length > bigTextThreshold) {\n''',
"bigtext override")

summary_anchor = '''        // Create/update summary notification for the per-app group.\n        // Uses a tag ("summary") to prevent ID collision with regular notification IDs.\n'''
w = replace_once(w, summary_anchor,
'''        if (hunProbe) {\n            Log.d(TAG, "HUN probe posted: variant=$hunProbeVariant id=$notifId; group summary suppressed")\n            return\n        }\n\n''' + summary_anchor,
"summary suppression")

wear.write_text(w)
print("HUN field probe applied")
