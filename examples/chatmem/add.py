#!/usr/bin/env python3
"""
Add Resource - CLI tool to add documents to OpenViking database
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.resource_manager import add_resource, create_client


def main():
    parser = argparse.ArgumentParser(
        description="Add documents, PDFs, or URLs to OpenViking database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a PDF file
  uv run add.py ~/Downloads/document.pdf

  # Add a URL
  uv run add.py https://example.com/README.md

  # Add with custom config and data paths
  uv run add.py document.pdf --config ./my.conf --data ./mydata

  # Add a directory
  uv run add.py ~/Documents/research/

  # Enable debug logging
  OV_DEBUG=1 uv run add.py document.pdf

Notes:
  - Supported formats: PDF, Markdown, Text, HTML, and more
  - URLs are automatically downloaded and processed
  - Large files may take several minutes to process
  - The resource becomes searchable after processing completes
        """,
    )

    parser.add_argument(
        "resource", type=str, help="Path to file/directory or URL to add to the database"
    )

    parser.add_argument(
        "--config", type=str, default="./ov.conf", help="Path to config file (default: ./ov.conf)"
    )

    parser.add_argument(
        "--data", type=str, default="./data", help="Path to data directory (default: ./data)"
    )

    args = parser.parse_args()

    # Expand user paths
    resource_path = (
        str(Path(args.resource).expanduser())
        if not args.resource.startswith("http")
        else args.resource
    )

    # Create client and add resource
    try:
        print(f"📋 Loading config from: {args.config}")
        client = create_client(args.config, args.data)

        print("🚀 Initializing OpenViking...")
        print("✓ Initialized\n")

        success = add_resource(client, resource_path)

        client.close()
        print("\n✓ Done")
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
