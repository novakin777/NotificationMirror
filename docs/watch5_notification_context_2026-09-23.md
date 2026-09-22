# Xiaomi Watch 5 / NotificationMirror rich notification context

Updated: 2026-09-23

## Goal
Deliver rich Telegram photo notifications to Xiaomi Watch 5 using the stock WearServices / MiWearSysUI notification path where possible, rather than reconstructing only a local watch notification.

## Working rules
- Runtime evidence > decompiled/static evidence > hypotheses.
- Keep experiments reversible and parallel to the normal NotificationMirror path until the stock route is proven.
- Track each patch as: base → changes → artifact → SHA256 → expected result → actual result.
- "Manifest inspection" means automated exported-component/code search.
- Avoid re-running branches already proven blocked unless new evidence changes the premise.

## Baseline NotificationMirror pipeline
Phone:
Telegram / Android app
→ Android NotificationManager
→ NotificationMirror NotificationListenerService
→ extracts title/text/messages/picture/actions/icon
→ own JSON payload
→ Wear MessageClient path /notification
→ Google Play Services.

Watch:
NotificationMirror receiver/listener
→ MessageHelper
→ NotificationHandler.handleNotification()
→ rebuilds a new Android notification
→ NotificationManager.notify()
→ Wear OS notification pipeline
→ WearServices parser
→ StreamItem / StreamItemData
→ MiWearSysUI HUN / FullView.

Important: NotificationMirror does not forward the original Notification object; it serializes and reconstructs it.

## Telegram media representation
Telegram photo notifications can carry media in Notification.MessagingStyle.Message:
- text
- timestamp
- sender / Person
- dataMimeType
- dataUri

Photo media is often attached with Message.setData("image/jpeg", content://...), not EXTRA_PICTURE.

The NotificationMirror control path was updated to:
1. check EXTRA_PICTURE;
2. inspect EXTRA_MESSAGES when EXTRA_PICTURE is absent;
3. locate the last image/* + content:// message;
4. decode/resize/JPEG/Base64;
5. forward in NotificationMirror's normal payload.

This is proven working.

## Confirmed Xiaomi rendering behavior
Normal HUN:
- contentTitle → title
- contentText → body

BigPicture:
- BigPictureStyle displays the image in Xiaomi HUN.

MessagingStyle:
- Xiaomi HUN selects the latest message and formats sender/conversation information.

Separate image paths exist:
- BigPicture: EXTRA_PICTURE / BigPictureStyle → WearServices → StreamItemData.imageProvider → BigPictureImageBackend → HUN.
- Message image: Message dataMimeType/dataUri → WearServices → messageImageProvider → MessageImageBackend → DefaultMessageImageLoader.

Known StreamItemData semantics from decompile:
- title J
- contentText M
- bigText N
- subText U
- bigTitle L
- displayName Y
- conversationTitle Z
- messages a0
- appName m
- .e() conversationTitle
- .m() messages
- .n() title
- .s() has messages
- .l() imageProvider-like

HUN-related classes seen:
- StreamAlerterNotifier
- HunStreamAlerter
- obfuscated Lrm/t;
- renderer Lrm/k;.a(Lle/a;)V

HUN / FullView / Glanceable are separate rendering paths.

## Closed/deferred legacy Xiaomi group7 route
Old Mi Fitness route:
BaseNotifySyncService → setupMessageStyle → loi / loi.f → BlueToothSender → koi → yjt → DeviceContact → MCU.

Recovered physical experiment:
MessagingStyle.Message image/jpeg + content://
→ loi
→ BlueToothSender.addNotifications
→ DeviceContact.call$default #3
→ yjt group=7 command=0
→ koi oneof=3
→ loi$e

No sendFile / MassCore.sendFile / qvg.d call was observed.

Conclusion: this path preserves timestamp/text/sender but drops message media, so it is not the target rich-media route.

## Modern WearServices / MiWearSysUI rich path
The watch software supports:
- NotificationData
- Message.dataMimeType / dataUri
- StreamItemToMcuNotificationConverter
- image request/transfer
- AP→MCU file transfer
- MiWearSysUI image loaders

Conceptual flow:
StreamItem
→ NotificationData.bigPictureStyle or message media
→ INotificationOffload
→ MCU

For images, MCU can request an icon/image URI and WearServices transfers data through:
McuTransmitManager → TransmitManager → TransmitFileClient.sendFilePfd.

## Direct low-level branches
### Direct CPC / NotificationOffloadSrv
Deferred:
- ap:cpcmanager exists.
- stock WearServices can get NotificationOffloadSrv.
- shell/app_process attempts were blocked by service visibility / RpcSession permission / SELinux.
- /dev/rpmsg* is root:root 0600.

Do not repeat the same shell CPC probe without new evidence.

### Direct WearServices NotificationApi Binder
Blocked for ordinary apps by:
com.google.wear.permission.ACCESS_WEAR_SYSTEM_SERVICE
(system/signature protection).

### Exported WearServices components inspected
Important results:
1. GcoreWearableListenerService
   - exported=true
   - handles Wear Data Layer events, including DATA_CHANGED.
2. BridgingManagerService
   - ACCESS_WEAR_SYSTEM_SERVICE protected.
3. McuNotificationActionForwardService
   - exported, but acts on already-existing notifications; not a general post API.
4. McuTransmitRxService
   - MCU transfer receiver, not a general notification post API.
5. NotificationCollectorService
   - BIND_NOTIFICATION_LISTENER_SERVICE protected.

## Stock Wear notification bridger discovery
WearServices registers a DataItem listener for the bridger prefix:
- registrar id observed: 90wavj
- URI prefix path: /bridger/

Relevant stock path format from RemoteStreamItemId:
```
/bridger/stream_item:<creatorNodeId>:<packageName>:<id>:<encodedTag>[:<encodedNotificationKey>]
```

Parser requires:
- prefix /bridger/stream_item
- creator node id
- package name
- integer notification id
- encoded tag (null_tag for null)
- optional encoded notification key

Wire encoding observed:
Uri.encode(str).replace("~", "%7E").replace('%', '~')

CreatorNodeId must correspond to the actual sender node id.

## WearServices rich message schema
Fresh decompile of WearServices.apk confirmed stock keys in DEX:
- /bridger/stream_item
- conversation_title
- conversation_title_raw
- display_name
- display_name_raw
- message_data_mime_type
- message_image
- message_sender_raw
- message_text_raw

WatchBridgedItemsController reconstructs MessagingStyle.Message using:
- message_text / message_text_raw
- message_sender / message_sender_raw
- message_sender_key
- message_timestamp
- message_data
- message_data_mime_type
- message_image Asset

If message_data_mime_type, message_data and message_image all exist, it:
1. creates a generated URI under the StreamItem URI;
2. maps the URI to the Data Layer Asset;
3. calls Message.setData(mime, generatedUri).

Then the StreamItem builder receives:
- messages = immutable message list
- messageImageProvider = DataAssetMessageImageProvider
- localOnly = true

This is direct evidence that the stock bridger can carry rich MessagingStyle images.

Other top-level fields seen include:
priority, is_emergency, notification_flags, group, user_id, group_alert_behavior,
is_work_profile, style_name, title_html/title_raw, ticker_html,
big_title_html/big_title_raw, sub_text_html/sub_text_raw,
text_html/text_raw, big_text_html/big_text_raw, summary_html/summary_raw,
when, show_when, uses_chronometer, chronometer_count_down,
supplemental_data Asset, icon Asset, large_icon Asset, big_picture Asset,
app_icon Asset, supplemental_assets, actions, wearable_actions,
content_action_index, content_launches_activity, start_scroll_bottom,
inbox_lines, has_content_intent/content_intent_id,
display_name/raw, conversation_title/raw,
device_user_key/avatar, messages.

Big-picture media is also supported through the big_picture Asset.

## Important Data Layer caveat
A matching path alone may not be sufficient. Wear Data Layer commonly scopes data by application/package/signing identity.

Therefore the key empirical question is:
Can a DataItem created by the ordinary NotificationMirror phone app be observed by WearServices' stock bridger listener?

Possible outcomes:
- If WearServices sees it, NotificationMirror can potentially feed the stock bridge directly.
- If NotificationMirror logs successful putDataItem but WearServices sees nothing, app-identity/Data Layer namespace isolation is the leading explanation.

## NotificationMirror stock bridger probe
Repository:
novakin777/NotificationMirror

Branch:
stock-bridger-probe

Latest successful probe commit:
2c735bf46147f3039b85e09005290744a04a8422

GitHub Actions run:
35237175940

Build result:
SUCCESS

Artifacts:
- NotificationMirror-Phone-StockBridgerProbe
- NotificationMirror-Watch-StockBridgerProbe

Phone artifact digest reported by GitHub:
sha256:56cacbe64e32c4c87d6585b66cab1639143b223167787c9e90ee4babfb687ca3

Extracted mobile-debug.apk SHA256:
cd943cda310af4a97384c6e2b192cc003f255ced208a4e89b712da6de2485958

## Probe implementation
StockBridgerSender.kt activates only for:
org.telegram.messenger.web

It:
- scans MessagingStyle messages;
- selects the last image/* message with dataUri;
- reads and JPEG-compresses the image;
- gets Wearable.getNodeClient(context).localNode;
- constructs stock /bridger/stream_item:* path;
- puts a message DataMap containing:
  - message_text_raw
  - message_sender_raw
  - message_sender_key
  - message_timestamp
  - message_data
  - message_data_mime_type
  - message_image Asset
- puts top-level metadata:
  - display_name_raw
  - title_raw
  - text_raw
  - conversation_title_raw
  - style_name
  - when
  - show_when
  - priority
  - notification_flags
  - messages
  - _notifmirror_probe_revision
- sends via DataClient.putDataItem(...setUrgent()).

The normal NotificationMirror /notification path remains enabled in parallel.

## Latest runtime evidence: phone side
Physical test log, 2026-09-17:
```
09-17 19:08:33.083 D NotifMirror: Extracted MessagingStyle image: mime=image/jpeg uri=content://org.telegram.messenger.web.provider/media/Android/data/org.telegram.messenger.web/files/Telegram/Telegram%20Images/-5287281780387947815_121.jpg 576x1280
09-17 19:08:33.087 D NotifMirror: Extracted notification picture: 576x1280 -> 180x400, 8143 bytes
09-17 19:08:33.089 D NotifMirror: Forwarding notification: F from org.telegram.messenger.web (2 actions)
09-17 19:08:33.104 D NotifMirror: Sent to node: Xiaomi Watch 5 D690
09-17 19:08:33.138 I STOCK-BRIDGER: SENT path=/bridger/stream_item:cc4c12e8:org.telegram.messenger.web:-389055965:null_tag:0~7Corg.telegram.messenger.web~7C-389055965~7Cnull~7C10243 bytes=11967 mime=image/jpeg node=cc4c12e8
```

Confirmed by this runtime evidence:
- Telegram MessagingStyle image extraction works.
- The normal NotificationMirror send path works.
- StockBridgerSender successfully constructs and submits the DataItem.
- The sender node id used in the path is cc4c12e8.
- The bridger payload includes a JPEG Asset (11967 bytes).
- Any remaining failure is downstream of the phone-side DataClient submit.

Not yet proven:
- whether WearServices receives this DataItem;
- whether its /bridger/ listener can see DataItems originating from NotificationMirror's app identity;
- whether the stock StreamItem / MCU path accepts this DataItem when visible.

## Next required physical evidence
On the watch, capture around a fresh Telegram photo:
```
logcat -c
logcat | grep -Ei "bridger|WBridgedItemsController|DataToStreamConverter|StreamItem|NotificationOffload|offload"
```

Interpretation:
- STOCK-BRIDGER SENT + WBridgedItemsController activity → direct stock bridge is visible and worth expanding.
- STOCK-BRIDGER SENT + no relevant watch activity → Data Layer app identity isolation becomes the primary branch.
- Watch sees item but converter rejects it → fix payload/schema/path semantics based on exact watch log.

## Deferred fallback if Data Layer visibility is blocked
Investigate an alternative integration path that publishes the same stock bridger DataItem from a system/Xiaomi application context that WearServices can observe.

Keep the experiment focused on:
- app identity / Data Layer namespace,
- stock bridger payload compatibility,
- minimal change surface,
- runtime proof before expanding functionality.

## Old Mi Fitness physical patch branch
v1:
- patched CompanionNotificationHandler Telegram → SEND;
- zzfaw legacy context;
- zzadm duplicated image bytes.
Failed:
- VerifyError due to overwritten StatusBarNotification register;
- full apktool repack lost META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory and caused startup crash.

v2:
- preserve original base ZIP structure;
- replace dex only;
- preserve service entries;
- sign splits.
User still observed a launch symptom; no newer runtime evidence was collected.
This branch is deferred while the stock WearServices bridger path is being tested.

## Branch status index
- Old Xiaomi group7/loi — CLOSED/DEFERRED.
- NotificationMirror control/reference — PROVEN.
- WearServices/MiWearSysUI rich downstream — PROVEN capable.
- Stock bridger schema and rich message_image support — PROVEN by decompile.
- Direct CPC shell/app_process — DEFERRED/BLOCKED.
- Direct NotificationApi Binder — BLOCKED for ordinary app.
- McuNotificationActionForwardService — non-primary.
- McuTransmitRxService — non-primary.
- GcoreWearableListenerService + /bridger/ DataItem — ACTIVE.
- NotificationMirror phone → stock /bridger/stream_item → WearServices → MCU — ACTIVE.
- Alternative system/Xiaomi app-context publisher — FALLBACK if Data Layer visibility is blocked.
- OHealth rich notification reference — DEFERRED.
- Double HUN/grouping experiments — ARCHIVED.

## Immediate next move
Capture watch log for a fresh Telegram photo using the successful phone probe.

Do not expand the payload yet. First answer the binary question:
Does WearServices observe the DataItem generated by NotificationMirror?
