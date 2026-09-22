# Xiaomi Watch 5 Notification RE — Context Checkpoint

Date: 2026-09-22
Project: Уведомления

## Active objective
Feed Telegram photo notifications into the Xiaomi Watch 5 stock rich-notification path through the Wear Data Layer / WearServices bridger, instead of the old Mi Fitness group7/loi path.

Active path:
Telegram -> NotificationMirror phone NotificationListener -> Wear Data Layer DataItem -> /bridger/stream_item:* -> WearServices WatchBridgedItemsController -> StreamItem -> stock notification rendering/offload.

## Confirmed Telegram representation
Telegram package: org.telegram.messenger.web

Telegram photo notifications can contain the image in Notification.MessagingStyle.Message:
- dataMimeType = image/jpeg
- dataUri = content://...

Latest phone log proves extraction:
Extracted MessagingStyle image: mime=image/jpeg ... 576x1280
Then normal NotificationMirror extraction:
Extracted notification picture: 576x1280 -> 180x400, 8143 bytes

## Confirmed WearServices stock bridger format
Actual WearServices.apk contains /bridger/stream_item.

RemoteStreamItemId format:
 /bridger/stream_item:<creatorNodeId>:<packageName>:<id>:<encodedTag>[:<encodedNotificationKey>]

Parser splits with limit 6 and validates /bridger/stream_item.

Wire encoding:
Uri.encode(value).replace("~", "%7E").replace('%', '~')

WatchBridgedItemsController reconstructs MessagingStyle messages from DataMap fields:
- message_text_raw
- message_sender_raw
- message_sender_key
- message_timestamp
- message_data
- message_data_mime_type
- message_image

For image media it creates a generated message URI and maps the DataItem Asset into a DataAssetMessageImageProvider.

Top-level supported fields include title_raw, text_raw, conversation_title_raw, display_name_raw, style_name, when, show_when, priority, notification_flags, messages, big_picture, icon, large_icon, app_icon, actions, wearable_actions, content-intent metadata and other notification metadata.

Therefore stock bridger is demonstrably capable of rich MessagingStyle images.

## NotificationMirror probe
Branch: stock-bridger-probe
Latest successful commit: 2c735bf46147f3039b85e09005290744a04a8422

Probe file:
mobile/src/main/java/com/notifmirror/mobile/StockBridgerSender.kt

It:
1. Finds the last image MessagingStyle.Message.
2. Opens its content URI.
3. Scales to max side 512.
4. JPEG quality 75.
5. Gets Wear local node ID.
6. Builds stock /bridger/stream_item:* path.
7. Sends a DataItem containing stock-style message fields and message_image Asset.
8. Adds _notifmirror_probe_revision to force repeated DATA_CHANGED.
9. Leaves the normal NotificationMirror /notification path enabled for diagnostics.

NotificationListener invokes the probe for org.telegram.messenger.web.

## Latest physical phone result
09-17 19:08:33.083 D NotifMirror: Extracted MessagingStyle image: mime=image/jpeg uri=content://org.telegram.messenger.web.provider/media/Android/data/org.telegram.messenger.web/files/Telegram/Telegram%20Images/-5287281780387947815_121.jpg 576x1280
09-17 19:08:33.087 D NotifMirror: Extracted notification picture: 576x1280 -> 180x400, 8143 bytes
09-17 19:08:33.089 D NotifMirror: Forwarding notification: F from org.telegram.messenger.web (2 actions)
09-17 19:08:33.104 D NotifMirror: Sent to node: Xiaomi Watch 5 D690
09-17 19:08:33.138 I STOCK-BRIDGER: SENT path=/bridger/stream_item:cc4c12e8:org.telegram.messenger.web:-389055965:null_tag:0~7Corg.telegram.messenger.web~7C-389055965~7Cnull~7C10243 bytes=11967 mime=image/jpeg node=cc4c12e8

Interpretation:
- Telegram image extraction works.
- Normal NotificationMirror delivery works.
- putDataItem() succeeds.
- Phone-side stock bridger path is confirmed.
- Remaining question is watch-side visibility/processing.

## Immediate next test
On watch:
logcat -c
logcat | grep -Ei "bridger|WBridgedItemsController|DataToStreamConverter|StreamItem|NotificationOffload|offload"

Then send another Telegram photo.

Interpretation:
- Bridger/DataToStreamConverter activity -> DataItem reached stock processing.
- Phone SENT with no watch activity -> investigate Data Layer package/signing namespace or source-node ownership.
- Watch activity but no image -> inspect StreamItem media Asset conversion and downstream renderer/offload.
- Only normal NotificationMirror notification -> compare IDs/grouping/ownership.

## Important caveat
Matching /bridger/stream_item:* alone may not guarantee that WearServices accepts an arbitrary third-party DataItem. Wear Data Layer visibility may be scoped by app/package/signing identity. This must be established by runtime evidence.

## WearServices manifest findings
Relevant exported components:
- GcoreWearableListenerService: exported, no custom manifest permission; receives Wear Data API events.
- BridgingManagerService: protected by ACCESS_WEAR_SYSTEM_SERVICE.
- McuNotificationActionForwardService: exported; forwards actions/openPopups for existing notifications.
- McuTransmitRxService: exported; MCU data/file receive path.
- NotificationCollectorService: notification-listener binding.

BridgedNotificationModule registers a DataItem listener for the /bridger/ path.

## Rich-media downstream
Confirmed downstream chain:
StreamItem -> NotificationData -> image provider -> WearServices notification offload/file transfer -> MCU/rendering.

No manual MCU serialization should be attempted unless stock DataItem entry is proven impossible.

## Closed/deferred branches
1. Old Xiaomi group7/loi path — CLOSED/DEFERRED; MessagingStyle media was lost before MCU.
2. Mi Fitness physical patch v1 — FAILED; VerifyError and later service-loader/main-dispatcher startup failure.
3. Mi Fitness physical patch v2 — DEFERRED/FAILED startup symptom; direct stock bridger preferred.
4. Direct CPC/NotificationOffloadSrv shell access — DEFERRED; shell access denied/null and SELinux enforcing.
5. Direct WearServices NotificationApi Binder — BLOCKED for ordinary app; protected by system|signature ACCESS_WEAR_SYSTEM_SERVICE.
6. McuNotificationActionForwardService — inspected; not a general notification-post API.
7. McuTransmitRxService — inspected; not a general notification-post API.
8. Double-HUN/grouping branch — archived.

## Current CI artifacts
Successful GitHub Actions run:
run ID 35237175940
branch stock-bridger-probe
commit 2c735bf46147f3039b85e09005290744a04a8422

Phone artifact:
NotificationMirror-Phone-StockBridgerProbe
artifact SHA256: 56cacbe64e32c4c87d6585b66cab1639143b223167787c9e90ee4babfb687ca3

Extracted mobile-debug.apk SHA256:
cd943cda310af4a97384c6e2b192cc003f255ced208a4e89b712da6de2485958

Watch artifact:
NotificationMirror-Watch-StockBridgerProbe

## Working rule
Prefer runtime evidence > decompiled/static evidence > hypothesis.
For every patch record:
base -> changes -> artifact -> SHA256 -> expected result -> actual result.
Do not repeat closed CPC shell probes or old group7/loi work unless new evidence points there.
