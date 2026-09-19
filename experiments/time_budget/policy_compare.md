
## machine speed as assumed (k = 1)

### box/TSMS  n=1653

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9925 | 4.5% | 0.2% | 0.2% | 5.2 / 8.6 | 0.51 | 0% |
| A: time limit only, alpha=8 | 0.9958 | 1.5% | 0.0% | 0.0% | 13.2 / 21.6 | 1.18 | 1% |
| B: stagnation only, patience 3 s | 0.9927 | 3.8% | 0.7% | 0.7% | 5.8 / 8.6 | 0.56 | 0% |
| B: stagnation only, patience 5 s | 0.9945 | 1.9% | 0.7% | 0.7% | 8.9 / 13.6 | 0.81 | 0% |
| B: stagnation only, patience 10 s | 0.9973 | 0.8% | 0.5% | 0.5% | 16.5 / 25.0 | 1.87 | 8% |
| B_L: patience 5 s, not before predicted first solution | 0.9945 | 1.9% | 0.5% | 0.5% | 9.0 / 13.7 | 0.81 | 0% |
| B_L: patience 10 s, not before predicted first solution | 0.9973 | 0.8% | 0.5% | 0.5% | 16.5 / 25.0 | 1.87 | 8% |
| C: PR rule, alpha=4 | 0.9915 | 6.0% | 0.2% | 0.2% | 4.3 / 6.6 | 0.43 | 0% |
| C: PR rule, alpha=8 | 0.9949 | 1.9% | 0.2% | 0.2% | 10.3 / 18.3 | 0.96 | 0% |

### box/TS  n=80

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9720 | 27.5% | 3.8% | 0.0% | 1.3 / 1.3 | 0.53 | 0% |
| A: time limit only, alpha=8 | 0.9875 | 11.2% | 1.2% | 0.0% | 6.4 / 6.4 | 2.13 | 0% |
| B: stagnation only, patience 3 s | 0.9867 | 13.8% | 1.2% | 0.0% | 3.1 / 6.0 | 2.01 | 0% |
| B: stagnation only, patience 5 s | 0.9875 | 10.0% | 1.2% | 0.0% | 5.1 / 10.9 | 2.68 | 0% |
| B: stagnation only, patience 10 s | 0.9955 | 3.8% | 1.2% | 0.0% | 10.1 / 19.5 | 3.41 | 2% |
| B_L: patience 5 s, not before predicted first solution | 0.9875 | 10.0% | 1.2% | 0.0% | 5.1 / 10.9 | 2.68 | 0% |
| B_L: patience 10 s, not before predicted first solution | 0.9955 | 3.8% | 1.2% | 0.0% | 10.1 / 19.5 | 3.41 | 2% |
| C: PR rule, alpha=4 | 0.9720 | 27.5% | 3.8% | 0.0% | 1.3 / 1.3 | 0.53 | 0% |
| C: PR rule, alpha=8 | 0.9867 | 13.8% | 1.2% | 0.0% | 3.2 / 6.1 | 2.03 | 0% |

### boxstacks/SOR (Stowly-like)  n=49

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9886 | 16.3% | 0.0% | 0.0% | 25.4 / 78.5 | 1.02 | 18% |
| A: time limit only, alpha=8 | 0.9989 | 0.0% | 0.0% | 0.0% | 78.5 / 78.5 | 1.81 | 53% |
| B: stagnation only, patience 3 s | 0.0000 | 44.9% | 26.5% | 26.5% | 4.3 / 8.1 | 0.21 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 36.7% | 20.4% | 20.4% | 7.8 / 15.1 | 0.46 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 22.4% | 12.2% | 12.2% | 16.0 / 25.7 | 0.95 | 0% |
| B_L: patience 5 s, not before predicted first solution | 0.9549 | 26.5% | 8.2% | 8.2% | 9.8 / 23.8 | 0.61 | 0% |
| B_L: patience 10 s, not before predicted first solution | 0.9758 | 22.4% | 8.2% | 8.2% | 16.7 / 29.6 | 0.95 | 0% |
| C: PR rule, alpha=4 | 0.9886 | 16.3% | 0.0% | 0.0% | 20.8 / 78.5 | 1.00 | 14% |
| C: PR rule, alpha=8 | 0.9989 | 0.0% | 0.0% | 0.0% | 67.1 / 78.5 | 1.81 | 43% |

### box/SSK  n=55

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 1.0000 | 7.3% | 7.3% | 3.6% | 2.3 / 33.9 | 1.00 | 0% |
| A: time limit only, alpha=8 | 1.0000 | 7.3% | 7.3% | 3.6% | 2.3 / 33.9 | 1.00 | 0% |
| B: stagnation only, patience 3 s | 0.0000 | 41.8% | 41.8% | 36.4% | 2.3 / 3.0 | 1.00 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 30.9% | 30.9% | 25.5% | 2.3 / 5.0 | 1.00 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 23.6% | 23.6% | 21.8% | 2.3 / 10.0 | 1.00 | 0% |
| B_L: patience 5 s, not before predicted first solution | 1.0000 | 3.6% | 3.6% | 1.8% | 2.3 / 33.9 | 1.00 | 0% |
| B_L: patience 10 s, not before predicted first solution | 1.0000 | 3.6% | 3.6% | 1.8% | 2.3 / 33.9 | 1.00 | 0% |
| C: PR rule, alpha=4 | 1.0000 | 7.3% | 7.3% | 3.6% | 2.3 / 33.9 | 1.00 | 0% |
| C: PR rule, alpha=8 | 1.0000 | 7.3% | 7.3% | 3.6% | 2.3 / 33.9 | 1.00 | 0% |

### boxstacks/SVC  n=32

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 1.0000 | 3.1% | 3.1% | 3.1% | 34.8 / 80.0 | 1.00 | 6% |
| A: time limit only, alpha=8 | 1.0000 | 3.1% | 3.1% | 3.1% | 34.8 / 80.0 | 1.00 | 6% |
| B: stagnation only, patience 3 s | 0.0000 | 100.0% | 100.0% | 100.0% | 3.0 / 3.0 | 0.12 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 93.8% | 93.8% | 93.8% | 5.0 / 5.0 | 0.21 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 78.1% | 78.1% | 78.1% | 10.0 / 10.0 | 0.41 | 0% |
| B_L: patience 5 s, not before predicted first solution | 1.0000 | 3.1% | 3.1% | 3.1% | 34.8 / 80.0 | 1.00 | 6% |
| B_L: patience 10 s, not before predicted first solution | 1.0000 | 3.1% | 3.1% | 3.1% | 34.8 / 80.0 | 1.00 | 6% |
| C: PR rule, alpha=4 | 1.0000 | 3.1% | 3.1% | 3.1% | 34.8 / 80.0 | 1.00 | 6% |
| C: PR rule, alpha=8 | 1.0000 | 3.1% | 3.1% | 3.1% | 34.8 / 80.0 | 1.00 | 6% |

### Stowly-like all (demo+synthetic)  n=179

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9925 | 8.4% | 3.4% | 2.8% | 12.4 / 69.5 | 1.00 | 6% |
| A: time limit only, alpha=8 | 0.9998 | 1.7% | 1.7% | 1.1% | 23.7 / 78.5 | 1.00 | 22% |
| B: stagnation only, patience 3 s | 0.0000 | 49.7% | 44.7% | 43.0% | 3.0 / 8.1 | 0.30 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 42.5% | 38.0% | 36.3% | 5.0 / 12.4 | 0.55 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 31.8% | 29.1% | 28.5% | 10.0 / 22.2 | 1.00 | 0% |
| B_L: patience 5 s, not before predicted first solution | 0.9800 | 14.5% | 8.9% | 8.4% | 9.3 / 37.5 | 1.00 | 1% |
| B_L: patience 10 s, not before predicted first solution | 0.9839 | 12.3% | 8.4% | 7.8% | 12.4 / 46.9 | 1.00 | 1% |
| C: PR rule, alpha=4 | 0.9925 | 8.4% | 3.9% | 3.4% | 9.7 / 58.0 | 1.00 | 5% |
| C: PR rule, alpha=8 | 0.9979 | 3.4% | 3.4% | 2.8% | 17.8 / 78.5 | 1.00 | 16% |

## machine 2x slower than assumed

### box/TSMS  n=1653

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9889 | 13.9% | 0.3% | 0.2% | 5.2 / 8.6 | 0.25 | 0% |
| A: time limit only, alpha=8 | 0.9932 | 3.8% | 0.2% | 0.2% | 13.2 / 21.6 | 0.63 | 0% |
| B: stagnation only, patience 3 s | 0.9903 | 9.0% | 1.1% | 1.1% | 7.1 / 10.1 | 0.37 | 0% |
| B: stagnation only, patience 5 s | 0.9920 | 5.0% | 0.8% | 0.8% | 10.2 / 14.9 | 0.52 | 0% |
| B: stagnation only, patience 10 s | 0.9945 | 1.9% | 0.7% | 0.7% | 17.9 / 27.3 | 0.81 | 0% |
| B_L: patience 5 s, not before predicted first solution | 0.9921 | 4.9% | 0.7% | 0.7% | 10.2 / 14.9 | 0.52 | 0% |
| B_L: patience 10 s, not before predicted first solution | 0.9945 | 1.9% | 0.7% | 0.7% | 17.9 / 27.3 | 0.81 | 0% |
| C: PR rule, alpha=4 | 0.9874 | 18.1% | 4.5% | 4.4% | 4.8 / 7.9 | 0.22 | 0% |
| C: PR rule, alpha=8 | 0.9926 | 4.3% | 0.2% | 0.2% | 11.2 / 18.8 | 0.55 | 0% |

### box/TS  n=80

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9630 | 31.2% | 3.8% | 0.0% | 1.3 / 1.3 | 0.26 | 0% |
| A: time limit only, alpha=8 | 0.9792 | 15.0% | 2.5% | 0.0% | 6.4 / 6.4 | 1.07 | 0% |
| B: stagnation only, patience 3 s | 0.9772 | 23.8% | 3.8% | 0.0% | 3.1 / 5.3 | 0.83 | 0% |
| B: stagnation only, patience 5 s | 0.9867 | 15.0% | 1.2% | 0.0% | 5.2 / 10.1 | 1.84 | 0% |
| B: stagnation only, patience 10 s | 0.9875 | 10.0% | 1.2% | 0.0% | 10.2 / 21.8 | 2.68 | 0% |
| B_L: patience 5 s, not before predicted first solution | 0.9867 | 15.0% | 1.2% | 0.0% | 5.2 / 10.1 | 1.84 | 0% |
| B_L: patience 10 s, not before predicted first solution | 0.9875 | 10.0% | 1.2% | 0.0% | 10.2 / 21.8 | 2.68 | 0% |
| C: PR rule, alpha=4 | 0.9630 | 31.2% | 3.8% | 0.0% | 1.3 / 1.3 | 0.26 | 0% |
| C: PR rule, alpha=8 | 0.9772 | 23.8% | 3.8% | 0.0% | 3.2 / 5.4 | 0.84 | 0% |

### boxstacks/SOR (Stowly-like)  n=49

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9844 | 28.6% | 0.0% | 0.0% | 25.4 / 145.9 | 0.69 | 8% |
| A: time limit only, alpha=8 | 0.9950 | 2.0% | 0.0% | 0.0% | 85.5 / 157.1 | 1.32 | 31% |
| B: stagnation only, patience 3 s | 0.0000 | 61.2% | 34.7% | 32.7% | 3.9 / 9.1 | 0.12 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 46.9% | 30.6% | 30.6% | 6.6 / 14.0 | 0.18 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 36.7% | 20.4% | 20.4% | 15.7 / 30.3 | 0.46 | 0% |
| B_L: patience 5 s, not before predicted first solution | 0.0000 | 36.7% | 14.3% | 14.3% | 10.1 / 22.5 | 0.31 | 0% |
| B_L: patience 10 s, not before predicted first solution | 0.0000 | 28.6% | 12.2% | 12.2% | 19.1 / 32.5 | 0.55 | 0% |
| C: PR rule, alpha=4 | 0.9827 | 30.6% | 2.0% | 2.0% | 21.2 / 107.0 | 0.69 | 8% |
| C: PR rule, alpha=8 | 0.9934 | 6.1% | 0.0% | 0.0% | 67.7 / 157.1 | 1.32 | 27% |

### box/SSK  n=55

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.0000 | 18.2% | 18.2% | 10.9% | 4.6 / 60.2 | 1.00 | 0% |
| A: time limit only, alpha=8 | 0.0000 | 18.2% | 18.2% | 10.9% | 4.6 / 60.2 | 1.00 | 0% |
| B: stagnation only, patience 3 s | 0.0000 | 58.2% | 58.2% | 50.9% | 3.0 / 3.1 | 0.65 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 45.5% | 45.5% | 38.2% | 4.6 / 5.0 | 1.00 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 30.9% | 30.9% | 25.5% | 4.6 / 10.0 | 1.00 | 0% |
| B_L: patience 5 s, not before predicted first solution | 0.5000 | 12.7% | 12.7% | 7.3% | 4.6 / 60.2 | 1.00 | 0% |
| B_L: patience 10 s, not before predicted first solution | 0.5000 | 10.9% | 10.9% | 7.3% | 4.6 / 60.2 | 1.00 | 0% |
| C: PR rule, alpha=4 | 0.0000 | 18.2% | 18.2% | 10.9% | 4.6 / 60.2 | 1.00 | 0% |
| C: PR rule, alpha=8 | 0.0000 | 18.2% | 18.2% | 10.9% | 4.6 / 60.2 | 1.00 | 0% |

### boxstacks/SVC  n=32

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.0000 | 34.4% | 34.4% | 34.4% | 57.3 / 80.0 | 1.00 | 0% |
| A: time limit only, alpha=8 | 0.0000 | 34.4% | 34.4% | 34.4% | 57.3 / 80.0 | 1.00 | 0% |
| B: stagnation only, patience 3 s | 0.0000 | 100.0% | 100.0% | 100.0% | 3.0 / 3.0 | 0.06 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 100.0% | 100.0% | 100.0% | 5.0 / 5.0 | 0.10 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 93.8% | 93.8% | 93.8% | 10.0 / 10.0 | 0.21 | 0% |
| B_L: patience 5 s, not before predicted first solution | 0.0000 | 34.4% | 34.4% | 34.4% | 57.3 / 80.0 | 1.00 | 0% |
| B_L: patience 10 s, not before predicted first solution | 0.0000 | 31.2% | 31.2% | 31.2% | 57.3 / 80.0 | 1.00 | 0% |
| C: PR rule, alpha=4 | 0.0000 | 34.4% | 34.4% | 34.4% | 57.3 / 80.0 | 1.00 | 0% |
| C: PR rule, alpha=8 | 0.0000 | 34.4% | 34.4% | 34.4% | 57.3 / 80.0 | 1.00 | 0% |

### Stowly-like all (demo+synthetic)  n=179

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.0000 | 21.8% | 12.3% | 11.2% | 13.3 / 72.5 | 1.00 | 2% |
| A: time limit only, alpha=8 | 0.0000 | 12.3% | 11.7% | 10.6% | 30.4 / 152.8 | 1.00 | 9% |
| B: stagnation only, patience 3 s | 0.0000 | 64.2% | 54.7% | 52.5% | 3.0 / 7.1 | 0.14 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 51.4% | 46.9% | 45.3% | 5.0 / 11.5 | 0.22 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 42.5% | 38.0% | 36.3% | 10.0 / 24.8 | 0.55 | 0% |
| B_L: patience 5 s, not before predicted first solution | 0.0000 | 26.3% | 20.1% | 19.0% | 10.0 / 61.5 | 1.00 | 0% |
| B_L: patience 10 s, not before predicted first solution | 0.0000 | 22.9% | 18.4% | 17.3% | 14.1 / 62.7 | 1.00 | 0% |
| C: PR rule, alpha=4 | 0.0000 | 27.4% | 17.9% | 16.8% | 12.8 / 71.2 | 1.00 | 2% |
| C: PR rule, alpha=8 | 0.0000 | 14.0% | 12.3% | 11.2% | 21.0 / 122.8 | 1.00 | 8% |

## machine 0.5x slower than assumed

### box/TSMS  n=1653

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9950 | 1.8% | 0.0% | 0.0% | 5.2 / 8.6 | 1.00 | 0% |
| A: time limit only, alpha=8 | 1.0000 | 0.5% | 0.0% | 0.0% | 13.0 / 13.0 | 1.98 | 50% |
| B: stagnation only, patience 3 s | 0.9951 | 1.5% | 0.7% | 0.7% | 5.2 / 8.0 | 1.00 | 0% |
| B: stagnation only, patience 5 s | 0.9973 | 0.8% | 0.5% | 0.5% | 8.3 / 12.5 | 1.87 | 8% |
| B: stagnation only, patience 10 s | 1.0000 | 0.2% | 0.2% | 0.2% | 13.0 / 13.0 | 2.26 | 68% |
| B_L: patience 5 s, not before predicted first solution | 0.9973 | 0.5% | 0.2% | 0.2% | 8.3 / 12.6 | 1.87 | 8% |
| B_L: patience 10 s, not before predicted first solution | 1.0000 | 0.2% | 0.2% | 0.2% | 13.0 / 13.0 | 2.26 | 68% |
| C: PR rule, alpha=4 | 0.9940 | 2.5% | 0.2% | 0.2% | 4.0 / 6.6 | 0.71 | 0% |
| C: PR rule, alpha=8 | 0.9975 | 0.7% | 0.0% | 0.0% | 9.9 / 13.0 | 1.91 | 27% |

### box/TS  n=80

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9775 | 17.5% | 3.8% | 0.0% | 1.3 / 1.3 | 0.90 | 0% |
| A: time limit only, alpha=8 | 0.9921 | 7.5% | 1.2% | 0.0% | 6.4 / 6.4 | 3.02 | 0% |
| B: stagnation only, patience 3 s | 0.9875 | 10.0% | 1.2% | 0.0% | 3.1 / 6.2 | 2.42 | 0% |
| B: stagnation only, patience 5 s | 0.9955 | 3.8% | 1.2% | 0.0% | 5.1 / 9.8 | 3.37 | 2% |
| B: stagnation only, patience 10 s | 1.0000 | 1.2% | 1.2% | 0.0% | 10.1 / 13.8 | 5.75 | 25% |
| B_L: patience 5 s, not before predicted first solution | 0.9955 | 3.8% | 1.2% | 0.0% | 5.1 / 9.8 | 3.37 | 2% |
| B_L: patience 10 s, not before predicted first solution | 1.0000 | 1.2% | 1.2% | 0.0% | 10.1 / 13.8 | 5.75 | 25% |
| C: PR rule, alpha=4 | 0.9775 | 17.5% | 3.8% | 0.0% | 1.3 / 1.3 | 0.90 | 0% |
| C: PR rule, alpha=8 | 0.9875 | 10.0% | 1.2% | 0.0% | 3.2 / 6.3 | 2.46 | 0% |

### boxstacks/SOR (Stowly-like)  n=49

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9969 | 0.0% | 0.0% | 0.0% | 25.4 / 39.3 | 1.44 | 33% |
| A: time limit only, alpha=8 | 1.0000 | 0.0% | 0.0% | 0.0% | 39.3 / 39.3 | 2.47 | 65% |
| B: stagnation only, patience 3 s | 0.0000 | 36.7% | 20.4% | 20.4% | 4.6 / 8.2 | 0.50 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 22.4% | 12.2% | 12.2% | 8.0 / 12.8 | 0.95 | 0% |
| B: stagnation only, patience 10 s | 0.9886 | 14.3% | 0.0% | 0.0% | 15.7 / 23.6 | 1.73 | 0% |
| B_L: patience 5 s, not before predicted first solution | 0.9811 | 18.4% | 0.0% | 0.0% | 10.1 / 18.6 | 0.96 | 2% |
| B_L: patience 10 s, not before predicted first solution | 0.9886 | 12.2% | 0.0% | 0.0% | 15.8 / 31.2 | 1.81 | 2% |
| C: PR rule, alpha=4 | 0.9950 | 6.1% | 0.0% | 0.0% | 17.8 / 39.3 | 1.44 | 29% |
| C: PR rule, alpha=8 | 0.9995 | 0.0% | 0.0% | 0.0% | 39.3 / 39.3 | 2.47 | 53% |

### box/SSK  n=55

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 1.0000 | 5.5% | 5.5% | 1.8% | 1.1 / 18.6 | 1.00 | 2% |
| A: time limit only, alpha=8 | 1.0000 | 5.5% | 5.5% | 1.8% | 1.1 / 18.6 | 1.00 | 2% |
| B: stagnation only, patience 3 s | 0.0000 | 29.1% | 29.1% | 23.6% | 1.2 / 3.0 | 1.00 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 23.6% | 23.6% | 21.8% | 1.2 / 5.0 | 1.00 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 18.2% | 18.2% | 18.2% | 1.2 / 10.0 | 1.00 | 0% |
| B_L: patience 5 s, not before predicted first solution | 1.0000 | 3.6% | 3.6% | 1.8% | 1.2 / 18.6 | 1.00 | 2% |
| B_L: patience 10 s, not before predicted first solution | 1.0000 | 1.8% | 1.8% | 1.8% | 1.2 / 18.6 | 1.00 | 2% |
| C: PR rule, alpha=4 | 1.0000 | 5.5% | 5.5% | 1.8% | 1.1 / 18.6 | 1.00 | 2% |
| C: PR rule, alpha=8 | 1.0000 | 5.5% | 5.5% | 1.8% | 1.1 / 18.6 | 1.00 | 2% |

### boxstacks/SVC  n=32

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 1.0000 | 0.0% | 0.0% | 0.0% | 17.4 / 67.1 | 1.00 | 16% |
| A: time limit only, alpha=8 | 1.0000 | 0.0% | 0.0% | 0.0% | 17.4 / 67.1 | 1.00 | 16% |
| B: stagnation only, patience 3 s | 0.0000 | 93.8% | 93.8% | 93.8% | 3.0 / 3.0 | 0.25 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 78.1% | 78.1% | 78.1% | 5.0 / 5.0 | 0.41 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 56.2% | 56.2% | 56.2% | 10.0 / 10.0 | 0.83 | 0% |
| B_L: patience 5 s, not before predicted first solution | 1.0000 | 0.0% | 0.0% | 0.0% | 17.4 / 67.1 | 1.00 | 16% |
| B_L: patience 10 s, not before predicted first solution | 1.0000 | 0.0% | 0.0% | 0.0% | 17.4 / 67.1 | 1.00 | 16% |
| C: PR rule, alpha=4 | 1.0000 | 0.0% | 0.0% | 0.0% | 17.4 / 67.1 | 1.00 | 16% |
| C: PR rule, alpha=8 | 1.0000 | 0.0% | 0.0% | 0.0% | 17.4 / 67.1 | 1.00 | 16% |

### Stowly-like all (demo+synthetic)  n=179

| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |
|---|---|---|---|---|---|---|---|
| A: time limit only, alpha=4 | 0.9992 | 1.1% | 1.1% | 0.6% | 9.4 / 39.3 | 1.00 | 14% |
| A: time limit only, alpha=8 | 1.0000 | 1.1% | 1.1% | 0.6% | 15.4 / 39.3 | 1.00 | 32% |
| B: stagnation only, patience 3 s | 0.0000 | 41.9% | 37.4% | 35.8% | 3.0 / 6.8 | 0.65 | 0% |
| B: stagnation only, patience 5 s | 0.0000 | 31.8% | 29.1% | 28.5% | 5.0 / 11.1 | 1.00 | 0% |
| B: stagnation only, patience 10 s | 0.0000 | 21.8% | 17.9% | 17.9% | 10.0 / 23.6 | 1.00 | 5% |
| B_L: patience 5 s, not before predicted first solution | 0.9946 | 7.8% | 2.8% | 2.2% | 7.7 / 26.3 | 1.00 | 4% |
| B_L: patience 10 s, not before predicted first solution | 0.9969 | 5.6% | 2.2% | 2.2% | 11.8 / 32.5 | 1.00 | 9% |
| C: PR rule, alpha=4 | 0.9969 | 4.5% | 2.8% | 2.2% | 6.8 / 39.3 | 1.00 | 12% |
| C: PR rule, alpha=8 | 1.0000 | 1.1% | 1.1% | 0.6% | 13.3 / 39.3 | 1.00 | 28% |