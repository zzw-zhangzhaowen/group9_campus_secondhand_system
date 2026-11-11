# Test Strategy Document
Author: ZHAO Xiaojun
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
- backend_zhang: user module `user_service`, item module `item_service` (developed by Member A)
- feature_du: `FavoriteService`, `IntentionService`, and `MessageService` (developed by Member C)
Note: LogService was only designed and has no runnable delivered implementation, so it is excluded from automated testing.

### 2.2 Manual GUI Functional Testing
Modules covered: The Tkinter-based frontend GUI, including complete business workflows for registration and login, item publishing, browsing and searching, favoriting, messaging, submitting purchase intentions, and delisting and deleting items.

## 3 Test Case Design Approach
For each external interface, three standard categories of test scenarios are designed:
1. **Positive/normal scenario**: Pass fully valid parameters and verify that the business workflow succeeds and returned data matches expectations;
2. **Boundary scenario**: Cover edge conditions, such as minimum and maximum username or password length, minimum valid price, and maximum description length;
3. **Exception/invalid scenario**: Empty inputs, whitespace-only content, non-positive integer IDs, incorrect passwords, duplicate usernames, categories outside the allowlist, unauthorized modification of another user’s item, and submitting a purchase intention for one’s own item.

## 4 Data Isolation Strategy
To prevent test operations from contaminating the project’s production JSON data files:
- Use `tempfile` to create an independent temporary directory; isolated temporary data files are automatically created when each test class initializes;
- The temporary directory and all its files are automatically removed after the test finishes;
- Automated tests never read from or modify production data stored under `backend_zhang/data/`;
- Rebind `user_service` and `item_service` to temporary data sources to fully isolate test data from production data.

## 5 Testing Tools and Environment Constraints
- Automation framework: Python’s built-in `unittest`; third-party frameworks such as pytest are not permitted;
- Dependencies: Only Python standard library modules are used. No extra packages need to be installed via pip, guaranteeing compatibility with the course assignment environment;
- Execution entry point: `python -m test_zhao.test_all`.

## 6 Defect Management and Regression Strategy
1. All discovered defects are logged in the automated test record, including defect ID, location, symptoms, severity level, and resolution status;
2. After team members fix defects or adjust their modules, the full automated test suite is re-run for regression verification;
3. High-severity defects related to interface consistency are prioritized during regression, to ensure runtime behavior matches the rules defined in `API_spec.md`;
4. After Member A and Member C completed their final code adjustments, a dedicated final regression run was performed to confirm no new failures were introduced.

## 7 Deliverables
1. `test_all.py`: Automated test source code
2. `API_spec.md`: Backend interface specification
3. `test_strategy.md`: This test strategy document
4. `auto_test_record.md`: Automated test execution log and bug tracking report
