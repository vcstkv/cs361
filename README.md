# CS361 Scripts

A collection of automation scripts for managing software engineering courses, including GitHub organization management and peer evaluation workflows.

## Overview

This repository contains tools to streamline common administrative tasks for computer science courses, particularly those involving team projects, GitHub organizations, and peer evaluations.

## Tools

### 🎓 [GitHub Student Inviter](github_student_inviter/)

Automatically invite students from Canvas to your GitHub organization.

**Features:**
- Bulk invite students using Canvas CSV exports
- Email-based invitations via SIS Login ID
- Dry-run mode for testing
- Rate limiting and error handling
- Duplicate detection

**Quick Start:**
```bash
cd github_student_inviter
pip install -r requirements.txt
python invite_students.py students.csv
```

[📖 Full Documentation](github_student_inviter/README.md)

---

### 📊 [Peer Review Tools](peer_review/)

Process team peer evaluations from Qualtrics surveys and calculate grades.

**Includes:**
1. **Contact List Generator** - Convert Canvas team data to Qualtrics contact lists
2. **Grade Calculator** - Process survey results and calculate peer evaluation scores

**Features:**
- Generate personalized Qualtrics contact lists
- Calculate normalized peer review grades
- Merge scores into Canvas gradebooks
- Visualize score distributions
- Handle missing evaluations gracefully

**Quick Start:**
```bash
cd peer_review
pip install -r requirements.txt

# Generate Qualtrics contacts
python generate-peer-eval-contacts.py teams.csv contacts.csv

# Calculate peer review grades
python calculate-peer-review-grade.py teams.csv survey.csv gradebook.csv output.csv updated_gradebook.csv
```

[📖 Full Documentation](peer_review/README.md)

---

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/cs361_scripts.git
   cd cs361_scripts
   ```

2. **Navigate to the tool directory:**
   ```bash
   cd github_student_inviter  # or peer_review
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Follow tool-specific setup instructions** in each directory's README

## Common Workflows

### Setting Up a New Course

1. **Invite students to GitHub organization:**
   ```bash
   cd github_student_inviter
   python invite_students.py canvas_export.csv
   ```

2. **Export team data from Canvas** for projects

3. **Generate Qualtrics contact list:**
   ```bash
   cd peer_review
   python generate-peer-eval-contacts.py teams.csv contacts.csv
   ```

4. **Send peer evaluation survey** via Qualtrics

5. **Process results and calculate grades:**
   ```bash
   python calculate-peer-review-grade.py teams.csv survey.csv gradebook.csv grades.csv updated_gradebook.csv
   ```

6. **Import updated gradebook** to Canvas

## Data Privacy & Security

⚠️ **Important Security Guidelines:**

- **Never commit sensitive data** to version control
- Keep student data (CSV files, gradebooks) in gitignored directories
- Store API tokens and credentials in `.env` files (not committed)
- Follow your institution's data privacy policies (FERPA, GDPR, etc.)
- Delete temporary data files when no longer needed
- Rotate API tokens regularly

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

