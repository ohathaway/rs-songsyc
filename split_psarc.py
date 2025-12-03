#!/usr/bin/env python3
"""Split bundled PSARC files into individual song PSARC files."""

import sys
import shutil
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import simplejson

from rsrtools.files.welder import Welder


class PSARCSplitter:
    """Split multi-song PSARC files into individual song files."""

    def __init__(self, source_psarc: Path, output_dir: Path, dry_run: bool = False):
        """Initialize splitter.

        Args:
            source_psarc: Path to the bundled PSARC file
            output_dir: Directory to write individual song PSARC files
            dry_run: If True, only preview without creating files
        """
        self.source_psarc = source_psarc
        self.output_dir = output_dir
        self.dry_run = dry_run
        self.songs: Dict[str, Dict] = {}  # song_key -> song info

    def analyze_psarc(self) -> None:
        """Analyze the PSARC to identify individual songs and their files."""
        print(f"Analyzing: {self.source_psarc.name}")

        with Welder(self.source_psarc, 'r') as psarc:
            # First pass: find all manifest files and identify songs
            manifests = {}
            for i in psarc:
                file_name = psarc.arc_name(i)

                if file_name.startswith("manifests/songs") and file_name.endswith(".json"):
                    data = psarc.arc_data(i)
                    manifest = simplejson.loads(data.decode())
                    entries = manifest.get("Entries", {})

                    if entries:
                        first_entry = next(iter(entries.values()))
                        attributes = first_entry.get("Attributes", {})
                        song_key = attributes.get("SongKey", "Unknown")

                        if song_key not in self.songs:
                            title = attributes.get("SongName", "Unknown")
                            artist = attributes.get("ArtistName", "Unknown")

                            self.songs[song_key] = {
                                "title": title,
                                "artist": artist,
                                "song_key": song_key,
                                "files": []
                            }

                        self.songs[song_key]["files"].append(file_name)
                        manifests[file_name] = song_key

            # Second pass: associate all files with songs
            file_to_song = {}

            with Welder(self.source_psarc, 'r') as psarc:
                for i in psarc:
                    file_name = psarc.arc_name(i)

                    # Try to match file to a song based on naming patterns
                    # Files typically follow patterns like:
                    # - manifests/songs_dlc_<songname>/
                    # - songs/bin/.../  (audio/chart files)

                    # Extract potential song identifier from path
                    parts = file_name.split('/')

                    # Check manifests first
                    if file_name in manifests:
                        song_key = manifests[file_name]
                        file_to_song[file_name] = song_key
                        continue

                    # For other files, try to match by path patterns
                    if len(parts) >= 2:
                        # Look for songs_dlc_<name> or similar patterns
                        for part in parts:
                            if part.startswith('songs_dlc_') or part.startswith('song_'):
                                # Try to match this to a song_key
                                for song_key, song_info in self.songs.items():
                                    # Simple heuristic: if song_key appears in the path
                                    if song_key.lower() in file_name.lower():
                                        file_to_song[file_name] = song_key
                                        if file_name not in song_info["files"]:
                                            song_info["files"].append(file_name)
                                        break
                                if file_name in file_to_song:
                                    break

        print(f"\nFound {len(self.songs)} songs in archive:")
        for song_key, song_info in self.songs.items():
            print(f"  - {song_info['artist']} - {song_info['title']} ({len(song_info['files'])} files)")

    def preview_split(self) -> None:
        """Show what files would be created."""
        print("\n" + "="*70)
        print("SPLIT PREVIEW")
        print("="*70)

        for song_key, song_info in self.songs.items():
            output_name = self._generate_filename(song_info)
            print(f"\n{output_name}")
            print(f"  Artist: {song_info['artist']}")
            print(f"  Title: {song_info['title']}")
            print(f"  Files to include: {len(song_info['files'])}")

            if len(song_info['files']) <= 10:
                for f in song_info['files']:
                    print(f"    - {f}")
            else:
                for f in song_info['files'][:5]:
                    print(f"    - {f}")
                print(f"    ... and {len(song_info['files']) - 5} more files")

        print("\n" + "="*70)
        print(f"Total: {len(self.songs)} PSARC files would be created")
        print(f"Output directory: {self.output_dir}")
        print("="*70)

    def split_songs(self) -> None:
        """Extract and create individual PSARC files for each song."""
        if self.dry_run:
            print("\n*** DRY RUN MODE - No files will be created ***")
            self.preview_split()
            return

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nExtracting songs to: {self.output_dir}")

        # Create a temporary extraction directory
        temp_dir = self.output_dir / "_temp_extract"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Extract the entire archive first
            print(f"Extracting source archive...")
            with Welder(self.source_psarc, 'r') as psarc:
                # Extract all files
                for i in psarc:
                    file_name = psarc.arc_name(i)
                    file_data = psarc.arc_data(i)

                    output_path = temp_dir / file_name
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(file_data)

            # Now create individual PSARC files for each song
            for song_key, song_info in self.songs.items():
                output_name = self._generate_filename(song_info)
                print(f"\nCreating: {output_name}")

                # Create a directory for this song's files
                song_dir = temp_dir.parent / f"_temp_{song_key}"
                song_dir.mkdir(exist_ok=True)

                # Copy only this song's files to the song directory
                for file_path in song_info['files']:
                    src = temp_dir / file_path
                    if src.exists():
                        dst = song_dir / file_path
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)

                # Create PSARC from the song directory
                try:
                    output_psarc = self.output_dir / output_name

                    # Use Welder to create the PSARC
                    # Note: Welder expects the directory name without .psarc extension
                    # and will create <dirname>.psarc
                    psarc_base = self.output_dir / output_name.replace('.psarc', '')

                    with Welder(song_dir, 'w') as new_psarc:
                        pass  # Welder automatically packs on creation

                    # Rename to correct name if needed
                    created_file = Path(str(song_dir) + '.psarc')
                    if created_file.exists() and created_file != output_psarc:
                        shutil.move(created_file, output_psarc)

                    print(f"  ✓ Created {output_name} ({len(song_info['files'])} files)")

                except Exception as e:
                    print(f"  ✗ Error creating {output_name}: {e}")

                finally:
                    # Clean up song temp directory
                    if song_dir.exists():
                        shutil.rmtree(song_dir)

        finally:
            # Clean up temp extraction directory
            if temp_dir.exists():
                print("\nCleaning up temporary files...")
                shutil.rmtree(temp_dir)

        print("\n" + "="*70)
        print("SPLIT COMPLETE")
        print("="*70)

    def _generate_filename(self, song_info: Dict) -> str:
        """Generate output filename for a song.

        Args:
            song_info: Song information dictionary

        Returns:
            Sanitized filename for the PSARC
        """
        artist = self._sanitize_filename(song_info['artist'])
        title = self._sanitize_filename(song_info['title'])

        # Detect platform from source filename
        source_name = self.source_psarc.name.lower()
        if '_p.psarc' in source_name:
            suffix = '_p.psarc'
        elif '_m.psarc' in source_name:
            suffix = '_m.psarc'
        else:
            suffix = '.psarc'

        return f"{artist}_{title}_v1{suffix}"

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use in filename.

        Args:
            name: String to sanitize

        Returns:
            Sanitized string
        """
        # Replace invalid characters
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', ' ']
        sanitized = name

        for char in invalid_chars:
            sanitized = sanitized.replace(char, '-')

        # Remove leading/trailing dashes and dots
        sanitized = sanitized.strip('.-')

        return sanitized if sanitized else "Unknown"


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Split bundled PSARC files into individual song files"
    )
    parser.add_argument(
        "source_psarc",
        type=Path,
        help="Path to bundled PSARC file to split"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output directory for individual song files (default: same directory as source with '_split' suffix)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be created without actually creating files"
    )

    args = parser.parse_args()

    source_psarc = args.source_psarc

    if not source_psarc.exists():
        print(f"Error: File does not exist: {source_psarc}")
        sys.exit(1)

    if not source_psarc.is_file():
        print(f"Error: Not a file: {source_psarc}")
        sys.exit(1)

    # Determine output directory
    if args.output:
        output_dir = args.output
    else:
        output_dir = source_psarc.parent / f"{source_psarc.stem}_split"

    # Create splitter and run
    splitter = PSARCSplitter(source_psarc, output_dir, dry_run=args.dry_run)

    # Analyze the archive
    splitter.analyze_psarc()

    if not splitter.songs:
        print("\nNo songs found in archive!")
        sys.exit(1)

    # Ask for confirmation unless in dry-run mode
    if not args.dry_run:
        splitter.preview_split()
        print("\nProceed with split? (yes/no): ", end="")
        response = input().strip().lower()

        if response not in ["yes", "y"]:
            print("Split cancelled.")
            sys.exit(0)

    # Execute split
    splitter.split_songs()


if __name__ == "__main__":
    main()
