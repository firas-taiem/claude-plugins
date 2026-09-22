---
name: tailor-resume
description: Tailor the user's master resume to one job posting, using only facts already in the master, then fact-check it, show the changes for approval, and make an ATS-safe PDF. Use when the user types /resume-kit:tailor-resume <job URL>, pastes a job description, or asks to tailor their resume for a job.
argument-hint: <job posting URL, or paste the job description>
---

# Tailor Resume

The user gives you a job posting. You produce a version of their resume tailored
to that job, built only from their master resume, and a PDF once they approve.

**The master resume** is the file in the current working folder named
`Resume - <Name>.md` (not inside `jobs/`). It is the only source of facts. Never
read facts about the person from anywhere else: no web search about them, no
LinkedIn profile, no memory of earlier conversations.

If there is no `Resume - <Name>.md` in the folder, stop and tell the user how to
create one: copy the template from this skill's `template/` folder (one level up
from the skill directory, at `<plugin>/template/Resume - Your Name.md`) or convert
their existing resume into that format, then run the skill again.

**Scripts** live in this skill's own `scripts/` folder. The base directory of this
skill is given at the top of this prompt; refer to the scripts as
`"<skill base directory>/scripts/check_claims.py"` and
`"<skill base directory>/scripts/render_pdf.py"`, always quoted.

**Python command:** use `python3`. If that fails (usually on Windows), use `python`,
then `py`. Use whichever works for the rest of the run.

## Steps

### 1. Get the job description
The argument is a URL or pasted text.
- **Pasted text:** use it as is.
- **URL:** fetch it with WebFetch first. That works for most company career sites.
- If WebFetch returns a login page, an empty page, or no real description (LinkedIn
  usually does this), and Claude in Chrome tools are available, open the URL in
  Chrome and read the page text. Only read. Never click Apply, never fill a form,
  never sign in on the user's behalf.
- If both fail, ask the user to paste the job description text, and wait.

### 2. Check the posting is still open
If the page says it is no longer accepting applications, has been filled or closed,
or is a 404 or a generic careers page with no matching job, stop and tell the user.
Do not tailor a closed posting.

### 3. Make the job folder and save the posting
Create `jobs/<YYYY-MM-DD> <Company> - <Job Title>/` in the working folder (today's
date; remove characters that are not allowed in file names). Save the full job
description there as `job-description.md`, with the URL and today's date at the
top. Postings get taken down, and this copy is what the user prepares from before
an interview.

### 4. Match the job against the master
Read the whole master. List the job's 8 to 12 most important requirements and
keywords. Put each one in one of three groups:
- **Have it:** the master already says it.
- **Have it, different words:** the master shows the same experience in other words.
  You may use the job's wording for it (see the rules).
- **Gap:** the master does not show it. It goes on the gaps list and never into
  the resume.

### 5. Tailor
Write `Resume - <Name> - <Company>.md` in the job folder. Start from a copy of the
master and change only what the rules below allow. Aim for two pages: if the master
is longer, choose and cut. Keep the master's markdown format exactly (headings,
`**Label:**` bullets, `*italic*` company descriptions, `**Title | dates**` lines),
because the PDF step reads that format.

### 6. Fact check
Run:

    python3 "<skill base directory>/scripts/check_claims.py" "<master>" "<tailored>"

- **FAILED:** fix every FAIL line by going back to what the master says, then run it
  again. If a FAIL is a fact the user may have left out of the master, do not add it:
  put it on the gaps list instead. Never show the user a version that fails.
- **WARN lines:** read each one. For every "Reworded" warning, compare the two lines
  and make sure the claim is the same (same action, same result, same scope). If it
  is not, restore the master's wording. Keep the warnings you are satisfied with for
  the change list.

Then check the real length before the user sees anything. This only counts pages
and leaves no PDF behind; the real PDF is made in step 8, after approval:

    python3 "<skill base directory>/scripts/render_pdf.py" --pages-only "<tailored .md>"

If `pages` is more than 2, cut the lowest-relevance content (older roles before
recent ones, and never a result the job asks for), run the fact check again, and
check the length again until it is 2 pages. The version the user reviews must be
the final length, so approval never leads to cuts they have not seen.

### 7. Show the user the changes and wait
Write `changes.md` in the job folder and show the same content in the chat:
1. **What was emphasized and why:** 3 to 5 lines tied to the job's requirements.
2. **Every change:** each changed line with the master line it came from.
3. **What was cut** to reach two pages.
4. **Gaps:** requirements the resume does not show. Tell the user: if one is true
   and missing, add it to the master in their own words and run again.
5. The fact check result.

Then stop and ask for approval. Apply any edits the user asks for, run the fact
check again, and show the updated changes. **Do not make the PDF until the user
says it is approved.**

### 8. Make the PDF
Run:

    python3 "<skill base directory>/scripts/render_pdf.py" "<tailored .md>"

It prints `{"pdf": ..., "pages": N}`.
- If the user's edits pushed it past 2 pages, do not cut on your own. Show them
  what you would cut and wait for their OK, then fact check and render again.
- If it prints an error about Chrome or Edge, tell the user the tailored markdown is
  ready and the PDF needs Google Chrome or Microsoft Edge installed.

Finish with the path to the job folder and the PDF.

## Rules

### Truth
- **Add nothing that is not in the master:** no new skill, tool, platform, number,
  employer, job title, date, certification, award, degree, team size, budget, or
  scope. If the job wants it and the master does not show it, it is a gap.
- **Never change what a claim says.** You may reorder, cut, shorten, and use the
  job's wording for experience the master already shows. You may not change the
  action or the result of an accomplishment. "Led" never becomes "built",
  "supported" never becomes "owned", "helped reduce" never becomes "reduced", and a
  team result never becomes a personal one. If a bullet needs new words to fit the
  job, the words change and the claim does not. Small rewordings add up over many
  applications until a resume claims something that never happened, so hold every
  version to the master, never to the last tailored copy.
- **Copy numbers exactly.** Never round, combine, convert, or recalculate them.
- **Never edit the master resume.** Only the user changes it.

### Voice
- Keep the person's own phrasing, sentence style, and bold run-in labels. A tailored
  resume should read like they wrote it.
- Only use words that already appear in the master or in the job description. Never
  add filler or buzzwords from neither.
- The headline may be shortened to the title that best matches the job, chosen from
  the titles already listed in the master's headline. Never write a new title.

### What may change, and what never changes
May change:
- The profile paragraph: choose, reorder, and trim its existing sentences; you may
  pull a sentence from elsewhere in the master if it fits the job better.
- Which achievements appear, and their order.
- The order of items within each Core Competencies line, and the order of those lines.
- The order of bullets within each job, and which bullets are cut.
- Using the job's wording for experience the master already shows.

Never changes:
- The name and contact line.
- Section headings and their order. A section may be removed only if it is optional
  (for example, Thought Leadership) and the page limit forces it.
- Employer names, locations, job titles, dates, and the italic company descriptions.
- Education, certifications, and awards.

### ATS format
Single column, standard section headings, no tables, no text boxes, no images, no
icons, and the LinkedIn address written out in full. The PDF step produces this
automatically when the markdown keeps the master's format.
