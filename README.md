# B to Bern (B2B) — Research & Expertise Navigator

B2B helps Bern economic-development staff turn a company's research needs into
source-backed reasons to explore Bern. Describe the company in ordinary language,
inspect relevant expertise, units and infrastructure, then keep the strongest
matches and export a reviewed “Why Bern?” brief.

Built for the **Bern Economic Development Agency** challenge at
[Hack Apertus](https://hackapertus.ch/). The pilot connects public research from
the University of Bern, ARTORG and Diabetes Center Berne, focusing on diabetes
technology. Apertus v1.5 interprets intent, prepares and assesses evidence, and
drafts cited reasons. Staff inspect the sources and decide what to include.

**Team Stregoni:** Renato Mignone, Elia Innocenti, Eric Ruiz Giménez,
Mohamed Kechiche.

**Judges: [start here](docs/judges/README.md).**

- [Run the demo or connected application](docs/judges/QUICKSTART.md)
- [Follow the product walkthrough](docs/judges/DEMO.md)
- [Understand the architecture](docs/judges/ARCHITECTURE.md)
- [Inspect verification and limitations](docs/judges/VERIFICATION.md)
- [Read the technical report](technical_report.md)

**Delivery snapshot — 19 October 2026:** authenticated HTTP application,
LangGraph worker, hybrid retrieval, source inspection and reviewed PDF export are
implemented. A real-provider partial report and PDF are recorded; broad retrieval
quality and the proposed air-gapped target are not certified. A seeded UI demo runs
without credentials; real research requires provisioned services and corpus access.
PowerPoint, manual plans and own-case comparison require explicit backend activation.
Demo URL, final report PDF and independent live access remain delivery items in the
[release checklist](docs/judges/DELIVERY.md).

Submissions must use the v1.5 Apertus model family.
The submission must comply with the [HackApertus T&C](https://hackapertus.ch/terms-and-conditions).

## 🎯 The Challenge

**Bern Economic Development Agency — Research & Expertise Navigator.**
Research information is scattered across institutional websites and uses specialist
terminology. B2B bridges everyday needs and scientific language while keeping public
factual statements attached to exact source passages.

The [challenge page](https://hackapertus.notion.site/bern-economic-development-agency)
and [supplied challenge snapshot](docs/challenge/CHALLENGE_BRIEF.md) define the
requirements. The challenge's 80% top-10 recall target is an evaluation goal,
not a measured B2B result.

## 🔧 Resources & Tools

Check our resources & tools page for detailed information:
[https://hackapertus.notion.site/liebefeld-resources-tools](https://hackapertus.notion.site/liebefeld-resources-tools)

| Models           | URL                                      |
|------------------|------------------------------------------|
| Apertus v1.5 8B  | [huggingface.co/swiss-ai/Apertus-v1.5-8B](https://huggingface.co/swiss-ai/Apertus-v1.5-8B)  |
| Apertus v1.5 70B | [huggingface.co/swiss-ai/Apertus-v1.5-70B](https://huggingface.co/swiss-ai/Apertus-v1.5-70B) |

## The structure

Keep the files and directories as shown below — don't rename or move them.

| Path | What it is |
| --- | --- |
| `README.md` | The challenge description and submission requirements |
| `technical_report.md` | The deeper write-up: architecture, evaluation, limitations |
| `LICENSE` | Apache-2.0 |
| `src/` | Your code |

## Environment

- Include instructions for running the project in your technical report.
- Use the following environment variables:
```
LLM_NAME — name and version of the model
LLM_BASE_URL — endpoint base URL
LLM_API_KEY — your API key
```

## 📦 Submission Requirements & Deliverables

The submission must:
1. follow the template repo and include all prerequisite files and definitions
2. run end-to-end when judges try to run it

### Git repo (URL)
- Create your repo from this template (**Use this template**).
- Keep the layout as it is: don't rename or move its files.
- Set the repo to PUBLIC (Settings --> Collaborators --> Manage Visibility)
- Submit the URL of YOUR Git repo.

### Technical Report (pdf)
- Update [technical_report.md](technical_report.md) in this repository with all the details for your submission.
- Upload a pdf of your technical report to the root of the repo, named as `TeamName_Report.pdf`.
- Format: pdf, max. 6 pages w/o references
- Submit the pdf of the technical report.

### Demo video (URL)
- Max. 2 min demo video of your prototype
- Add the link to the **Demo** field at the top of [technical_report.md](technical_report.md)
- Submit the URL of the video.

## ⚖️ Judging Criteria

Each challenge has its own criteria, listed in its challenge description.

The main jury scores every submission on 6 dimensions (relevant for Top 6 teams):
1. **Purposeful use of AI**
2. **Technical rigour**
3. **Value, cost & scalability**
4. **Sovereign deployability**
5. **Implementation feasibility**
6. **Pitch & presentation**

Each dimension is scored from 0 to 5.

## Getting started

For a credential-free UI tour, install Node 22.18+. From the repository root,
use PowerShell:

```powershell
cd src/frontend
npm ci
$env:VITE_API_MODE = 'mock'
npm run dev -- --host 127.0.0.1
```

Open the local URL Vite prints (normally `http://127.0.0.1:5173`). The
[quickstart](docs/judges/QUICKSTART.md#1-seeded-ui-demo-no-services-or-credentials)
provides Bash commands and mode-switching instructions. This is scripted sample content, not live Apertus
research. For the default authenticated HTTP mode and local synthetic backend,
follow the same quickstart. Never put credentials in `VITE_*` variables.

## License

All Hack Apertus projects are open-sourced. Please check our Terms & Conditions for specific licensing details (6. What you build is open source): https://hackapertus.ch/terms-and-conditions

## Support

### FAQ
💡 https://hackapertus.ch/faq

### Contact

💬 In case you have questions, join the conversation on Discord. Alternatively, send an email to “hello@hackapertus.ch”.
