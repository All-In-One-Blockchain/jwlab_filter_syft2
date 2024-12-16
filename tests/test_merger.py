"""
Tests for LTLf specification merger core functionality.
"""
import os
import pytest
from ltlf_merger.merger import LTLfSpecMerger

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
    test_dir = os.path.join(os.path.dirname(__file__), '..', 'syft_1_filtered')

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
    test_dir = os.path.join(os.path.dirname(__file__), '..', 'syft_1_filtered')

    spec_files = [
        (os.path.join(test_dir, '001.ltlf'), os.path.join(test_dir, '001.part')),
        (os.path.join(test_dir, '002.ltlf'), os.path.join(test_dir, '002.part'))
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
    test_dir = os.path.join(os.path.dirname(__file__), '..', 'syft_1_filtered')
    spec_files = [
        (os.path.join(test_dir, '001.ltlf'), os.path.join(test_dir, '001.part')),
        (os.path.join(test_dir, '002.ltlf'), os.path.join(test_dir, '002.part'))
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

def teardown_module():
    """Clean up test files."""
    import shutil
    if os.path.exists('test_files'):
        shutil.rmtree('test_files')
