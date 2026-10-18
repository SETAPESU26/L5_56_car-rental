
# Lab 5: Static Code Analysis — Reflection

## 1. What is static code analysis?

Static code analysis examines source code without executing it to identify potential bugs, security vulnerabilities, and coding-style problems.

## 2. What are the differences between Pylint, Bandit, and Flake8?

- Pylint checks code quality, naming conventions, documentation, and potential programming errors.
- Bandit identifies common security vulnerabilities in Python code.
- Flake8 checks Python formatting and style violations.

## 3. What issues were identified and fixed?

The initial analysis identified SQL injection risks, unsafe dynamic code execution, weak hashing, insecure temporary-file handling, and style violations. I also corrected logical problems involving negative rental prices, invalid rental dates, and duplicate bookings.

## 4. How did static analysis improve the program?

Static analysis helped identify security weaknesses and improve code readability and maintainability. After making the changes, Pylint reported 10.00/10, Bandit reported no issues, and Flake8 reported no violations.
