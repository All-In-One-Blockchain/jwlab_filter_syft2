"""
Core implementation of LTLf specification merger.
"""
from typing import List, Tuple
import re


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

    def _check_variable_conflicts(self, env_vars: List[List[str]], sys_vars: List[List[str]]):
        """Check for conflicts between environment and system variables."""
        env_set = set().union(*[set(vars) for vars in env_vars])
        sys_set = set().union(*[set(vars) for vars in sys_vars])
        if conflicts := env_set & sys_set:
            raise ValueError(f"Environment and system variables share names: {conflicts}")

    def _calculate_merge_vars_count(self, var_counts: List[List[str]]) -> int:
        """Calculate number of variables in merged result based on share ratio."""
        counts = [len(vars) for vars in var_counts]
        if self.share_ratio == 1.0:
            return max(counts)
        elif self.share_ratio == 0.0:
            return len(set().union(*[set(vars) for vars in var_counts]))
        return max(counts) + int((sum(counts) - max(counts)) * self.share_ratio)

    def _get_used_variables(self, formula: str) -> Tuple[set, set]:
        """Extract used environment and system variables from formula."""
        env_vars = set(re.findall(r'\b(env_\d+)(?:\W|$)', formula))
        sys_vars = set(re.findall(r'\b(sys_\d+)(?:\W|$)', formula))
        p_vars = set(re.findall(r'\b(p\d+)(?:\W|$)', formula))
        env_vars.update(f"env_{var[1:]}" for var in p_vars)
        return env_vars, sys_vars

    def merge_specs(self, spec_files: List[Tuple[str, str]]) -> Tuple[str, str]:
        """
        Merge multiple LTLf specs according to the algorithm in README.md.

        Args:
            spec_files: List of tuples (ltlf_file, part_file)

        Returns:
            Tuple of (merged_ltlf_content, merged_part_content)
        """
        formulas = []
        env_vars_lists = []
        sys_vars_lists = []

        # Read all specifications and convert variables
        for ltlf_file, part_file in spec_files:
            formula = self._read_ltlf_file(ltlf_file)
            formula = re.sub(r'\bp(\d+)\b', r'env_\1', formula)
            formulas.append(formula)

            env_vars, sys_vars = self._read_part_file(part_file)
            env_vars_lists.append(env_vars)
            sys_vars_lists.append(sys_vars)

        self._check_variable_conflicts(env_vars_lists, sys_vars_lists)

        # Merge formulas first to determine which variables are actually used
        merged_ltlf = " && ".join(f"({formula})" for formula in formulas)
        used_env_vars, used_sys_vars = self._get_used_variables(merged_ltlf)

        # Get all available variables from original specs
        all_env_vars_p = sorted(set().union(*[set(vars) for vars in env_vars_lists]))
        all_sys_vars = sorted(set().union(*[set(vars) for vars in sys_vars_lists]))

        # Convert all variables that appear in formula to env_ format
        all_formula_vars = sorted(set(
            [f"env_{var[1:]}" for var in all_env_vars_p] +
            [f"env_{var[1:]}" for var in all_sys_vars if var.startswith('p')]
        ))

        # Calculate target variable counts based on actual formula usage
        env_vars_in_formula = set(used_env_vars)
        sys_vars_in_formula = set(used_sys_vars)

        # For share_ratio = 0.0, keep all variables used in formula
        if self.share_ratio == 0.0:
            final_env_vars = sorted(env_vars_in_formula)
            final_sys_vars = sorted(sys_vars_in_formula)
            # Add any p-format variables used in formula
            for var in all_formula_vars:
                if var in used_env_vars:
                    final_env_vars.append(var)
            final_env_vars = sorted(set(final_env_vars))
        elif self.share_ratio == 1.0:
            # For maximum sharing, keep only used variables up to max count
            max_env_count = max(len(vars) for vars in env_vars_lists)
            max_sys_count = max(len(vars) for vars in sys_vars_lists)

            # Start with used variables
            final_env_vars = sorted(used_env_vars)
            final_sys_vars = sorted(used_sys_vars)

            # Add unused variables if needed to reach max count
            remaining_env_vars = [v for v in all_formula_vars if v not in final_env_vars]
            remaining_sys_vars = [v for v in all_sys_vars if v not in final_sys_vars]

            while len(final_env_vars) < max_env_count and remaining_env_vars:
                final_env_vars.append(remaining_env_vars.pop(0))
            while len(final_sys_vars) < max_sys_count and remaining_sys_vars:
                final_sys_vars.append(remaining_sys_vars.pop(0))

            final_env_vars = sorted(final_env_vars)[:max_env_count]
            final_sys_vars = sorted(final_sys_vars)[:max_sys_count]
        else:
            # For partial sharing, start with used variables and add until target count
            env_count = self._calculate_merge_vars_count(env_vars_lists)
            sys_count = self._calculate_merge_vars_count(sys_vars_lists)


            final_env_vars = list(used_env_vars)
            final_sys_vars = list(used_sys_vars)

            remaining_env_vars = [v for v in all_formula_vars if v not in final_env_vars]
            remaining_sys_vars = [v for v in all_sys_vars if v not in final_sys_vars]

            while len(final_env_vars) < env_count and remaining_env_vars:
                final_env_vars.append(remaining_env_vars.pop(0))
            while len(final_sys_vars) < sys_count and remaining_sys_vars:
                final_sys_vars.append(remaining_sys_vars.pop(0))

            final_env_vars = sorted(final_env_vars)[:env_count]
            final_sys_vars = sorted(final_sys_vars)[:sys_count]

        # Convert env_ format back to p format for .part file
        final_env_vars_part = [f"p{var[4:]}" for var in final_env_vars]

        # Create merged .part content
        merged_part = (f".inputs: {' '.join(final_env_vars_part)}\n"
                      f".outputs: {' '.join(final_sys_vars)}\n")

        return merged_ltlf, merged_part
