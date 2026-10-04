# SolarFren's maintenance guide

## The normal routine

- **New project:** Review its submission issue and upstream evidence, then apply the `approved` label. The **Prepare approved submission** workflow checks that the label was applied by a repository maintainer and creates a review branch and pull request. Review the JSON file and merge. This closes the submission issue.
- **Existing project:** Open its JSON file in [`data/projects/`](data/projects/), click the pencil, and commit the change. The website's **Edit entry** link opens that same file directly.
- **Correction from someone else:** Check their source, edit the entry, then close their issue or merge their pull request.

The catalog build checks every entry, regenerates the complete GitHub index and README counts, and builds the website. Once Pages is enabled, the same workflow deploys it.

## One-time GitHub settings

1. [Settings → Pages](https://github.com/solarfren69420/GameDecompLibrary/settings/pages): under **Build and deployment → Source**, choose **GitHub Actions**. Rerun **Build and update catalog** from Actions. It publishes to https://solarfren69420.github.io/GameDecompLibrary/.
2. [Settings → Actions → General](https://github.com/solarfren69420/GameDecompLibrary/settings/actions): enable **Allow GitHub Actions to create and approve pull requests** if you want the approval workflow to open PRs automatically. It never approves or merges them. If GitHub blocks PR creation, the workflow still creates the branch and posts a link to open the PR yourself.
3. GitHub Issues must stay enabled for the submission forms. Repository Watch → Custom → Issues enables notifications for new submissions if desired.

The build workflow creates the `submission`, `needs-review`, `approved` and `catalog-update` labels on its first run. Anyone with write/admin access can review submissions. An ordinary visitor cannot approve an entry by adding a label.

## If an approval needs attention

Open the workflow run in **Actions → Prepare approved submission**. Missing fields, duplicate repositories, invalid URLs or percentages stop the change before a branch is created. Correct the issue fields, then rerun the workflow or use **Run workflow** with its issue number. The workflow is repeatable and reuses its issue branch and open PR.

Pull requests created with GitHub's built-in workflow token may not trigger other workflows. Run **Build and update catalog** manually on the generated branch to validate the proposed catalog if needed; its default-branch maintenance and deployment steps only run on `main`. The preparation script validates the new entry before committing it. Ordinary human-created PRs run catalog checks automatically.

## Update progress responsibly

Update `sources`, `snapshot_date`, `report_date`, `report_commit` and the matching numeric values together. Preserve platform/region scope. Snapshot date is when you read the source; report date belongs to the underlying evidence.

Do not turn unknown progress into zero or convert a maintainer's completion claim into a matching-byte percentage. The library does not run upstream builds or test suites. A game can report 100% for a code target while ports, documentation and assets still require work.

## Local work

```sh
python3 scripts/build.py --update-docs
python3 -m http.server 8080 --directory _site
```

The app is static and uses relative asset URLs, so it works at the repository's Pages subpath. Python's standard library performs the build and automation; Node is only used for checking JavaScript syntax. No secrets belong in project records.
