#!/usr/bin/env python3
"""Find duplicate PSARC files in Rocksmith library."""

import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import simplejson

from rsrtools.files.welder import Welder


class DuplicateFinder:
    """Find duplicate songs in Rocksmith PSARC library."""

    def __init__(self, library_path: Path):
        """Initialize duplicate finder.

        Args:
            library_path: Root directory containing PSARC files
        """
        self.library_path = library_path
        self.songs_by_key: Dict[str, List[Path]] = defaultdict(list)
        self.songs_by_title_artist: Dict[Tuple[str, str], List[Path]] = defaultdict(list)
        self.files_by_hash: Dict[str, List[Path]] = defaultdict(list)
        self.files_by_name: Dict[str, List[Path]] = defaultdict(list)

    def scan_library(self) -> None:
        """Scan library and categorize files."""
        print(f"Scanning directory: {self.library_path}")

        psarc_files = list(self.library_path.glob("**/*.psarc"))

        if not psarc_files:
            print("No PSARC files found!")
            return

        print(f"Found {len(psarc_files)} PSARC files\n")
        print("Analyzing files for duplicates...")

        for i, psarc_file in enumerate(psarc_files, 1):
            if i % 50 == 0:
                print(f"  Processed {i}/{len(psarc_files)} files...")

            # Get metadata
            try:
                song_key, title, artist = self._get_song_info(psarc_file)

                # Track by song key
                if song_key != "Unknown":
                    self.songs_by_key[song_key].append(psarc_file)

                # Track by title + artist
                if title != "Unknown" and artist != "Unknown":
                    self.songs_by_title_artist[(title.lower(), artist.lower())].append(psarc_file)

                # Track by filename
                self.files_by_name[psarc_file.name.lower()].append(psarc_file)

            except Exception as e:
                print(f"Warning: Could not read {psarc_file.name}: {e}")

        print(f"  Completed analyzing {len(psarc_files)} files\n")

    def _get_song_info(self, psarc_path: Path) -> Tuple[str, str, str]:
        """Extract song key, title, and artist from PSARC.

        Args:
            psarc_path: Path to PSARC file

        Returns:
            Tuple of (song_key, title, artist)
        """
        with Welder(psarc_path, 'r') as psarc:
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
                        title = attributes.get("SongName", attributes.get("FullName", "Unknown"))
                        artist = attributes.get("ArtistName", "Unknown")

                        return song_key, title, artist

        return "Unknown", "Unknown", "Unknown"

    def find_exact_duplicates(self) -> Dict[str, List[Path]]:
        """Find files that are exact duplicates by song key.

        Returns:
            Dictionary of song_key -> list of duplicate files
        """
        duplicates = {}

        for song_key, files in self.songs_by_key.items():
            if len(files) > 1:
                # Group by platform to separate legitimate PC/Mac pairs from true duplicates
                pc_files = [f for f in files if f.name.lower().endswith('_p.psarc')]
                mac_files = [f for f in files if f.name.lower().endswith('_m.psarc')]
                other_files = [f for f in files if f not in pc_files and f not in mac_files]

                # True duplicates are when we have multiple of the same platform
                has_duplicates = len(pc_files) > 1 or len(mac_files) > 1 or len(other_files) > 1

                if has_duplicates:
                    duplicates[song_key] = files

        return duplicates

    def find_metadata_duplicates(self) -> Dict[Tuple[str, str], List[Path]]:
        """Find songs with same title and artist but different song keys.

        Returns:
            Dictionary of (title, artist) -> list of files
        """
        duplicates = {}

        for (title, artist), files in self.songs_by_title_artist.items():
            if len(files) > 1:
                # Check if they have different song keys (indicating versions)
                song_keys = set()
                for f in files:
                    song_key, _, _ = self._get_song_info(f)
                    song_keys.add(song_key)

                if len(song_keys) > 1:
                    duplicates[(title, artist)] = files

        return duplicates

    def find_filename_duplicates(self) -> Dict[str, List[Path]]:
        """Find files with identical filenames in different locations.

        Returns:
            Dictionary of filename -> list of files
        """
        duplicates = {}

        for filename, files in self.files_by_name.items():
            if len(files) > 1:
                duplicates[filename] = files

        return duplicates

    def report_duplicates(self) -> None:
        """Generate and display duplicate report."""
        print("="*70)
        print("DUPLICATE ANALYSIS REPORT")
        print("="*70)

        # Exact duplicates (same song key)
        exact_dupes = self.find_exact_duplicates()
        if exact_dupes:
            print(f"\n🔴 EXACT DUPLICATES: {len(exact_dupes)} songs with duplicate files")
            print("-"*70)

            for song_key, files in sorted(exact_dupes.items()):
                # Get song info from first file
                _, title, artist = self._get_song_info(files[0])

                print(f"\n{artist} - {title} (SongKey: {song_key})")
                print(f"  {len(files)} copies found:")

                for f in files:
                    rel_path = f.relative_to(self.library_path)
                    size_mb = f.stat().st_size / 1024 / 1024
                    print(f"    📁 {rel_path} ({size_mb:.1f} MB)")

        else:
            print("\n✅ No exact duplicates found (by song metadata)")

        # Filename duplicates
        filename_dupes = self.find_filename_duplicates()
        if filename_dupes:
            print(f"\n🟡 FILENAME DUPLICATES: {len(filename_dupes)} filenames in multiple locations")
            print("-"*70)

            for filename, files in sorted(filename_dupes.items()):
                print(f"\n{filename}")
                print(f"  Found in {len(files)} locations:")

                for f in files:
                    rel_path = f.relative_to(self.library_path)
                    print(f"    📁 {rel_path}")

        else:
            print("\n✅ No filename duplicates found")

        # Metadata duplicates (different versions)
        metadata_dupes = self.find_metadata_duplicates()
        if metadata_dupes:
            print(f"\n🟠 POSSIBLE VERSIONS: {len(metadata_dupes)} songs with multiple versions")
            print("-"*70)
            print("(Same title/artist but different song keys - likely different versions)")

            for (title, artist), files in sorted(metadata_dupes.items()):
                print(f"\n{artist.title()} - {title.title()}")
                print(f"  {len(files)} versions found:")

                for f in files:
                    song_key, _, _ = self._get_song_info(f)
                    rel_path = f.relative_to(self.library_path)
                    print(f"    📁 {rel_path}")
                    print(f"       SongKey: {song_key}")

        else:
            print("\n✅ No version duplicates found")

        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)

        total_duplicate_files = sum(len(files) - 1 for files in exact_dupes.values())
        total_filename_dupes = sum(len(files) - 1 for files in filename_dupes.values())

        print(f"Total exact duplicate files: {total_duplicate_files}")
        print(f"Total filename duplicates:   {total_filename_dupes}")
        print(f"Multiple versions found:     {len(metadata_dupes)}")

        if total_duplicate_files > 0:
            print(f"\n💡 You can safely delete {total_duplicate_files} exact duplicate files")
        else:
            print("\n✅ Your library appears to be clean!")

        print("="*70)

    def generate_cleanup_script(self, output_file: Path) -> None:
        """Generate a bash script to remove duplicates.

        Args:
            output_file: Path for output bash script
        """
        exact_dupes = self.find_exact_duplicates()

        if not exact_dupes:
            print("No duplicates to clean up!")
            return

        with open(output_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated duplicate cleanup script\n")
            f.write("# Review this script before running!\n\n")
            f.write("set -e\n\n")

            for song_key, files in sorted(exact_dupes.items()):
                _, title, artist = self._get_song_info(files[0])

                f.write(f"\n# {artist} - {title}\n")

                # Separate by platform
                pc_files = [file for file in files if file.name.lower().endswith('_p.psarc')]
                mac_files = [file for file in files if file.name.lower().endswith('_m.psarc')]
                other_files = [file for file in files if file not in pc_files and file not in mac_files]

                # For each platform group, keep the best copy and delete duplicates
                for platform_files in [pc_files, mac_files, other_files]:
                    if not platform_files:
                        continue

                    if len(platform_files) == 1:
                        # Only one file for this platform - keep it
                        keep_file = platform_files[0]
                        f.write(f"# Keeping: {keep_file.relative_to(self.library_path)}\n")
                    else:
                        # Multiple files for same platform - keep best, delete rest
                        files_sorted = sorted(platform_files, key=lambda x: (len(x.parts), -x.stat().st_mtime))
                        keep_file = files_sorted[0]
                        f.write(f"# Keeping: {keep_file.relative_to(self.library_path)}\n")

                        # Delete the duplicates
                        for dup_file in files_sorted[1:]:
                            rel_path = dup_file.relative_to(self.library_path)
                            f.write(f'echo "Deleting: {rel_path}"\n')
                            f.write(f'# rm "{dup_file}"\n')

        # Make executable
        output_file.chmod(0o755)

        print(f"\n✅ Cleanup script generated: {output_file}")
        print("⚠️  Review the script before running (delete lines are commented out)")
        print("    Uncomment the 'rm' lines when ready to delete")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find duplicate PSARC files in Rocksmith library"
    )
    parser.add_argument(
        "library_path",
        type=Path,
        help="Path to Rocksmith library directory"
    )
    parser.add_argument(
        "--generate-cleanup",
        type=Path,
        metavar="SCRIPT_PATH",
        help="Generate bash script to remove duplicates"
    )

    args = parser.parse_args()

    library_path = args.library_path

    if not library_path.exists():
        print(f"Error: Path does not exist: {library_path}")
        sys.exit(1)

    if not library_path.is_dir():
        print(f"Error: Not a directory: {library_path}")
        sys.exit(1)

    # Create finder and scan
    finder = DuplicateFinder(library_path)
    finder.scan_library()

    # Generate report
    finder.report_duplicates()

    # Generate cleanup script if requested
    if args.generate_cleanup:
        finder.generate_cleanup_script(args.generate_cleanup)


if __name__ == "__main__":
    main()
