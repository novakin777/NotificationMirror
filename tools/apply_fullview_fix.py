from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)


wear = Path("wear/src/main/java/com/notifmirror/wear/NotificationHandler.kt")
w = wear.read_text()

if "import androidx.core.content.FileProvider\n" not in w:
    w = replace_once(
        w,
        "import androidx.core.app.RemoteInput\n",
        "import androidx.core.app.RemoteInput\nimport androidx.core.content.FileProvider\n",
        "FileProvider import",
    )

if "import java.io.File\n" not in w:
    w = replace_once(
        w,
        "import org.json.JSONObject\n",
        "import org.json.JSONObject\nimport java.io.File\n",
        "File import",
    )

old_style = '''        // Xiaomi Watch 5's interruption screen only displays the notification title.
        // Put the latest message directly into android.title so the text is visible
        // immediately, while keeping contentText/BigTextStyle for the notification shade.
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

new_style = '''        // Preserve MessagingStyle semantics for Xiaomi MiWearSysUI NotificationFullView.
        // MiWearSysUI's long-lived full-view maps message attachments from
        // MessagingStyle.Message dataMimeType/dataUri, not from BigPictureStyle.
        if (!hideContent && isMessagingStyle) {
            val recent = if (conversationHistory.isNotEmpty()) {
                conversationHistory.takeLast(50)
            } else {
                listOf(Pair(title, text))
            }
            val selfPerson = Person.Builder().setName("You").build()
            val distinctSenders = recent.map { it.first }.distinct()
            val isGroupConversation = distinctSenders.size > 1
            val messagingStyle = NotificationCompat.MessagingStyle(selfPerson)
                .setGroupConversation(isGroupConversation)
                .setConversationTitle(if (isGroupConversation) (conversationTitle.ifEmpty { title }) else null)

            val attachmentUri = if (pictureBitmap != null) {
                createNotificationImageUri(context, notifKey, pictureBitmap)
            } else null

            for ((idx, pair) in recent.withIndex()) {
                val (senderName, msgText) = pair
                val sender = if (senderName == "You") null
                    else Person.Builder().setName(senderName).build()
                val compatMessage = NotificationCompat.MessagingStyle.Message(
                    msgText,
                    System.currentTimeMillis() - (recent.size - idx) * 1000L,
                    sender
                )
                if (idx == recent.lastIndex && attachmentUri != null) {
                    compatMessage.setData("image/jpeg", attachmentUri)
                    Log.d(TAG, "Attached full-view message image URI: $attachmentUri")
                }
                messagingStyle.addMessage(compatMessage)
            }

            builder.setStyle(messagingStyle)
            builder.setNumber(recent.size)
            builder.setContentTitle(if (conversationTitle.isNotEmpty()) conversationTitle else title)
            builder.setContentText(text)
            builder.setTicker(text)
            builder.setSubText(appLabel)
        } else if (!hideContent && pictureBitmap != null) {
            // Non-messaging notifications keep the conventional BigPictureStyle path.
            builder.setStyle(
                NotificationCompat.BigPictureStyle()
                    .bigPicture(pictureBitmap)
                    .setSummaryText(text)
            )
        } else if (!hideContent && text.length > bigTextThreshold) {
            builder.setStyle(NotificationCompat.BigTextStyle().bigText(text))
        }

'''

w = replace_once(w, old_style, new_style, "replace v7 peek style with MiWear full-view MessagingStyle")

helper_anchor = '''    /**
     * Manually vibrate the watch using Vibrator API.
'''
helper = '''    private fun createNotificationImageUri(context: Context, notifKey: String, bitmap: Bitmap): Uri? {
        return try {
            val imageDir = File(context.cacheDir, "notification_images").apply { mkdirs() }
            val fileName = "msg_${notifKey.hashCode() and 0x7FFFFFFF}.jpg"
            val imageFile = File(imageDir, fileName)
            imageFile.outputStream().use { output ->
                if (!bitmap.compress(Bitmap.CompressFormat.JPEG, 85, output)) {
                    throw IllegalStateException("Bitmap JPEG compression failed")
                }
            }
            FileProvider.getUriForFile(
                context,
                "${context.packageName}.notification_images",
                imageFile
            )
        } catch (e: Exception) {
            Log.w(TAG, "Failed to create MessagingStyle image URI", e)
            null
        }
    }

'''
w = replace_once(w, helper_anchor, helper + helper_anchor, "image URI helper")
wear.write_text(w)

manifest = Path("wear/src/main/AndroidManifest.xml")
m = manifest.read_text()
provider_anchor = '''        <uses-library
            android:name="com.google.android.wearable"
            android:required="false" />
'''
provider = '''        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.notification_images"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/notification_image_paths" />
        </provider>

'''
if "notification_image_paths" not in m:
    m = replace_once(m, provider_anchor, provider_anchor + "\n" + provider, "FileProvider manifest entry")
manifest.write_text(m)

paths = Path("wear/src/main/res/xml/notification_image_paths.xml")
paths.parent.mkdir(parents=True, exist_ok=True)
paths.write_text('''<?xml version="1.0" encoding="utf-8"?>\n<paths xmlns:android="http://schemas.android.com/apk/res/android">\n    <cache-path name="notification_images" path="notification_images/" />\n</paths>\n''')

print("MiWear full-view MessagingStyle image bridge applied")
