# ***FractalLauncher v1.2.4 (Optimize Patch)***

## Bug Fixes

- Fixed the first-launch onboarding flow not appearing on fresh installs, including configs written by the bootstrap.
- Fixed settings being overwritten on save; settings now merge into the existing config and preserve unrelated keys.
- Added support for both camelCase and snake_case config keys (`javaPath`/`java_path`, `authlibPath`/`authlib_injector_path`, `defaultMcDir`/`default_mc_dir`, `hideOnGame`/`hide_launcher_on_game`, `firstLaunch`/`first_launch`).
- Fixed Fabric/Quilt version detection using the loader version instead of the Minecraft version; version parsing now prefers the installed version JSON's `inheritsFrom`, then applies loader-aware numeric matching.
- Fixed loader profiles launching without the required vanilla parent installed; the base version is now installed first, then the loader version launches.
- Fixed corrupt or stub version JSONs breaking the installed-versions list; versions are now scanned per folder and invalid entries are skipped.
- Fixed the launcher being hidden while the game runs; the window now hides on launch and restores on exit.
- Fixed stale Microsoft account tokens not being refreshed before launch.
- Fixed the Home and Settings screens getting stuck on “Loading…” during the pywebview startup RPC race; both now retry with a watchdog.
- Fixed console event flooding and ordering; console lines are batched and flushed in order.
- Fixed install progress bars not reliably reaching 100%; progress is throttled to ~10 Hz with a guaranteed final update.
- Fixed profile deletion leaving the profile's game folder behind; deleting a profile now removes `FractalLauncher_profiles/<profile id>` without touching `.minecraft` or unrelated folders.
- Fixed language changes not persisting; language is now saved immediately.
- Fixed the launcher automatically switching to the Console on launch or exit; the Console is now offered only after a crash.
- Fixed duplicate launch callback definitions that interfered with hide-on-game behavior.
- Fixed external profile imports creating duplicates; profiles are now deduplicated by version and mod loader.
- Fixed external profile imports ignoring existing per-profile game folders; orphaned folders are now reattached when possible.
- Fixed legacy launcher-name references still appearing across the UI.
- Fixed installed shader packs and resource packs not appearing in their Installed panels or search results; both lists now refresh after install/removal and support folder-based packs.
- Fixed screenshot editor overwrites appearing not to work because WebView kept showing the cached thumbnail; thumbnails now refresh by file timestamp and JPEG screenshots are saved as JPEG.
- Fixed stale shortcut/taskbar icons after updating; installers now use a versioned icon path, notify the shell, and the app applies its current window icon explicitly.

## Security Fixes

- Added HTML escaping for dynamic account names, filenames, error messages, and status messages.
- Restricted diagnostics repair actions to an explicit allowlist before executing filesystem or shell actions.

## Removed Features

- Removed the Servers page, built-in server browser, Add Server modal, server ping display, and Copy IP controls.
- Removed the Cerebras AI theme-generation flow and API-key modal from Settings.
- Removed the unused `_DownloadTracker` and `IncompleteReadError` classes.
- Replaced the emoji-based UI icon usage with an SVG icon system.

## New Features

- Added a six-step first-run onboarding tour with spotlight highlighting, keyboard navigation, Skip, and “Take me there” shortcuts.
- Added a visual Theme Editor with per-color pickers, per-color save feedback, named themes, and persistent custom theme saving.
- Added automatic detection of Minecraft profiles created by other launchers, including official launcher profile names and custom game directories.
- Added profile import with mod-loader detection, version/loader deduplication, dismissed-profile memory, and orphaned profile-folder adoption.
- Added a diagnostics overhaul covering system, Java, Minecraft, network, account, and launcher health.
- Added diagnostic summaries, grouped results, category icons, one-click fixes, and a copyable diagnostic report.
- Added hardware, memory, disk-space, network, crash-report, log, mod, resource-pack, shader-pack, and world checks.
- Added loader-aware game-version diagnostics for vanilla, Fabric, Quilt, Forge, and NeoForge.
- Added persistent language selection and translations for the new diagnostics, onboarding, and profile-description strings.
- Added a new SVG icon set, keyboard-accessible action cards, hover/active states, and lazy-loaded thumbnail images.
- Added EULA and TOS documents.
- Added a factory-reset script that backs up launcher data before resetting and leaves personal Minecraft data intact.

## Unresolved Bugs

- Multiplayer skin support.

## Soon to be added

- Built-in free server hosting.
- Hybrid core: Java + Bedrock.

## Behind The Scenes

- Added a shared `requests.Session` for Modrinth API and download requests to reuse connections and TLS handshakes.
- Added cached JSON parsing for version and asset-index files used during launch checks.
- Reduced UI overhead by batching console events and throttling install-progress updates.
- Improved installed-version scanning so one broken version folder no longer invalidates the entire list.
- Added loader/version filesystem helpers for detecting loaders, resolving base versions, validating version JSONs, and finding installed loader variants.
- Improved home/settings startup reliability with retry loops and per-attempt watchdogs.
- Slimmed the PyInstaller build by collecting only the required webview submodules/data, adding the Windows winforms backend explicitly, and excluding `setuptools`, `pkg_resources`, and `numpy`.
- Updated the application icon from 229,740 bytes to 4,286 bytes.
- Added repository-level legal/reset files while keeping runtime logs and Python cache files out of the release comparison.
