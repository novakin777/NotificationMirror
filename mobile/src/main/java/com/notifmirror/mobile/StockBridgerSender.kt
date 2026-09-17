package com.notifmirror.mobile

import android.app.Notification
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.service.notification.StatusBarNotification
import android.util.Log
import com.google.android.gms.wearable.Asset
import com.google.android.gms.wearable.DataMap
import com.google.android.gms.wearable.PutDataMapRequest
import com.google.android.gms.wearable.Wearable
import kotlinx.coroutines.tasks.await
import java.io.ByteArrayOutputStream

object StockBridgerSender {
    private const val TAG = "STOCK-BRIDGER"
    private const val TELEGRAM = "org.telegram.messenger.web"

    suspend fun sendTelegramPhoto(context: Context, sbn: StatusBarNotification): Boolean {
        if (sbn.packageName != TELEGRAM) return false
        val notification = sbn.notification ?: return false
        val extras = notification.extras ?: return false
        val media = findLastImageMessage(notification) ?: run {
            Log.d(TAG, "SKIP no image MessagingStyle message key=${sbn.key}")
            return false
        }
        val imageBytes = readAndCompressImage(context, media.uri) ?: run {
            Log.w(TAG, "SKIP failed to read image uri=${media.uri}")
            return false
        }
        val localNode = try {
            Wearable.getNodeClient(context).localNode.await()
        } catch (t: Throwable) {
            Log.e(TAG, "getLocalNode failed", t)
            return false
        }
        val path = buildPath(localNode.id, sbn.packageName, sbn.id, sbn.tag, sbn.key)
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
        val conversationTitle = extras.getCharSequence(Notification.EXTRA_CONVERSATION_TITLE)?.toString() ?: title

        val messageMap = DataMap().apply {
            putString("message_text_raw", media.text.ifBlank { text })
            putString("message_sender_raw", media.sender.ifBlank { title })
            putString("message_sender_key", media.sender.ifBlank { "telegram_sender" })
            putLong("message_timestamp", media.timestamp)
            putString("message_data", "telegram_photo_0")
            putString("message_data_mime_type", media.mime)
            putAsset("message_image", Asset.createFromBytes(imageBytes))
        }

        val request = PutDataMapRequest.create(path).apply {
            dataMap.putString("display_name_raw", "Telegram")
            dataMap.putString("title_raw", title)
            dataMap.putString("text_raw", text)
            dataMap.putString("conversation_title_raw", conversationTitle)
            dataMap.putString("style_name", Notification.MessagingStyle::class.java.name)
            dataMap.putLong("when", sbn.postTime)
            dataMap.putBoolean("show_when", true)
            dataMap.putInt("priority", notification.priority)
            dataMap.putInt("notification_flags", notification.flags)
            dataMap.putDataMapArrayList("messages", arrayListOf(messageMap))
            dataMap.putLong("_notifmirror_probe_revision", System.currentTimeMillis())
        }

        return try {
            val result = Wearable.getDataClient(context)
                .putDataItem(request.asPutDataRequest().setUrgent())
                .await()
            Log.i(TAG, "SENT path=${result.uri.path} bytes=${imageBytes.size} mime=${media.mime} node=${localNode.id}")
            true
        } catch (t: Throwable) {
            Log.e(TAG, "putDataItem failed path=$path", t)
            false
        }
    }

    private data class MediaMessage(
        val text: String,
        val sender: String,
        val timestamp: Long,
        val mime: String,
        val uri: Uri
    )

    private fun findLastImageMessage(notification: Notification): MediaMessage? {
        val bundles = notification.extras?.getParcelableArray(Notification.EXTRA_MESSAGES) ?: return null
        val messages = try {
            Notification.MessagingStyle.Message.getMessagesFromBundleArray(bundles)
        } catch (t: Throwable) {
            Log.e(TAG, "getMessagesFromBundleArray failed", t)
            return null
        }
        for (msg in messages.asReversed()) {
            val mime = msg.dataMimeType ?: continue
            val uri = msg.dataUri ?: continue
            if (!mime.startsWith("image/")) continue
            return MediaMessage(
                text = msg.text?.toString().orEmpty(),
                sender = msg.senderPerson?.name?.toString() ?: msg.sender?.toString().orEmpty(),
                timestamp = msg.timestamp,
                mime = mime,
                uri = uri
            )
        }
        return null
    }

    private fun readAndCompressImage(context: Context, uri: Uri): ByteArray? = try {
        val bitmap = context.contentResolver.openInputStream(uri).use { input ->
            if (input == null) return null
            BitmapFactory.decodeStream(input)
        } ?: return null
        val scaled = scaleDown(bitmap, 512)
        val output = ByteArrayOutputStream()
        scaled.compress(Bitmap.CompressFormat.JPEG, 75, output)
        if (scaled !== bitmap) scaled.recycle()
        bitmap.recycle()
        output.toByteArray()
    } catch (t: Throwable) {
        Log.e(TAG, "readAndCompressImage failed uri=$uri", t)
        null
    }

    private fun scaleDown(bitmap: Bitmap, maxSide: Int): Bitmap {
        if (bitmap.width <= maxSide && bitmap.height <= maxSide) return bitmap
        val scale = maxSide.toFloat() / maxOf(bitmap.width, bitmap.height).toFloat()
        return Bitmap.createScaledBitmap(
            bitmap,
            (bitmap.width * scale).toInt().coerceAtLeast(1),
            (bitmap.height * scale).toInt().coerceAtLeast(1),
            true
        )
    }

    private fun buildPath(creatorNodeId: String, packageName: String, id: Int, tag: String?, notificationKey: String?): String {
        val safeTag = tag?.let(::wireEncode) ?: "null_tag"
        val safeKey = notificationKey?.let(::wireEncode)
        return buildString {
            append("/bridger/stream_item:")
            append(creatorNodeId)
            append(':').append(packageName)
            append(':').append(id)
            append(':').append(safeTag)
            if (safeKey != null) append(':').append(safeKey)
        }
    }

    private fun wireEncode(value: String): String =
        Uri.encode(value).replace("~", "%7E").replace('%', '~')
}
