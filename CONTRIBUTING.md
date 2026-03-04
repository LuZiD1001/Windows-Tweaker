# Contributing to LuzidSettings

Thanks for contributing — every tweak, bugfix and improvement counts.

---

## How to Contribute

### Reporting Bugs

Open an issue using the Bug Report template. Include:
- Windows version
- Python version or "using EXE"
- Full error message / traceback
- Steps to reproduce

### Suggesting Tweaks or Features

Open an issue with the `enhancement` label. Describe what you want and why it helps.

### Submitting Code

```bash
# Fork the repo, then:
git clone https://github.com/YOUR_USERNAME/LuzidSettings.git
cd LuzidSettings
pip install -r requirements.txt

git checkout -b feature/my-change
# make your changes
git commit -m "feat: describe what you did"
git push origin feature/my-change
# open Pull Request on GitHub
```

---

## Adding a New Tweak

Tweaks are defined in `src/gui/mainwindow_new.py` in one of three lists near the top:

- `_GENERAL_TWEAKS` — system-level tweaks
- `_PRIVACY_TWEAKS` — privacy and telemetry
- `_WIN11_TWEAKS` — Windows 11 specific

**Step 1 — Add the definition:**

```python
("My Tweak Label",  "my_tweak_on",  "my_tweak_off",
 "Short description of what this does."),
```

Format: `(display_label, enable_fn_name, disable_fn_name, description)`
Use `None` as disable_fn_name if the tweak is one-way (e.g. uninstall).

**Step 2 — Implement the logic in `_apply_toggle()`:**

```python
elif fn_name == "my_tweak_on":
    _reg("HKLM", r"SOFTWARE\Path\To\Key", "ValueName", 1)
elif fn_name == "my_tweak_off":
    _reg("HKLM", r"SOFTWARE\Path\To\Key", "ValueName", 0)
```

Available helpers inside `_apply_toggle`:

| Helper | Usage |
|---|---|
| `_reg(hive, path, name, value)` | Write a registry DWORD or string value |
| `_svc(name)` | Disable and stop a Windows service |
| `_run(cmd)` | Run a shell command silently |

**Step 3 — Test both enable and disable.** Make sure it's reversible.

**Step 4 — Update CHANGELOG.md** under `[Unreleased]`.

---

## Commit Style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add tweak for disabling Xbox Game DVR
fix: resolve status_lbl scope issue in toggle rows
docs: add screenshots to README
refactor: extract registry helpers to separate module
chore: update dependencies
```

---

## Pull Request Checklist

- [ ] Tested on Windows 10 or 11
- [ ] Both enable and disable sides work
- [ ] CHANGELOG.md updated
- [ ] No unrelated changes mixed in
- [ ] Screenshots included if it's a UI change
