#Contact Manager (Python Project)

A fully–featured, production-style Contact Manager built in Python.  
Supports CSV & JSON storage, daily automatic backups, undo system, searching, tags, favorites, vCard export, and advanced error handling.

# Features

# Core Features
- Add new contacts  
- View all contacts in a formatted table  
- Search using:
  -  Simple substring
  -  Regex search (`/pattern/`)
- Update contact details  
- Delete contacts  

# Data Handling
- CSV storage (`contacts.csv`)
- JSON export & import
- Custom filtered JSON export (favorites, tags)
- vCard (`.vcf`) single-contact export

# Advanced Features
- **Daily backup system**  
  - Only ONE backup created per day  
  - Backup stored inside `/backups/`
- **Undo last write** using snapshot
- **Tag support** (comma-separated)
- **Favorite contacts**
- **Auto-merge similar names** (fuzzy matching)
- **Phone/email validation**
- **Bulk import** from another CSV
- **Restore from backup**
- **Error logging** (`error_log.txt`)



