"""
Core implementation of LTLf specification merger.
"""
from typing import List, Tuple, Dict, Set
import random

class LTLfSpecMerger:
    def __init__(self, share_ratio: float = 0.5):
        """
        Initialize LTLf specification merger.

        Args:
            share_ratio: Float between 0 and 1 indicating the degree of variable sharing.
                        0 means minimum sharing (sum of variables),
                        1 means maximum sharing (max of variables).
        """
        if not 0 <= share_ratio <= 1:
            raise ValueError("share_ratio must be between 0 and 1")
        self.share_ratio = share_ratio

    def _read_part_file(self, part_file: str) -> Tuple[List[str], List[str]]:
        """Read .part file and return environment and system variables."""
        with open(part_file, 'r') as f:
            lines = f.readlines()

        env_vars = []
        sys_vars = []

        for line in lines:
            if line.startswith('.inputs:'):
                env_vars = line.replace('.inputs:', '').strip().split()
            elif line.startswith('.outputs:'):
                sys_vars = line.replace('.outputs:', '').strip().split()

        return env_vars, sys_vars

    def _read_ltlf_file(self, ltlf_file: str) -> str:
        """Read .ltlf file and return the formula."""
        with open(ltlf_file, 'r') as f:
            return f.read().strip()

    def _check_variable_conflicts(self, env_vars: List[str], sys_vars: List[str]):
        """Check for conflicts between environment and system variables."""
        env_set = set(env_vars)
        sys_set = set(sys_vars)
        conflicts = env_set.intersection(sys_set)
        if conflicts:
            raise ValueError(f"Environment and system variables share names: {conflicts}")

    def _calculate_merge_vars_count(self, var_counts: List[int]) -> int:
        """Calculate number of variables in merged result based on share ratio."""
        max_vars = max(var_counts)
        sum_vars = sum(var_counts)
        return int(max_vars + (sum_vars - max_vars) * self.share_ratio)

    def merge_specs(self, spec_files: List[Tuple[str, str]]) -> Tuple[str, str]:
        """
        Merge multiple LTLf specs according to the algorithm in README.md.

        Args:
            spec_files: List of tuples (ltlf_file, part_file)

        Returns:
            Tuple of (merged_ltlf_content, merged_part_content)
        """
        # Read all specs
        specs = []
        env_var_counts = []
        sys_var_counts = []

        for ltlf_file, part_file in spec_files:
            env_vars, sys_vars = self._read_part_file(part_file)
            formula = self._read_ltlf_file(ltlf_file)
            self._check_variable_conflicts(env_vars, sys_vars)

            specs.append({
                'formula': formula,
                'env_vars': env_vars,
                'sys_vars': sys_vars
            })
            env_var_counts.append(len(env_vars))
            sys_var_counts.append(len(sys_vars))

        # Calculate merged variable counts
        merge_env_count = self._calculate_merge_vars_count(env_var_counts)
        merge_sys_count = self._calculate_merge_vars_count(sys_var_counts)

        # Generate new variable names
        merged_env_vars = [f"env_{i}" for i in range(merge_env_count)]
        merged_sys_vars = [f"sys_{i}" for i in range(merge_sys_count)]

        # Create variable mappings for each spec
        formulas = []
        for spec in specs:
            # Map environment variables
            env_mapping = {}
            available_env_vars = merged_env_vars.copy()
            for env_var in spec['env_vars']:
                new_var = random.choice(available_env_vars)
                env_mapping[env_var] = new_var
                available_env_vars.remove(new_var)

            # Map system variables
            sys_mapping = {}
            available_sys_vars = merged_sys_vars.copy()
            for sys_var in spec['sys_vars']:
                new_var = random.choice(available_sys_vars)
                sys_mapping[sys_var] = new_var
                available_sys_vars.remove(new_var)

            # Apply mappings to formula
            formula = spec['formula']
            for old_var, new_var in {**env_mapping, **sys_mapping}.items():
                formula = formula.replace(old_var, new_var)
            formulas.append(f"({formula})")

        # Combine formulas with AND operator
        merged_ltlf = " && ".join(formulas)

        # Create merged .part content
        merged_part = f".inputs: {' '.join(merged_env_vars)}\n.outputs: {' '.join(merged_sys_vars)}\n"

        return merged_ltlf, merged_part
