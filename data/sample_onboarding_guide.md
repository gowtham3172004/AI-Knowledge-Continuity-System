# Sample Document: Company Onboarding Guide

## Welcome to the Team!

This document provides essential information for new employees joining our organization.

## Getting Started

### First Day Checklist

1. **IT Setup**
   - Collect your laptop from IT department
   - Set up your email account
   - Request access to necessary systems (Jira, Confluence, GitHub)

2. **HR Paperwork**
   - Complete tax forms
   - Set up direct deposit
   - Review benefits enrollment

3. **Meet Your Team**
   - Schedule 1:1 with your manager
   - Attend team standup meeting
   - Get introduced to key stakeholders

## Development Environment Setup

### Prerequisites
- Python 3.10 or higher
- Git
- Docker (for local development)

### Steps

```bash
# Clone the main repository
git clone https://github.com/company/main-project.git

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run the application
python main.py
```

## Key Contacts

| Role | Name | Email |
|------|------|-------|
| Engineering Manager | John Smith | john.smith@company.com |
| Tech Lead | Jane Doe | jane.doe@company.com |
| HR Representative | Bob Wilson | bob.wilson@company.com |
| IT Support | helpdesk@company.com | - |

## Important Policies

### Code Review Process
All code changes must go through peer review before merging:
1. Create a pull request with clear description
2. Request review from at least 2 team members
3. Address all feedback
4. Obtain approval before merging

**Why this process?** We believe thorough code review:
- Catches bugs early
- Spreads knowledge across the team
- Maintains code quality standards
- Helps onboard new developers

### Deployment Process
We follow a CI/CD pipeline:
1. Push to feature branch
2. Automated tests run
3. Merge to main triggers staging deployment
4. Manual approval for production deployment

**Decision rationale:** This staged approach was chosen after the 2023 incident where a direct-to-production push caused 4 hours of downtime. The manual approval step ensures human oversight for critical changes.

## FAQ

**Q: How do I request time off?**
A: Use the HR portal at hr.company.com/timeoff. Requests should be submitted at least 2 weeks in advance.

**Q: Who do I contact for technical questions?**
A: Post in the #engineering-help Slack channel or reach out to your assigned mentor.

**Q: What's the work from home policy?**
A: We follow a hybrid model - 3 days in office, 2 days remote. Coordinate with your team for in-office days.
