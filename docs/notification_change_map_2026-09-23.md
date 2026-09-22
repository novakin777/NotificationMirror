# Notification rich-media change map

Updated: 2026-09-23

## Current active chain
```
Telegram notification
  │
  ├─ Android Notification.MessagingStyle.Message
  │    ├─ text
  │    ├─ sender
  │    ├─ timestamp
  │    ├─ dataMimeType=image/jpeg
  │    └─ dataUri=content://...
  │
  └─ NotificationMirror phone
       ├─ NORMAL PATH (control)
       │    ├─ extract MessagingStyle image
       │    ├─ resize/JPEG/Base64
       │    └─ MessageClient /notification
       │         └─ NotificationMirror watch rebuild
       │
       └─ STOCK BRIDGER PROBE
            ├─ StockBridgerSender
            ├─ image URI → JPEG bytes
            ├─ Asset.createFromBytes(...)
            ├─ path:
            │   /bridger/stream_item:<node>:<pkg>:<id>:<tag>:<key>
            └─ DataClient.putDataItem(setUrgent)
                 │
                 └─ [CURRENT UNKNOWN BOUNDARY]
                      │
                      ├─ expected: WearServices GcoreWearableListenerService
                      ├─ expected: /bridger/ DataItem listener
                      ├─ expected: WatchBridgedItemsController
                      ├─ expected: MessagingStyle.Message.setData(...)
                      ├─ expected: StreamItemData.messageImageProvider
                      ├─ expected: NotificationOffload
                      └─ expected: MCU / MiWearSysUI render
```

## Repository changes
Repository: novakin777/NotificationMirror

Active branch: stock-bridger-probe

Latest successful build commit:
2c735bf46147f3039b85e09005290744a04a8422

### Added
`mobile/src/main/java/com/notifmirror/mobile/StockBridgerSender.kt`

Purpose:
- generate a stock-compatible bridger DataItem for Telegram photo notifications;
- keep the existing NotificationMirror path untouched for comparison.

### Modified by probe patch
`mobile/src/main/java/com/notifmirror/mobile/NotificationListener.kt`

Insertion point:
after app/keyword filtering and before unchanged-content early return.

Behavior:
- for org.telegram.messenger.web, launch StockBridgerSender in the existing coroutine scope;
- continue normal NotificationMirror processing afterward.

### Build automation
GitHub Actions workflow runs both source patch scripts and builds:
- :mobile:assembleDebug
- :wear:assembleDebug

Successful run:
35237175940

Artifacts:
- NotificationMirror-Phone-StockBridgerProbe
- NotificationMirror-Watch-StockBridgerProbe

## Probe payload map
Top-level DataMap:
```
display_name_raw          "Telegram"
title_raw                 notification title
text_raw                  notification text
conversation_title_raw    conversation title
style_name                android.app.Notification$MessagingStyle
when                      sbn.postTime
show_when                 true
priority                  notification.priority
notification_flags        notification.flags
messages                  ArrayList<DataMap>
_notifmirror_probe_revision currentTimeMillis()
```

Message DataMap:
```
message_text_raw           message text
message_sender_raw         sender
message_sender_key         sender-derived key
message_timestamp          original message timestamp
message_data               "telegram_photo_0"
message_data_mime_type     image/*
message_image              Asset(JPEG bytes)
```

## Runtime result map
### Proven
```
Telegram image in MessagingStyle
  ↓
NotificationMirror reads content:// URI
  ↓
image decode succeeds (576x1280)
  ↓
normal mirror image compression succeeds (180x400, 8143 B)
  ↓
normal /notification send succeeds
  ↓
StockBridgerSender image payload created (11967 B)
  ↓
DataClient.putDataItem succeeds
  ↓
STOCK-BRIDGER: SENT
```

Observed stock path:
```
/bridger/stream_item:cc4c12e8:org.telegram.messenger.web:-389055965:null_tag:0~7Corg.telegram.messenger.web~7C-389055965~7Cnull~7C10243
```

### Unknown boundary
```
DataClient accepted DataItem
  ↓
? WearServices receives DATA_CHANGED
  ↓
? WatchBridgedItemsController parses RemoteStreamItemId
  ↓
? DataToStreamConverter accepts payload
  ↓
? StreamItem goes to NotificationOffload / MCU
  ↓
? Xiaomi UI shows stock rich image
```

## Decision tree for next run
```
Phone: STOCK-BRIDGER SENT?
  ├─ no → fix phone extraction/DataClient
  └─ yes
      │
      └─ Watch: bridger/WBridgedItemsController activity?
           ├─ yes
           │    ├─ accepts item → expand stock payload/action/dismiss support
           │    └─ rejects item → patch exact missing/invalid schema from log
           │
           └─ no
                └─ investigate Data Layer app-identity visibility
                     └─ fallback: publish same stock item from an observable system/Xiaomi app context
```

## Closed/deferred map
```
Mi Fitness legacy group7 / loi
  └─ media lost before MCU → CLOSED/DEFERRED

Direct NotificationApi binder
  └─ system/signature permission → BLOCKED

Direct CPC shell/app_process
  └─ service/RpcSession/SELinux restrictions → DEFERRED

McuNotificationActionForwardService
  └─ actions for existing notifications only → NON-PRIMARY

McuTransmitRxService
  └─ transfer receiver only → NON-PRIMARY

Mi Fitness physical v1/v2 patch
  └─ startup/verification packaging failures → DEFERRED

Double HUN/grouping
  └─ archived
```

## Next evidence to collect
Watch:
```
logcat -c
logcat | grep -Ei "bridger|WBridgedItemsController|DataToStreamConverter|StreamItem|NotificationOffload|offload"
```

Trigger one Telegram photo and preserve the complete time window around the event.

## Success criterion for current phase
Current phase is successful when runtime logs prove:
```
NotificationMirror DataClient item
→ WearServices /bridger listener
→ stock StreamItem conversion
```

Only after this is proven should the stock sender be expanded with:
- app icon / large icon
- full message history
- actions
- content-intent semantics
- update/revision semantics
- dismiss/delete sync
- replacing the normal NotificationMirror reconstruction path.
