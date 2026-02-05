# Changelog

## [1.1.0] - 2026-02-05
### Fixed
- Fixed issue where custom files in subdirectories were not accessible on Windows due to path separator handling.
- Fixed syntax error in `index.html` preventing page load.
- Fixed theme persistence issue where the app might reset to Dark Mode on reload. Added script to prevent Flash of Unstyled Content (FOUC).
### Added
- **Sidebar Filtering**: Added buttons to filter the file list by "All", "Default" (root), and "Custom" (subdirectories).
- **Visual Improvements**: 
    - Replaced text badges with a subtle dot indicator for custom files.
    - Improved Dark Mode contrast and styling in the separate Visual Preview pane.
- Helper scripts `run.ps1` and `run.sh` to automatically manage venv and run the app.
- Light/Dark mode toggle (persisted via LocalStorage).
- Configuration changes: `config.ini` is now git-ignored. `config.example.ini` is provided with default PRTG paths.
- Auto-reload support for development via `--reload` flag or `PRTG_DEBUG` env var (uses `hupper`).
- Type selector for switching between Device Templates, SNMP Libraries, and Lookups.
- Configuration for multiple template paths in `config.ini`.
- Single-page interface updates to support multi-template management.

## [1.0.0] - 2026-02-05
### Added
- Initial release of PRTG Template Studio.
- Secure, dark-mode web interface for editing `.odt` files.
- Automatic Git versioning on save.
- Visual XML preview.
- HTTP Basic Auth.


The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup.
