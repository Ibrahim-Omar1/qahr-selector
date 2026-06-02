# Auto-HP

Drives the game's **own** auto-potion: a toggle + a "drink below X%" slider that
write the native auto-HP-pot settings. The game does the drinking (on its own
thread), so this is just a small settings **write** — no injection, no tripwire,
no potion ids to configure.

## How it works
`MemoryReader.set_auto_hp(pct)` writes (verify-before-write, read-back):
- `hero+0x4EC8` (byte) — `1` enables the idle HP-pot path, `0` disables.
- `hero+0x4ED0` (dword) — HP% threshold (cadence path).
- `[ninjaSkillMgr]+0x154` (dword, `ninjaSkillMgr = [0x1A058E4]`) — HP% threshold
  (main path; the field the trigger compares against).

The game's trigger (`0x00F78502`) drinks when `currentHP < maxHP*pct/100`, a
cooldown has elapsed, and a potion is in its list. Verified live: writing
`enable=1, pct=60` is read back correctly; the game then auto-drinks below 60%.

`AutoController` (`viewmodels/auto_vm.py`) is a thin, plain object — Auto-HP is
"write two values", so there's nothing to poll. UI: `ui/pages/auto_page.py`.

## Not included: Auto-Mana
The game's native **MP** auto-pot only runs **while Auto-Hunt is actively
hunting** (gated by the hunt state), and its MP threshold isn't reachable as a
plain field. So idle Auto-Mana would need the heavier active-call path
(`UsageFunc` from the tick) — deferred.
