# SOP: Scheduled Trigger (Phase 5)

## Goal
Run `run_pipeline.py` once a day at **07:30 local time**, so fresh articles are in `data/articles.json` before the user's morning check.

## Mechanism
- **Scheduler:** macOS launchd user agent `~/Library/LaunchAgents/com.hippo.ainews.pipeline.plist` (`StartCalendarInterval` Hour=7 Minute=30).
- **Interpreter:** `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3` (absolute path; launchd does not load the shell `PATH`).
- **Working directory:** project root. Required, since all tools use relative paths (`.tmp/`, `data/`).
- **Logs:** `.tmp/launchd_pipeline.out.log` and `.tmp/launchd_pipeline.err.log`.

## Behavior
- If the Mac is asleep at 07:30, launchd runs the job once on wake. If it is powered off, that day's run is skipped.
- The job survives reboots and logouts. No terminal needs to stay open.
- `trigger_daemon.py` (24h sleep loop) is kept as a manual fallback. Do not run it alongside the launch agent.

## Operations
- Load: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hippo.ainews.pipeline.plist`
- Run now (test): `launchctl kickstart gui/$(id -u)/com.hippo.ainews.pipeline`
- Unload: `launchctl bootout gui/$(id -u)/com.hippo.ainews.pipeline`
- Change time: edit Hour/Minute in the plist, then unload and load again.
