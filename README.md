## LTLf synthesis spec Merger

### What is a LTLf synthesis spec?

a pair of `.ltlf` and `.part` files

- `.ltlf` file: only one line, which is a LTLf formula
- `.part` file: two lines, one line begin with `.inputs:` which is followed by boolean environment variable names splited by space, one line begin with `.outputs:` which is followed by boolean system variable names splited by space

> NOTE: environment variables and system variables cannot share a same variable name, we consider this as conflictions

### How to merge two LTLf synthesis specs?

> NOTE: the merge operator is defaultly && (and) here.
> NOTE: keep the semantic and realizabilty of two LTLf spec while merging

- for `.ltlf` files or LTLf formulae, it's very easy, just combine with merge operator
    - NOTE: for sake of semantic ambiguity, add full brackets when merging, like "((formula1) && (formula2))"
- for `.part` files
    - logic of merging environment variables and system variables are the same, here we take merge of environment variables as example
        - suppose spec1 has n1 environment variables, spec2 has n2 environment variables
        - then the new merge spec can have [max(n1, n2), n1+n2] environment variables
            - if the new merge spec has only max(n1, n2) environment variables, then the two specs share the most environment variables after merge
            - if the new merge spec has only n1+n2 environment variables, then the two specs share the least environment variables after merge
            - if the new merge spec has more than n1+n2 environment variables, then there must exist some environment variables which is not used by either spec1 or spec2 after merge
                - this is meaningless, so we don't want it
            - if the new merge spec has less than max(n1, n2) environment variables, (suppose n1 > n2) then the spec1 after merge will not have enough environment variables to keep its raw logic, since it has to see two different environment variables before merge as the same one after merge
                - this is also meaningless, so we don't want it
    - again, don't let environment variables and system variables cannot share a same variable name, we consider this as conflictions

### How to merge multiple (more than two) LTLf synthesis specs?

- the merge logic is similar to above (merge two LTLf synthesis specs)
- and a easy approach is, first merge the first two LTLf synthesis specs as merged_spec1, then merge merged_spec1 and the 3rd spec, and so on
- in the next section (Merge Algorithm), we will show a full merge algorithm to merge multiple (more than two) LTLf synthesis specs directly, in other word, we will merge multiple LTLf synthesis specs only by one merge

### Merge Algorithm for merge multiple (more than two) LTLf synthesis specs

#### Problem Statements

spec1: en1 environment variables, sn1 environment variables
spec2: en2 environment variables, sn2 environment variables
...
speck: enk environment variables, snk environment variables

> we also have another input: variables share ratio, which indicates the degree of variable sharing in the spec after merging;
> the value of variables share ratio range is 0-1

#### Merge Algorithm

##### merge of environment variables

> According to before statement, the new merge spec can have [max(en1, en2, ..., enk), sum(en1, en2, ..., enk)] environment variables.
> if the value of variables share ratio is 0, we expect to have max(en1, en2, ..., enk) environment vairables in the merge results
> if the value of variables share ratio is 1, we expect to have sum(en1, en2, ..., enk) environment vairables in the merge results
> NOTE: just expect, not exactly the number!

let sum_en = sum(en1, en2, ..., enk), max_en = max(en1, en2, ..., enk), the value of variables share ratio is share_ratio
so, the number of environment variables we expect is merge_en = max_en + (sum_en-max_en)*share_ratio

1. initial merge_en environment vairables for futher use
2. iteratively traverse each spec, and replace each environment variable with new environment vairables, but we should follow a principle that if before replace, env_var1 and env_var2 are different environment vairables in one same spec, then they must also be different environment vairables after replace/merge. Note two environment vairables in different specs before merge, we don't care whether they are same environment vairable after merge as long as they are also environment vairables not system vairables. So our replace approach for environment variables of one spec is as following:
    i. suppose we are now plan to replace environment variables with new one for spec_i, which has eni environment variables before merge, and we make its eni environment variables before merge notes as array env_var_arr_i
    ii. get a new copy of merge_en environment vairables, note as tmp_merge_env_var_arr
    iii. then we just traverse element(environment variable), note as env_var_j=env_var_arr_i[j], in array env_var_arr_i:
        - randomly take a new environment variable in tmp_merge_env_var_arr, to replace env_var_j, and then erase the chosen environment variable from tmp_merge_env_var_arr
        - Note we should use a map to record the replace relation for each spec respectively, and after get the replace plan for a spec, we can replace the corresponding LTLf formula in `.ltlf` file according to this record map
