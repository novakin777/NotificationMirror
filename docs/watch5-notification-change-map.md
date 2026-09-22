# Xiaomi Watch 5 Notification — Change Map

## Branch
stock-bridger-probe

## Current head
2c735bf46147f3039b85e09005290744a04a8422

## Baseline
NotificationMirror existing:
- NotificationListener receives StatusBarNotification.
- Existing Telegram/MessagingStyle extraction.
- Normal Wear Data Layer path: /notification.
- Watch reconstructs notification locally.

## Change 1 — Telegram media extraction
Purpose: preserve Telegram MessagingStyle image attachments for the existing NotificationMirror path.

Source:
mobile/src/main/java/com/notifmirror/mobile/NotificationListener.kt

Behavior:
- checks EXTRA_PICTURE;
- if absent, scans EXTRA_MESSAGES;
- looks for image/* + content URI;
- reads the URI;
- decodes/scales/compresses image;
- forwards bounded JPEG.

Observed:
576x1280 -> 180x400, 8143 bytes.

## Change 2 — Stock bridger probe
New:
mobile/src/main/java/com/notifmirror/mobile/StockBridgerSender.kt

Behavior:
- Telegram Web only;
- reads last MessagingStyle image;
- creates JPEG Asset;
- obtains local Wear node;
- emits /bridger/stream_item:<node>:<package>:<id>:<tag>[:<key>];
- writes message_text_raw/message_sender_raw/message_sender_key/message_timestamp;
- writes message_data/message_data_mime_type/message_image;
- writes basic top-level notification fields;
- uses _notifmirror_probe_revision for repeat updates.

The ordinary /notification path remains enabled.

## Change 3 — NotificationListener integration
NotificationListener invokes StockBridgerSender for Telegram Web before the unchanged-content skip.

This is intentionally a parallel probe, not a replacement of the existing mirror path.

## Change 4 — CI
GitHub Actions:
- applies the existing Telegram media source changes;
- applies the stock bridger probe;
- runs git diff --check;
- builds :mobile:assembleDebug and :wear:assembleDebug;
- uploads phone/watch debug APK artifacts.

## Build correction
Initial probe failed Kotlin compilation because a function with expression body used return.
Fixed by changing that function to block-body form.

Result:
commit 2c735bf46147f3039b85e09005290744a04a8422
GitHub Actions run 35237175940 succeeded.

## Runtime evidence
Phone test:
STOCK-BRIDGER: SENT
path=/bridger/stream_item:cc4c12e8:org.telegram.messenger.web:-389055965:null_tag:0~7Corg.telegram.messenger.web~7C-389055965~7Cnull~7C10243
bytes=11967
mime=image/jpeg
node=cc4c12e8

This proves the phone-side DataItem submission succeeds.

## Next change — NOT YET IMPLEMENTED
Do not change code until watch-side evidence is collected.

Next diagnostic:
watch logcat around:
bridger
WBridgedItemsController
DataToStreamConverter
StreamItem
NotificationOffload
offload

Decision:
A. Watch sees bridger -> inspect processing/render/offload.
B. Watch sees nothing -> investigate Data Layer app/package/signing/source-node visibility.
C. Watch processes but image absent -> inspect Asset/media fields and generated URI.
D. Only normal NotificationMirror appears -> compare notification IDs/grouping/ownership.

## Branch history relevant to this work
Closed/deferred:
- old group7/loi
- Mi Fitness v1
- Mi Fitness v2
- direct CPC shell probe
- direct NotificationApi Binder
- action-forward service as posting route
- MCU RX service as posting route
- double-HUN/grouping experiments

## Artifact record
Phone artifact:
NotificationMirror-Phone-StockBridgerProbe
GitHub artifact SHA256:
56cacbe64e32c4c87d6585b66cab1639143b223167787c9e90ee4babfb687ca3

mobile-debug.apk SHA256:
cd943cda310af4a97384c6e2b192cc003f255ced208a4e89b712da6de2485958

Expected result:
WearServices consumes the stock DataItem and produces a stock rich notification.

Actual result so far:
Phone submission confirmed; watch-side processing not yet established.
