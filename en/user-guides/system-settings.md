# System settings

Open **System** in `esp32-config` to change the hostname, login password, time,
or startup program. Run the command-line examples as root on the board.

## Hostname and login password

Choose **Hostname**, enter a name, and select **Save and apply**. The hostname
changes immediately and is restored at boot. From the command line:

```sh
esp32-config system hostname my-s31
```

Choose **Change login password** to set the root account's password. The menu
opens the system password prompt, which asks for the new password twice. This
changes the password used by the board's login service. The equivalent command
is:

```sh
esp32-config system password
```

## Date and time

Choose **Date and time → Time zone and automatic time**. Select an installed
zone such as `America/Los_Angeles` or `Asia/Shanghai`, then choose whether to
use a network time server. The zone's daylight-saving rules apply automatically. The image includes a
curated set of nine zones from `configs/esp32-config-timezones.list`, rather
than the entire timezone database; available names are listed in
`/usr/share/esp32-config/timezones`.

For example, to select Los Angeles time and enable network time:

```sh
esp32-config system time configure America/Los_Angeles 1 pool.ntp.org
esp32-config system time status
```

The arguments are `ZONE`, `AUTOMATIC` (`0` or `1`), and `SERVER`. The default
zone is `Etc/UTC`; automatic time is initially off. Saved settings are applied
at startup. Automatic synchronization needs a working network connection.

To request an update immediately:

```sh
esp32-config system time sync
```

This waits up to 30 seconds and reports whether the update completed. Enabling
the time service alone does not mean that the clock has synchronized.

For an offline board, choose **Set date and time manually** or run:

```sh
esp32-config system time set '2026-09-26 12:00:00'
```

Replace the example with the current local time in the selected zone. Manual
setting turns automatic time off. It updates the running clock; after power
loss, set the clock again or enable network time. The saved time-zone setting
survives reboot.

## Run a program at startup

Install your executable or an executable shell script on persistent storage.
For example, make an existing script executable:

```sh
chmod +x /root/start-player.sh
```

Choose **Startup program → Program and arguments**. Enter the absolute path,
then put each argument on a separate line. Arguments are passed literally;
place pipelines, redirection, or other shell commands inside the script.
Select **Run at startup → Enabled** to run it when Linux boots.

The equivalent commands are:

```sh
esp32-config system autostart configure /root/start-player.sh
esp32-config system autostart enable
esp32-config system autostart start
esp32-config system autostart status
```

To pass arguments, append them to `configure`, using normal shell quoting:

```sh
esp32-config system autostart configure /root/start-player.sh --volume 50
```

Changing the saved program or startup switch does not restart a running
program. Use **Stop program**, then **Start saved program** to run the new
selection immediately. You can also start the saved program once while startup
is disabled. Disabling startup leaves the current instance running:

```sh
esp32-config system autostart disable
esp32-config system autostart stop
```

The program runs as root with no console input. Keep the program in the
foreground so the launcher can track its exit and stop it. It runs once per
start; it is not automatically restarted after exit. Applications on removable
storage need that volume mounted before they start.

The page shows whether the program is running and its last exit status. You
can also read the result with `esp32-config system autostart status`. The
last-run result is temporary and cleared by reboot; the program selection and
arguments are persistent.

The launcher discards standard output and standard error. If your application
needs logs, have its script direct them to an appropriate file and limit their
size. For backing up the configuration, see
[Configuration](../resources/configuration.md).
