"""
Command-line interface for LTLf specification merger.
"""
import argparse
import sys
import os
from typing import List, Tuple

from ltlf_merger.merger import LTLfSpecMerger


def parse_input_pairs(input_str: str) -> List[Tuple[str, str]]:
    """Parse input string into pairs of ltlf and part files."""
    pairs = []
    for pair in input_str.split():
        try:
            ltlf_file, part_file = pair.split(',')
            if not ltlf_file.endswith('.ltlf') or not part_file.endswith('.part'):
                raise ValueError(f"Invalid file pair: {pair}")
            pairs.append((ltlf_file, part_file))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            print("Input format should be: spec1.ltlf,spec1.part spec2.ltlf,spec2.part",
                  file=sys.stderr)
            sys.exit(1)
    return pairs


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='Merge LTLf specifications.')
    parser.add_argument('--input', required=True,
                       help='Space-separated pairs of .ltlf and .part files '
                            '(e.g., "spec1.ltlf,spec1.part spec2.ltlf,spec2.part")')
    parser.add_argument('--share-ratio', type=float, default=0.5,
                       help='Share ratio between 0 and 1 (default: 0.5)')
    parser.add_argument('--output-folder', type=str, default="drafts",
                        help='output folder for merged .ltlf and .part files '
                            '(default: "drafts")')

    args = parser.parse_args()

    try:
        # Parse and validate share ratio
        if not 0 <= args.share_ratio <= 1:
            raise ValueError("Share ratio must be between 0 and 1")

        # Parse input file pairs
        spec_pairs = parse_input_pairs(args.input)
        if len(spec_pairs) < 2:
            raise ValueError("At least two specifications are required for merging")

        # Create merger and process specifications
        merger = LTLfSpecMerger(share_ratio=args.share_ratio)
        merged_ltlf, merged_part = merger.merge_specs(spec_pairs)

        # Write output to files
        merged_ltlf_path = os.path.join(args.output_folder, 'merged.ltlf')
        with open(merged_ltlf_path, 'w') as f:
            f.write(merged_ltlf)
        merged_part_path = os.path.join(args.output_folder, 'merged.part')
        with open(merged_part_path, 'w') as f:
            f.write(merged_part)

        print("Successfully merged specifications:")
        print("- Merged LTLf formula written to: merged.ltlf")
        print("- Merged variable definitions written to: merged.part")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
