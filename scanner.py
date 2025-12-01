#!/usr/bin/env python3
"""Rocksmith PSARC metadata scanner and library organizer."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import simplejson

from rsrtools.files.welder import Welder


class RocksmithScanner:
    """Scanner for extracting metadata from Rocksmith PSARC files."""

    MAC_SUFFIX = "_m.psarc"
    PC_SUFFIX = "_p.psarc"

    # Tuning names database (from rsrtools)
    TUNING_DB = {
        "000000": "E Standard",
        "-200000": "Drop D",
        "-1-1-1-1-1-1": "Eb Standard",
        "-3-1-1-1-1-1": "Eb Drop Db",
        "-2-2-2-2-2-2": "D Standard",
        "-4-2-2-2-2-2": "D Drop C",
        "-3-3-3-3-3-3": "C# Standard",
        "-4-4-4-4-4-4": "C Standard",
        "-200-1-2-2": "Open D",
        "002220": "Open A",
        "-2-2000-2": "Open G",
        "022100": "Open E",
        "111111": "F Standard",
        "-5-5-5-5-5-5": "B Standard",
        "-6-6-6-6-6-6": "Bb Standard",
        "-7-7-7-7-7-7": "A Standard",
        "-8-8-8-8-8-8": "Ab Standard",
        "-5-3-3-3-3-3": "C# Drop B",
        "-6-4-4-4-4-4": "C Drop A#",
        "-7-5-5-5-5-5": "B Drop A",
        "-8-6-6-6-6-6": "Bb Drop Ab",
        "-9-7-7-7-7-7": "A Drop G",
        "-20000-2": "Double Drop D",
        "-3-1-1-1-1-3": "Double Drop Db",
        "-4-2-2-2-2-4": "Double Drop C",
        "-5-3-3-3-3-5": "Double Drop B",
        "-6-4-4-4-4-6": "Double Drop A#",
        "-200-21-2": "Open Dm7",
        "-4-2-20-40": "CGCGGE",
        "-4-2-2000": "CGCGBE",
        "0-2000-2": "Open Em9",
        "-4-4-2-2-2-4": "Open F",
        "-2000-2-2": "DADGAD",
        "-40-2010": "CACGCE",
        "-20023-2": "DADADd",
        "0000-20": "EADGAe",
        "000012": "All Fourth",
        # Bass tunings
        "0000": "E Standard Bass",
        "-2-2-2-2": "D Standard Bass",
        "-5-5-5-5-4-4": "B Standard 6 String Bass",
        "-6-6-6-6-5-5": "Bb Standard 6 String Bass",
        "-7-7-7-7-6-6": "A Standard 6 String Bass",
        "-8-8-8-8-7-7": "Ab Standard 6 String Bass",
        "-7-5-5-5-4-4": "B Drop A 6 String Bass",
        "-8-6-6-6-5-5": "Bb Drop Ab 6 String Bass",
        "-9-7-7-7-6-6": "A Drop G 6 String Bass",
    }

    def __init__(self, library_path: Path):
        """Initialize scanner with library path.

        Args:
            library_path: Root directory containing PSARC files
        """
        self.library_path = library_path
        self.songs: Dict[str, Dict[str, Any]] = {}

    def scan_directory(self) -> None:
        """Recursively scan directory for PSARC files and extract metadata."""
        print(f"Scanning directory: {self.library_path}")

        # Find all PSARC files
        psarc_files = list(self.library_path.glob("**/*.psarc"))

        if not psarc_files:
            print("No PSARC files found!")
            return

        print(f"Found {len(psarc_files)} PSARC files")

        for psarc_file in psarc_files:
            print(f"Processing: {psarc_file.name}")
            self._process_psarc(psarc_file)

    def _process_psarc(self, psarc_path: Path) -> None:
        """Extract metadata from a single PSARC file.

        Args:
            psarc_path: Path to the PSARC file
        """
        try:
            with Welder(psarc_path, 'r') as psarc:
                # Look for manifest files
                for i in psarc:
                    file_name = psarc.arc_name(i)

                    # Process JSON manifests (contains song metadata)
                    if file_name.startswith("manifests/songs") and file_name.endswith(".json"):
                        self._extract_song_metadata(psarc, i, psarc_path)

        except Exception as e:
            print(f"Error processing {psarc_path.name}: {e}")

    def _extract_song_metadata(self, psarc: Welder, index: int, psarc_path: Path) -> None:
        """Extract song metadata from manifest JSON.

        Args:
            psarc: Welder instance
            index: File index in archive
            psarc_path: Path to the PSARC file
        """
        try:
            data = psarc.arc_data(index)
            manifest = simplejson.loads(data.decode())

            # Get the entries from the manifest
            entries = manifest.get("Entries", {})

            if not entries:
                return

            # Process all entries to get arrangement information
            arrangements = []
            song_key = None
            title = None
            artist = None
            album = None
            year = None
            song_length = None

            for entry_key, entry_data in entries.items():
                attributes = entry_data.get("Attributes", {})

                # Extract core metadata (same for all arrangements)
                if song_key is None:
                    song_key = attributes.get("SongKey", "Unknown")
                    title = attributes.get("SongName", attributes.get("FullName", "Unknown"))
                    artist = attributes.get("ArtistName", "Unknown")
                    album = attributes.get("AlbumName", "Unknown")
                    year = attributes.get("SongYear", 0)
                    song_length = attributes.get("SongLength", 0)

                # Extract arrangement-specific info
                arrangement_name = attributes.get("ArrangementName", "Unknown")
                arrangement_type = self._get_arrangement_type(attributes)
                tuning = self._get_tuning(attributes)

                arrangements.append({
                    "name": arrangement_name,
                    "type": arrangement_type,
                    "tuning": tuning
                })

            # Determine platform from filename
            platform = self._get_platform(psarc_path)

            # Use song_key as unique identifier
            if song_key not in self.songs:
                self.songs[song_key] = {
                    "song_key": song_key,
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "year": year,
                    "song_length": song_length,
                    "arrangements": [],
                    "platforms": [],
                    "files": {}
                }

            # Add platform and file information
            song_data = self.songs[song_key]
            if platform not in song_data["platforms"]:
                song_data["platforms"].append(platform)

            song_data["files"][platform] = str(psarc_path)

            # Merge arrangements (avoid duplicates)
            for arr in arrangements:
                # Check if this arrangement already exists
                arr_exists = any(
                    existing["name"] == arr["name"] and
                    existing["type"] == arr["type"]
                    for existing in song_data["arrangements"]
                )
                if not arr_exists:
                    song_data["arrangements"].append(arr)

            # Update metadata if it was missing
            if song_data["title"] == "Unknown" and title != "Unknown":
                song_data["title"] = title
            if song_data["artist"] == "Unknown" and artist != "Unknown":
                song_data["artist"] = artist
            if song_data["album"] == "Unknown" and album != "Unknown":
                song_data["album"] = album

        except Exception as e:
            print(f"Error extracting metadata from manifest: {e}")

    def _get_arrangement_type(self, attributes: Dict[str, Any]) -> str:
        """Determine arrangement type (Lead, Rhythm, Bass, Combo, Vocals).

        Args:
            attributes: Attributes dictionary from manifest

        Returns:
            Arrangement type string
        """
        arrangement_name = attributes.get("ArrangementName", "").lower()

        # Check for vocals
        if "vocals" in arrangement_name or arrangement_name == "jvocals":
            return "Vocals"

        # Check arrangement properties for guitar/bass
        arr_props = attributes.get("ArrangementProperties", {})

        # Determine path type
        path_lead = arr_props.get("pathLead", 0) == 1
        path_rhythm = arr_props.get("pathRhythm", 0) == 1
        path_bass = arr_props.get("pathBass", 0) == 1
        route_mask = arr_props.get("routeMask", 0)

        # Check for combo (multiple paths)
        if route_mask == 7 or "combo" in arrangement_name:
            return "Combo"

        # Determine specific path
        if path_bass or route_mask == 4:
            return "Bass"
        elif path_rhythm or route_mask == 2:
            return "Rhythm"
        elif path_lead or route_mask == 1:
            return "Lead"

        return "Unknown"

    def _get_tuning(self, attributes: Dict[str, Any]) -> str:
        """Extract and format tuning information.

        Args:
            attributes: Attributes dictionary from manifest

        Returns:
            Tuning name or tuning string
        """
        tuning_data = attributes.get("Tuning", {})

        if not tuning_data:
            return "Unknown"

        # Build tuning string from individual string values
        tuning_parts = []
        for i in range(6):  # Standard 6-string guitar
            string_key = f"string{i}"
            if string_key in tuning_data:
                tuning_parts.append(str(tuning_data[string_key]))

        # Handle bass (4 strings)
        if len(tuning_parts) == 0:
            for i in range(4):
                string_key = f"string{i}"
                if string_key in tuning_data:
                    tuning_parts.append(str(tuning_data[string_key]))

        if not tuning_parts:
            return "Unknown"

        tuning_str = "".join(tuning_parts)

        # Look up in tuning database
        return self.TUNING_DB.get(tuning_str, f"Custom ({tuning_str})")

    def _get_platform(self, psarc_path: Path) -> str:
        """Determine platform from PSARC filename.

        Args:
            psarc_path: Path to PSARC file

        Returns:
            Platform string ("PC", "Mac", or "Unknown")
        """
        filename = psarc_path.name.lower()

        if filename.endswith(self.PC_SUFFIX.lower()):
            return "PC"
        elif filename.endswith(self.MAC_SUFFIX.lower()):
            return "Mac"
        else:
            return "Unknown"

    def export_json(self, output_path: Path) -> None:
        """Export collected metadata to JSON file.

        Args:
            output_path: Path for output JSON file
        """
        # Convert to list and sort by artist, then title
        songs_list = sorted(
            self.songs.values(),
            key=lambda x: (x["artist"].lower(), x["title"].lower())
        )

        output_data = {
            "total_songs": len(songs_list),
            "songs": songs_list
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\nMetadata exported to: {output_path}")
        print(f"Total unique songs: {len(songs_list)}")

    def print_summary(self) -> None:
        """Print summary statistics of the scanned library."""
        total_songs = len(self.songs)
        pc_only = sum(1 for s in self.songs.values() if s["platforms"] == ["PC"])
        mac_only = sum(1 for s in self.songs.values() if s["platforms"] == ["Mac"])
        both = sum(1 for s in self.songs.values() if "PC" in s["platforms"] and "Mac" in s["platforms"])

        # Count arrangement types
        lead_count = 0
        rhythm_count = 0
        bass_count = 0
        vocals_count = 0

        for song in self.songs.values():
            arrangements = song.get("arrangements", [])
            has_lead = any(a["type"] == "Lead" for a in arrangements)
            has_rhythm = any(a["type"] == "Rhythm" for a in arrangements)
            has_bass = any(a["type"] == "Bass" for a in arrangements)
            has_vocals = any(a["type"] == "Vocals" for a in arrangements)

            if has_lead:
                lead_count += 1
            if has_rhythm:
                rhythm_count += 1
            if has_bass:
                bass_count += 1
            if has_vocals:
                vocals_count += 1

        print("\n" + "="*60)
        print("LIBRARY SUMMARY")
        print("="*60)
        print(f"Total unique songs: {total_songs}")
        print(f"PC only:            {pc_only}")
        print(f"Mac only:           {mac_only}")
        print(f"Both platforms:     {both}")
        print("-"*60)
        print("ARRANGEMENTS")
        print(f"Songs with Lead:    {lead_count}")
        print(f"Songs with Rhythm:  {rhythm_count}")
        print(f"Songs with Bass:    {bass_count}")
        print(f"Songs with Vocals:  {vocals_count}")
        print("="*60)

        # Show artists
        artists = set(s["artist"] for s in self.songs.values())
        print(f"\nTotal unique artists: {len(artists)}")


def main():
    """Main entry point for the scanner."""
    if len(sys.argv) < 2:
        print("Usage: python scanner.py <path-to-rocksmith-dlc-folder>")
        print("\nExample:")
        print("  python scanner.py /path/to/rocksmith/dlc")
        sys.exit(1)

    library_path = Path(sys.argv[1])

    if not library_path.exists():
        print(f"Error: Path does not exist: {library_path}")
        sys.exit(1)

    if not library_path.is_dir():
        print(f"Error: Path is not a directory: {library_path}")
        sys.exit(1)

    # Create scanner and process files
    scanner = RocksmithScanner(library_path)
    scanner.scan_directory()

    # Print summary
    scanner.print_summary()

    # Export to JSON
    output_path = library_path / "library.json"
    scanner.export_json(output_path)


if __name__ == "__main__":
    main()
