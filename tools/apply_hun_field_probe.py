from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)


main = Path("mobile/src/main/java/com/notifmirror/mobile/MainActivity.kt")
s = main.read_text()

# Reuse the existing IMAGE enum value so no exhaustive when(TestNotifType) branches break.
s = replace_once(
    s,
    '        IMAGE("With Image", "Notification with an attached picture (BigPictureStyle)")\n',
    '        IMAGE("HUN Field Probe", "3 diagnostic HUNs: text fields, BigPicture, MessagingStyle")\n',
    "rename IMAGE probe type",
)

s = replace_once(
    s,
    '''                    TestNotifType.IMAGE -> {\n                        countRow.visibility = View.GONE\n                        delayRow.visibility = View.GONE\n                        titleInput.setText("Photo Shared")\n                        textInput.setText("Check out this picture!")\n                    }\n''',
    '''                    TestNotifType.IMAGE -> {\n                        countRow.visibility = View.GONE\n                        delayRow.visibility = View.GONE\n                        titleInput.setText("HUN PROBE")\n                        textInput.setText("Field mapping diagnostic")\n                    }\n''',
    "IMAGE probe UI",
)

s = replace_once(
    s,
    '''                    if (index < testMessages.size - 1 && testMessages.size > 1) {\n                        kotlinx.coroutines.delay(delayMs)\n                    }\n''',
    '''                    if (index < testMessages.size - 1 && testMessages.size > 1) {\n                        val effectiveDelay = if (type == TestNotifType.IMAGE) 8000L else delayMs\n                        kotlinx.coroutines.delay(effectiveDelay)\n                    }\n''',
    "probe delay",
)

old_image_case = '''            TestNotifType.IMAGE -> {\n                listOf(buildBaseTestJson(packageName, title, text, "_image").apply {\n                    // Generate a small colored gradient test image as base64\n                    val bmp = android.graphics.Bitmap.createBitmap(200, 150, android.graphics.Bitmap.Config.ARGB_8888)\n                    val canvas = android.graphics.Canvas(bmp)\n                    val paint = android.graphics.Paint()\n                    val gradient = android.graphics.LinearGradient(\n                        0f, 0f, 200f, 150f,\n                        intArrayOf(0xFF6200EE.toInt(), 0xFF03DAC5.toInt(), 0xFFBB86FC.toInt()),\n                        null, android.graphics.Shader.TileMode.CLAMP\n                    )\n                    paint.shader = gradient\n                    canvas.drawRect(0f, 0f, 200f, 150f, paint)\n                    val textPaint = android.graphics.Paint().apply {\n                        color = android.graphics.Color.WHITE\n                        textSize = 40f\n                        textAlign = android.graphics.Paint.Align.CENTER\n                        isAntiAlias = true\n                        typeface = android.graphics.Typeface.DEFAULT_BOLD\n                    }\n                    canvas.drawText("TEST", 100f, 85f, textPaint)\n                    val stream = java.io.ByteArrayOutputStream()\n                    bmp.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, stream)\n                    bmp.recycle()\n                    put("picture", android.util.Base64.encodeToString(stream.toByteArray(), android.util.Base64.NO_WRAP))\n                })\n            }\n'''

new_image_case = '''            TestNotifType.IMAGE -> {\n                fun probePicture(label: String): String {\n                    val bmp = android.graphics.Bitmap.createBitmap(320, 200, android.graphics.Bitmap.Config.ARGB_8888)\n                    val canvas = android.graphics.Canvas(bmp)\n                    canvas.drawColor(0xFF1565C0.toInt())\n                    val p = android.graphics.Paint().apply {\n                        color = android.graphics.Color.WHITE\n                        textSize = 42f\n                        textAlign = android.graphics.Paint.Align.CENTER\n                        isAntiAlias = true\n                        typeface = android.graphics.Typeface.DEFAULT_BOLD\n                    }\n                    canvas.drawText(label, 160f, 115f, p)\n                    val out = java.io.ByteArrayOutputStream()\n                    bmp.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out)\n                    bmp.recycle()\n                    return android.util.Base64.encodeToString(out.toByteArray(), android.util.Base64.NO_WRAP)\n                }\n\n                val basic = buildBaseTestJson(packageName, "TITLE_A", "TEXT_B", "_hun_basic").apply {\n                    put("hunProbe", true)\n                    put("hunProbeVariant", "basic")\n                    put("subText", "SUB_C")\n                    put("notifPriority", 2)\n                    put("showOpenButton", false)\n                    put("showMuteButton", false)\n                    put("showSnoozeButton", false)\n                }\n\n                val picture = buildBaseTestJson(packageName, "PIC_TITLE_A", "PIC_TEXT_B", "_hun_picture").apply {\n                    put("hunProbe", true)\n                    put("hunProbeVariant", "picture")\n                    put("subText", "PIC_SUB_C")\n                    put("picture", probePicture("BIGPIC_P"))\n                    put("notifPriority", 2)\n                    put("showOpenButton", false)\n                    put("showMuteButton", false)\n                    put("showSnoozeButton", false)\n                }\n\n                val msgs = JSONArray().apply {\n                    put(JSONObject().apply { put("sender", "SENDER_M"); put("text", "MESSAGE_M1") })\n                    put(JSONObject().apply { put("sender", "SENDER_N"); put("text", "MESSAGE_M2") })\n                }\n                val messaging = buildBaseTestJson(packageName, "MSG_TITLE_A", "MSG_TEXT_B", "_hun_msg").apply {\n                    put("hunProbe", true)\n                    put("hunProbeVariant", "messaging")\n                    put("subText", "MSG_SUB_C")\n                    put("isMessagingStyle", true)\n                    put("conversationTitle", "CONV_H")\n                    put("conversationMessages", msgs)\n                    put("notifPriority", 2)\n                    put("showOpenButton", false)\n                    put("showMuteButton", false)\n                    put("showSnoozeButton", false)\n                }\n                listOf(basic, picture, messaging)\n            }\n'''

s = replace_once(s, old_image_case, new_image_case, "replace IMAGE with 3-part probe")
main.write_text(s)

wear = Path("wear/src/main/java/com/notifmirror/wear/NotificationHandler.kt")
w = wear.read_text()

w = replace_once(
    w,
    '''            val pictureBase64 = json.optString("picture", "")\n            val appLabel = json.optString("appLabel", "")\n''',
    '''            val pictureBase64 = json.optString("picture", "")\n            val appLabel = json.optString("appLabel", "")\n            val hunProbe = json.optBoolean("hunProbe", false)\n            val hunProbeVariant = json.optString("hunProbeVariant", "")\n''',
    "read probe metadata",
)

w = replace_once(
    w,
    '''                isMessagingStyle = isMessagingStyle,\n                notifTag = notifTag, shortcutId = shortcutId\n            )\n''',
    '''                isMessagingStyle = isMessagingStyle,\n                notifTag = notifTag, shortcutId = shortcutId,\n                hunProbe = hunProbe, hunProbeVariant = hunProbeVariant\n            )\n''',
    "pass probe metadata",
)

w = replace_once(
    w,
    '''        isMessagingStyle: Boolean = false,\n        notifTag: String = "",\n        shortcutId: String = ""\n    ) {\n''',
    '''        isMessagingStyle: Boolean = false,\n        notifTag: String = "",\n        shortcutId: String = "",\n        hunProbe: Boolean = false,\n        hunProbeVariant: String = ""\n    ) {\n''',
    "probe args",
)

builder_anchor = '''            .setOnlyAlertOnce(silentUpdate)\n            .setSilent(isSilent || vibrateOnly || silentUpdate || alertMode == 1 || alertMode == 2)\n\n'''
probe_renderer = builder_anchor + '''        if (hunProbe) {\n            builder.setPriority(NotificationCompat.PRIORITY_MAX)\n                .setCategory(NotificationCompat.CATEGORY_MESSAGE)\n                .setContentTitle(when (hunProbeVariant) {\n                    "picture" -> "PIC_TITLE_A"\n                    "messaging" -> "MSG_TITLE_A"\n                    else -> "TITLE_A"\n                })\n                .setContentText(when (hunProbeVariant) {\n                    "picture" -> "PIC_TEXT_B"\n                    "messaging" -> "MSG_TEXT_B"\n                    else -> "TEXT_B"\n                })\n                .setSubText(when (hunProbeVariant) {\n                    "picture" -> "PIC_SUB_C"\n                    "messaging" -> "MSG_SUB_C"\n                    else -> "SUB_C"\n                })\n                .setTicker(when (hunProbeVariant) {\n                    "picture" -> "PIC_TICKER_G"\n                    "messaging" -> "MSG_TICKER_G"\n                    else -> "TICKER_G"\n                })\n                .setGroup(null)\n\n            when (hunProbeVariant) {\n                "picture" -> if (pictureBitmap != null) {\n                    if (iconBitmap != null) builder.setLargeIcon(iconBitmap)\n                    builder.setStyle(\n                        NotificationCompat.BigPictureStyle()\n                            .bigPicture(pictureBitmap)\n                            .setBigContentTitle("PIC_BIGTITLE_E")\n                            .setSummaryText("PIC_SUMMARY_D")\n                    )\n                }\n                "messaging" -> {\n                    val user = Person.Builder().setName("USER_U").build()\n                    val st = NotificationCompat.MessagingStyle(user)\n                        .setConversationTitle("CONV_H")\n                        .setGroupConversation(true)\n                    st.addMessage(NotificationCompat.MessagingStyle.Message(\n                        "MESSAGE_M1", System.currentTimeMillis() - 1000L,\n                        Person.Builder().setName("SENDER_M").build()\n                    ))\n                    st.addMessage(NotificationCompat.MessagingStyle.Message(\n                        "MESSAGE_M2", System.currentTimeMillis(),\n                        Person.Builder().setName("SENDER_N").build()\n                    ))\n                    builder.setStyle(st)\n                }\n                else -> builder.setStyle(\n                    NotificationCompat.BigTextStyle()\n                        .setBigContentTitle("BIGTITLE_E")\n                        .bigText("BIGTEXT_F")\n                        .setSummaryText("SUMMARY_D")\n                )\n            }\n        }\n\n'''
w = replace_once(w, builder_anchor, probe_renderer, "probe renderer")

# The stable Telegram patch runs before this probe and changes these style conditions.
w = replace_once(
    w,
    '''        if (!hideContent && pictureBitmap != null) {\n''',
    '''        if (!hunProbe && !hideContent && pictureBitmap != null) {\n''',
    "disable normal picture style during probe",
)
w = replace_once(
    w,
    '''        } else if (!hideContent && conversationHistory.isNotEmpty()) {\n''',
    '''        } else if (!hunProbe && !hideContent && conversationHistory.isNotEmpty()) {\n''',
    "disable normal messaging style during probe",
)
w = replace_once(
    w,
    '''        } else if (!hideContent && text.length > bigTextThreshold) {\n''',
    '''        } else if (!hunProbe && !hideContent && text.length > bigTextThreshold) {\n''',
    "disable normal bigtext during probe",
)

summary_anchor = '''        // Create/update summary notification for the per-app group.\n        // Uses a tag ("summary") to prevent ID collision with regular notification IDs.\n'''
w = replace_once(
    w,
    summary_anchor,
    '''        if (hunProbe) {\n            Log.d(TAG, "HUN probe posted: variant=$hunProbeVariant id=$notifId; group summary suppressed")\n            return\n        }\n\n''' + summary_anchor,
    "suppress probe summary",
)

wear.write_text(w)
print("HUN field probe applied using existing IMAGE type")
