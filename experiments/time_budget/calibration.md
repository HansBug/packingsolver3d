# Load calibration: 80 instances rerun on the idle machine (2 slots)

| solver/path | n | first-solution ratio load/idle p25 / p50 / p75 | time-to-99% ratio p50 (n) | idle cores per solve p50 |
|---|---|---|---|---|
| box/SSK | 9 | 1.08 / 1.14 / 1.23 | 1.18 (9) | 1.0 |
| box/SVC | 3 | 1.53 / 1.53 / 1.87 | 1.53 (2) | 6.3 |
| box/TS | 6 | nan / nan / nan | 1.76 (2) | 6.0 |
| box/TSMS | 36 | 2.16 / 2.31 / 2.42 | 2.22 (36) | 1.0 |
| boxstacks/SOR | 18 | 1.81 / 1.91 / 2.57 | 2.34 (9) | 1.3 |
| boxstacks/SVC | 8 | 1.05 / 1.12 / 1.33 | 1.12 (8) | 1.0 |
| all (first solution > 50 ms) | 63 | 1.70 / 2.17 / 2.40 | | |
