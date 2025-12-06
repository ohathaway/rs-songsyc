#!/usr/bin/env python3
"""Convert Rocksmith PSARC files between PC and Mac platforms."""

import sys
import shutil
from pathlib import Path
from typing import Dict, List

from rsrtools.files.welder import Welder


# Platform-specific paths and encryption keys (from rsrtools)
MAC_PATH = "songs/bin/macos/"
MAC_KEY = bytes.fromhex(
    "9821330E34B91F70D0A48CBD625993126970CEA09192C0E6CDA676CC9838289D"
)
WIN_PATH = "songs/bin/generic/"
WIN_KEY = bytes.fromhex(
    "CB648DF3D12A16BF71701414E69619EC171CCA5D2A142E3E59DE7ADDA18A3A30"
)


class PlatformConverter:
    """Convert PSARC files between PC and Mac platforms."""

    def __init__(self, source_psarc: Path, output_dir: Path, target_platform: str, dry_run: bool = False, skip_confirm: bool = False):
        """Initialize converter.

        Args:
            source_psarc: Path to source PSARC file
            output_dir: Directory for output file
            target_platform: Target platform ('pc' or 'mac')
            dry_run: If True, only preview without creating files
            skip_confirm: If True, skip confirmation prompts
        """
        self.source_psarc = source_psarc
        self.output_dir = output_dir
        self.target_platform = target_platform.lower()
        self.dry_run = dry_run
        self.skip_confirm = skip_confirm

        # Detect source platform
        source_name = source_psarc.name.lower()
        if '_p.psarc' in source_name:
            self.source_platform = 'pc'
        elif '_m.psarc' in source_name:
            self.source_platform = 'mac'
        else:
            # Try to detect from content
            self.source_platform = None

    def detect_source_platform(self) -> str:
        """Detect source platform by examining archive contents.

        Returns:
            'pc' or 'mac'
        """
        if self.source_platform:
            return self.source_platform

        # Check for platform-specific paths in the archive
        with Welder(self.source_psarc, 'r') as psarc:
            for i in psarc:
                file_name = psarc.arc_name(i)
                if WIN_PATH in file_name:
                    self.source_platform = 'pc'
                    return 'pc'
                elif MAC_PATH in file_name:
                    self.source_platform = 'mac'
                    return 'mac'

        # Default to PC if can't determine
        self.source_platform = 'pc'
        return 'pc'

    def preview_conversion(self) -> None:
        """Show conversion preview."""
        source_platform = self.detect_source_platform()

        print("\n" + "="*70)
        print("PLATFORM CONVERSION PREVIEW")
        print("="*70)
        print(f"Source file:      {self.source_psarc.name}")
        print(f"Source platform:  {source_platform.upper()}")
        print(f"Target platform:  {self.target_platform.upper()}")
        print(f"Output directory: {self.output_dir}")

        output_name = self._generate_output_name()
        print(f"Output file:      {output_name}")

        print("\nConversion will:")
        if source_platform == self.target_platform:
            print("  ⚠️  Source and target platforms are the same!")
            print("      File will be copied with no conversion.")
        else:
            print(f"  • Extract all files from {source_platform.upper()} archive")
            print(f"  • Re-encrypt .sng files with {self.target_platform.upper()} key")
            print(f"  • Update file paths for {self.target_platform.upper()}")
            print(f"  • Repackage as {self.target_platform.upper()} PSARC")

        print("="*70)

    def convert(self) -> None:
        """Perform platform conversion."""
        if self.dry_run:
            print("\n*** DRY RUN MODE - No files will be created ***")
            self.preview_conversion()
            return

        source_platform = self.detect_source_platform()

        if source_platform == self.target_platform and not self.skip_confirm:
            print(f"\n⚠️  Warning: Source is already {self.target_platform.upper()} format!")
            print("Do you want to continue anyway? (yes/no): ", end="")
            response = input().strip().lower()
            if response not in ["yes", "y"]:
                print("Conversion cancelled.")
                return
        elif source_platform == self.target_platform and self.skip_confirm:
            # Skip silently when using --yes flag
            print(f"⚠️  Warning: Source is already {self.target_platform.upper()} format! Skipping.")
            return

        print(f"\nConverting {source_platform.upper()} → {self.target_platform.upper()}")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary extraction directory
        temp_dir = self.output_dir / "_temp_convert"
        temp_dir.mkdir(exist_ok=True)

        try:
            print("Extracting source archive...")

            # Extract and convert files
            # Use sng_crypto=False to get raw encrypted .sng data
            # We'll manually decrypt/re-encrypt with the correct platform keys
            with Welder(self.source_psarc, 'r', sng_crypto=False) as psarc:
                for i in psarc:
                    file_name = psarc.arc_name(i)
                    file_data = psarc.arc_data(i)

                    # Convert path if needed
                    converted_name = self._convert_path(file_name, source_platform)

                    # Re-encrypt .sng files if needed
                    if file_name.endswith('.sng') and source_platform != self.target_platform:
                        # Decrypt with source platform key
                        source_key = WIN_KEY if source_platform == 'pc' else MAC_KEY
                        target_key = WIN_KEY if self.target_platform == 'pc' else MAC_KEY

                        decrypted = Welder.decrypt_sng(file_data, source_key)
                        file_data = Welder.encrypt_sng(decrypted, target_key)

                    # Write to temp directory
                    output_path = temp_dir / converted_name
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(file_data)

            print("Creating converted PSARC...")

            # Create new PSARC from converted files
            output_name = self._generate_output_name()
            output_psarc = self.output_dir / output_name

            # Use Welder to pack
            with Welder(temp_dir, 'w', sng_crypto=True) as new_psarc:
                pass  # Welder automatically packs on creation

            # Rename if needed
            created_file = Path(str(temp_dir) + '.psarc')
            if created_file.exists() and created_file != output_psarc:
                shutil.move(created_file, output_psarc)

            print(f"\n✓ Conversion complete!")
            print(f"  Output: {output_psarc}")

        except Exception as e:
            print(f"\n✗ Error during conversion: {e}")
            raise

        finally:
            # Clean up temp directory
            if temp_dir.exists():
                print("Cleaning up temporary files...")
                shutil.rmtree(temp_dir)

    def _convert_path(self, file_path: str, source_platform: str) -> str:
        """Convert file path for target platform.

        Args:
            file_path: Original file path
            source_platform: Source platform ('pc' or 'mac')

        Returns:
            Converted file path
        """
        # Only need to convert paths in songs/bin/
        if source_platform == 'pc' and self.target_platform == 'mac':
            return file_path.replace(WIN_PATH, MAC_PATH)
        elif source_platform == 'mac' and self.target_platform == 'pc':
            return file_path.replace(MAC_PATH, WIN_PATH)

        return file_path

    def _generate_output_name(self) -> str:
        """Generate output filename.

        Returns:
            Output filename with appropriate platform suffix
        """
        source_name = self.source_psarc.stem

        # Remove existing platform suffix
        if source_name.endswith('_p'):
            source_name = source_name[:-2]
        elif source_name.endswith('_m'):
            source_name = source_name[:-2]

        # Add target platform suffix
        if self.target_platform == 'pc':
            return f"{source_name}_p.psarc"
        else:
            return f"{source_name}_m.psarc"


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert Rocksmith PSARC files between PC and Mac platforms"
    )
    parser.add_argument(
        "source_psarc",
        type=Path,
        help="Path to source PSARC file"
    )
    parser.add_argument(
        "target_platform",
        choices=['pc', 'mac', 'PC', 'Mac'],
        help="Target platform (pc or mac)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output directory (default: same directory as source)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview conversion without creating files"
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts (useful for batch processing)"
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
        output_dir = source_psarc.parent

    # Create converter and run
    converter = PlatformConverter(
        source_psarc,
        output_dir,
        args.target_platform,
        dry_run=args.dry_run,
        skip_confirm=args.yes
    )

    # Show preview (skip if --yes flag is used)
    if not args.yes:
        converter.preview_conversion()

    if not args.dry_run and not args.yes:
        print("\nProceed with conversion? (yes/no): ", end="")
        response = input().strip().lower()

        if response not in ["yes", "y"]:
            print("Conversion cancelled.")
            sys.exit(0)

    # Execute conversion
    converter.convert()


if __name__ == "__main__":
    main()
