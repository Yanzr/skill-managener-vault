---
name: screenshot
description: "Use this skill whenever the user asks to take a screenshot, capture the screen, or make a screen capture on their Windows computer. This includes: full screen capture, capturing specific windows, or saving screenshots to a specified location."
---

# Screenshot Skill

## Available Scripts

| Script | Purpose |
|--------|---------|
| `scripts/capture_gdi.ps1 [output_path]` | Full-screen capture via GDI BitBlt (handles high-DPI correctly) |

## Usage

When the user requests a screenshot, run from the skill's script directory (`~/.claude/skills/screenshot/scripts/`):

```powershell
powershell.exe -ExecutionPolicy Bypass -File "$HOME\.claude\skills\screenshot\scripts\capture_gdi.ps1" [output_path]
```

Or use the full path directly:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\lenovo\.claude\skills\screenshot\scripts\capture_gdi.ps1" [output_path]
```

### Parameters

- `output_path` — Optional. Full path to save the PNG file. Default: `$HOME\Desktop\screenshot.png`

### Examples

```powershell
# Save to default location (Desktop\screenshot.png)
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\lenovo\.claude\skills\screenshot\scripts\capture_gdi.ps1"

# Save to specific path
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\lenovo\.claude\skills\screenshot\scripts\capture_gdi.ps1" "C:\Users\lenovo\Desktop\ccstart\myscreenshot.png"
```

## How It Works

The script uses Win32 GDI APIs (`BitBlt`, `CreateCompatibleBitmap`) to capture the screen at the physical pixel resolution, bypassing DPI scaling issues. It:

1. Sets process DPI awareness via `SetProcessDpiAwareness`
2. Reads physical resolution via `EnumDisplaySettings`
3. Creates a compatible bitmap and copies screen content via `BitBlt`
4. Saves as PNG

This approach correctly handles high-DPI displays (125%, 150%, 200% scaling).
