# Xiaomi Watch 5 / NotificationMirror — consolidated logs

Updated: 2026-09-23  
Repository: `novakin777/NotificationMirror`  
Active branch: `stock-bridger-probe`

This file keeps runtime/build evidence in one place. Each block is separated by device/source, experiment and interpretation.

---

## 1. PHONE — latest physical Telegram photo test

### Context
- Device side: phone
- App: NotificationMirror
- Source notification: Telegram `org.telegram.messenger.web`
- Experiment: `stock-bridger-probe`
- Date in log: 09-17
- Goal: confirm Telegram MessagingStyle image extraction, normal NotificationMirror transport, and stock-style `/bridger/stream_item:*` DataItem submission.

### Raw log

```text
09-17 19:08:33.083  5750  5750 D NotifMirror: Extracted MessagingStyle image: mime=image/jpeg uri=content://org.telegram.messenger.web.provider/media/Android/data/org.telegram.messenger.web/files/Telegram/Telegram%20Images/-5287281780387947815_121.jpg 576x1280
09-17 19:08:33.087  5750  5750 D NotifMirror: Extracted notification picture: 576x1280 -> 180x400, 8143 bytes
09-17 19:08:33.089  5750  5750 D NotifMirror: Forwarding notification: F from org.telegram.messenger.web (2 actions)
09-17 19:08:33.104  5750  5802 D NotifMirror: Sent to node: Xiaomi Watch 5 D690
09-17 19:08:33.138  5750  5802 I STOCK-BRIDGER: SENT path=/bridger/stream_item:cc4c12e8:org.telegram.messenger.web:-389055965:null_tag:0~7Corg.telegram.messenger.web~7C-389055965~7Cnull~7C10243 bytes=11967 mime=image/jpeg node=cc4c12e8
```

### Parsed checkpoints

```text
[PASS] Telegram MessagingStyle image found
       mime=image/jpeg
       original=576x1280

[PASS] Normal NotificationMirror picture conversion
       resized=180x400
       jpeg_size=8143 bytes

[PASS] Normal NotificationMirror notification forwarding
       package=org.telegram.messenger.web
       actions=2

[PASS] Normal NotificationMirror Wear send
       target=Xiaomi Watch 5 D690

[PASS] Stock bridger DataItem submission
       path=/bridger/stream_item:cc4c12e8:org.telegram.messenger.web:-389055965:null_tag:0~7Corg.telegram.messenger.web~7C-389055965~7Cnull~7C10243
       asset_size=11967 bytes
       mime=image/jpeg
       creator_node_id=cc4c12e8

[UNKNOWN] Watch WearServices receipt
[UNKNOWN] StreamItem creation
[UNKNOWN] Notification offload to MCU
[UNKNOWN] MiWearSysUI rich-media render
```

### Current conclusion from this block

Phone-side stock probe works up to and including successful `DataClient.putDataItem()` completion. This does **not yet prove** that stock WearServices on the watch can see the DataItem, because Wear Data Layer visibility may depend on application/package/signing identity.

---

## 2. PHONE — expected stock probe diagnostic messages

### Successful stock submit

```text
STOCK-BRIDGER: SENT path=/bridger/stream_item:... bytes=... mime=image/jpeg node=...
```

Meaning: Telegram media was found, the URI was readable, the DataMap was built, and `DataClient.putDataItem()` completed successfully.

### No image found in MessagingStyle

```text
STOCK-BRIDGER: SKIP no image MessagingStyle message key=...
```

### Image URI read/decode failure

```text
STOCK-BRIDGER: SKIP failed to read image uri=...
```

### Wear local node lookup failure

```text
STOCK-BRIDGER: getLocalNode failed
```

### Data API submission failure

```text
STOCK-BRIDGER: putDataItem failed path=/bridger/stream_item:...
```

---

## 3. WATCH — target log capture for the next physical test

### Command

```sh
logcat -c
logcat | grep -Ei "bridger|WBridgedItemsController|DataToStreamConverter|StreamItem|NotificationOffload|offload"
```

### Components / tags of interest

```text
WBridgedItemsController
DataToStreamConverter
StreamItem
NotificationOffload
offload
bridger
```

### Interpretation matrix

```text
CASE A
Phone: STOCK-BRIDGER: SENT
Watch: bridger / WBridgedItemsController activity present

=> stock DataItem is visible to WearServices
=> direct route is viable
=> next: full stock payload parity, actions, updates, dismiss lifecycle

CASE B
Phone: STOCK-BRIDGER: SENT
Watch: no stock bridger activity

=> strong evidence of Wear Data Layer app/signature namespace isolation
=> next: keep same proven stock payload format, change only integration context

CASE C
Phone: SKIP no image MessagingStyle message

=> Telegram notification representation differs
=> inspect raw Notification extras / MessagingStyle messages

CASE D
Phone: putDataItem failed

=> investigate phone-side Wear Data API / connectivity first
```

---

## 4. WATCH — previous diagnostic receiver expected log patterns

Artifact: `watch_rich_receiver_v3-stockpath-signed-aligned.apk`

Expected log patterns:

```text
RICH-RX-V3: onDataChanged
RICH-RX-V3: MATCH path=/bridger/stream_item:...
RICH-RX-V3: LEGACY embedded bytes=...
RICH-RX-V3: POSTED bytes=...
```

Diagnostic value:

```text
Receiver sees item + WearServices does not
=> strong evidence that Data Layer routing/visibility differs by app identity

Receiver also does not see item
=> investigate synchronization, matching package identity and Data Layer scope
```

---

## 5. CI — first stock bridger build failure

### Workflow
- Branch: `stock-bridger-probe`
- Workflow: `Build Stock Bridger Probe`
- Failed run: `35236626708`

### Relevant compiler error

```text
e: file:///home/runner/work/NotificationMirror/NotificationMirror/mobile/src/main/java/com/notifmirror/mobile/StockBridgerSender.kt:115:14 Returns are not allowed for functions with expression body. Use block body in '{...}'

> Task :mobile:compileDebugKotlin FAILED

FAILURE: Build failed with an exception.

* What went wrong:
Execution failed for task ':mobile:compileDebugKotlin'.
> A failure occurred while executing org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWorkAction
  > Compilation error. See log for more details

BUILD FAILED in 2m 4s
```

### Cause
`readAndCompressImage(...)` used an expression body while containing direct `return null` statements.

### Fix
Convert the function to a normal block body.

---

## 6. CI — successful stock bridger build

### Branch
```text
stock-bridger-probe
```

### Successful commit
```text
2c735bf46147f3039b85e09005290744a04a8422
```

### Workflow run
```text
35237175940
```

### Result

```text
build: success
Set up job: success
Checkout: success
Set up JDK 17: success
Apply Telegram media source changes: success
Apply stock bridger probe: success
Verify source diff: success
Make Gradle executable: success
Build phone and watch debug APKs: success
Upload phone APK: success
Upload watch APK: success
```

### Artifacts

```text
NotificationMirror-Phone-StockBridgerProbe
NotificationMirror-Watch-StockBridgerProbe
```

### Extracted phone APK SHA256

```text
cd943cda310af4a97384c6e2b192cc003f255ced208a4e89b712da6de2485958
```

---

## 7. OLD MI FITNESS PATCH — historical failure signatures

### v1 failure class

```text
VerifyError
```

Cause: register handling / overwritten `StatusBarNotification` state in patched bytecode.

### v1 repack failure class

```text
kotlinx.coroutines Main dispatcher initialization failure
```

Cause: full apktool repack lost entries such as:

```text
META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory
```

### v2
Packaging was changed to preserve the original APK ZIP container and service metadata while replacing DEX only. Startup symptom still reported; no fresh decisive v2 log was captured; branch deferred.

---

## 8. CLOSED ROUTE — old Xiaomi group7 / loi evidence

Observed physical/static route:

```text
MessagingStyle.Message image/jpeg + content://
-> loi
-> BlueToothSender.addNotifications
-> DeviceContact.call$default #3
-> yjt group=7 command=0
-> koi oneof=3
-> loi$e
```

Not observed:

```text
sendFile
MassCore.sendFile
qvg.d
```

Conclusion: the old group7 route carries text/sender/timestamp-style data; no convincing rich-media file-transfer stage was found.

---

## 9. Current runtime decision point

Strongest runtime evidence:

```text
STOCK-BRIDGER: SENT ...
```

Confirmed phone-side chain:

```text
Telegram
-> NotificationListener
-> MessagingStyle image URI
-> image decode/compress
-> stock DataMap
-> stock /bridger/stream_item:* path
-> DataClient.putDataItem()
-> success
```

Still unresolved:

```text
paired watch
-> WearServices receives DataItem ?
-> WBridgedItemsController ?
-> StreamItem / StreamItemData ?
-> NotificationOffload ?
-> MCU ?
-> MiWearSysUI image render ?
```

The next watch-side log capture is the decisive experiment.
