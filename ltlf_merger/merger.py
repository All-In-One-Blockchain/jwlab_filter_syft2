"""
Core implementation of LTLf specification merger.
"""
from typing import List, Tuple, Mapping
import re
import random

def check_variable_repeat(vars: List[str]):
    """Check for repeated variables in a list."""
    if len(set(vars)) != len(vars):
        raise ValueError("Variables must be unique")

def check_variable_conflicts(env_vars: List[str], sys_vars: List[str]):
    """Check for conflicts between environment and system variables."""
    env_set = set(env_vars)
    sys_set = set(sys_vars)
    if conflicts := env_set & sys_set:
        raise ValueError(f"Environment and system variables share names: {conflicts}")

def add_brackets_if_needed(formula: str) -> str:
    """Add brackets around formula if it doesn't"""
    if formula.startswith('(') and formula.endswith(')'):
        return formula
    return f"({formula})"

def create_variable_array(count: int, prefix: str) -> List[str]:
    """Create an array of variables with a given count and prefix."""
    return [f"{prefix}{i}" for i in range(count)]

def get_random_replace_plan(old_vars_lists: List[List[str]], final_vars: List[str]) -> Tuple[List[Mapping[str, str]], List[str]]:
    vars_replace_map_arr = []
    used_vars = set()
    for old_vars in old_vars_lists:
        cur_vars_replace_map = {}
        tmp_vars = final_vars.copy()
        # impl random choose by shuffle
        random.shuffle(tmp_vars)

        for old_var in old_vars:
            chosen_var = tmp_vars.pop()
            cur_vars_replace_map[old_var] = chosen_var
            used_vars.add(chosen_var)

        vars_replace_map_arr.append(cur_vars_replace_map)
    return vars_replace_map_arr, list(used_vars)

def get_prefix_without_digits(s: str) -> str:
    if not s:  # 如果字符串为空
        raise ValueError("input string is empty")
    
    match = re.match(r'^[^\d]+', s)  # 匹配非数字的部分
    if match:
        return match.group(0)
    else:
        raise ValueError("input string is all digits")

def relabel_vars_in_plan(vars_replace_map_arr: List[Mapping[str, str]], used_vars: List[str]) -> Tuple[List[Mapping[str, str]], List[str]]:
    """find prefix in used_vars, the var in used_vars is like 'p1', 'p2', 'p3'"""
    if used_vars is None or len(used_vars) == 0:
        raise ValueError("used_vars is empty")
    prefix = get_prefix_without_digits(used_vars[0])
    
    """the var num in used_vars maybe not continuous, so we need to relabel them"""
    relabel_map = {}
    relabel_vars = []
    for i, var in enumerate(used_vars):
        relabel_map[var] = f"{prefix}{i}"
        relabel_vars.append(f"{prefix}{i}")

    new_vars_replace_map_arr = []
    for vars_replace_map in vars_replace_map_arr:
        new_vars_replace_map = {}
        for old_var, new_var in vars_replace_map.items():
            new_vars_replace_map[old_var] = relabel_map[new_var]
        new_vars_replace_map_arr.append(new_vars_replace_map)
    return new_vars_replace_map_arr, relabel_vars


def convert_spec_to_string(formulas: List[str], env_vars: List[str], sys_vars: List[str]) -> Tuple[str, str]:
    """Write merged LTLf formula and .part content to files."""
    merged_ltlf = ' && '.join(formulas)
    merged_part = (f".inputs: {' '.join(env_vars)}\n"
                  f".outputs: {' '.join(sys_vars)}\n")
    return merged_ltlf, merged_part

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

    def _calculate_merge_vars_count(self, vars_lists: List[List[str]]) -> int:
        """Calculate number of variables in merged result based on share ratio."""
        counts = [len(vars) for vars in vars_lists]
        return max(counts) + int((sum(counts) - max(counts)) * self.share_ratio)

    def _get_used_variables(self, formula: str) -> Tuple[set, set]:
        """Extract used variables from formula."""
        used_vars = set(re.findall(r'p[a-zA-Z0-9_]+', formula))
        return used_vars
    
    def load_specs(self, spec_files: List[Tuple[str, str]]) -> Tuple[List[str], List[List[str]], List[List[str]]]:
        formulas = []
        env_vars_lists = []
        sys_vars_lists = []
        """Read all specifications and convert variables"""
        for ltlf_file, part_file in spec_files:
            formula = self._read_ltlf_file(ltlf_file)
            formula = add_brackets_if_needed(formula)
            formulas.append(formula)

            env_vars, sys_vars = self._read_part_file(part_file)
            check_variable_repeat(env_vars)
            check_variable_repeat(sys_vars)
            check_variable_conflicts(env_vars, sys_vars)

            used_var_set = self._get_used_variables(formula)
            # filter used variables for env_vars and sys_vars
            used_env_vars = [var for var in env_vars if var in used_var_set]
            used_sys_vars = [var for var in sys_vars if var in used_var_set]

            env_vars_lists.append(used_env_vars)
            sys_vars_lists.append(used_sys_vars)
        return formulas, env_vars_lists, sys_vars_lists
    
    def merge_specs(self, spec_files: List[Tuple[str, str]]) -> Tuple[str, str]:
        """
        Merge multiple LTLf specs according to the algorithm in README.md.

        Args:
            spec_files: List of tuples (ltlf_file, part_file)

        Returns:
            Tuple of (merged_ltlf_content, merged_part_content)
        """
        formulas, env_vars_lists, sys_vars_lists = self.load_specs(spec_files)
        res_tuple = self.merge_specs_inner(formulas, env_vars_lists, sys_vars_lists)
        return convert_spec_to_string(*res_tuple)

    def merge_specs_inner(self, formulas: List[str], env_vars_lists: List[List[str]], sys_vars_lists: List[List[str]]) -> Tuple[List[str], List[str], List[str]]:
        """
        Merge multiple LTLf specs according to the algorithm in README.md.

        Args:
            formulas: List of LTLf formulas
            env_vars_lists: List of environment variables
            sys_vars_lists: List of system variables

        Returns:
            Tuple of (merged_ltlf_content, merged_part_content)
        """
        # For partial sharing, start with used variables and add until target count
        env_count = self._calculate_merge_vars_count(env_vars_lists)
        sys_count = self._calculate_merge_vars_count(sys_vars_lists)
        final_env_vars = create_variable_array(env_count, 'e')
        final_sys_vars = create_variable_array(sys_count, 's')

        # Get random replace plan
        env_vars_replace_map_arr, used_env_vars = relabel_vars_in_plan(*get_random_replace_plan(env_vars_lists, final_env_vars))
        sys_vars_replace_map_arr, used_sys_vars = relabel_vars_in_plan(*get_random_replace_plan(sys_vars_lists, final_sys_vars))

        # Merge formulas first to determine which variables are actually used
        replaced_formulas = []
        for formula, env_vars_replace_map, sys_vars_replace_map in zip(formulas, env_vars_replace_map_arr, sys_vars_replace_map_arr):
            for old_var, new_var in env_vars_replace_map.items():
                formula = formula.replace(old_var, new_var)
            for old_var, new_var in sys_vars_replace_map.items():
                formula = formula.replace(old_var, new_var)
            replaced_formulas.append(formula)
        
        return replaced_formulas, used_env_vars, used_sys_vars
