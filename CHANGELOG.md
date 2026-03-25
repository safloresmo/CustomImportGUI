# Changelog

## [1.3.0] - 2026-03-24

### Added
- Tabbed interface: Import, Search, Configuration, Library, Design Blocks, History
- Integrated JLCPCB/LCSC component search with images and pricing
- KiCad Official library search (GitLab - no auth required)
- Sub-library organization by category (automatic and manual)
- Move, copy, edit and delete components from the Library tab
- Design Blocks support: create, import schematics, edit metadata, delete
- Batch import for EasyEDA (multiple IDs separated by comma)
- Import history with clear and view functionality
- Progress bar during imports
- Configuration profiles with export/import (JSON)
- Auto-update checker (checks GitHub releases on startup)
- Search filter in Library tab
- Duplicate detection when searching
- Create new libraries and sub-libraries from the plugin
- Auto-create directories on first run
- Dynamic version from metadata.json
- ZIP validation with clear error messages
- Dark theme compatibility (system colors)
- 101 automated tests

### Changed
- Refactored into 8 modules (was 1 file with 2728 lines)
- Window size increased for better layout
- Improved i18n coverage (Spanish and English)

### Fixed
- Design block library format updated from .kicad_dblk to .kicad_blocks (KiCad 10)

## [1.2.0] - 2026-03-20

### Added
- KiCad 10 compatibility
- Auto-configure environment variables
- IPC API support (dual mode: IPC + SWIG fallback)

## [1.1.0] - 2025-10-31

### Added
- Custom metadata on imported components
- EasyEDA import improvements
- Plugin interface enhancements

## [1.0.0] - 2025-10-15

### Added
- Initial release
- Multi-source import (EasyEDA, Octopart, Samacsys, UltraLibrarian, Snapeda)
- Customizable library names and environment variables
- Drag and drop ZIP import
