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

            // Scale down if too large — Wear MessageClient has a ~100KB payload limit,
            // and we're already sending icon + actions + messages in the same payload.
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

old_start = '''        // Stack conversation messages using MessagingStyle for better WearOS rendering
        if (!hideContent && conversationHistory.size > 1) {
'''
new_start = '''        // Media takes priority because a notification can have only one Style.
        // Telegram is MessagingStyle but may also carry an image attachment.
        if (!hideContent && pictureBitmap != null) {
            builder.setStyle(
                NotificationCompat.BigPictureStyle()
                    .bigPicture(pictureBitmap)
                    .setSummaryText(displayText)
            )
        // Use MessagingStyle even for the first message so its text is shown consistently.
        } else if (!hideContent && conversationHistory.isNotEmpty()) {
'''
w = replace_once(w, old_start, new_start, "wear MessagingStyle condition")

old_picture = '''        } else if (!hideContent && pictureBitmap != null) {
            // BigPictureStyle for notifications with attached images (e.g. photo messages)
            builder.setStyle(
                NotificationCompat.BigPictureStyle()
                    .bigPicture(pictureBitmap)
                    .setSummaryText(text)
            )
'''
w = replace_once(w, old_picture, "", "wear duplicate BigPictureStyle")
wear.write_text(w)

print("Telegram media source changes applied")
