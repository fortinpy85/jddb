#!/usr/bin/env python3

import re

# Test patterns
FILENAME_PATTERNS = [
    # New pattern: "EX-01 Dir, Business Analysis 103249 - JD.txt"
    re.compile(
        r"(?P<classification>EX-\d{2})\s+(?P<title>[^0-9]+?)\s+(?P<job_number>\d+)\s*-\s*(?P<lang_code>JD|DE)\.(?P<extension>\w+)$",
        re.IGNORECASE,
    ),
    # Pattern for SJD files with language code: "EX-01 SJD Director, Special Projects EN.docx"
    re.compile(
        r"(?P<classification>EX-\d{2})\s+(?P<title>.+?)\s+(?P<lang_code>EN|FR)\.(?P<extension>\w+)$",
        re.IGNORECASE,
    ),
    # Legacy pattern: "JD_EX-01_123456_Director.txt"
    re.compile(
        r"(?P<lang_code>JD|DE)_(?P<classification>EX-\d{2})_(?P<job_number>\d+)_?(?P<title>.*)?\.(?P<extension>\w+)$",
        re.IGNORECASE,
    ),
    # Flexible pattern for variations: "Director Business Analysis EX-01 103249.txt"
    re.compile(
        r"(?P<title>.+?)\s+(?P<classification>EX-\d{2})\s+(?P<job_number>\d+)(?:\s*-\s*(?P<lang_code>JD|DE))?\.(?P<extension>\w+)$",
        re.IGNORECASE,
    ),
]

# Test filenames
test_filenames = [
    "EX-01 SJD Director, Special Projects EN.docx",
    "EX-02 SJD Executive Director, Special Projects EN.docx",
    "EX-03 SJD DG Special Projects EN.docx",
]

print("Testing filename patterns...")
for filename in test_filenames:
    print(f"\nTesting: {filename}")
    match_found = False

    for i, pattern in enumerate(FILENAME_PATTERNS):
        match = pattern.match(filename)
        if match:
            groups = match.groupdict()
            print(f"  [OK] Pattern {i + 1} matched!")
            print(f"     Classification: {groups.get('classification')}")
            print(f"     Title: {groups.get('title')}")
            print(f"     Job Number: {groups.get('job_number')}")
            print(f"     Language: {groups.get('lang_code')}")
            print(f"     Extension: {groups.get('extension')}")
            match_found = True
            break

    if not match_found:
        print("  [FAIL] No pattern matched")
