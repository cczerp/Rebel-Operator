# Requirements Installation Guide

## Overview

Dependencies are split into multiple files to handle Windows vs Linux differences and prevent conflicts:

- **requirements-core.txt** - NON-NEGOTIABLE pinned versions (Python 3.11.9 compatible)
- **requirements-windows.txt** - Windows-only packages (GUI, automation)
- **requirements-linux.txt** - Linux-only packages (for Render/production)
- **requirements.txt** - All other dependencies (flexible versions)

## Installation

### For Windows Development

```bash
pip install -r requirements-core.txt -r requirements-windows.txt -r requirements.txt
```

### For Linux/Render (Production)

```bash
pip install -r requirements-core.txt -r requirements-linux.txt -r requirements.txt
```

## Non-Negotiable Core Dependencies

These versions are **LOCKED** and tested together. DO NOT change without testing:

- **Python**: 3.11.9 (required for faiss-cpu)
- **faiss-cpu**: 1.9.0.post1 (only version with Python 3.11 wheels)
- **numpy**: 1.26.4 (must be < 2.0 for faiss-cpu compatibility)
- **torch**: 2.2.1 (compatible with numpy 1.26.4)
- **transformers**: 4.35.0 (compatible with torch 2.2.1)
- **chromadb**: 0.4.18 (needs faiss-cpu and numpy)

## Fixed Conflicts

- **urllib3**: Pinned to 2.0.7 to satisfy both `kubernetes` (<2.4.0) and `qdrant-client` (<2.0.0)
- **Windows packages**: Separated to prevent Linux installation failures

## Platform Differences

### Windows Only
- `customtkinter` - GUI framework
- `pywin32` - Windows API access
- `PyAutoGUI`, `PyGetWindow`, etc. - Windows automation
- `win32_setctime` - Windows file timestamps

### Linux Only
- `gunicorn` - Web server (also in core for Render)
- All Windows packages are excluded

## Troubleshooting

If you get dependency conflicts:

1. **Always install core first**: `pip install -r requirements-core.txt`
2. **Then platform-specific**: `pip install -r requirements-windows.txt` (or linux)
3. **Finally extras**: `pip install -r requirements.txt`

If conflicts persist, check `pip check` output and verify urllib3 version.

