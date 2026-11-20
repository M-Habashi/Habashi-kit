# Candidate Profile

> Extract facts from your CV/resume once and maintain this file as the single source of truth during job runs. Reopen your CV PDF only for file uploads or profile updates.

## Candidate Header
- **Full Name**: `<First Last>`
- **Email**: `<email@example.com>`
- **Phone**: `<+1-000-000-0000>`
- **Location**: `<City, State/Province, Postal Code, Country>`
- **LinkedIn**: `<https://www.linkedin.com/in/your-handle>`
- **Portfolio / GitHub / Website**: `<Optional URL>`
- **Resume PDF Path**: `docs/<Your_Resume.pdf>`

## Education
> List exact degree titles, institutions, dates, and exact GPA with its original scale (never auto-convert scales).

1. **<Degree Title, Field of Study>** — `<University Name>`, `<City, Country>`
   - **Dates**: `<Month YYYY – Month YYYY or Expected Month YYYY>`
   - **Status**: `<Completed | In Progress>`
   - **GPA**: `<Exact GPA / Exact Scale, e.g. 3.85 / 4.00>`
   - **Highlights / Thesis / Relevant Coursework**: `<Key facts>`

## Licenses & Certifications
> Distinguish clearly between passed exams and active state/national registrations.

- `<Credential Name>` — **Status**: `<Passed Exam | Active License | In Progress>` | **Issuer**: `<Board/Organization>` | **Date / ID**: `<Date / Optional ID>`

## Work History (Preferred CV Order)
> Preserve this exact order in forms and cover letters unless a portal forces date sorting.

1. **<Job Title>** — `<Employer Name>`, `<Location>` (`<Month YYYY – Month YYYY or Present>`)
   - `<Measurable achievement or responsibility #1>`
   - `<Measurable achievement or responsibility #2>`
2. **<Job Title>** — `<Employer Name>`, `<Location>` (`<Month YYYY – Month YYYY>`)
   - `<Measurable achievement or responsibility #1>`
   - `<Measurable achievement or responsibility #2>`

## Confirmed Skills & Software
> Only list tools and methods you genuinely know. Mirror software names in `rules.json` under `confirmed_software`.

- **Core Technical / Domain Skills**: `<Skill A>, <Skill B>`
- **Confirmed Software & Tools**: `<Tool 1>, <Tool 2>`
- **Languages**: `<Language (Proficiency)>`

## Selected Projects & Publications
1. **<Project Title>** (`<YYYY>`) — `<1-2 line factual summary with tools and outcomes>`
