# NotificationMirror / Xiaomi Watch 5 — change & experiment map

Updated: 2026-09-23
Repo: `novakin777/NotificationMirror`

| State | Branch / experiment | Change | Artifact / commit | Expected | Actual / conclusion |
|---|---|---|---|---|---|
| ACTIVE | Stock bridger DataItem probe | Parallel Telegram image sender using stock `/bridger/stream_item:*`, `message_image` Asset and stock DataMap fields | `stock-bridger-probe`, commit `2c735bf46147f3039b85e09005290744a04a8422` | WearServices receives stock DataItem and reconstructs rich MessagingStyle | Phone confirmed `STOCK-BRIDGER: SENT`; watch visibility pending |
| PROVEN | Telegram MessagingStyle media extraction | Read `EXTRA_MESSAGES`, find `image/*` + dataUri, decode/resize/JPEG | current mobile build | Telegram photos available to sender | Physical test passed |
| PROVEN | Normal NotificationMirror control | Keep existing `/notification` MessageClient path enabled | current build | Control notification remains available | Physical test passed |
| PROVEN STATIC | WearServices rich message-image parser | mime + message_data + message_image Asset -> generated URI -> Message.setData -> DataAssetMessageImageProvider | actual `WearServices.apk` | Stock bridger can carry image messages | Confirmed in `WatchBridgedItemsController` |
| PROVEN STATIC | Stock path parser | `/bridger/stream_item:<node>:<pkg>:<id>:<tag>[:<key>]` | `RemoteStreamItemId.java` | Match stock parser | Runtime path matches |
| PROVEN STATIC | WearServices DataItem listener | registration for `/bridger/` | `BridgedNotificationModule` / `GcoreWearableListenerService` | Stock DataItems enter bridger when visible | Registration confirmed |
| OPEN RISK | Wear Data Layer namespace | third-party NotificationMirror writes stock path from its own app identity | current probe | WearServices can see it | Next watch log decides |
| CLOSED/DEFERRED | Mi Fitness group7 / loi | old notification-to-MCU path | traces | Rich media transfer | Media lost; no file-transfer evidence |
| DEFERRED | Direct CPC / NotificationOffload | shell/app_process access | watch runtime probes | Direct offload | stock service exists but ordinary context is not useful |
| BLOCKED | WearServices NotificationApi Binder | direct API call | manifest/permission inspection | Direct stock post | system/signature permission required |
| NON-PRIMARY | McuNotificationActionForwardService | inspect exported service | static inspection | possible stock API | only action/popup forwarding |
| NON-PRIMARY | McuTransmitRxService | inspect exported service | static inspection | possible ingress | transfer RX, not general notification post |
| FAILED/DEFERRED | Mi Fitness patch v1 | physical patch | v1 APKS | rich media injection | VerifyError + repack service metadata problem |
| FAILED/DEFERRED | Mi Fitness patch v2 | original container + DEX replacement | v2 APKS | fix v1 startup | launch symptom persisted |
| ARCHIVED | double HUN/grouping | grouping/summary behavior | prior branches | UI behavior | separate issue |
| DIAGNOSTIC | watch rich receiver v3 | listen for stock `/bridger/stream_item:*` | `watch_rich_receiver_v3-stockpath-signed-aligned.apk` | diagnose Data Layer visibility | retained as optional probe |

## Current build chain

1. Branch: `stock-bridger-probe`
2. CI: `Build Stock Bridger Probe`
3. Successful workflow run: `35237175940`
4. Commit: `2c735bf46147f3039b85e09005290744a04a8422`
5. Phone artifact: `NotificationMirror-Phone-StockBridgerProbe`
6. Watch artifact: `NotificationMirror-Watch-StockBridgerProbe`
7. Phone APK SHA256: `cd943cda310af4a97384c6e2b192cc003f255ced208a4e89b712da6de2485958`

## Latest runtime checkpoint

```text
NotifMirror: Extracted MessagingStyle image: mime=image/jpeg ... 576x1280
NotifMirror: Extracted notification picture: 576x1280 -> 180x400, 8143 bytes
NotifMirror: Forwarding notification: F from org.telegram.messenger.web (2 actions)
NotifMirror: Sent to node: Xiaomi Watch 5 D690
STOCK-BRIDGER: SENT path=/bridger/stream_item:cc4c12e8:org.telegram.messenger.web:-389055965:null_tag:0~7Corg.telegram.messenger.web~7C-389055965~7Cnull~7C10243 bytes=11967 mime=image/jpeg node=cc4c12e8
```

Status:
- extraction: PASS
- normal NotificationMirror transport: PASS
- stock DataMap construction: PASS
- DataClient.putDataItem: PASS
- watch WearServices receipt: UNKNOWN
- StreamItem creation: UNKNOWN
- MCU offload/render: UNKNOWN

## Next decision gate

Watch command:

```sh
logcat -c
logcat | grep -Ei "bridger|WBridgedItemsController|DataToStreamConverter|StreamItem|NotificationOffload|offload"
```

Interpretation:
- stock bridger activity -> direct route viable; expand to full payload and lifecycle;
- no stock activity despite phone `SENT` -> Data Layer app/signature visibility becomes primary blocker.

## Historical hashes

Stock bridger probe source package v1:
`5e97878bbae5e4436df20fb5335722418a1ccf14975fc8214c6e044b3cc106fa`

Mi Fitness v1:
- APKS `1e8a18cf5536a99f4b9fa9b0bdc02732242aa06942cf0f717989a3cb31431dae`
- receiver `41fab3d67b86148d57d58de450aa9a4afbfa6de614da446165c93636c85d3777`

Mi Fitness v2:
- APKS `82769e154fc8e138d71cebbc4b27c50c1907e746ccf41f306a4b7dfed380bfbb`
- base `fa79bf1c1439a3f08f07cfd80ec50f2a5beb502d2281e1c76d6716d2fe543744`
- cert `d0f2eedc11efa7a86502cceb444fbe6d33c82a4d58281514263bfd52da0b6d78`
