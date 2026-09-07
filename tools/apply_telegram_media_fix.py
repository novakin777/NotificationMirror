from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)


mobile = Path("mobile/src/main/java/com/notifmirror/mobile/NotificationListener.kt")
s = mobile.read_text()

if "import android.graphics.BitmapFactory\n" not in s:
    s = replace_once(
        s,
        "import android.graphics.Bitmap\n",
        "import android.graphics.Bitmap\nimport android.graphics.BitmapFactory\n",
        "mobile Bitmap import",
    )

old_func = '''    private fun extractPictureBase64(extras: android.os.Bundle): String? {
        return try {
            // EXTRA_PICTURE is set by BigPictureStyle notifications (photo messages, etc.)
            val picture = extras.getParcelable<Bitmap>(Notification.EXTRA_PICTURE) ?: return null

            // Scale down if too large — Wear MessageClient has a ~100KB payload limit,
            // and we're already sending icon + actions + messages in the same payload.
            // Target max dimension 400px for a good balance of quality vs size on watch.
            val maxDim = 400
            val scaled = if (picture.width > maxDim || picture.height > maxDim) {
                val ratio = minOf(maxDim.toFloat() / picture.width, maxDim.toFloat() / picture.height)
                val newW = (picture.width * ratio).toInt().coerceAtLeast(1)
                val newH = (picture.height * ratio).toInt().coerceAtLeast(1)
                Bitmap.createScaledBitmap(picture, newW, newH, true)
            } else {
                picture
            }

            val baos = ByteArrayOutputStream()
            scaled.compress(Bitmap.CompressFormat.JPEG, 70, baos)
            val bytes = baos.toByteArray()
            Log.d(TAG, "Extracted notification picture: ${picture.width}x${picture.height} -> ${scaled.width}x${scaled.height}, ${bytes.size} bytes")
            Base64.encodeToString(bytes, Base64.NO_WRAP)
        } catch (e: Exception) {
            Log.w(TAG, "Failed to extract notification picture", e)
            null
        }
    }
'''

new_func = '''    private fun extractPictureBase64(extras: android.os.Bundle): String? {
        return try {
            // Existing BigPictureStyle path.
            val bigPicture = extras.getParcelable<Bitmap>(Notification.EXTRA_PICTURE)

            // Telegram and some other messaging apps attach images to a
            // MessagingStyle.Message via setData(mimeType, contentUri).
            // In EXTRA_MESSAGES these are Bundle keys "type" and "uri".
            val messagingPicture = if (bigPicture == null) {
                val messageBundles = extras.getParcelableArray(Notification.EXTRA_MESSAGES)
                var found: Bitmap? = null
                if (messageBundles != null) {
                    for (i in messageBundles.indices.reversed()) {
                        val item = messageBundles[i] as? android.os.Bundle ?: continue
                        val mime = item.getString("type") ?: continue
                        if (!mime.startsWith("image/")) continue
                        val uri = item.getParcelable<android.net.Uri>("uri") ?: continue
                        try {
                            contentResolver.openInputStream(uri)?.use { input ->
                                val decoded = BitmapFactory.decodeStream(input)
                                if (decoded != null) {
                                    found = decoded
                                    Log.d(TAG, "Extracted MessagingStyle image: mime=$mime uri=$uri ${decoded.width}x${decoded.height}")
                                }
                            }
                        } catch (e: Exception) {
                            Log.w(TAG, "Failed to decode MessagingStyle image: $mime $uri", e)
                        }
                        if (found != null) break
                    }
                }
                found
            } else null

            val picture = bigPicture ?: messagingPicture ?: return null

            val maxDim = 400
            val scaled = if (picture.width > maxDim || picture.height > maxDim) {
                val ratio = minOf(maxDim.toFloat() / picture.width, maxDim.toFloat() / picture.height)
                val newW = (picture.width * ratio).toInt().coerceAtLeast(1)
                val newH = (picture.height * ratio).toInt().coerceAtLeast(1)
                Bitmap.createScaledBitmap(picture, newW, newH, true)
            } else {
                picture
            }

            val baos = ByteArrayOutputStream()
            scaled.compress(Bitmap.CompressFormat.JPEG, 70, baos)
            val bytes = baos.toByteArray()
            Log.d(TAG, "Extracted notification picture: ${picture.width}x${picture.height} -> ${scaled.width}x${scaled.height}, ${bytes.size} bytes")
            Base64.encodeToString(bytes, Base64.NO_WRAP)
        } catch (e: Exception) {
            Log.w(TAG, "Failed to extract notification picture", e)
            null
        }
    }
'''

s = replace_once(s, old_func, new_func, "mobile extractPictureBase64")
mobile.write_text(s)

wear = Path("wear/src/main/java/com/notifmirror/wear/NotificationHandler.kt")
w = wear.read_text()

old_category = '''            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setGroup(groupId)
'''
new_category = '''            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setGroup(groupId)
'''
w = replace_once(w, old_category, new_category, "wear notification visibility")

old_large_icon = '''        if (iconBitmap != null) {
            builder.setLargeIcon(iconBitmap)
        }
'''
new_large_icon = '''        if (pictureBitmap != null) {
            builder.setLargeIcon(pictureBitmap)
        } else if (iconBitmap != null) {
            builder.setLargeIcon(iconBitmap)
        }
'''
w = replace_once(w, old_large_icon, new_large_icon, "wear glance image")

style_start = '''        // Stack conversation messages using MessagingStyle for better WearOS rendering
        if (!hideContent && conversationHistory.size > 1) {
'''
start = w.find(style_start)
if start < 0:
    raise SystemExit("anchor not found: wear style block start")

style_end_marker = '''        if (actionsArray != null) {
'''
end = w.find(style_end_marker, start)
if end < 0:
    raise SystemExit("anchor not found: wear style block end")

new_style_block = '''        // Keep the previously working child-notification rendering.
        val latestConversationMessage = conversationHistory.lastOrNull()
        val senderName = latestConversationMessage?.first?.takeIf { it.isNotEmpty() } ?: displayTitle
        val peekText = latestConversationMessage?.second?.takeIf { it.isNotEmpty() } ?: displayText
        val peekTitle = if (isMessagingStyle && peekText.isNotEmpty()) {
            if (senderName.isNotEmpty() && senderName != peekText) "$senderName: $peekText" else peekText
        } else {
            displayTitle
        }

        if (!hideContent) {
            builder.setContentTitle(peekTitle)
            builder.setContentText(peekText)
            builder.setTicker(peekText)

            if (pictureBitmap != null) {
                builder.setStyle(
                    NotificationCompat.BigPictureStyle()
                        .bigPicture(pictureBitmap)
                        .setBigContentTitle(peekTitle)
                        .setSummaryText(peekText)
                )
            } else if (isMessagingStyle || peekText.length > bigTextThreshold) {
                builder.setStyle(
                    NotificationCompat.BigTextStyle()
                        .setBigContentTitle(peekTitle)
                        .bigText(peekText)
                )
            }
        }

'''

w = w[:start] + new_style_block + w[end:]

old_summary = '''        val summaryBuilder = NotificationCompat.Builder(context, channelId)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(appLabel)
            .setContentText(title)
            .setSubText(appLabel)
            .setGroup(groupId)
            .setGroupSummary(true)
            .setAutoCancel(true)
            .setSilent(true)
            .setStyle(NotificationCompat.InboxStyle()
                .setSummaryText(appLabel))
        nm.notify(SUMMARY_TAG, summaryId, summaryBuilder.build())
'''

new_summary = '''        // Xiaomi MiWearSysUI turns the group summary into the long-lived HUN.
        // With only one active child this summary is unnecessary and steals the HUN
        // from the real notification (including its BigPictureStyle). Suppress it.
        val activeChildCount = synchronized(idLock) {
            convKeyToPackage.values.count { it == packageName }
        }

        if (activeChildCount > 1) {
            val summaryBuilder = NotificationCompat.Builder(context, channelId)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(appLabel)
                .setContentText(title)
                .setSubText(appLabel)
                .setGroup(groupId)
                .setGroupSummary(true)
                .setGroupAlertBehavior(NotificationCompat.GROUP_ALERT_CHILDREN)
                .setAutoCancel(true)
                .setSilent(true)
                .setPriority(NotificationCompat.PRIORITY_MIN)
                .setStyle(NotificationCompat.InboxStyle()
                    .setSummaryText(appLabel))
            nm.notify(SUMMARY_TAG, summaryId, summaryBuilder.build())
            Log.d(TAG, "Posted non-alerting group summary for $packageName ($activeChildCount children)")
        } else {
            // Remove a stale summary if the package dropped back to one conversation.
            nm.cancel(SUMMARY_TAG, summaryId)
            Log.d(TAG, "Suppressed group summary for $packageName; child owns HUN")
        }
'''

w = replace_once(w, old_summary, new_summary, "MiWear child-only HUN routing")
wear.write_text(w)

print("Telegram media + MiWear child-only HUN routing source changes applied")
