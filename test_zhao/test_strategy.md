# Test Strategy Document
Author: ZHAO Xiaojun (Member D, Test Lead)
Date: 2026-11-05

## 1 Test Objectives
In accordance with the course project requirements, test the campus secondhand goods trading management system:
1. Verify that all externally exposed backend business interfaces operate correctly in accordance with their specifications;
2. Verify that the system performs reasonable validation and handling of invalid inputs, boundary inputs, and unauthorized operations, without throwing uncaught exceptions or crashing;
3. Identify integration and business-logic defects as early as possible, record them, and track their remediation status;
4. Use unittest to implement automated coverage of backend business logic; conduct manual testing of the Tkinter GUI.

## 2 Test Scope and Categories
### 2.1 Automated Unit Tests (unittest)
Modules covered:
- backend_zhang: user module user_service, item module item_service (Member A)
- feature_du: FavoriteService, IntentionService, and MessageService (Member C)
Note: LogService was only designed and has no runnable code delivered, so it is not included in the automated testing scope.

### 2.2 Manual GUI Functional Testing
Modules covered: The Tkinter-based frontend GUI, including the complete business workflows for registration and login, item listing, browsing and searching, favoriting, messaging, submitting purchase intentions, and delisting and deleting items.


## 3 Test Case Design Approach
For each external interface, design three standard test scenarios:
1. **Positive/normal scenario**: Pass entirely valid parameters and verify that the business workflow succeeds and the returned data meets expectations;
2. **Boundary scenario**: Cover edge conditions, such as minimum and maximum username/password lengths, minimum price, and maximum description length;
3. **Exception/invalid scenario**: Empty inputs, whitespace-only content, non-positive-integer IDs, incorrect passwords, duplicate usernames, categories not on the allowlist, unauthorized modification of another user's item, and submitting a purchase intention for one's own item.

## 4 Data Isolation Strategy
To prevent test operations from contaminating the project's production business JSON files:
- Use `tempfile` to create a separate temporary directory, and automatically generate isolated temporary data files when each test class is initialized;
- Automatically delete the temporary directory and files after test execution;
- Ensure automated tests never read from or modify production data under `backend_zhang/data/`;
- Call `reset_user_service()` and `reset_item_service()` to bind the services to temporary files, thereby isolating test data.

## 5 Testing Tools and Environment Constraints
- Automation framework: Python's built-in `unittest`; do not use third-party testing frameworks such as pytest;
- Dependencies: Python standard library only; no additional third-party packages need to be installed via pip, ensuring compatibility with the course assignment environment;
- Entry point: `python -m test_zhao.test_all`.

## 6 Defect Management and Regression Strategy
1. Record discovered defects in the automated test report, including the defect ID, location, symptoms, severity, and remediation status;
2. After team members fix defects, run all automated test cases for regression testing;
3. Prioritize regression testing for high-severity interface-alignment defects to ensure interface behavior remains consistent with the specifications in API_spec.md.

## 7 Deliverables
1. `test_all.py`: automated test source code
2. `API_spec.md`: backend interface specification
3. `test_strategy.md`: test strategy document
4. `auto_test_record.md`: automated test execution log and bug tracking report