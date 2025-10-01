# GitHub Organization Student Inviter

Automatically invite students from a Canvas CSV export to your GitHub organization using their email addresses from the "SIS Login ID" field.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create GitHub Personal Access Token:**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Give it a descriptive name (e.g., "Student Inviter")
   - Select the `admin:org` scope (required for organization invitations)
   - Copy the generated token

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your values:
   ```
   GITHUB_TOKEN=ghp_your_actual_token
   GITHUB_ORG=your-organization-name
   ```

## Usage

### Basic Usage

```bash
python invite_students.py students.csv
```

### Dry Run (Preview without sending invitations)

```bash
python invite_students.py students.csv --dry-run
```

### Interactive Mode

If you don't provide a CSV file path, the script will prompt you:

```bash
python invite_students.py
```

## CSV Format

The script uses the **`SIS Login ID`** column from Canvas exports, which contains student email addresses. The invitations are sent to these email addresses.

## Features

- ✅ Email-based invitations using Canvas "SIS Login ID" field
- ✅ Dry-run mode to preview before sending invitations
- ✅ Detects users who are already members or invited
- ✅ Rate limiting to avoid GitHub API limits
- ✅ Detailed progress and error reporting
- ✅ Interactive prompts for missing configuration
- ✅ Safe confirmation before sending invitations

## Troubleshooting

### "403 Forbidden" Error
- Ensure your GitHub token has the `admin:org` scope
- Verify you have admin/owner permissions in the organization

### "Resource not found" Error
- This may occur if the email address is not associated with a GitHub account
- Students will receive an invitation email to join GitHub and your organization

### "Already invited or member" Warning
- The user has already been invited or is already a member
- This is normal and can be ignored

### Invalid Email Format
- Ensure the "SIS Login ID" column contains valid email addresses
- Check for empty rows or malformed data in your CSV

## Security Notes

- Never commit your `.env` file to version control
- Keep your GitHub token secure and rotate it regularly
- Use tokens with minimal required scopes

## Requirements

- Python 3.7+
- GitHub organization admin/owner access
- Personal Access Token with `admin:org` scope

