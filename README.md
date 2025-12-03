# rs-songsyc

A Python utility for organizing and cataloging Rocksmith CDLC libraries.

## Features

- **Automatic Organization**: Recursively scans directories and organizes PSARC files by artist
- **Metadata Cataloging**: Generates comprehensive JSON metadata for all songs in your library
- **Platform Detection**: Tracks which platform versions (PC/Mac) are available for each song

## Requirements

- Python 3.14+
- rstools package

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd rs-songsyc

# Create and activate virtual environment
python3 -m venv .
source bin/activate  # On macOS/Linux
# or
.\Scripts\activate  # On Windows

# Install dependencies
pip install rstools
```

## Usage

### Scanning and Generating Metadata

```bash
# Scan library and generate library.json with all metadata
python scanner.py <path-to-rocksmith-dlc-folder>
```

This will:
- Recursively scan for all PSARC files
- Extract metadata (artist, album, title, year, arrangements, tunings)
- Generate `library.json` with comprehensive song information
- Display summary statistics

### Organizing Files by Artist

```bash
# Preview changes (dry-run mode)
python organize.py <path-to-rocksmith-dlc-folder> --dry-run

# Execute organization (will prompt for confirmation)
python organize.py <path-to-rocksmith-dlc-folder>
```

This will:
- Scan PSARC files in the root directory
- Extract artist names from file metadata
- Create artist-named subdirectories
- Move files into their respective artist folders

### Splitting Bundled PSARC Files

Some PSARC files contain multiple songs (like RS1 compatibility packs). Use the splitter to extract individual songs:

```bash
# Preview what would be extracted
python split_psarc.py /path/to/bundled_file.psarc --dry-run

# Split into individual song files
python split_psarc.py /path/to/bundled_file.psarc

# Specify output directory
python split_psarc.py /path/to/bundled_file.psarc -o /output/directory/
```

This will:
- Analyze the bundled PSARC to identify individual songs
- Extract each song with all its associated files
- Create separate PSARC files for each song
- Generate appropriate filenames (Artist_Title_v1_p.psarc)

### Converting Between PC and Mac

Convert PSARC files between PC and Mac platforms:

```bash
# Preview conversion (dry-run)
python convert_platform.py /path/to/song_p.psarc mac --dry-run

# Convert PC to Mac
python convert_platform.py /path/to/song_p.psarc mac

# Convert Mac to PC
python convert_platform.py /path/to/song_m.psarc pc

# Specify output directory
python convert_platform.py /path/to/song_p.psarc mac -o /output/directory/
```

This will:
- Detect the source platform automatically
- Re-encrypt .sng files with the target platform's encryption key
- Update file paths for the target platform
- Create a properly formatted PSARC for the target platform

**Note:** The conversion process handles the platform-specific encryption that Rocksmith uses for its chart files (.sng).

## File Naming Conventions

Rocksmith PSARC files follow these patterns:
- **PC version**: `*_p.psarc`
- **Mac version**: `*_m.psarc`

Songs may have both PC and Mac versions in your library.

## Output

### scanner.py
Generates **library.json** with comprehensive metadata:
- Song title, artist, album, year, length
- Platform availability (PC, Mac, or both)
- File paths for each platform
- **Arrangements**: Lead, Rhythm, Bass, Combo, Vocals
- **Tunings**: Named tunings (E Standard, Drop D, DADGAD, etc.) for each arrangement

### organize.py
Creates an **organized directory structure**:
```
rocksmith-dlc/
├── Avenged Sevenfold/
│   ├── song1_p.psarc
│   └── song1_m.psarc
├── Metallica/
│   ├── song2_p.psarc
│   └── song3_p.psarc
└── ...
```

## Web Viewer

A static web viewer is included in the `docs/` directory for browsing your library in a browser.

### Setup GitHub Pages

1. Generate your library:
   ```bash
   python scanner.py /path/to/rocksmith/dlc
   ```

2. Copy library.json to docs:
   ```bash
   cp library.json docs/library.json
   ```

3. Enable GitHub Pages in your repository settings (deploy from `/docs` folder)

### Features

- 🔍 Search and filter songs
- 📊 View library statistics
- 🎸 Browse arrangements and tunings
- 📱 Mobile-friendly interface
- 🌙 Dark theme
- ⬇️ Optional Dropbox download links

### Dropbox Integration

Enable download links by editing `docs/config.js`:

```javascript
const CONFIG = {
    dropboxBaseUrl: "https://www.dropbox.com/home/RockSmithDLC",
    dropboxOrganizedByArtist: true,
};
```

Platform badges (PC/Mac) become clickable download links when configured.

See [docs/README.md](docs/README.md) for more details.

## License

MIT
