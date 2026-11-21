# xremap for Fedora

- **Package**
  - Fedora 44 and 45, on x86_64 and aarch64.
  - Upstream's `full` variant supports X11, GNOME, KDE, Hyprland, wlroots,
    Niri, COSMIC, Pantheon, and the socket bridge.
  - Includes system and user units, a dedicated account, uinput setup,
    Bash/Zsh/Fish completions, upstream documentation, and example mappings.
  - Services are disabled by default. No active mappings or desktop-user
    permission grants are installed.
  - The service files are Fedora packaging adaptations of upstream's
    examples, not a separate upstream installer.

- **Install**
  - On Fedora:
    ```sh
    sudo dnf copr enable scottames/xremap
    sudo dnf install xremap
    ```
  - On an Atomic Desktop, add the COPR repository to the host or image, then
    install through the normal image/layering workflow and reboot.
  - This package installs `/usr/lib/modules-load.d/xremap.conf` to load
    `uinput` at boot and a udev rule granting its device to `xremap:xremap`.
    - This changes device setup even while the services are disabled.
    - It does not grant the desktop user raw input or uinput access.
    - To apply it without rebooting:
      ```sh
      sudo modprobe uinput
      sudo udevadm control --reload-rules
      sudo udevadm trigger --action=add --subsystem-match=misc --sysname-match=uinput
      ```

- **Choose one remapper mode**
  - The recommended mode is the system service with a desktop-session bridge.
    - The system process gets raw input access; the desktop user does not.
    - All users share the system mappings.
  - Alternatively, use the direct user remapper.
    - It requires separate administrator-approved raw input and uinput access.
    - It exposes the desktop account to keylogging and input injection.
  - Do not run both remappers against the same devices.
    - The two user units conflict with each other.
    - The system and user managers cannot enforce conflicts across managers.

- **System service**
  - Validate your configuration before deployment:
    ```sh
    xremap --validate-config ./config.yml
    sudo install -o root -g root -m 0644 ./config.yml /etc/xremap/config.yml
    ```
    - YAML and TOML are supported. The default unit uses `config.yml`.
    - For TOML, install `config.toml` and replace the configuration path in
      `ExecStart` through `sudo systemctl edit xremap.service`.
    - Examples are in `/usr/share/doc/xremap/`; none are installed as active
      configuration.
  - The unit runs as the unprivileged `xremap` account.
    - `SupplementaryGroups=input` grants input access only to the service.
    - The udev rule grants uinput access to its primary group.
    - Configuration and unit files remain root-owned.
    - Do not add desktop users to the service's `xremap` group.
  - The default command is:
    ```sh
    /usr/bin/xremap --desktop=socket --watch=device --no-window-logging /etc/xremap/config.yml
    ```
    - To use global mappings without a bridge, override `--desktop=socket`
      with `--desktop=none`.
    - Reset `ExecStart` before replacing it in a drop-in:
      ```ini
      [Service]
      ExecStart=
      ExecStart=/usr/bin/xremap --desktop=none --watch=device --no-window-logging /etc/xremap/config.yml
      ```
  - Start only after configuration and permissions are ready:
    ```sh
    sudo systemctl enable --now xremap.service
    ```

- **Desktop bridge and per-user socket setup**
  - The bridge runs in the desktop session with no raw input access.
  - An administrator must create a separate socket-access group for each
    intended user.
    - Replace `USERNAME`, `UID`, and `SOCKET_GROUP` below.
    - Find the numeric UID with `id -u USERNAME`.
    - Do not use `input` or the service's `xremap` group as `SOCKET_GROUP`.
    ```sh
    sudo groupadd --system SOCKET_GROUP
    sudo usermod --append --groups SOCKET_GROUP USERNAME
    sudo install -d -m 0755 /etc/systemd/system/xremap.service.d
    sudo systemctl edit xremap.service
    ```
  - Add this system-service drop-in:
    ```ini
    [Service]
    SupplementaryGroups=SOCKET_GROUP
    ExecStartPre=+/usr/bin/install -d -o xremap -g SOCKET_GROUP -m 2770 /run/xremap/UID
    ```
    - `SupplementaryGroups` adds to the unit's `input` membership.
    - The `+` prefix gives this directory-creation command root credentials;
      the remapper itself remains unprivileged.
    - The setgid directory restricts the socket to the service and that user.
    - Repeat the group and drop-in entries for each intended user.
  - Log out and back in so the desktop session gets its group membership.
  - Restart the system service to create the directory, then enable the
    bridge from a desktop terminal:
    ```sh
    sudo systemctl daemon-reload
    sudo systemctl restart xremap.service
    systemctl --user enable --now xremap-bridge.service
    ```
  - The bridge auto-selects the desktop.
    - Use `systemctl --user edit xremap-bridge.service` to reset `ExecStart`
      and set `--desktop=niri`, `--desktop=kde`, or another supported backend
      when auto-selection is unsuitable.
    - Ensure the user manager has the desktop environment and connection
      variables, such as `NIRI_SOCKET`, `WAYLAND_DISPLAY`, or `DISPLAY`.
    - The session must manage `graphical-session.target` for automatic
      startup/shutdown. Otherwise use the desktop's session-start mechanism.
    - GNOME may use its upstream extension instead of this bridge.
  - See the installed `doc/running_as_system_service.md` for upstream's
    socket model and desktop-specific requirements.

- **Direct user remapper**
  - First arrange explicit raw input and uinput grants with the administrator.
    - The package does not grant these to your account automatically.
    - The upstream `doc/running_without_sudo.md` explains the tradeoffs.
    - Its example grants uinput to `input`; this package instead reserves
      uinput for `xremap`. A local rule or ACL is needed for direct user mode.
  - Put your configuration in `~/.config/xremap/config.yml` and validate it.
    ```sh
    xremap --validate-config ~/.config/xremap/config.yml
    systemctl --user enable --now xremap.service
    ```
  - Desktop auto-selection, configuration-path overrides, and graphical
    session handling work as described above.
  - Stop the system remapper before starting this mode.

- **Defaults and security**
  - All units use `RUST_LOG=warn` and `--no-window-logging` for quiet logs.
    - Override these explicitly for diagnostics.
    - Debug output may include keystrokes; explicit print actions can still
      print window information. Inspect logs before sharing them.
  - Command launching retains upstream's defaults.
    - The remapper defaults to allowing launch actions.
    - The bridge defaults to denying them; launching in a socket-based
      session needs explicit `--allow-launch=true` on the bridge.
    - For no command execution, explicitly set `--allow-launch=false` on
      both processes and keep launch actions out of the mappings.
  - The package does not impose a personal confinement profile.
    - Administrators can add hardening through service drop-ins.
    - Do not hide the required input devices, desktop sockets, or logind IPC.
  - Remapping can remain active while the screen is locked.
    - Validate lock/unlock, user switching, and logout behavior for your setup.
  - Fedora SELinux remains enabled.
    - No custom policy or permissive-mode workaround is installed.
    - Live device/session behavior must be checked on the intended host.

- **Updates and removal**
  - Unit presets disable fresh installations but respect administrator
    overrides and existing enablement on upgrades.
  - Updates do not request an automatic restart of the remapper.
    - Restart deliberately after checking the new configuration.
  - Stop and disable the chosen units before removing the package.
    ```sh
    systemctl --user disable --now xremap-bridge.service
    systemctl --user disable --now xremap.service
    sudo systemctl disable --now xremap.service
    ```
    - Run only the commands for the modes you enabled.
  - Local configuration, per-user groups, and administrator drop-ins are not
    removed by the RPM.
    - The service account is retained to avoid reusing its UID for old files.
    - Remove obsolete socket groups/directories and local device grants
      separately when no longer needed.
    - Reload udev rules after removal, or reboot. Existing device permissions
      and the loaded module need not disappear when a rule is removed.

- **Build inputs**
  - v0.15.18 resolves to commit `23e880d441bf968de396c731fdcea18b1af62d9b`.
    - The spec verifies the source archive and upstream lockfile hashes.
    - The packaged lock changes only rustix 1.1.5 to 1.1.6 and its checksum.
    - The replacement lockfile hash is checked in `%prep`.
  - Cargo and rustc are pinned to 1.99.1 on Fedora 44 and 1.100.0 on Fedora 45.
    - Keep the buildroot package list with each build; OS tooling can affect
      the output even when Rust inputs are locked.
  - Build and test with:
    ```sh
    cargo build --release --locked --no-default-features --features full
    cargo test --release --locked --no-default-features --features full
    ```
    - `device-test` is excluded.
    - COPR networking must be enabled so Cargo can fetch verified locked crates.

- **Dependency review**
  - Review the exact normal/build graph for each architecture:
    ```sh
    cargo tree --locked --target x86_64-unknown-linux-gnu \
      --no-default-features --features full -e normal,build
    cargo tree --locked --target aarch64-unknown-linux-gnu \
      --no-default-features --features full -e normal,build
    ```
  - On 2026-11-21, both target graphs contained the same 152 distinct
    crates.io name/version pairs.
    - An OSV `v1/querybatch` check returned four findings, all previously
      recorded unmaintained-crate exceptions.
    - rustix 1.1.6 addresses RUSTSEC-2026-0486 and had no OSV finding.
    - Temporarily retain unsafe-libyaml 0.2.11 (RUSTSEC-2024-0449) for upstream
      YAML support; revisit when upstream replaces or gates the parser.
    - Temporarily retain zbus_names 4.3.5 / zvariant 5.15.1 /
      zvariant_derive 5.15.1 (RUSTSEC-2026-0371, -0370, -0372) for upstream's
      zbus 5 integrations; revisit at the next upstream update.
    - YAML remains a compiled dependency even when mappings use TOML.
    - A migration to zbus 6 needs source and service testing, not just a lock
      update.
  - Recheck advisories before promotion and record findings in SCT-382.
    - This extends the earlier 118-crate `socket,niri` review to `full`.

- **Package tests**
  - `%check` runs the non-device Rust tests, verifies all desktop integrations,
    and checks valid YAML/TOML and invalid configuration.
  - PR builds also run `test-package.sh` after building the RPM.
    - The script installs, reinstalls, and removes the package in a disposable
      Fedora container; it never starts a remapper.
    - It checks account creation, unit/rule syntax, file ownership, disabled
      initial services, and preservation of local configuration and enablement.
    - Never run it on a real host. It writes `/etc` and removes the RPM.
    - Physical device access, desktop connections, SELinux behavior, and
      restart/lock/session behavior still need live testing.

- **COPR builds**
  - The existing project is `scottames/xremap`; do not create it again.
  - While reviewing PR #780, its SCM package tracks `feat/sct-382-xremap`.
    - Change it to `main` after merge.
  - Explicitly request the four supported targets:
    ```sh
    copr-cli build-package --name xremap \
      --chroot fedora-44-x86_64 --chroot fedora-44-aarch64 \
      --chroot fedora-45-x86_64 --chroot fedora-45-aarch64 scottames/xremap
    ```
    - Inspect any already-requested build before submitting a duplicate.
    - Rawhide is not an acceptance target for this package change.
  - Record build IDs, packaging commit, chroots, RPM/SRPM SHA-256 checksums,
    and dependency findings in SCT-382.
  - Scotty's deployment belongs to SCT-376.
    - Discuss ownership between `dots` and `containers` with Scotty when that
      issue is worked; no personal repository split is decided here.
