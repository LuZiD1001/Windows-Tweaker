"""Application shortcuts and help information"""

SHORTCUTS = {
    'Command Palette': 'Ctrl + Shift + P',
    'Quick Profile - Gaming': 'Ctrl + 1',
    'Quick Profile - Streaming': 'Ctrl + 2',
    'Quick Profile - Balanced': 'Ctrl + 3',
    'Quick Profile - Office': 'Ctrl + 4',
    'Run Full Optimization': 'Ctrl + Shift + O',
    'Dashboard': 'Ctrl + 1',
    'Minimize': 'Ctrl + M',
}

HELP_TEXT = """
╔════════════════════════════════════════════╗
║     LUZIDSETTINGS - HELP GUIDE        ║
╚════════════════════════════════════════════╝

📚 FEATURES:

⚡ QUICK PROFILES
  One-click optimization profiles:
  • Gaming - Maximum FPS & response time
  • Streaming - CPU efficiency
  • Balanced - Good performance + stability
  • Office - Minimal resource usage
  • Ultra - Apply ALL optimizations

📊 DASHBOARD
  Real-time system monitoring:
  • CPU, RAM, Disk usage
  • System health indicator
  • Temperature monitoring
  • Process count

⚙️ TWEAKS
  Individual optimization modules:
  • Anti-Analysis Shield - Block telemetry
  • Network Zenith - Network optimization
  • Memory Vacuum - Clear cache & memory
  • Input Latency Fix - Reduce input lag
  • Trace Eraser - Clean temporary files

📈 MONITOR
  Advanced system monitoring and statistics.

🔧 SETTINGS
  Application preferences and configuration:
  • Theme selection
  • Auto-start options
  • Tray icon settings
  • Logging configuration

🤖 AUTOMATION
  Schedule automatic optimizations:
  • Daily profiles
  • Weekly deep optimization
  • Hourly cache cleanup
  • On-startup optimization

📋 LOGS
  View application logs and statistics.

╔════════════════════════════════════════════╗
║           KEYBOARD SHORTCUTS              ║
╚════════════════════════════════════════════╝

"""

for action, shortcut in SHORTCUTS.items():
    HELP_TEXT += f"  {action:<30} {shortcut}\n"

HELP_TEXT += """
╔════════════════════════════════════════════╗
║              SYSTEM REQUIREMENTS          ║
╚════════════════════════════════════════════╝

✓ Windows 10 / Windows 11
✓ Python 3.9+
✓ Administrator privileges (recommended)
✓ 100MB free disk space

╔════════════════════════════════════════════╗
║            TROUBLESHOOTING                ║
╚════════════════════════════════════════════╝

Q: Nothing happens when I click "Apply"
A: Some features require Administrator privileges.
   Run LuzidSettings as Admin.

Q: My performance didn't improve
A: Results depend on your current system state.
   Try the "Ultra" profile for maximum effect.

Q: Is it safe to use?
A: Yes! All operations are reversible and safe.
   The app only modifies:
   • System temporary files
   • DNS/Network settings
   • Event logs
   • Registry cached values

📧 SUPPORT:
For issues or feature requests, visit:
https://github.com/luzid/LuzidSettings
"""
