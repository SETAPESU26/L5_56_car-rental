
# Lab 5: Static Code Analysis — Issues Report

## Initial Analysis

- Pylint score: 4.94/10
- Bandit: 11 potential issues reported
- Flake8: Multiple formatting and style violations

## Issues Identified and Fixes Applied

| Issue | Type | Line(s) Before Fix | Description | Fix Approach |
|---|---|---:|---|---|
| Weak SHA-1 hashing | Security — High | 48 | SHA-1 is unsuitable for modern security-sensitive hashing. | Replaced SHA-1 with SHA-256. |
| Insecure file permissions | Security — High | 67 | Setting permissions to 0o777 allows excessive file access. | Removed the permissive chmod operation. |
| Dynamic code execution | Security — Medium | 53 | exec() can execute arbitrary code from a supplied rule. | Replaced exec() with predefined promotion rules. |
| SQL injection in customer registration | Security — Medium | 23 | String interpolation allows SQL input to alter a query. | Used parameterized SQL queries. |
| SQL injection in customer lookup | Security — Medium | 26 | User input was concatenated into an SQL statement. | Used a parameterized SELECT query. |
| Unsafe temporary-file creation | Security — Medium | 63 | tempfile.mktemp() can create a race condition. | Used NamedTemporaryFile() with delete=False. |
| Mutable default argument | Code quality | 16 | The default features list could be shared between calls. | Used None and created a new list for each car. |
| Bare exception handler | Code quality | 41 | A bare except hides unexpected errors. | Removed the broad exception handler and explicitly validated returns. |
| Invalid rental dates | Logic bug | 31 | End dates earlier than start dates could produce negative costs. | Validated that the rental duration is positive. |
| Negative daily rate | Logic bug | 18–19 | A negative rate could produce an invalid rental price. | Rejected negative daily rates. |
| Duplicate rental booking | Logic bug | 29–34 | The same car could be rented again without checking availability. | Checked availability and marked the car unavailable after booking. |
| Hardcoded admin password | Security | 70–71 | Credentials were embedded in the source code. | Read the password from an environment variable and used constant-time comparison. |
| Poor naming and missing documentation | Style | Multiple | Function names did not follow snake_case and functions lacked docstrings. | Renamed functions and added docstrings. |
| Formatting violations | Style | Multiple | Unused imports, long lines, spacing issues, and Boolean comparisons violated style rules. | Removed unused imports and corrected formatting. |

## Verification After Fixes

- Pylint: 10.00/10
- Bandit: No issues identified
- Flake8: No reported violations

The program was executed after the fixes. It rejected invalid rental dates, negative car rates, duplicate bookings, and SQL injection input.
