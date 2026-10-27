# Error Cards

AI/automatic diagnostic labeling from immutable first-batch evidence; not model self-report and not human gold

Nine old shared REJECT UIDs and three non-shared controls; each card uses the real question, immutable final-attempt raw response and visible context.

## 01de2123-400f-4411-98d9-cd3f9f1e4136 — old_shared_reject

- Question: For adjusted operating costs, what was the percentage change in the amount of before exceptional items, acquisition related costs, acquired intangible asset amortisation and share-based payment between 2018 and 2019?
- Answer type / source: `arithmetic` / `paragraph`
- Diagnosis: The visible paragraph supplies 2019=4.3 and 2018=19.6 million, but each arm instead returns the table's 3.1 row change: wrong row binding and wrong typed operation.
- Labels: citation_support, fact_entity_row_period_binding, operation_reduction, reference_defect, unit_direction

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 13 | REJECT | REJECT | answer:numeric_answer_mismatch, evidence:semantic_reference_mismatch, numeric_unit:numeric_value_mismatch_or_direction |
| table_top5 | 14 | REJECT | REJECT | answer:numeric_answer_mismatch, evidence:semantic_reference_mismatch, numeric_unit:numeric_value_mismatch_or_direction |
| table_all | 15 | REJECT | REJECT | answer:numeric_answer_mismatch, evidence:semantic_reference_mismatch, numeric_unit:numeric_value_mismatch_or_direction |

Visible context:

```text
P1: 2. Before exceptional items, acquisition related costs, acquired intangible asset amortisation and share-based payment amounting to $4.3 million in total (2018 $19.6 million).

TABLE
columns: C0=$ million | C1=2019 | C2=2018 | C3=Change (%)
R1 [Order intake1] C0=Order intake1 | C1=532.0 | C2=470.0 | C3=13.2
R2 [Revenue] C0=Revenue | C1=503.6 | C2=476.9 | C3=5.6
R3 [Gross profit] C0=Gross profit | C1=368.6 | C2=344.5 | C3=7.0
R4 [Gross margin (%)] C0=Gross margin (%) | C1=73.2 | C2=72.2 | C3=1.0
R5 [Adjusted operating costs2] C0=Adjusted operating costs2 | C1=275.7 | C2=267.4 | C3=3.1
R6 [Adjusted operating profit2] C0=Adjusted operating profit2 | C1=92.9 | C2=77.1 | C3=20.5
R7 [Adjusted operating margin3 (%)] C0=Adjusted operating margin3 (%) | C1=18.4 | C2=16.2 | C3=2.2
R8 [Reported operating profit] C0=Reported operating profit | C1=88.6 | C2=57.5 | C3=54.1
R9 [Effective tax rate4 (%)] C0=Effective tax rate4 (%) | C1=13.0 | C2=15.4 | C3=(2.4)
R10 [Reported profit before tax] C0=Reported profit before tax | C1=89.6 | C2=61.2 | C3=46.4
R11 [Adjusted basic earnings per share5 (cents)] C0=Adjusted basic earnings per share5 (cents) | C1=13.40 | C2=10.86 | C3=23.4
R12 [Basic earnings per share (cents)] C0=Basic earnings per share (cents) | C1=12.79 | C2=9.14 | C3=39.9
R13 [Free cash flow6] C0=Free cash flow6 | C1=100.1 | C2=50.9 | C3=96.7
R14 [Closing cash] C0=Closing cash | C1=183.2 | C2=121.6 | C3=50.7
R15 [Final dividend per share7 (cents)] C0=Final dividend per share7 (cents) | C1=3.45 | C2=2.73 | C3=26.4
```

## 5e67e832-44c4-4284-96d3-75b81cd1ac26 — old_shared_reject

- Question: What is the amount of payroll taxes in 2019 and 2018 respectively?
- Answer type / source: `multi-span` / `both`
- Diagnosis: The two payroll values are numerically correct, but numeric_value is an array under a scalar contract and the evidence is column-broad rather than row-bound.
- Labels: citation_support, format, reference_defect

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 5 | REJECT | STRICT_FAIL | evidence:nonexistent_reference, final_delivery:invalid_numeric_value_type;numeric_array_contract, strict:invalid_numeric_value_type;numeric_array_contract |
| table_top5 | 7 | REJECT | STRICT_FAIL | evidence:nonexistent_reference, final_delivery:invalid_numeric_value_type;numeric_array_contract, strict:invalid_numeric_value_type;numeric_array_contract |
| table_all | 9 | REJECT | STRICT_FAIL | evidence:nonexistent_reference, final_delivery:invalid_numeric_value_type;numeric_array_contract, strict:invalid_numeric_value_type;numeric_array_contract |

Visible context:

```text
P1: Accrued liabilities at April 30, 2019 and 2018, respectively, consisted of the following (in thousands):

TABLE
columns: C0= | C1=2019 | C2=2018
R1 [Vacation and other compensation] C0=Vacation and other compensation | C1=$1,659 | C2=$1,433
R2 [Incentive compensation] C0=Incentive compensation | C1=346 | C2=411
R3 [Payroll taxes] C0=Payroll taxes | C1=155 | C2=113
R4 [Deferred revenue] C0=Deferred revenue | C1=- | C2=68
R5 [Warranty reserve] C0=Warranty reserve | C1=529 | C2=520
R6 [Commissions] C0=Commissions | C1=378 | C2=307
R7 [Other] C0=Other | C1=504 | C2=564
R8 [] C0= | C1=$3,571 | C2=$3,416
```

## 7a1f65b6-25e2-48e2-a3cc-baddc688545e — non_shared_control

- Question: What is the total external revenues from Canada in 2019?
- Answer type / source: `span` / `both`
- Diagnosis: The Canada value is correct, but USD/$ is used instead of the visible thousand scale and TABLE:C1 is not row-bound; top3 also lacks the scale paragraph.
- Labels: citation_support, reference_defect, unit_direction, visible_information_insufficient

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 10 | ACCEPT | PENDING_ADJUDICATION | evidence:legal_semantic_reference_not_reconstructible, final_delivery:numeric_unit:expected_scale_not_reconstructible_from_visible_evidence;evidence:legal_semantic_reference_not_reconstructible, numeric_unit:expected_scale_not_reconstructible_from_visible_evidence |
| table_top5 | 11 | ACCEPT | REJECT | evidence:broad_reference_not_role_bound, numeric_unit:unit_or_scale_mismatch |
| table_all | 12 | ACCEPT | REJECT | evidence:broad_reference_not_role_bound, numeric_unit:unit_or_scale_mismatch |

Visible context:

```text
P1: Expressed in US $000's except share and per share amounts

TABLE
columns: C0= | C1=Years ended | C2= | C3= | C4=
R1 [] C0= | C1=December 31, 2019 | C2= | C3=December 31, 2018 | C4=
R2 [] C0= | C1=$ | C2=% | C3=$ | C4=%
R3 [Canada] C0=Canada | C1=96,168 | C2=6.1% | C3=70,774 | C4=6.6%
R4 [United States] C0=United States | C1=1,079,520 | C2=68.4% | C3=755,454 | C4=70.4%
R5 [United Kingdom] C0=United Kingdom | C1=103,498 | C2=6.6% | C3=69,596 | C4=6.5%
R6 [Australia] C0=Australia | C1=68,571 | C2=4.3% | C3=47,937 | C4=4.5%
R7 [Rest of World] C0=Rest of World | C1=230,416 | C2=14.6% | C3=129,468 | C4=12.0%
R8 [] C0= | C1=1,578,173 | C2=100.0% | C3=1,073,229 | C4=100.0%
```

## 7e942684-fe9e-4ded-a3e9-2f3a5aa707fe — old_shared_reject

- Question: What services have their costs included within the audit fees?
- Answer type / source: `multi-span` / `paragraph`
- Diagnosis: The question asks for enumerated services, while every arm returns fee categories; paragraph and column references therefore do not support the requested fact.
- Labels: fact_entity_row_period_binding, format, reference_defect, visible_information_insufficient

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 19 | REJECT | REJECT | answer:exact_text_set_mismatch, evidence:legal_semantic_reference_not_reconstructible |
| table_top5 | 20 | REJECT | REJECT | answer:exact_text_set_mismatch, evidence:legal_semantic_reference_not_reconstructible |
| table_all | 22 | REJECT | STRICT_FAIL | answer:exact_text_set_mismatch, evidence:invalid_reference, final_delivery:invalid_evidence_reference_syntax, strict:invalid_evidence_reference_syntax |

Visible context:

```text
P1: (1) Includes the cost of services rendered in connection with (i) auditing our annual consolidated financial statements, (ii) auditing our internal control over financial reporting in accordance with Section 404 of the Sarbanes-Oxley Act of 2002, (iii) reviewing our quarterly financial statements, (iv) auditing the financial statements of several of our subsidiaries, (v) reviewing our registration statements and issuing related comfort letters, (vi) statutory audits for certain of our foreign subsidiaries, and (vii) consultations regarding accounting standards. In addition, the amount listed for 2018 includes a final billing of $785,000 that was received after we finalized our 2019 proxy statement and consequently was not reflected in the auditor fee table included in our 2019 proxy statement.

TABLE
columns: C0= | C1=Amount Billed | C2=
R1 [] C0= | C1=2018 | C2=2019
R2 [Audit Fees(1)] C0=Audit Fees(1) | C1=$16,014,014 | C2=$17,639,702
R3 [Audit-Related Fees(2)] C0=Audit-Related Fees(2) | C1=106,528 | C2=153,203
R4 [Tax Fees(3)] C0=Tax Fees(3) | C1=1,318,798 | C2=119,098
R5 [Other] C0=Other | C1=— | C2=—
R6 [Total Fees] C0=Total Fees | C1=$17,439,340 | C2=$17,912,003
```

## 8a3fb2be-150b-410f-a6d5-f3a3dd1fdba3 — old_shared_reject

- Question: What was the change in the diluted weighted-average number of shares between 2017 and 2018?
- Answer type / source: `arithmetic` / `both`
- Diagnosis: All arms return 2,991 rather than the 2018-minus-2017 diluted-share difference 3,251, indicating period/operation binding failure; references are only column-broad.
- Labels: citation_support, fact_entity_row_period_binding, operation_reduction, unit_direction

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 38 | REJECT | REJECT | answer:numeric_answer_mismatch, evidence:broad_reference_not_role_bound, numeric_unit:numeric_value_mismatch_or_direction |
| table_top5 | 39 | REJECT | REJECT | answer:numeric_answer_mismatch, evidence:broad_reference_not_role_bound, numeric_unit:numeric_value_mismatch_or_direction |
| table_all | 40 | REJECT | REJECT | answer:numeric_answer_mismatch, evidence:broad_reference_not_role_bound, numeric_unit:numeric_value_mismatch_or_direction |

Visible context:

```text
P1: The following table presents the basic and diluted weighted-average number of shares of common stock (amounts in thousands, except per share data):

TABLE
columns: C0= | C1= | C2=Fiscal Years Ended March 31, | C3=
R1 [] C0= | C1=2019 | C2=2018 | C3=2017
R2 [Numerator] C0=Numerator | C1= | C2= | C3=
R3 [Net income (1)] C0=Net income (1) | C1=$206,587 | C2=$254,127 | C3=$47,157
R4 [Denominator:] C0=Denominator: | C1= | C2= | C3=
R5 [Weighted-average common shares outstanding:] C0=Weighted-average common shares outstanding: | C1= | C2= | C3=
R6 [Basic] C0=Basic | C1=57,840 | C2=52,798 | C3=46,552
R7 [Assumed conversion of employee stock grants] C0=Assumed conversion of employee stock grants | C1=1,242 | C2=2,291 | C3=2,235
R8 [Assumed conversion of warrants] C0=Assumed conversion of warrants | C1=— | C2=3,551 | C3=6,602
R9 [Diluted] C0=Diluted | C1=$59,082 | C2=$58,640 | C3=$55,389
R10 [Net income per basic share (1)] C0=Net income per basic share (1) | C1=$3.57 | C2=$4.81 | C3=$1.01
R11 [Net income per diluted share (1)] C0=Net income per diluted share (1) | C1=$3.50 | C2=$4.33 | C3=$0.85
```

## 9e3493de-9a29-4db8-ad06-52dc6ff1fdaf — old_shared_reject

- Question: How many services have their costs included within the audit fees?
- Answer type / source: `count` / `paragraph`
- Diagnosis: All arms enumerate fee-table categories but never count the seven paragraph services; the required visible paragraph is absent from the top3/top5 contexts.
- Labels: citation_support, format, operation_reduction, reference_defect, visible_information_insufficient

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 16 | REJECT | STRICT_FAIL | answer:numeric_answer_not_complete_or_reduced, evidence:legal_semantic_reference_not_reconstructible, final_delivery:count_must_be_nonnegative_integer;numeric_value_required, numeric_unit:numeric_value_missing_or_non_numeric, strict:count_must_be_nonnegative_integer;numeric_value_required |
| table_top5 | 17 | REJECT | STRICT_FAIL | answer:numeric_answer_not_complete_or_reduced, evidence:legal_semantic_reference_not_reconstructible, final_delivery:count_must_be_nonnegative_integer;numeric_value_required, numeric_unit:numeric_value_missing_or_non_numeric, strict:count_must_be_nonnegative_integer;numeric_value_required |
| table_all | 18 | REJECT | STRICT_FAIL | answer:numeric_answer_not_complete_or_reduced, evidence:semantic_reference_mismatch, final_delivery:count_must_be_nonnegative_integer;numeric_value_required, numeric_unit:numeric_value_missing_or_non_numeric, strict:count_must_be_nonnegative_integer;numeric_value_required |

Visible context:

```text
P1: (1) Includes the cost of services rendered in connection with (i) auditing our annual consolidated financial statements, (ii) auditing our internal control over financial reporting in accordance with Section 404 of the Sarbanes-Oxley Act of 2002, (iii) reviewing our quarterly financial statements, (iv) auditing the financial statements of several of our subsidiaries, (v) reviewing our registration statements and issuing related comfort letters, (vi) statutory audits for certain of our foreign subsidiaries, and (vii) consultations regarding accounting standards. In addition, the amount listed for 2018 includes a final billing of $785,000 that was received after we finalized our 2019 proxy statement and consequently was not reflected in the auditor fee table included in our 2019 proxy statement.

TABLE
columns: C0= | C1=Amount Billed | C2=
R1 [] C0= | C1=2018 | C2=2019
R2 [Audit Fees(1)] C0=Audit Fees(1) | C1=$16,014,014 | C2=$17,639,702
R3 [Audit-Related Fees(2)] C0=Audit-Related Fees(2) | C1=106,528 | C2=153,203
R4 [Tax Fees(3)] C0=Tax Fees(3) | C1=1,318,798 | C2=119,098
R5 [Other] C0=Other | C1=— | C2=—
R6 [Total Fees] C0=Total Fees | C1=$17,439,340 | C2=$17,912,003
```

## a75bb0b1-4fb1-405c-b2f1-1df4ee3cc9be — non_shared_control

- Question: What are the components factored in the calculation of investments in subsidiaries at end of the period?
- Answer type / source: `multi-span` / `table`
- Diagnosis: All arms add 'At end of the period' as a component even though it is the result row, and duplicate column-broad citations do not bind each span.
- Labels: citation_support, fact_entity_row_period_binding, reference_defect

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 32 | ACCEPT | REJECT | answer:exact_text_set_mismatch, evidence:semantic_reference_mismatch |
| table_top5 | 33 | ACCEPT | REJECT | answer:exact_text_set_mismatch, evidence:semantic_reference_mismatch |
| table_all | 34 | ACCEPT | REJECT | answer:exact_text_set_mismatch, evidence:semantic_reference_mismatch |

Visible context:

```text
P1: 3. Investments in subsidiaries
P2: The additions in the year and prior year relate to equity-settled share-based payments granted to the employees of subsidiary companies.

TABLE
columns: C0= | C1=2019 | C2=2018
R1 [] C0= | C1=£m | C2=£m
R2 [At beginning of the period] C0=At beginning of the period | C1=1,212.9 | C2=1,210.5
R3 [Additions] C0=Additions | C1=3.1 | C2=2.4
R4 [At end of the period] C0=At end of the period | C1=1,216.0 | C2=1,212.9
```

## ad42fe3e-38cd-446f-a313-b9a50f5e6937 — old_shared_reject

- Question: What is the average trade receivables for 2018 and 2019?
- Answer type / source: `arithmetic` / `both`
- Diagnosis: All arms expose the two trade-receivable operands but omit the mean reduction and scalar numeric_value, so correct operands do not constitute complete delivery.
- Labels: citation_support, format, operation_reduction, unit_direction

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 1 | REJECT | STRICT_FAIL | answer:numeric_answer_not_complete_or_reduced, evidence:broad_reference_not_role_bound, final_delivery:numeric_value_required, numeric_unit:numeric_value_missing_or_non_numeric;unit_or_scale_mismatch, strict:numeric_value_required |
| table_top5 | 2 | REJECT | STRICT_FAIL | answer:numeric_answer_not_complete_or_reduced, evidence:broad_reference_not_role_bound, final_delivery:numeric_value_required, numeric_unit:numeric_value_missing_or_non_numeric;unit_or_scale_mismatch, strict:numeric_value_required |
| table_all | 3 | REJECT | STRICT_FAIL | answer:numeric_answer_not_complete_or_reduced, evidence:broad_reference_not_role_bound, final_delivery:numeric_value_required, numeric_unit:numeric_value_missing_or_non_numeric;unit_or_scale_mismatch, strict:numeric_value_required |

Visible context:

```text
P1: Expressed in US $000's except share and per share amounts

TABLE
columns: C0= | C1=December 31, 2019 | C2=December 31, 2018 | C3=January 1, 2018
R1 [] C0= | C1=$ | C2=$ | C3=$
R2 [Indirect taxes receivable] C0=Indirect taxes receivable | C1=36,821 | C2=3,774 | C3=832
R3 [Unbilled revenues] C0=Unbilled revenues | C1=31,629 | C2=12,653 | C3=7,616
R4 [Trade receivables] C0=Trade receivables | C1=9,660 | C2=11,191 | C3=7,073
R5 [Accrued interest] C0=Accrued interest | C1=5,754 | C2=5,109 | C3=2,015
R6 [Other receivables] C0=Other receivables | C1=6,665 | C2=8,620 | C3=4,403
R7 [] C0= | C1=90,529 | C2=41,347 | C3=21,939
```

## cb4abf04-9551-46e2-8a32-46672e284167 — old_shared_reject

- Question: What was the percentage change in Total operating income in 2019 from 2018?
- Answer type / source: `arithmetic` / `table`
- Diagnosis: All arms return 302%, the raw total rather than (302-148)/148=104.05%; the operation and direction are wrong and references are column-broad.
- Labels: citation_support, fact_entity_row_period_binding, operation_reduction, unit_direction

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 26 | REJECT | REJECT | answer:numeric_answer_mismatch, evidence:broad_reference_not_role_bound, numeric_unit:numeric_value_mismatch_or_direction |
| table_top5 | 27 | REJECT | REJECT | answer:numeric_answer_mismatch, evidence:broad_reference_not_role_bound, numeric_unit:numeric_value_mismatch_or_direction |
| table_all | 28 | REJECT | REJECT | answer:numeric_answer_mismatch, evidence:broad_reference_not_role_bound, numeric_unit:numeric_value_mismatch_or_direction |

Visible context:

```text
P1: Operating income included the following:

TABLE
columns: C0= | C1= | C2=Fiscal
R1 [] C0= | C1=2019 | C2=2018
R2 [] C0= | C1= | C2=(in millions)
R3 [Acquisition-related charges:] C0=Acquisition-related charges: | C1= | C2=
R4 [Acquisition and integration costs] C0=Acquisition and integration costs | C1=$  27 | C2=$  14
R5 [Charges associated with the amortization of acquisition related fair value adjustments] C0=Charges associated with the amortization of acquisition related fair value adjustments | C1=3 | C2=8
R6 [] C0= | C1=30 | C2=22
R7 [Restructuring and other charges, net] C0=Restructuring and other charges, net | C1=255 | C2=126
R8 [Other items(1)] C0=Other items(1) | C1=17 | C2=—
R9 [Total] C0=Total | C1=$  302 | C2=$  148
```

## e14c60c4-3460-42eb-8d21-c29abdbce3a8 — old_shared_reject

- Question: How many quarters did the basic earnings per share exceed $0.30?
- Answer type / source: `count` / `table`
- Diagnosis: All arms find First/Second/Fourth but omit the count 3 and cite nonexistent columns C6/C8 instead of the visible quarter columns.
- Labels: citation_support, format, operation_reduction, reference_defect

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 29 | REJECT | STRICT_FAIL | answer:numeric_answer_not_complete_or_reduced, evidence:nonexistent_reference, final_delivery:count_must_be_nonnegative_integer;numeric_value_required, numeric_unit:numeric_value_missing_or_non_numeric, strict:count_must_be_nonnegative_integer;numeric_value_required |
| table_top5 | 30 | REJECT | STRICT_FAIL | answer:numeric_answer_not_complete_or_reduced, evidence:nonexistent_reference, final_delivery:count_must_be_nonnegative_integer;numeric_value_required, numeric_unit:numeric_value_missing_or_non_numeric, strict:count_must_be_nonnegative_integer;numeric_value_required |
| table_all | 31 | REJECT | STRICT_FAIL | answer:numeric_answer_not_complete_or_reduced, evidence:nonexistent_reference, final_delivery:count_must_be_nonnegative_integer;numeric_value_required, numeric_unit:numeric_value_missing_or_non_numeric, strict:count_must_be_nonnegative_integer;numeric_value_required |

Visible context:

```text
P1: NOTES TO CONSOLIDATED FINANCIAL STATEMENTS (in thousands, except for share and per share data)

TABLE
columns: C0= | C1=First | C2=Second | C3=Third | C4=Fourth
R1 [2019] C0=2019 | C1= | C2= | C3= | C4=
R2 [Net sales] C0=Net sales | C1=$117,625 | C2=$120,684 | C3=$115,651 | C4=$115,040
R3 [Gross margin] C0=Gross margin | C1=$40,615 | C2=$41,204 | C3=$37,057 | C4=$38,700
R4 [Operating earnings] C0=Operating earnings | C1=$14,218 | C2=$17,083 | C3=$10,124 | C4=$12,391
R5 [Net earnings] C0=Net earnings | C1=$11,419 | C2=$11,943 | C3=$2,722 | C4=$10,062
R6 [Basic earnings per share] C0=Basic earnings per share | C1=$0.35 | C2=$0.36 | C3=$0.08 | C4=$0.31
R7 [Diluted earnings per share] C0=Diluted earnings per share | C1=$0.34 | C2=$0.36 | C3=$0.08 | C4=$0.31
R8 [2018] C0=2018 | C1= | C2= | C3= | C4=
R9 [Net sales] C0=Net sales | C1=$113,530 | C2=$118,021 | C3=$118,859 | C4=$120,073
R10 [Gross margin] C0=Gross margin | C1=$38,433 | C2=$41,813 | C3=$42,082 | C4=$42,645
R11 [Operating earnings] C0=Operating earnings | C1=$13,359 | C2=$14,544 | C3=$16,118 | C4=$17,017
R12 [Net earnings] C0=Net earnings | C1=$ 11,54 | C2=$7,209 | C3=$10,211 | C4=$17,564
R13 [Basic earnings per share] C0=Basic earnings per share | C1=$0.35 | C2=$0.22 | C3=$0.31 | C4=$0.53
R14 [Diluted earnings per share] C0=Diluted earnings per share | C1=$0.34 | C2=$0.21 | C3=$0.30 | C4=$0.52
```

## f37d1be3-b3fe-487f-bd05-253c20f55eb2 — old_shared_reject

- Question: What is the units used for the data in the table?
- Answer type / source: `span` / `paragraph`
- Diagnosis: All arms answer 'dollars' although the visible paragraph states '(in thousands)'; the citation is visible but the unit is wrong.
- Labels: fact_entity_row_period_binding

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 23 | REJECT | REJECT | answer:exact_text_set_mismatch |
| table_top5 | 24 | REJECT | REJECT | answer:exact_text_set_mismatch |
| table_all | 25 | REJECT | REJECT | answer:exact_text_set_mismatch |

Visible context:

```text
P1: (in thousands)

TABLE
columns: C0= | C1= | C2=Years Ended December 31, | C3=31,
R1 [] C0= | C1=2019 | C2=2018 | C3=2017
R2 [Current provision for income taxes:] C0=Current provision for income taxes: | C1= | C2= | C3=
R3 [State] C0=State | C1=$49 | C2=$44 | C3=$48
R4 [Foreign] C0=Foreign | C1=1,716 | C2=953 | C3=1,023
R5 [Total current] C0=Total current | C1=1,765 | C2=997 | C3=1,071
R6 [Deferred tax expense (benefit):] C0=Deferred tax expense (benefit): | C1= | C2= | C3=
R7 [Federal] C0=Federal | C1=3 | C2=(13) | C3=26
R8 [Foreign] C0=Foreign | C1=(361) | C2=98 | C3=109
R9 [Total deferred] C0=Total deferred | C1=(358) | C2=85 | C3=135
R10 [Provision for income taxes] C0=Provision for income taxes | C1=$1,407 | C2=$1,082 | C3=$1,206
```

## fcb5e3fa-fb0c-4cce-a86c-229ac3734bd2 — non_shared_control

- Question: What is the net sales arising from total electronic components in 2019?
- Answer type / source: `span` / `table`
- Diagnosis: The value and thousand scale are correct, but TABLE:C4 is column-broad rather than row-bound to Total Electronic Components.
- Labels: citation_support, reference_defect

| Arm | Call | Historical | V2 | Failed/pending layers |
|---|---:|---|---|---|
| table_top3 | 35 | REJECT | REJECT | evidence:nonexistent_reference |
| table_top5 | 36 | ACCEPT | REJECT | evidence:nonexistent_reference |
| table_all | 37 | ACCEPT | REJECT | evidence:nonexistent_reference |

Visible context:

```text
P1: Electronic Component sales were $1,290.0 million for the fiscal year ended March 31, 2019 compared to $1,235.2 million during the fiscal year ended March 31, 2018.
The sales increase in Electronic Components product sales was driven by increased volume and a favorable pricing environment in our Ceramic and Tantalum
Components across most markets resulting from favorable global market conditions and increased demand for our electronic component products resulting from
technological advances across a broad range of industries driven by IoT and an increasingly connected world led by the automotive, industrial, telecommunications,
networking, and computer markets. Fiscal year 2019 Advanced Components group sales include $113.3 million of Ethertronics product as compared to $12.7 million for
fiscal year 2018. These increases were partially offset by the loss of Kyocera resale product sales which were $19.0 million for fiscal year 2019 as compared to $296.3
million for fiscal year 2018.

TABLE
columns: C0=Net sales (in thousands) | C1=2018 | C2=2019
R1 [Ceramic Components] C0=Ceramic Components | C1=$226,204 | C2=$421,849
R2 [Tantalum Components] C0=Tantalum Components | C1=366,194 | C2=382,905
R3 [Advanced Components] C0=Advanced Components | C1=642,775 | C2=485,208
R4 [Total Electronic Components] C0=Total Electronic Components | C1=1,235,173 | C2=1,289,962
R5 [Interconnect, Sensing and Control Devices] C0=Interconnect, Sensing and Control Devices | C1=327,301 | C2=501,828
R6 [Total Net Sales] C0=Total Net Sales | C1=$1,562,474 | C2=$1,791,790
```
