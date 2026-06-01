import os
import re

def check_file_exists(filepath):
    exists = os.path.exists(filepath)
    print(f"[CHECK] {filepath} exists: {exists}")
    return exists

def check_version_sync():
    with open('VERSION.md', 'r') as f:
        version = f.read().strip()

    with open('CHANGELOG.md', 'r') as f:
        changelog = f.read()

    # Look for the latest version in changelog (e.g., ## [6.6.1])
    match = re.search(r'## \[([\d\.]+)\]', changelog)
    if match:
        latest_changelog_version = match.group(1)
        sync = version == latest_changelog_version
        print(f"[CHECK] Version Sync (VERSION.md: {version}, CHANGELOG.md: {latest_changelog_version}): {sync}")
        return sync
    else:
        print("[CHECK] Version Sync: FAILED (No version found in CHANGELOG.md)")
        return False

def check_documentation_suite():
    required_docs = ['ROADMAP.md', 'TODO.md', 'MEMORY.md', 'HANDOFF.md', 'GOVERNANCE.md', 'VISION.md']
    all_exist = all(check_file_exists(doc) for doc in required_docs)
    print(f"[CHECK] Documentation Suite Complete: {all_exist}")
    return all_exist

def check_log_hygiene():
    with open('app.py', 'r') as f:
        content = f.read()

    has_rotation = 'RotatingFileHandler' in content
    print(f"[CHECK] Log Rotation (app.py): {has_rotation}")
    return has_rotation

def run_compliance_tests():
    print("=== StepManiaX B2B Governance Compliance Tests ===")
    results = [
        check_version_sync(),
        check_documentation_suite(),
        check_log_hygiene()
    ]

    if all(results):
        print("\n✅ GOVERNANCE COMPLIANCE VERIFIED")
    else:
        print("\n❌ GOVERNANCE COMPLIANCE FAILED")
        exit(1)

if __name__ == "__main__":
    run_compliance_tests()
