# Hardware-in-the-loop testing

The HIL tools run checks on an ESP32-S31 board and, for wired or radio peer
tests, a programmable test board. A host script controls the serial consoles
and saves the results.

## Test tools

| Tool | Runs on | Purpose |
|---|---|---|
| `tools/hil/s31_hil.py` | Host computer | Select and coordinate test cases |
| `s31-hil-agent` | ESP32-S31 Linux | Run board-side checks |
| `tools/hil/esp32p4-tester/` | ESP32-P4 test board | Provide GPIO, serial, bus, and other peer functions |

The P4 tester keeps fixture outputs disabled until a test arms them and
returns them to the disarmed state afterwards. Use the fixture wiring and
firmware instructions in its
[README](https://github.com/GrieferPig/esp32-s31-linux/blob/main/tools/hil/esp32p4-tester/README.md).

## 1. Run host tests

From the parent checkout, run:

```sh
python3 tools/tests/test_s31_feature_contracts.py
python3 tools/tests/test_s31_selftest.py
make btstack-source
python3 tools/tests/test_s31_btstack_reset.py
```

The feature tests use a host C compiler to exercise I2C command generation,
SPI word ordering, I2S configuration, and EAP provisioning. The BTstack test
uses the source fetched by `make btstack-source`.

## 2. Prepare the boards

Build the full-peripheral image and flash the S31:

```sh
export S31_LEAN_RADIO=0
make all
```

Follow the [flashing guide](../get-started/flash-and-first-boot.md), then install
the P4 tester firmware for cases that need it. Connect the fixture according
to its pin map, with a common ground and compatible signal voltages. Close
serial monitors before starting the host runner.

Check the runner's available cases and serial-port options:

```sh
python3 tools/hil/s31_hil.py --help
```

## 3. Run a test

For a wired I2C test with both boards:

```sh
mkdir -p logs
python3 tools/hil/s31_hil.py --board both --case i2c \
  --output logs/hil-i2c.json
```

To repeat the test at 400 kHz:

```sh
python3 tools/hil/s31_hil.py --board both --case i2c \
  --i2c-speed 400000 --repeat 12 --output logs/hil-i2c-repeat.json
```

Other wired cases include `gpio`, `uart`, `spi`, `i2s`, and `pwm-pcnt`.
`spi-stress` and `i2s-stress` use longer transfers for characterization.

For S31-only checks, select `--board s31`:

```sh
python3 tools/hil/s31_hil.py --board s31 --case lp-core \
  --output logs/hil-lp-core.json
python3 tools/hil/s31_hil.py --board s31 --case smp-irq-dma \
  --output logs/hil-smp-irq-dma.json
```

The host runner and target agent have different command-line options. Use
the runner examples above when controlling tests from your computer.

## Storage tests

Insert the appropriate storage device before running `sdmmc` or `usb-drive`:

```sh
python3 tools/hil/s31_hil.py --board s31 --case sdmmc
python3 tools/hil/s31_hil.py --board s31 --case usb-drive
```

The SD/MMC case uses the 1-bit CLK/CMD/DAT0 fixture and reads from the card.
The USB case is read-only by default. To allow its temporary 64 KiB write
test on a disposable test drive, add `--allow-usb-write`.

## Radio tests

With the P4/C6 radio peer connected, run:

```sh
python3 tools/hil/s31_hil.py --board both --case c6-wifi \
  --peer-connected --output logs/hil-wifi.json
python3 tools/hil/s31_hil.py --board both --case c6-ble \
  --peer-connected --output logs/hil-ble.json
```

The Wi-Fi case sets up a fixture access point and temporary station profile,
then checks association, address assignment, and packet exchange. It also
temporarily changes radio services and restores them during cleanup.

For power-management tests, check the current
[suspend limitations](../api-guides/power-management.md) first. GPIO wake
requires wiring to LP GPIO0–7 rather than the normal higher-numbered fixture
pins.

## Read the results

Board results use `HIL1` JSON records. Tests report PASS, FAIL, or SKIP, along
with the operation and a short explanation. Check any failed or skipped
prerequisites and review cleanup errors before starting another case.

Keep the output file with a brief description of the board, firmware build,
wiring, and command used. For data-transfer tests, include the peer result;
for power tests, include wake reason and any current measurements separately.
Update the [support matrix](../resources/support-matrix.md) when a result
changes the documented feature status.

## Add a test case

Add the host sequence, S31 operation, and peer response needed for the test.
Set timeouts for waits and include cleanup for success, error, and interruption.
A useful case checks the returned data or resulting device behavior and gives
a clear explanation when a required device or fixture is missing.
