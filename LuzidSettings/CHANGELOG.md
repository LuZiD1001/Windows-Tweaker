# Changelog

All notable changes to LuzidSettings are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [Unreleased]

---

## [4.0.0] — 2026-03-04

### Added
- Complete UI redesign — tactical dark cyber interface with 15-tab sidebar navigation
- 28 General tweaks from Optimizer-16.7 (services, NTFS, HPET, SMB, hibernation, menu delay, UTC time, volume mixer, sticky keys, compatibility assistant, sensor services, error reporting, print spooler, fax, HomeGroup, SmartScreen, system restore, long paths, modern standby, all notification icons, detailed login, network throttling)
- 19 Privacy tweaks (activity history, Cortana, Windows Ink, spell check, cloud clipboard, NVIDIA telemetry, Chrome telemetry, Firefox telemetry, Visual Studio telemetry, Office 2016 telemetry, Edge telemetry, Edge AI/Discover, CoPilot, OneDrive disable, OneDrive uninstall, Insider service, My People, Start Menu ads, taskbar search)
- 20 Windows 11 tweaks (Gaming Mode, Xbox Live, Game Bar, driver exclusion from updates, automatic updates, Store updates, TPM 2.0 bypass, classic right-click menu, taskbar left align, Widgets, Teams/Chat, Snap Assist, Stickers, compact Explorer, classic Photo Viewer, VBS/HVCI disable, Cast to Device removal, classic Explorer, S0ix disable, News and Interests)
- Live system monitor tab with 60-second rolling CPU and RAM graphs
- FPS overlay — transparent always-on-top frame counter
- Auto game detection with automatic profile switching
- System restore point manager with async progress callback
- Registry tweaker tab with preset registry operations
- Benchmark engine for CPU, RAM and disk
- Startup manager — view and toggle all Windows autostart entries
- Process scanner with kill support
- Network analyzer with 4-second auto-refresh
- Profile system: Gaming, Work, Silent, Balanced presets
- Thread-safe UI update queue — background threads use `queue.Queue` instead of direct `self.after()` calls
- `_process_ui_queue` polling loop drains the queue every 100ms on the main thread

### Fixed
- **TclError: cannot use geometry manager pack inside frame which already has slaves managed by grid** — `_build_general_tab` was appending a label via `.pack()` directly into a CTkTabview-managed frame that uses `grid` internally. Resolved by building the description label directly inside the `CTkScrollableFrame` which uses only `pack`
- **RuntimeError: main thread is not in main loop** — multiple background `_load` threads called `self.after()` directly. Replaced all such calls with `self._ui_queue.put(lambda: ...)` which is drained safely on the main thread
- **NameError: name 'status_lbl' is not defined** — `status_lbl` was defined in `_build_toggle_tab` but not passed as a parameter to `_toggle_row`, causing a NameError when toggle switches were fired. Fixed by adding `status_lbl` as an explicit parameter to `_toggle_row` and updating all call sites

### Changed
- Mainwindow fully rebuilt as `mainwindow_new.py` replacing the old `mainwindow.py`
- All tab content builders separated into individual `_build_*_tab()` methods
- `self.tabs` CTkTabview is now created before `_build_nav()` is called, preventing reference errors in nav button lambdas

---

## [3.0.0] — Prior release

- Original HarteSettings V3 codebase
- Basic optimization engine
- Simple single-window layout
