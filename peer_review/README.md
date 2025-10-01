# Peer Review Scripts

This directory contains Python scripts for managing team peer evaluations using Canvas and Qualtrics.

## Overview

These scripts automate the process of:
1. Generating Qualtrics contact lists from Canvas team data
2. Processing peer evaluation survey results and calculating grades

## Scripts

### 1. `generate-peer-eval-contacts.py`

Converts Canvas team/group data into a Qualtrics contact list format for peer evaluation surveys.

**Input:** Canvas team CSV file with fields:
- `name` - Student name (format: "Last, First")
- `canvas_user_id`
- `user_id`
- `login_id` - Student email
- `sections`
- `group_name` - Team name
- `canvas_group_id`
- `group_id`

**Output:** Qualtrics contact list CSV with fields:
- `Email` - Student email
- `First Name` - Extracted from name field
- `Last Name` - Extracted from name field
- `Team` - Team/group name
- `Team Member 1`, `Team Member 2`, ..., `Team Member N` - Emails of teammates (excluding self)

**Usage:**
```bash
python generate-peer-eval-contacts.py <input_file> <output_file>

# Example:
python generate-peer-eval-contacts.py data/CS362_S2025_Teams.csv data/qualtrics-contacts-2025.csv
```

**How it works:**
1. Reads Canvas team data
2. Determines the maximum team size
3. For each student, creates columns for all their teammates (excluding themselves)
4. Populates teammate emails so Qualtrics can send personalized survey links

---

### 2. `calculate-peer-review-grade.py`

Processes Qualtrics peer evaluation survey results and calculates peer review grades for each student.

**Survey Questions:**

The script expects a Qualtrics survey with the following structure:

**Question 2** (Likert scale questions for each team member):
- Q2_X_1: Does the member do an appropriate quantity of work?
- Q2_X_2: How about the quality of the member's work?
- Q2_X_3: Rate the member's attitude as a team player
- Q2_X_4: Rate the overall value of the member's technical contribution
- Q2_X_5: Would you want to work with this person on a project again?

**Question 3** (Point distribution):
- Q3_X: Divide 100 points among team members based on contribution

(X ranges from 1 to 4, where 1 is self and 2-4 are team members)

**Usage:**
```bash
python calculate-peer-review-grade.py <groups_file> <survey_file> <gradebook_file> <output_file> <gradebook_output_file> [--plot-output <plot_file>]

# Example:
python calculate-peer-review-grade.py \
    data/CS362_S2025_Teams.csv \
    data/CS_362_001_S2025_Team_Peer_Evaluations.csv \
    data/2025-06-10T0945_Grades-CS_362_001_S2025.csv \
    data/CS_362_001_S2025_Peer_Review_Grades.csv \
    data/CS_362_001_S2025_Peer_Review_Grades_Gradebook.csv \
    --plot-output data/peer_eval_distribution.png
```

**Arguments:**
- `groups_file` - Canvas team data CSV
- `survey_file` - Qualtrics survey results CSV
- `gradebook_file` - Canvas gradebook CSV
- `output_file` - Output file for detailed peer review grades
- `gradebook_output_file` - Updated gradebook with peer evaluation scores
- `--plot-output` - (Optional) Path for distribution visualization (default: `peer_evaluation_distribution.png`)

**How it works:**
1. Reads team sizes from Canvas data
2. Processes Qualtrics survey responses
3. For each student, aggregates peer evaluations from teammates
4. Calculates mean scores for each question
5. Normalizes and shifts scores using the formulas:
   - Q2 questions: `(mean * 10) + 50` (normalized to ~50-100 scale)
   - Q3 (points): `mean * team_size` then shifted using a quadratic function to prevent extreme scores
6. Calculates final `PeerEvaluationScore` as average of normalized scores
7. Generates a histogram comparing original vs shifted Q3 distributions
8. Merges scores into Canvas gradebook
9. Sets default score of 60 for students with no peer evaluations

**Output Files:**
- Detailed peer review data with individual question scores
- Updated gradebook ready to import into Canvas
- Histogram visualization of score distributions

**Summary Statistics:**
The script prints summary statistics including:
- Total students evaluated
- Mean, median, standard deviation of peer evaluation scores
- Minimum and maximum scores

---

## Installation

### Requirements

- Python 3.7 or higher
- Required packages (see `requirements.txt`)

### Setup

1. Create a virtual environment (recommended):
```bash
cd peer_review
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Workflow

### Complete Peer Evaluation Process

1. **Export team data from Canvas**
   - Navigate to your Canvas course
   - Go to Groups
   - Export group membership data as CSV

2. **Generate Qualtrics contact list**
   ```bash
   python generate-peer-eval-contacts.py \
       data/canvas_teams.csv \
       data/qualtrics_contacts.csv
   ```

3. **Import contact list to Qualtrics**
   - In Qualtrics, go to your directory
   - Import the generated CSV as a new mailing list

4. **Send peer evaluation survey**
   - Use the Qualtrics contact list to send personalized surveys
   - Each student receives teammate information via piped text

5. **Export survey results**
   - After survey closes, export results from Qualtrics as CSV
   - Include all response data

6. **Export Canvas gradebook**
   - Download current gradebook from Canvas as CSV

7. **Calculate peer review grades**
   ```bash
   python calculate-peer-review-grade.py \
       data/canvas_teams.csv \
       data/qualtrics_survey_results.csv \
       data/canvas_gradebook.csv \
       data/peer_review_grades.csv \
       data/updated_gradebook.csv \
       --plot-output data/score_distribution.png
   ```

8. **Review results**
   - Check the output files for any anomalies
   - Review the distribution plot
   - Examine summary statistics

9. **Import grades to Canvas**
   - Import the updated gradebook CSV to Canvas
   - Verify the peer evaluation scores column

## Data Privacy

⚠️ **Important:** These scripts handle student data. Always:
- Keep data files in a secure location (e.g., in a `data/` directory that's gitignored)
- Never commit student data to version control
- Follow your institution's data privacy policies
- Delete temporary files when done

## Troubleshooting

### Common Issues

**Issue:** "Column not found" error
- **Solution:** Verify that your input CSV files have the expected column names. Check the Canvas/Qualtrics export settings.

**Issue:** Scores seem incorrect
- **Solution:** Verify that the survey questions are properly mapped (Q2_X_1 through Q2_X_5, Q3_X). Check that team sizes match.

**Issue:** Empty peer evaluations
- **Solution:** Some students may not have received evaluations if teammates didn't complete the survey. The script assigns a default score of 60 in the final gradebook.

**Issue:** Plot doesn't generate
- **Solution:** Ensure matplotlib is installed correctly. Try running with a different output path.

## License

These scripts are part of the cs361_scripts repository. See the LICENSE file in the root directory.

## Contributing

If you find bugs or have suggestions for improvements, please open an issue or submit a pull request.

