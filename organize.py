#!/usr/bin/env python3
"""Rocksmith PSARC library organizer - organize files by artist."""

import sys
import shutil
from pathlib import Path
from typing import Dict, List, Any, Set
import simplejson

from rsrtools.files.welder import Welder


class RocksmithOrganizer:
    """Organizer for moving PSARC files into artist directories."""

    MAC_SUFFIX = "_m.psarc"
    PC_SUFFIX = "_p.psarc"

    def __init__(self, library_path: Path, dry_run: bool = False):
        """Initialize organizer with library path.

        Args:
            library_path: Root directory containing PSARC files
            dry_run: If True, only preview changes without moving files
        """
        self.library_path = library_path
        self.dry_run = dry_run
        self.file_metadata: Dict[Path, Dict[str, Any]] = {}
        self.moves: List[Dict[str, Path]] = []

    def scan_files(self) -> None:
        """Scan all PSARC files and extract artist metadata."""
        print(f"Scanning directory: {self.library_path}")

        # Find all PSARC files
        psarc_files = list(self.library_path.glob("**/*.psarc"))

        if not psarc_files:
            print("No PSARC files found!")
            return

        print(f"Found {len(psarc_files)} PSARC files\n")

        for psarc_file in psarc_files:
            # Skip files already in artist subdirectories (one level deep)
            relative_path = psarc_file.relative_to(self.library_path)
            if len(relative_path.parts) > 1:
                # File is already in a subdirectory
                continue

            artist = self._get_artist_from_psarc(psarc_file)
            if artist and artist != "Unknown":
                self.file_metadata[psarc_file] = {
                    "artist": artist,
                    "original_path": psarc_file
                }

        print(f"Found {len(self.file_metadata)} files to organize\n")

    def _get_artist_from_psarc(self, psarc_path: Path) -> str:
        """Extract artist name from PSARC file.

        Args:
            psarc_path: Path to the PSARC file

        Returns:
            Artist name or "Unknown"
        """
        try:
            with Welder(psarc_path, 'r') as psarc:
                # Look for first manifest file
                for i in psarc:
                    file_name = psarc.arc_name(i)

                    if file_name.startswith("manifests/songs") and file_name.endswith(".json"):
                        data = psarc.arc_data(i)
                        manifest = simplejson.loads(data.decode())

                        entries = manifest.get("Entries", {})
                        if entries:
                            first_entry = next(iter(entries.values()))
                            attributes = first_entry.get("Attributes", {})
                            artist = attributes.get("ArtistName", "Unknown")
                            return self._sanitize_dirname(artist)

        except Exception as e:
            print(f"Warning: Could not read artist from {psarc_path.name}: {e}")

        return "Unknown"

    def _sanitize_dirname(self, name: str) -> str:
        """Sanitize artist name for use as directory name.

        Args:
            name: Artist name

        Returns:
            Sanitized directory name
        """
        # Replace characters that are invalid in directory names
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = name

        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')

        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')

        return sanitized if sanitized else "Unknown"

    def plan_organization(self) -> None:
        """Plan the file moves and create the move list."""
        for psarc_file, metadata in self.file_metadata.items():
            artist = metadata["artist"]
            artist_dir = self.library_path / artist

            # Determine new path
            new_path = artist_dir / psarc_file.name

            # Check if file would be moved (not already in the right place)
            if psarc_file.parent != artist_dir:
                self.moves.append({
                    "source": psarc_file,
                    "dest": new_path,
                    "artist": artist,
                    "needs_mkdir": not artist_dir.exists()
                })

    def preview_changes(self) -> None:
        """Display a preview of planned changes."""
        if not self.moves:
            print("No files need to be organized (all files are already in artist directories).")
            return

        # Group by artist
        by_artist: Dict[str, List[Dict[str, Path]]] = {}
        for move in self.moves:
            artist = move["artist"]
            if artist not in by_artist:
                by_artist[artist] = []
            by_artist[artist].append(move)

        print("="*70)
        print("PLANNED ORGANIZATION")
        print("="*70)

        total_dirs = sum(1 for artist in by_artist.keys()
                        if any(m["needs_mkdir"] for m in by_artist[artist]))

        print(f"\nWill create {total_dirs} new artist directories")
        print(f"Will move {len(self.moves)} files\n")

        for artist in sorted(by_artist.keys()):
            moves = by_artist[artist]
            print(f"\n{artist}/ ({len(moves)} files)")
            print("-" * 70)

            for move in moves[:5]:  # Show first 5 files per artist
                print(f"  {move['source'].name}")

            if len(moves) > 5:
                print(f"  ... and {len(moves) - 5} more files")

        print("\n" + "="*70)

    def execute_organization(self) -> None:
        """Execute the planned file moves."""
        if not self.moves:
            print("No files to organize.")
            return

        if self.dry_run:
            print("\n*** DRY RUN MODE - No files will be moved ***\n")
            self.preview_changes()
            return

        print(f"\nOrganizing {len(self.moves)} files...")

        # Create artist directories
        dirs_created: Set[Path] = set()
        for move in self.moves:
            artist_dir = move["dest"].parent
            if move["needs_mkdir"] and artist_dir not in dirs_created:
                artist_dir.mkdir(exist_ok=True)
                dirs_created.add(artist_dir)
                print(f"Created directory: {artist_dir.name}/")

        print()

        # Move files
        success_count = 0
        error_count = 0

        for move in self.moves:
            try:
                source = move["source"]
                dest = move["dest"]

                # Check if destination already exists
                if dest.exists():
                    print(f"Warning: {dest.name} already exists in {move['artist']}/, skipping")
                    error_count += 1
                    continue

                # Move the file
                shutil.move(str(source), str(dest))
                success_count += 1

                if success_count % 10 == 0:  # Progress indicator
                    print(f"Moved {success_count}/{len(self.moves)} files...")

            except Exception as e:
                print(f"Error moving {source.name}: {e}")
                error_count += 1

        print(f"\n{'='*70}")
        print("ORGANIZATION COMPLETE")
        print(f"{'='*70}")
        print(f"Successfully moved: {success_count} files")
        if error_count > 0:
            print(f"Errors/Skipped:     {error_count} files")
        print(f"{'='*70}")


def main():
    """Main entry point for the organizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organize Rocksmith PSARC files into artist directories"
    )
    parser.add_argument(
        "library_path",
        type=Path,
        help="Path to Rocksmith DLC folder"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without moving files"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show detailed preview of planned changes"
    )

    args = parser.parse_args()

    library_path = args.library_path

    if not library_path.exists():
        print(f"Error: Path does not exist: {library_path}")
        sys.exit(1)

    if not library_path.is_dir():
        print(f"Error: Path is not a directory: {library_path}")
        sys.exit(1)

    # Create organizer
    organizer = RocksmithOrganizer(library_path, dry_run=args.dry_run)

    # Scan files
    organizer.scan_files()

    # Plan organization
    organizer.plan_organization()

    # Preview if requested
    if args.preview or args.dry_run:
        organizer.preview_changes()

    # Ask for confirmation if not in dry-run mode
    if not args.dry_run and not args.preview:
        organizer.preview_changes()
        print("\nProceed with organization? (yes/no): ", end="")
        response = input().strip().lower()

        if response not in ["yes", "y"]:
            print("Organization cancelled.")
            sys.exit(0)

    # Execute
    if not args.preview:
        organizer.execute_organization()


if __name__ == "__main__":
    main()
