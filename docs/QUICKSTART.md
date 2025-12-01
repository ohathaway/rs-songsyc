# Quick Start Guide

## For Repository Owners

### 1. Generate Your Library Data

```bash
# Navigate to your project root
cd rs-songsyc

# Activate virtual environment
source bin/activate  # On macOS/Linux
# or
.\Scripts\activate  # On Windows

# Scan your Rocksmith library
python scanner.py /path/to/your/rocksmith/dlc/folder
```

This creates `library.json` in the current directory.

### 2. Copy to Web Viewer

```bash
# Copy the generated library.json to the docs folder
cp library.json docs/library.json
```

### 3. Test Locally

```bash
# Start a local web server
cd docs
python -m http.server 8000

# Open your browser to:
# http://localhost:8000
```

### 4. Deploy to GitHub Pages

1. Commit and push your changes:
   ```bash
   git add docs/library.json
   git commit -m "Update library data"
   git push
   ```

2. Enable GitHub Pages:
   - Go to repository Settings
   - Click "Pages" in the sidebar
   - Under "Source", select "Deploy from a branch"
   - Select branch: `main` (or `master`)
   - Select folder: `/docs`
   - Click "Save"

3. Wait a few minutes, then visit:
   `https://your-username.github.io/rs-songsyc/`

## For Viewers (No Setup Required)

Just visit the GitHub Pages URL to browse the library!

## Updating Your Library

When you add new songs to your Rocksmith library:

1. Run the scanner again:
   ```bash
   python scanner.py /path/to/rocksmith/dlc
   ```

2. Copy the new library.json:
   ```bash
   cp library.json docs/library.json
   ```

3. Commit and push:
   ```bash
   git add docs/library.json
   git commit -m "Update library with new songs"
   git push
   ```

GitHub Pages will automatically update in a few minutes.

## Using the Viewer

### Search
- Type in the search box to filter by song title, artist, or album
- Search is case-insensitive and matches partial text

### Filters
- **Artist**: Select a specific artist from the dropdown
- **Arrangement**: Filter by Lead, Rhythm, Bass, Vocals, or Combo
- **Tuning**: Filter songs by specific tunings (e.g., Drop D, E Standard)
- **Platform**: Show only PC, Mac, or songs available on both platforms

### Reset
- Click "Reset Filters" to clear all filters and show all songs

### Statistics
The top bar shows:
- Total number of songs in your library
- Number of unique artists
- Count of songs with Lead, Rhythm, and Bass arrangements

## Optional: Enable Dropbox Downloads

To add download links to your library viewer:

1. Upload your PSARC files to Dropbox (if you haven't already)

2. Edit `docs/config.js` and add your Dropbox folder URL:

```javascript
const CONFIG = {
    dropboxBaseUrl: "https://www.dropbox.com/home/RockSmithDLC",
    dropboxOrganizedByArtist: true,
};
```

3. Commit and push the config changes

4. Platform badges (PC/Mac) will now be clickable download links with a ⬇ icon

## Troubleshooting

### "Error loading library" message
- Make sure `library.json` exists in the `docs/` folder
- Check that the JSON file is valid (re-run scanner if needed)
- If testing locally, ensure you're using a web server (not just opening the HTML file)

### Changes not showing on GitHub Pages
- Wait 3-5 minutes after pushing for GitHub to rebuild the site
- Check the Actions tab in your repository to see build status
- Clear your browser cache

### No songs displayed
- Check that your library.json contains song data
- Try clicking "Reset Filters" - you may have filters active
- Open browser console (F12) to check for JavaScript errors
