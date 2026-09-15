# Track-A controlled fault injection (production audit code; all Track-A-passing archived rows)

Base rows: 1619

| Fault type | expected | n | rejected | retained | rejection rate % | retention rate % | failing check(s) |
|---|---|---|---|---|---|---|---|
| wrong_pmid_in_corpus | reject | 1619 | 1619 | 0 | 100.0 | 0.0 | sentence_anchored=1619 |
| wrong_pmid_not_in_corpus | reject | 1619 | 1619 | 0 | 100.0 | 0.0 | citation_valid=1619, sentence_anchored=1619 |
| sentence_from_other_pmid | reject | 1619 | 1619 | 0 | 100.0 | 0.0 | sentence_anchored=1619 |
| number_changed | reject | 346 | 346 | 0 | 100.0 | 0.0 | sentence_anchored=346 |
| direction_word_changed | reject | 669 | 669 | 0 | 100.0 | 0.0 | sentence_anchored=669 |
| sentence_composed_two_abstracts | reject | 1614 | 1614 | 0 | 100.0 | 0.0 | sentence_anchored=1614 |
| word_dropped | reject | 1614 | 1614 | 0 | 100.0 | 0.0 | sentence_anchored=1614 |
| schema_missing_field | reject | 1619 | 1619 | 0 | 100.0 | 0.0 | schema_valid=1619 |
| schema_strength_out_of_range | reject | 1619 | 1619 | 0 | 100.0 | 0.0 | schema_valid=1619 |
| whitespace_variant | retain | 1619 | 0 | 1619 | 0.0 | 100.0 |  |
| nbsp_variant | retain | 1619 | 0 | 1619 | 0.0 | 100.0 |  |
| trailing_period_removed | retain | 1554 | 0 | 1554 | 0.0 | 100.0 |  |
| case_variant | surface | 1619 | 1618 | 1 | 99.9 | 0.1 | sentence_anchored=1618 |
| unicode_dash_quote_variant | surface | 865 | 865 | 0 | 100.0 | 0.0 | sentence_anchored=865 |
| truncated_quote | surface | 1590 | 0 | 1590 | 0.0 | 100.0 |  |
