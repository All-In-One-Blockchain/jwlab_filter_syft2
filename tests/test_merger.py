"""
Tests for LTLf specification merger core functionality.
"""
import os
import pytest
from ltlf_merger.merger import LTLfSpecMerger
import re


def test_init_share_ratio():
    """Test share ratio validation in constructor."""
    # Valid share ratios
    LTLfSpecMerger(0.0)
    LTLfSpecMerger(0.5)
    LTLfSpecMerger(1.0)

    # Invalid share ratios
    with pytest.raises(ValueError):
        LTLfSpecMerger(-0.1)
    with pytest.raises(ValueError):
        LTLfSpecMerger(1.1)


def test_variable_conflicts():
    """Test detection of environment and system variable conflicts."""
    merger = LTLfSpecMerger()

    # Create test files with conflicting variables
    os.makedirs('test_files', exist_ok=True)
    with open('test_files/conflict.ltlf', 'w') as f:
        f.write('p1 U p2')
    with open('test_files/conflict.part', 'w') as f:
        f.write('.inputs: p1 shared\n.outputs: p2 shared\n')

    with pytest.raises(ValueError) as exc_info:
        merger.merge_specs([('test_files/conflict.ltlf', 'test_files/conflict.part')])
    assert "share names" in str(exc_info.value)


def test_merge_two_specs():
    """Test merging two LTLf specifications."""
    merger = LTLfSpecMerger(share_ratio=0.5)

    spec_files = [
        (os.path.join('syft_1_filtered', '001.ltlf'), os.path.join('syft_1_filtered', '001.part')),
        (os.path.join('syft_1_filtered', '002.ltlf'), os.path.join('syft_1_filtered', '002.part'))
    ]

    merged_ltlf, merged_part = merger.merge_specs(spec_files)

    # Verify formula structure
    assert merged_ltlf.startswith('(')
    assert merged_ltlf.endswith(')')
    assert ' && ' in merged_ltlf

    # Verify .part file structure
    assert merged_part.startswith('.inputs:')
    assert '.outputs:' in merged_part
    assert merged_part.endswith('\n')

    # Parse merged .part content
    env_line, sys_line = merged_part.strip().split('\n')
    env_vars = env_line.replace('.inputs:', '').strip().split()
    sys_vars = sys_line.replace('.outputs:', '').strip().split()

    # Verify no variable name conflicts
    assert not set(env_vars).intersection(set(sys_vars))

    # Verify variable count constraints
    orig_env_counts = [1, 1]  # from 001.part and 002.part
    max_env = max(orig_env_counts)
    sum_env = sum(orig_env_counts)
    assert max_env <= len(env_vars) <= sum_env


def test_variable_share_ratios():
    """Test different variable share ratios."""
    spec_files = [
        (os.path.join('syft_1_filtered', '001.ltlf'), os.path.join('syft_1_filtered', '001.part')),
        (os.path.join('syft_1_filtered', '002.ltlf'), os.path.join('syft_1_filtered', '002.part'))
    ]

    # Test minimum sharing (ratio = 0)
    merger_min = LTLfSpecMerger(share_ratio=0.0)
    _, part_min = merger_min.merge_specs(spec_files)
    env_vars_min = part_min.split('\n')[0].replace('.inputs:', '').strip().split()
    assert len(env_vars_min) == 2  # sum of original env vars

    # Test maximum sharing (ratio = 1)
    merger_max = LTLfSpecMerger(share_ratio=1.0)
    _, part_max = merger_max.merge_specs(spec_files)
    env_vars_max = part_max.split('\n')[0].replace('.inputs:', '').strip().split()
    assert len(env_vars_max) == 1  # max of original env vars


def test_unused_variable_removal():
    """Test that unused variables are removed from output."""
    merger = LTLfSpecMerger(share_ratio=0.0)  # Use max variables
    spec_files = [
        (os.path.join('syft_1_filtered', '001.ltlf'), os.path.join('syft_1_filtered', '001.part')),
        (os.path.join('syft_1_filtered', '002.ltlf'), os.path.join('syft_1_filtered', '002.part'))
    ]

    merged_ltlf, merged_part = merger.merge_specs(spec_files)

    # Parse merged .part content
    env_line, sys_line = merged_part.strip().split('\n')
    env_vars = env_line.replace('.inputs:', '').strip().split()
    sys_vars = sys_line.replace('.outputs:', '').strip().split()

    # Convert p format to env_ format for comparison with formula
    env_vars_formula = [f"env_{var[1:]}" for var in env_vars]

    # Extract all variables from formula using the same regex as the merger
    formula_env_vars = set(re.findall(r'\b(env_\d+)(?:\W|$)', merged_ltlf))
    formula_sys_vars = set(re.findall(r'\b(sys_\d+)(?:\W|$)', merged_ltlf))

    # Verify that all variables in .part are used in formula
    assert set(env_vars_formula) == formula_env_vars, "Some env variables in .part file don't match formula"
    assert set(sys_vars) == formula_sys_vars, "Some sys variables in .part file don't match formula"


def teardown_module():
    """Clean up test files."""
    import shutil
    if os.path.exists('test_files'):
        shutil.rmtree('test_files')
