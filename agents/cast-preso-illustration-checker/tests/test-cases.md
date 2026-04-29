# Test Cases: taskos-preso-illustration-checker

| # | Scenario | Input | Expected Verdict | Validates |
|---|----------|-------|------------------|-----------|
| TC-4B-1 | Pass 1 reject — wrong subject | Image of a cat when brief says "architecture diagram" | RESTART | Pass 1 check 1.1, RESTART action |
| TC-4B-2 | Pass 1 reject — garbled text | Image with visible misspelled text | CONTINUE (pass 1) | Text detection |
| TC-4B-3 | Pass 2 element count mismatch | Diagram with 3 nodes, brief says 4 | CONTINUE with structured feedback | Accuracy audit, feedback format |
| TC-4B-4 | Pass 3 style drift | Digital art aesthetic vs watercolor anchor | CONTINUE with style feedback | Style consistency check |
| TC-4B-5 | All passes pass | Clean watercolor matching brief | STOP | Happy path, approval |
| TC-4B-6 | Oscillation detection | Iter 2 fixes color, breaks layout (iter 1 fixed layout) | ESCALATE | Oscillation trigger |
| TC-4B-7 | Budget exhaustion | 4th iteration of complex, still failing Pass 2 | ESCALATE | Budget enforcement |
| TC-4B-8 | Regression detection | Iter 2 worse on multiple dimensions vs iter 1 | BACKTRACK | BACKTRACK action |
| TC-4B-9 | Cross-deck consistency | 4 illustrations, one with different palette | Flag outlier, NOT modify Style Bible | Cross-deck protocol |
| TC-4B-10 | what_worked field | Any failing illustration | Non-empty what_worked | Mandatory positive feedback |
| TC-4B-11 | Vision-first protocol | Any illustration | blind_description present, describes BEFORE evaluating | Describe-then-judge enforcement |
| TC-4B-12 | Communication value fail | Pretty illustration that doesn't match Slot 6 | ESCALATE (3.4 fail) | Decorative vs communicative |
