# CLAUDE.md - Project Context

## Project Overview
**rs-songsyc** is a Python utility for managing Rocksmith CDLC (Custom Downloadable Content) libraries.

## Purpose
This tool scans directories recursively for Rocksmith `.psarc` files and performs two primary functions:
1. **Organization**: Moves all PSARC files into directories organized by artist name
2. **Cataloging**: Generates a comprehensive JSON metadata file containing song information and platform availability

## Key Technical Details

### File Naming Conventions
- PC version files: `*_p.psarc`
- Mac version files: `*_m.psarc`
- Songs may have both PC and Mac versions

### Dependencies
- **rstools**: Python package for reading and parsing Rocksmith PSARC files
- Python 3.14 (based on venv configuration)

### Current State
- Virtual environment created at project root
- rsrtools package installed (note: package is `rsrtools` not `rstools`)
- Initial scanner implementation created in `scanner.py`

## Data Structure
The JSON output should track:
- Song metadata (title, artist, album, etc.)
- Platform availability (PC, Mac, or both)
- File locations
- Any other relevant metadata extractable from PSARC files

## Implementation Notes
- Must handle recursive directory scanning ✓ (implemented)
- Need to safely move files to artist-named directories ✓ (implemented in organize.py)
- Should handle duplicate songs (same song, different platforms) ✓ (implemented)
- JSON output should be comprehensive and well-structured ✓ (implemented)

## Files

### scanner.py
Main metadata scanner that:
- Recursively scans directories for `.psarc` files
- Uses `rsrtools.files.welder.Welder` to read PSARC archives
- Extracts song metadata from manifest JSON files inside archives
- Detects platform (PC/Mac) based on filename suffix
- Handles songs that have both PC and Mac versions
- **Extracts arrangement information**: Lead, Rhythm, Bass, Combo, Vocals
- **Detects tunings**: Maps tuning data to named tunings (E Standard, Drop D, etc.)
- Exports comprehensive JSON with all song metadata including arrangements and tunings
- Provides summary statistics including arrangement counts

**Extracted Data:**
- Song title, artist, album, year, length
- Platform availability (PC, Mac, or both)
- File paths
- Arrangements with type and tuning for each

Usage: `python scanner.py <path-to-rocksmith-dlc-folder>`

### split_psarc.py
Utility to split bundled PSARC files (like rs1compatibilitydlc_p.psarc) into individual song files:
- Analyzes bundled PSARC files to identify individual songs
- Extracts and groups files belonging to each song
- Creates separate PSARC files for each song
- Automatically generates appropriate filenames based on artist and title
- **Safety features**:
  - Dry-run mode to preview what would be created
  - Confirmation prompt before creating files
  - Preserves platform suffix (_p.psarc or _m.psarc)
  - Clean temporary file handling

**Usage:**
```bash
# Preview what songs would be extracted (dry-run)
python split_psarc.py /path/to/bundled_file.psarc --dry-run

# Split into individual files (default output: source_split/)
python split_psarc.py /path/to/bundled_file.psarc

# Specify custom output directory
python split_psarc.py /path/to/bundled_file.psarc -o /path/to/output/
```

**Note:** This is useful for bundled archives like RS1 compatibility packs where multiple songs are in one file.

### convert_platform.py
Platform converter to convert PSARC files between PC and Mac:
- Auto-detects source platform from filename or file contents
- Re-encrypts .sng files with target platform's encryption key
- Updates file paths for target platform (songs/bin/generic/ ↔ songs/bin/macos/)
- Creates properly formatted PSARC for target platform
- **Safety features**:
  - Dry-run mode to preview conversion
  - Confirmation prompt before converting
  - Validates source and target platforms
  - Clean temporary file handling

**Usage:**
```bash
# Preview conversion (dry-run)
python convert_platform.py /path/to/song_p.psarc mac --dry-run

# Convert PC to Mac
python convert_platform.py /path/to/song_p.psarc mac

# Convert Mac to PC
python convert_platform.py /path/to/song_m.psarc pc

# Specify output directory
python convert_platform.py /path/to/song.psarc mac -o /output/
```

**Note:** Rocksmith uses platform-specific encryption for .sng chart files. This tool handles the decryption/re-encryption automatically.

### organize.py
File organizer that moves PSARC files into artist-named directories:
- Scans directory for PSARC files in the root level
- Extracts artist name from manifest data
- Creates artist directories with sanitized names (removes invalid characters)
- Moves files into appropriate artist folders
- **Safety features**:
  - Dry-run mode to preview changes without moving files
  - Confirmation prompt before executing moves
  - Skips files already in subdirectories
  - Handles duplicate filenames
  - Progress indicators for large libraries

**Usage:**
```bash
# Preview changes without moving files
python organize.py <path-to-rocksmith-dlc-folder> --dry-run

# Show detailed preview
python organize.py <path-to-rocksmith-dlc-folder> --preview

# Execute organization (will ask for confirmation)
python organize.py <path-to-rocksmith-dlc-folder>
```

### docs/ - Web Viewer
Static website for browsing the library in a browser (GitHub Pages compatible):

**Files:**
- `index.html` - Main viewer page
- `styles.css` - Dark theme styling with responsive design
- `viewer.js` - JavaScript for loading, filtering, and displaying library data
- `config.js` - Configuration for Dropbox integration (optional)
- `README.md` - Setup instructions for GitHub Pages
- `QUICKSTART.md` - Quick start guide for deployment
- `library.json` - Copy of generated library data (user must copy this)

**Features:**
- Real-time search across title, artist, and album
- Multi-criteria filtering:
  - Artist dropdown (dynamically populated)
  - Arrangement type (Lead, Rhythm, Bass, Vocals, Combo)
  - Tuning dropdown (dynamically populated from library)
  - Platform (PC, Mac, Both)
- Statistics dashboard showing:
  - Total songs and artists
  - Count of songs with Lead/Rhythm/Bass arrangements
- Card-based layout with hover effects
- Dark theme optimized for viewing
- Fully responsive (mobile-friendly)
- No backend required - pure static HTML/CSS/JS
- **Optional Dropbox integration**:
  - Configurable via config.js
  - Platform badges become clickable download links
  - Supports both organized (by artist) and flat file structures
  - Generates proper Dropbox preview URLs

**Setup:**
1. Run scanner.py to generate library.json
2. Copy library.json to docs/ folder
3. Enable GitHub Pages in repository settings (deploy from /docs folder)

### Next Steps
1. Consider adding backup/undo functionality to organize.py
2. Add ability to reorganize already-organized files (if artist metadata changed)
3. Add export options to web viewer (CSV, filtered JSON)
4. Add sorting options to web viewer (by title, artist, year)
