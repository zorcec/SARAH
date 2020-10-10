<img src="https://github.com/arendst/Tasmota/blob/master/tools/logo/TASMOTA_FullLogo_Vector.svg" alt="Logo" align="right" height="76"/>

# RELEASE NOTES

## Migration Information

See [migration path](https://tasmota.github.io/docs/Upgrading#migration-path) for instructions how to migrate to a major version. Pay attention to the following version breaks due to dynamic settings updates:

1. Migrate to **Sonoff-Tasmota 3.9.x**
2. Migrate to **Sonoff-Tasmota 4.x**
3. Migrate to **Sonoff-Tasmota 5.14**
4. Migrate to **Sonoff-Tasmota 6.x**
5. Migrate to **Tasmota 7.x**

--- Major change in parameter storage layout ---

6. Migrate to **Tasmota 8.1**
7. Migrate to **Tasmota 8.x**

While fallback or downgrading is common practice it was never supported due to Settings additions or changes in newer releases. Starting with release **v8.1.0 Doris** the Settings are re-allocated in such a way that fallback is only allowed and possible to release **v7.2.0 Constance**. Once at v7.2.0 you're on your own when downgrading even further.

## Supported Core versions

This release will be supported from ESP8266/Arduino library Core version **2.7.2.1** due to reported security and stability issues on previous Core version. This will also support gzipped binaries.

Support of Core versions before 2.7.1 has been removed.

## Support of TLS

To save resources when TLS is enabled mDNS needs to be disabled. In addition to TLS using fingerprints now also user supplied CA certs and AWS IoT is supported. Read [full documentation](https://tasmota.github.io/docs/AWS-IoT)

## Initial configuration tools

For initial configuration this release supports Webserver based **WifiManager** or **Serial** based command interface only. Support for **WPS** and **SmartConfig** has been removed.

## Provided Binary Downloads

The following binary downloads have been compiled with ESP8266/Arduino library core version **2.7.2.1**.

- **tasmota.bin** = The Tasmota version with most drivers. **RECOMMENDED RELEASE BINARY**
- **tasmota-BG.bin** to **tasmota-TW.bin** = The Tasmota version in different languages.
- **tasmota-lite.bin** = The Lite version without most drivers and sensors.
- **tasmota-knx.bin** = The Knx version without some features but adds KNX support.
- **tasmota-sensors.bin** = The Sensors version adds more useful sensors.
- **tasmota-ir** = The InfraRed Receiver and transmitter version allowing all available protocols provided by library IRremoteESP8266 but without most other features.
- **tasmota-display.bin** = The Display version without Energy Monitoring but adds display support.
- **tasmota-zbbridge.bin** = The dedicated Sonoff Zigbee Bridge version.
- **tasmota-minimal.bin** = The Minimal version allows intermediate OTA uploads to support larger versions and does NOT change any persistent parameter. This version **should NOT be used for initial installation**.

[List](MODULES.md) of embedded modules.

[Complete list](BUILDS.md) of available feature and sensors.

## Changelog

### Version 8.4.0 George

- Remove Arduino ESP8266 Core support for versions before 2.7.1
- Change to limited support of Arduino IDE as an increasing amount of features cannot be compiled with Arduino IDE
- Change IRRemoteESP8266 library from v2.7.6 to v2.7.8.10, fixing Samsung and Pioneer protocols (#8938)
- Change Adafruit_SGP30 library from v1.0.3 to v1.2.0 (#8519)
- Change Energy JSON Total field from ``"Total":[33.736,11.717,16.978]`` to ``"Total":33.736,"TotalTariff":[11.717,16.978]``
- Change Energy JSON ExportActive field from ``"ExportActive":[33.736,11.717,16.978]`` to ``"ExportActive":33.736,"ExportTariff":[11.717,16.978]``
- Change ESP32 USER GPIO template representation decreasing template message size
- Change define USE_TASMOTA_SLAVE into USE_TASMOTA_CLIENT
- Change commands ``SlaveSend`` and ``SlaveReset`` into ``ClientSend`` and ``ClientReset``
- Change all timer references from ``Arm`` to ``Enable`` in GUI, ``Timer`` command and JSON message
- Change Domoticz commands prefix from ``Domoticz`` to ``Dz``
- Change Zigbee randomizing of parameters at first run or after Reset
- Fix escape of non-JSON received serial data (#8329)
- Fix exception or watchdog on rule re-entry (#8757)
- Add command ``Rule0`` to change global rule parameters
- Add command ``Time 4`` to display timestamp using milliseconds (#8537)
- Add command ``SetOption94 0/1`` to select MAX31855 or MAX6675 thermocouple support (#8616)
- Add command ``SetOption97 0/1`` to switch between Tuya serial speeds 9600 bps (0) or 115200 bps (1)
- Add command ``SetOption98 0/1`` to provide rotary rule triggers (1) instead of controlling light (0)
- Add command ``SetOption99 0/1`` to enable zero cross detection on PWM dimmer
- Add command ``SetOption100 0/1`` to remove Zigbee ``ZbReceived`` value from ``{"ZbReceived":{xxx:yyy}}`` JSON message
- Add command ``SetOption101 0/1`` to add the Zigbee source endpoint as suffix to attributes, ex `Power3` instead of `Power` if sent from endpoint 3
- Add command ``DzSend<type> <index>,<value1(;value2)|state>`` to send values or state to Domoticz
- Add command ``Module2`` to configure fallback module on fast reboot (#8464)
- Add command (``S``)``SerialSend6`` \<comma seperated values\> (#8937)
- Add commands ``LedPwmOn 0..255``, ``LedPwmOff 0..255`` and ``LedPwmMode1 0/1`` to control led brightness by George (#8491)
- Add ESP32 ethernet commands ``EthType 0/1``, ``EthAddress 0..31`` and ``EthClockMode 0..3``
- Add more functionality to command ``Switchmode`` 11 and 12 (#8450)
- Add rule trigger ``System#Init`` to allow early rule execution without wifi and mqtt initialized yet
- Add support for unique MQTTClient (and inherited fallback topic) by full Mac address using ``mqttclient DVES_%12X`` (#8300)
- Add wildcard pattern ``?`` for JSON matching in rules
- Add Three Phase Export Active Energy to SDM630 driver
- Add Zigbee options to ``ZbSend`` to write and report attributes
- Add Zigbee auto-responder for common attributes
- Add ``CpuFrequency`` to ``status 2``
- Add ``FlashFrequency`` to ``status 4``
- Add compile time interlock parameters (#8759)
- Add compile time user template (#8766)
- Add support for VEML6075 UVA/UVB/UVINDEX Sensor by device111 (#8432)
- Add support for VEML7700 Ambient light intensity Sensor by device111 (#8432)
- Add support for up to two BH1750 sensors controlled by commands ``BH1750Resolution`` and ``BH1750MTime`` (#8139)
- Add support for up to eight MCP9808 temperature sensors by device111 (#8594)
- Add support for BL0940 energy monitor as used in Blitzwolf BW-SHP10 (#8175)
- Add support for Telegram bot (#8619)
- Add support for HP303B Temperature and Pressure sensor by Robert Jaakke (#8638)
- Add support for Energy sensor (Denky) for French Smart Metering meter provided by global Energy Providers, need a adaptater. See dedicated full [blog](http://hallard.me/category/tinfo/) about French teleinformation stuff
- Add support for ESP32 ethernet adding commands ``Wifi 0/1`` and ``Ethernet 0/1`` both default ON
- Add support for single wire LMT01 temperature Sensor by justifiably (#8713)
- Add support for rotary encoder as light dimmer and optional color temperature if button1 still pressed (#8670)
- Add support for switches/relays using an AC detection circuitry e.g. MOES MS-104B or BlitzWolf SS5 (#8606)
- Add support for Schneider Electric iEM3000 series Modbus energy meter by Marius Bezuidenhout
- Add support for Sonoff Zigbee Bridge as module 75 (#8583)
