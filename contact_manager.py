#!/usr/bin/env python3
"""
Name: Ravi Kumar
Date: 2025-11-14
Project: Contact Book Manager
Roll No: 2501940047
Description:
 Advanced contact manager with validation, duplicates merge, tags, favorites,
 undo, backups, bulk import, regex search, sort, and vCard export along with CSV/JSON.
"""

import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime
from difflib import SequenceMatcher, get_close_matches
from typing import List, Dict, Optional
from pathlib import Path

CSV_FILE = "contacts.csv"
JSON_FILE = "contacts.json"
ERROR_LOG = "error_log.txt"
BACKUP_DIR = "backups"
PREV_SNAPSHOT = ".prev_contacts_snapshot.json"
CSV_FIELDS = ["name", "phone", "email", "tags", "favorite"]


def log_error(operation: str, exc: Exception) -> None:
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] Operation: {operation}\n")
            f.write(f"Error: {type(exc).__name__}: {exc}\n")
            f.write("-" * 60 + "\n")
    except Exception:
        print("Could not write to error log.", file=sys.stderr)


def safe_makedirs(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        log_error("safe_makedirs", e)


def snapshot_before_write(contacts: List[Dict[str, str]]) -> None:
    try:
        with open(PREV_SNAPSHOT, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_error("snapshot_before_write", e)


def load_prev_snapshot() -> Optional[List[Dict[str, str]]]:
    try:
        if not os.path.isfile(PREV_SNAPSHOT):
            return None
        with open(PREV_SNAPSHOT, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_error("load_prev_snapshot", e)
        return None


PHONE_RE = re.compile(r"^\+?\d{7,15}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z0-9]{2,}$")


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return digits 


def is_valid_phone(phone: str) -> bool:
    p = normalize_phone(phone)
    return 7 <= len(p) <= 15


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ""))


def ensure_csv_exists() -> None:
    if not os.path.isfile(CSV_FILE):
        try:
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
        except Exception as e:
            log_error("ensure_csv_exists", e)
            print("Unable to create contacts file. See error_log.txt for details.")


def read_contacts() -> List[Dict[str, str]]:
    contacts = []
    try:
        with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                contact = {k: (row.get(k, "").strip() if row.get(k, "") is not None else "") for k in CSV_FIELDS}
                if contact.get("name"):
                    contact["tags"] = contact.get("tags", "")
                    contact["favorite"] = contact.get("favorite", "").strip().lower() in ("1", "true", "yes", "y")
                    contacts.append(contact)
    except FileNotFoundError:
        pass
    except Exception as e:
        log_error("read_contacts", e)
        print("Error reading contacts. See error_log.txt for details.")
    return contacts


def write_contacts(contacts: List[Dict[str, str]]) -> None:
    try:
        safe_makedirs(BACKUP_DIR)
        try:
            old = read_contacts()
            snapshot_before_write(old)
        except Exception as e:
            log_error("snapshot_before_write_in_write_contacts", e)

        today_str = datetime.now().strftime("%Y%m%d")
        existing_for_today = False
        try:
            for fname in os.listdir(BACKUP_DIR):
                if fname.startswith(f"contacts_backup_{today_str}_") and fname.endswith(".csv"):
                    existing_for_today = True
                    break
        except FileNotFoundError:
            existing_for_today = False
        except Exception as e:
            log_error("check_existing_backups", e)

        if not existing_for_today and os.path.isfile(CSV_FILE):
            try:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                shutil.copy2(CSV_FILE, os.path.join(BACKUP_DIR, f"contacts_backup_{ts}.csv"))
            except Exception as e:
                log_error("create_daily_backup", e)
            
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for c in contacts:
                row = {
                    "name": c.get("name", ""),
                    "phone": c.get("phone", ""),
                    "email": c.get("email", ""),
                    "tags": c.get("tags", ""),
                    "favorite": "1" if c.get("favorite") else "0",
                }
                writer.writerow(row)
    except Exception as e:
        log_error("write_contacts", e)
        print("Error saving contacts. See error_log.txt for details.")




def display_contacts(contacts: List[Dict[str, str]], sort_by: str = "name") -> None:
    if not contacts:
        print("\nNo contacts found.\n")
        return
    if sort_by in ("name", "phone", "email"):
        contacts = sorted(contacts, key=lambda x: (x.get(sort_by) or "").lower())
    elif sort_by == "favorite":
        contacts = sorted(contacts, key=lambda x: not bool(x.get("favorite")))
    name_w = max(len("Name"), *(len(c.get("name", "")) for c in contacts))
    phone_w = max(len("Phone"), *(len(c.get("phone", "")) for c in contacts))
    email_w = max(len("Email"), *(len(c.get("email", "")) for c in contacts))
    tags_w = max(len("Tags"), *(len(c.get("tags", "")) for c in contacts))
    header = f"{'Fav':3}\t{'Name':<{name_w}}\t{'Phone':<{phone_w}}\t{'Email':<{email_w}}\t{'Tags':<{tags_w}}"
    print()
    print(header)
    print("-" * (len(header) + 10))
    for c in contacts:
        fav = "*" if c.get("favorite") else " "
        print(f"{fav:3}\t{c.get('name',''):<{name_w}}\t{c.get('phone',''):<{phone_w}}\t{c.get('email',''):<{email_w}}\t{c.get('tags',''):<{tags_w}}")
    print()


def find_by_name_exact(contacts: List[Dict[str, str]], name: str) -> Optional[Dict[str, str]]:
    for c in contacts:
        if c.get("name", "").lower() == name.lower():
            return c
    return None


def add_contact_interactive() -> None:
    try:
        name = input("Enter name: ").strip()
        if not name:
            print("Name cannot be empty.")
            return
        phone = input("Enter phone number: ").strip()
        email = input("Enter email address: ").strip()
        tags = input("Tags (comma-separated, optional): ").strip()
        fav = input("Mark favorite? (y/N): ").strip().lower() in ("y", "yes")
        phone_n = normalize_phone(phone)
        if phone and not is_valid_phone(phone):
            print("Warning: phone looks invalid (kept digits only).")
        if email and not is_valid_email(email):
            print("Warning: email looks invalid.")
        contact = {"name": name, "phone": phone_n, "email": email.strip(), "tags": tags, "favorite": fav}
        contacts = read_contacts()
        names = [c["name"] for c in contacts]
        close = get_close_matches(name, names, n=3, cutoff=0.85)
        if close:
            print("Similar existing names found:", ", ".join(close))
            choice = input("Type M to merge, A to add as new, or C to cancel [A]: ").strip().upper() or "A"
            if choice == "M":
                target = find_by_name_exact(contacts, close[0]) or next((c for c in contacts if c["name"] == close[0]), None)
                if target:
                    if not target.get("phone") and contact.get("phone"):
                        target["phone"] = contact["phone"]
                    if not target.get("email") and contact.get("email"):
                        target["email"] = contact["email"]
                    merged_tags = set(t.strip() for t in (target.get("tags","") + "," + contact.get("tags","")).split(",") if t.strip())
                    target["tags"] = ",".join(sorted(merged_tags))
                    target["favorite"] = target.get("favorite") or contact.get("favorite")
                    write_contacts(contacts)
                    print("Merged into existing contact.")
                    return
        contacts.append(contact)
        write_contacts(contacts)
        print("Contact added successfully.")
    except Exception as e:
        log_error("add_contact_interactive", e)
        print("Failed to add contact. See error_log.txt for details.")


def search_contacts() -> None:
    try:
        q = input("Enter search term (or regex: /pattern/): ").strip()
        if not q:
            print("Empty query.")
            return
        contacts = read_contacts()
        results = []
        if q.startswith("/") and q.endswith("/"):
            pattern = q[1:-1]
            try:
                rx = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                print("Invalid regex:", e)
                return
            for c in contacts:
                if rx.search(c.get("name","")) or rx.search(c.get("phone","")) or rx.search(c.get("email","")) or rx.search(c.get("tags","")):
                    results.append(c)
        else:
            qs = q.lower()
            for c in contacts:
                if qs in (c.get("name","").lower() + c.get("phone","") + c.get("email","").lower() + c.get("tags","").lower()):
                    results.append(c)
        display_contacts(results)
    except Exception as e:
        log_error("search_contacts", e)
        print("Search failed. See error_log.txt for details.")


def update_contact_interactive() -> None:
    try:
        name = input("Enter exact name of contact to update: ").strip()
        if not name:
            return
        contacts = read_contacts()
        target = find_by_name_exact(contacts, name)
        if not target:
            print("Contact not found.")
            return
        print("Current:")
        display_contacts([target])
        new_phone = input(f"New phone (leave empty to keep '{target.get('phone','')}'): ").strip()
        new_email = input(f"New email (leave empty to keep '{target.get('email','')}'): ").strip()
        new_tags = input(f"New tags (leave empty to keep '{target.get('tags','')}'): ").strip()
        fav = input(f"Mark favorite? (y/N, leave empty to keep current '{target.get('favorite')}'): ").strip().lower()
        if new_phone:
            target["phone"] = normalize_phone(new_phone)
            if not is_valid_phone(new_phone):
                print("Warning: invalid phone.")
        if new_email:
            target["email"] = new_email.strip()
            if not is_valid_email(new_email):
                print("Warning: invalid email.")
        if new_tags:
            target["tags"] = new_tags
        if fav in ("y", "yes"):
            target["favorite"] = True
        elif fav in ("n", "no"):
            target["favorite"] = False
        write_contacts(contacts)
        print("Contact updated.")
    except Exception as e:
        log_error("update_contact_interactive", e)
        print("Update failed. See error_log.txt for details.")


def delete_contact_interactive() -> None:
    try:
        name = input("Enter exact name to delete: ").strip()
        if not name:
            return
        contacts = read_contacts()
        remaining = [c for c in contacts if c.get("name","").lower() != name.lower()]
        if len(remaining) == len(contacts):
            print("Not found.")
            return
        write_contacts(remaining)
        print(f"Deleted contact '{name}'.")
    except Exception as e:
        log_error("delete_contact_interactive", e)
        print("Delete failed. See error_log.txt for details.")


def bulk_import_csv() -> None:
    try:
        path = input("Path to CSV to import (will append): ").strip()
        if not path or not os.path.isfile(path):
            print("File not found.")
            return
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            incoming = []
            for row in reader:
                name = row.get("name","").strip()
                if not name:
                    continue
                contact = {
                    "name": name,
                    "phone": normalize_phone(row.get("phone","")),
                    "email": (row.get("email","") or "").strip(),
                    "tags": row.get("tags","") or "",
                    "favorite": str(row.get("favorite","")).strip() in ("1","true","yes","y")
                }
                incoming.append(contact)
        if not incoming:
            print("No valid contacts in file.")
            return
        contacts = read_contacts()
        contacts.extend(incoming)
        write_contacts(contacts)
        print(f"Imported {len(incoming)} contacts.")
    except Exception as e:
        log_error("bulk_import_csv", e)
        print("Bulk import failed.")


def export_vcard_selected() -> None:
    try:
        name = input("Enter exact name to export to vCard: ").strip()
        contacts = read_contacts()
        target = find_by_name_exact(contacts, name)
        if not target:
            print("Not found.")
            return
        filename = f"{re.sub(r'[^a-zA-Z0-9_-]', '_', target['name'])}.vcf"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("BEGIN:VCARD\nVERSION:3.0\n")
            f.write(f"N:{target['name']}\n")
            if target.get("phone"):
                f.write(f"TEL;TYPE=CELL:{target['phone']}\n")
            if target.get("email"):
                f.write(f"EMAIL;TYPE=INTERNET:{target['email']}\n")
            f.write("END:VCARD\n")
        print(f"Exported vCard to {filename}.")
    except Exception as e:
        log_error("export_vcard_selected", e)
        print("vCard export failed.")


def create_backup() -> None:
    try:
        safe_makedirs(BACKUP_DIR)
        if not os.path.isfile(CSV_FILE):
            print("No CSV to backup.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = os.path.join(BACKUP_DIR, f"contacts_backup_{ts}.csv")
        shutil.copy2(CSV_FILE, dst)
        print(f"Backup created: {dst}")
    except Exception as e:
        log_error("create_backup", e)
        print("Backup failed.")


def list_backups() -> List[str]:
    safe_makedirs(BACKUP_DIR)
    files = sorted(Path(BACKUP_DIR).glob("contacts_backup_*.csv"), reverse=True)
    return [str(p) for p in files]


def restore_backup() -> None:
    try:
        files = list_backups()
        if not files:
            print("No backups available.")
            return
        print("Available backups:")
        for i, f in enumerate(files, 1):
            print(f"{i}. {f}")
        choice = input("Choose number to restore or C to cancel: ").strip()
        if choice.upper() == "C":
            return
        try:
            idx = int(choice) - 1
            sel = files[idx]
            shutil.copy2(sel, CSV_FILE)
            print(f"Restored backup from {sel}")
        except Exception:
            print("Invalid choice.")
    except Exception as e:
        log_error("restore_backup", e)
        print("Restore failed.")


def undo_last_write() -> None:
    try:
        prev = load_prev_snapshot()
        if not prev:
            print("No previous snapshot available to undo.")
            return
        write_contacts(prev)
        try:
            os.remove(PREV_SNAPSHOT)
        except Exception:
            pass
        print("Undo successful: previous contacts restored.")
    except Exception as e:
        log_error("undo_last_write", e)
        print("Undo failed.")



def export_to_json() -> None:
    try:
        contacts = read_contacts()
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=4, ensure_ascii=False)
        print(f"Exported {len(contacts)} contacts to {JSON_FILE}.")
    except Exception as e:
        log_error("export_to_json", e)
        print("Export failed. See error_log.txt for details.")


def import_from_json() -> None:
    try:
        if not os.path.isfile(JSON_FILE):
            print(f"{JSON_FILE} does not exist.")
            return
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print("Invalid JSON format.")
            return
        normalized = []
        for item in data:
            if not isinstance(item, dict):
                continue
            name = item.get("name","").strip()
            if not name:
                continue
            normalized.append({
                "name": name,
                "phone": normalize_phone(item.get("phone","")),
                "email": (item.get("email","") or "").strip(),
                "tags": item.get("tags","") or "",
                "favorite": bool(item.get("favorite"))
            })
        if not normalized:
            print("JSON contains no valid contacts.")
            return
        confirm = input("This will overwrite current CSV contacts. Type YES to proceed: ").strip()
        if confirm != "YES":
            print("Import cancelled.")
            return
        write_contacts(normalized)
        print(f"Imported {len(normalized)} contacts from {JSON_FILE}.")
    except Exception as e:
        log_error("import_from_json", e)
        print("Import failed. See error_log.txt for details.")


def name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def merge_duplicates(auto_threshold: float = 0.9) -> None:
    """Find likely duplicates by name similarity and offer merges (or auto-merge)."""
    try:
        contacts = read_contacts()
        n = len(contacts)
        if n < 2:
            print("Not enough contacts to check duplicates.")
            return
        names = [c["name"] for c in contacts]
        merged_any = False
        used = set()
        for i, c in enumerate(contacts):
            if i in used: 
                continue
            for j in range(i + 1, n):
                if j in used:
                    continue
                sim = name_similarity(c["name"], contacts[j]["name"])
                if sim >= auto_threshold:
                    print(f"Possible duplicate:\n 1) {c['name']}  2) {contacts[j]['name']} (sim={sim:.2f})")
                    action = input("Type M to merge, S to skip, A to always auto-merge similar > ").strip().upper()
                    if action == "M" or action == "A":
                        target = c
                        src = contacts[j]
                        if not target.get("phone") and src.get("phone"):
                            target["phone"] = src["phone"]
                        if not target.get("email") and src.get("email"):
                            target["email"] = src["email"]
                        merged_tags = set(t.strip() for t in (target.get("tags","") + "," + src.get("tags","")).split(",") if t.strip())
                        target["tags"] = ",".join(sorted(merged_tags))
                        target["favorite"] = target.get("favorite") or src.get("favorite")
                        used.add(j)
                        merged_any = True
                        if action == "A":
                            continue
                    else:
                        continue
        if merged_any:
            new_contacts = [contacts[i] for i in range(len(contacts)) if i not in used]
            write_contacts(new_contacts)
            print("Duplicates merged and saved.")
        else:
            print("No merges performed.")
    except Exception as e:
        log_error("merge_duplicates", e)
        print("Duplicate merge failed.")

def show_menu() -> None:
    print("""
Advanced Contact Manager
------------------------
1. Add contact 
2. View all contacts
3. Search contacts 
4. Update contact
5. Delete contact
6. Export contacts to JSON
7. Import contacts from JSON 
8. Bulk import CSV
9. Export a contact to vCard
10. Create manual backup
11. Restore from backup
12. Undo last write
13. Merge duplicates
14. Export selected contacts to JSON by tag/favorites
15. Exit
""")


def export_filtered_json() -> None:
    try:
        contacts = read_contacts()
        choice = input("Filter by tag name (t:tag) or favorite (f) or ALL: ").strip()
        if not choice or choice.upper() == "ALL":
            sel = contacts
        elif choice.lower().startswith("t:"):
            tag = choice[2:].strip().lower()
            sel = [c for c in contacts if tag in (c.get("tags","").lower())]
        elif choice.lower() == "f":
            sel = [c for c in contacts if c.get("favorite")]
        else:
            print("Unknown filter.")
            return
        if not sel:
            print("No contacts match filter.")
            return
        fn = input("Filename to save (default filtered_contacts.json): ").strip() or "filtered_contacts.json"
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(sel, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(sel)} contacts to {fn}.")
    except Exception as e:
        log_error("export_filtered_json", e)
        print("Filtered export failed.")


def main_loop() -> None:
    ensure_csv_exists()
    print("Welcome to Advanced Contact Book — now with validation, dedupe, backups, undo, tags, and vCard.")
    while True:
        try:
            show_menu()
            choice = input("Choose an option (1-15): ").strip()
            if choice == "1":
                add_contact_interactive()
            elif choice == "2":
                sort_by = input("Sort by name/phone/email/favorite (default name): ").strip().lower() or "name"
                display_contacts(read_contacts(), sort_by=sort_by)
            elif choice == "3":
                search_contacts()
            elif choice == "4":
                update_contact_interactive()
            elif choice == "5":
                delete_contact_interactive()
            elif choice == "6":
                export_to_json()
            elif choice == "7":
                import_from_json()
            elif choice == "8":
                bulk_import_csv()
            elif choice == "9":
                export_vcard_selected()
            elif choice == "10":
                create_backup()
            elif choice == "11":
                restore_backup()
            elif choice == "12":
                undo_last_write()
            elif choice == "13":
                merge_duplicates()
            elif choice == "14":
                export_filtered_json()
            elif choice == "15":
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting.")
            break
        except Exception as e:
            log_error("main_loop", e)
            print("Unexpected error. See error_log.txt.")


if __name__ == "__main__":
    main_loop()
