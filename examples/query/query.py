#!/usr/bin/env python3
"""
Query - CLI tool to search and generate answers using OpenViking + LLM
"""
import boring_logging_config  # Configure logging (set OV_DEBUG=1 for debug mode)
import argparse
import json
import sys
import os
from pathlib import Path
from recipe import Recipe


def query(
    question: str,
    config_path: str = "./ov.conf",
    data_path: str = "./data",
    top_k: int = 5,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    verbose: bool = False
):
    """
    Query the database and generate an answer using LLM

    Args:
        question: The question to ask
        config_path: Path to config file
        data_path: Path to data directory
        top_k: Number of search results to use as context
        temperature: LLM temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate
        verbose: Show detailed information
    """
    print("=" * 80)
    print("  🚀 OpenViking RAG Query")
    print("=" * 80 + "\n")

    if verbose:
        print(f"📋 Config: {config_path}")
        print(f"📂 Data: {data_path}")
        print(f"🔍 Top-K: {top_k}")
        print(f"🌡️  Temperature: {temperature}")
        print(f"📝 Max tokens: {max_tokens}\n")

    # Initialize pipeline
    try:
        pipeline = Recipe(config_path=config_path, data_path=data_path)
    except Exception as e:
        print(f"❌ Error initializing pipeline: {e}")
        return False

    try:
        # Display question
        print(f"❓ Question:")
        print(f"   {question}\n")
        print("=" * 80 + "\n")

        # Query
        result = pipeline.query(
            user_query=question,
            search_top_k=top_k,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Display answer
        print("🤖 ANSWER")
        print("=" * 80)
        print(result['answer'])
        print("=" * 80 + "\n")

        # Show sources
        if result['context']:
            print(f"📚 Sources ({len(result['context'])} documents)")
            print("-" * 80)
            for i, ctx in enumerate(result['context'], 1):
                uri_parts = ctx['uri'].split('/')
                filename = uri_parts[-1] if uri_parts else ctx['uri']
                print(f"{i}. {filename}")
                print(f"   Relevance: {ctx['score']:.4f}")

                if verbose:
                    print(f"   URI: {ctx['uri']}")
                    print(f"   Preview: {ctx['content'][:120]}...")

                print()
        else:
            print("⚠️  No relevant sources found\n")

        return True

    except Exception as e:
        print(f"\n❌ Error during query: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        pipeline.close()


def main():
    parser = argparse.ArgumentParser(
        description="Search database and generate answers using RAG (Retrieval-Augmented Generation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic query
  uv run query.py "What is prompt engineering?"

  # Query with more context
  uv run query.py "Explain chain of thought prompting" --top-k 10

  # Adjust creativity (temperature)
  uv run query.py "Give me creative prompt ideas" --temperature 0.9

  # Get detailed output
  uv run query.py "What are the best practices?" --verbose

  # Use custom config and data
  uv run query.py "Question?" --config ./my.conf --data ./mydata

  # Enable debug logging
  OV_DEBUG=1 uv run query.py "Question?"

Temperature Guide:
  0.0-0.3  → Deterministic, focused, consistent (good for facts)
  0.4-0.7  → Balanced creativity and accuracy (default: 0.7)
  0.8-1.0  → Creative, varied, exploratory (good for brainstorming)

Top-K Guide:
  3-5   → Quick, focused answers (default: 5)
  5-10  → More comprehensive context
  10+   → Maximum context (may include less relevant info)
        """
    )

    parser.add_argument(
        'question',
        type=str,
        help='Your question to ask the LLM'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='./ov.conf',
        help='Path to config file (default: ./ov.conf)'
    )

    parser.add_argument(
        '--data',
        type=str,
        default='./data',
        help='Path to data directory (default: ./data)'
    )

    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of search results to use as context (default: 5)'
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='LLM temperature 0.0-1.0 (default: 0.7)'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=2048,
        help='Maximum tokens to generate (default: 2048)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )

    args = parser.parse_args()

    # Validate temperature
    if not 0.0 <= args.temperature <= 1.0:
        print("❌ Error: Temperature must be between 0.0 and 1.0")
        sys.exit(1)

    # Validate top-k
    if args.top_k < 1:
        print("❌ Error: top-k must be at least 1")
        sys.exit(1)

    # Run query
    success = query(
        question=args.question,
        config_path=args.config,
        data_path=args.data,
        top_k=args.top_k,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        verbose=args.verbose
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
