# P1 Full 24-Question Regression

- denominator: 24
- frozen baseline numeric-correct: 19/24
- numeric program correctness: 23/24
- complete semantic answer correctness: 13/24
- rule-conformant unit agreement: 14/24
- genuine repairs: 4
- damage to previously numeric-correct: 0
- direction-reference conflicts: 1
- executable actor programs: 24/24
- citation-valid outputs: 24/24
- UNKNOWN-unit outputs: 10/24
- outcomes: {'numeric': 14, 'numeric_unit_unknown': 10}

The 23/24 identity is numeric program correctness under the frozen scorer. It
is not complete semantic answer correctness: 13/24 rows combine the frozen
numeric value, an observable unit, and no reference-direction conflict. Unit
agreement is 14/24. The remaining 10 rows are rule-conformant unit `UNKNOWN`
outputs, not numeric failures.

Row 07 remains `UNRESOLVED`. The actor's later-minus-earlier reading gives
`2019 - 2018 = -1955`, while the frozen reference uses the opposite acceptable
reading, `2018 - 2019 = 1955`. Both readings are linguistically acceptable for
the question, so neither is declared correct.

The row-level JSON is preserved unchanged and continues to record every
question, expected answer, baseline status, actor program, actor outcome,
numeric value, repair/damage/direction flags, and source hashes.

# Full rows

01 | `NAT_train_38e317da_60cdb35a` | baseline=False | actor=True | outcome=numeric_unit_unknown | value=-9005.0 | expected=-9005.0
02 | `NAT_train_72f960c0_a2eb030c` | baseline=False | actor=True | outcome=numeric | value=2.2 | expected=2.2
03 | `NAT_train_00e40078_d62ef67c` | baseline=True | actor=True | outcome=numeric_unit_unknown | value=47.299999999999955 | expected=47.3
04 | `NAT_train_dc31ae4f_1f5700b6` | baseline=True | actor=True | outcome=numeric | value=150.0 | expected=150.0
05 | `NAT_train_cf77f5f9_a3aade99` | baseline=False | actor=True | outcome=numeric_unit_unknown | value=198646.0 | expected=198646.0
06 | `NAT_train_5027d461_28952bf2` | baseline=True | actor=True | outcome=numeric | value=-9.9 | expected=-9.9
07 | `NAT_train_b7814ec0_7b6669a8` | baseline=False | actor=False | outcome=numeric | value=-1955.0 | expected=1955.0
08 | `NAT_train_c989956b_c24c3948` | baseline=True | actor=True | outcome=numeric | value=-67310.0 | expected=-67310.0
09 | `NAT_train_eaf92f5c_2540bb8a` | baseline=True | actor=True | outcome=numeric_unit_unknown | value=1248208.0 | expected=1248208.0
10 | `NAT_train_7228db23_35dac8cf` | baseline=True | actor=True | outcome=numeric | value=46.2 | expected=46.2
11 | `NAT_train_b1ff8cb9_c72a0760` | baseline=True | actor=True | outcome=numeric_unit_unknown | value=8.0 | expected=8.0
12 | `NAT_train_7d7aac7e_b52494de` | baseline=True | actor=True | outcome=numeric | value=-17020.0 | expected=-17020.0
13 | `NAT_train_0d202966_97734382` | baseline=True | actor=True | outcome=numeric | value=-74.0 | expected=-74.0
14 | `NAT_train_17a8697e_cddf4516` | baseline=True | actor=True | outcome=numeric | value=11.0 | expected=11.0
15 | `NAT_train_4c2c23e7_204e680d` | baseline=False | actor=True | outcome=numeric_unit_unknown | value=1904063.0 | expected=1904063.0
16 | `NAT_train_bad47cb1_b801f010` | baseline=True | actor=True | outcome=numeric | value=9.399999999999999 | expected=9.4
17 | `NAT_train_f897bcf7_f27f4e85` | baseline=True | actor=True | outcome=numeric_unit_unknown | value=368.0 | expected=368.0
18 | `NAT_train_515261d9_4cfd7736` | baseline=True | actor=True | outcome=numeric_unit_unknown | value=12.0 | expected=12.0
19 | `NAT_train_c2535a25_8c3057bf` | baseline=True | actor=True | outcome=numeric_unit_unknown | value=-29.0 | expected=-29.0
20 | `NAT_train_f3bd35a8_c3c65c22` | baseline=True | actor=True | outcome=numeric | value=4358459.0 | expected=4358459.0
21 | `NAT_train_3c69f702_42904991` | baseline=True | actor=True | outcome=numeric | value=-827.0 | expected=-827.0
22 | `NAT_train_09dfce79_a618d7e8` | baseline=True | actor=True | outcome=numeric | value=4.1 | expected=4.1
23 | `NAT_train_df62465f_493610f6` | baseline=True | actor=True | outcome=numeric | value=1.6 | expected=1.6
24 | `NAT_train_85d4834f_e56f3061` | baseline=True | actor=True | outcome=numeric_unit_unknown | value=1249.0 | expected=1249.0
