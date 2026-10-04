<p align="center"><img src="web/banner.svg" alt="Game Decompilation Library — Recovered source. Shared tools. A place to build from." width="100%"></p>

<p align="center">
  <a href="CATALOG.md"><strong>Browse every project</strong></a> ·
  <a href="https://github.com/solarfren69420/GameDecompLibrary/issues/new?template=add-project.yml"><strong>Submit your GitHub</strong></a> ·
  <a href="https://github.com/solarfren69420/GameDecompLibrary/issues/new?template=update-project.yml">Suggest an update</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

A community-maintained catalog of game decompilations, Rust bindings, asset parsers and reverse engineering tools. Find an upstream project, follow its progress, or share your own repository with SolarFren.

<!-- catalog-stats:start -->
**303 projects** · 220 game projects · 71 tools · 11 related projects · 1 unconfirmed link
<!-- catalog-stats:end -->

Every original repository from the supplied catalog is retained, including the GitLab entries and the unconfirmed link. Upstream maintainers own their projects; this library links to them.

| Start here | What you'll find |
| --- | --- |
| [Game projects](CATALOG.md#game-decompilations) | Console, handheld and PC decompilations with sourced target progress |
| [Bindings and tools](CATALOG.md#bindings-and-tools) | Rust interfaces, asset formats, native interop, analysis and testing |
| [Related projects](CATALOG.md#ports-recompilations-and-source-releases) | Ports, recompilations, disassemblies and official source releases |
| [Unconfirmed links](CATALOG.md#unconfirmed-original-links) | Preserved original entries that need a working upstream URL |

### From the shelf

| Project | Platform | Published progress | Upstream |
| --- | --- | --- | --- |
| The Legend of Zelda: Breath of the Wild | Switch 1.5.0 | 17.489% | [zeldaret/botw](https://github.com/zeldaret/botw) |
| Super Mario Odyssey | Switch | 15.77% | [MonsterDruide1/OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp) |
| Fallout: New Vegas | Xbox 360 | 1.36% | [ieee802dot11ac/fnv](https://github.com/ieee802dot11ac/fnv) |
| Super Smash Bros. Melee | GameCube | 100% | [doldecomp/melee](https://github.com/doldecomp/melee) |
| FromSoftware Rust bindings | Runtime tooling | No game decompilation percentage | [vswarte/fromsoftware-rs](https://github.com/vswarte/fromsoftware-rs) |

These are the supplied **2026-10-04 snapshots**. Consult each entry's [evidence and report date](CATALOG.md); underlying reports may be older.

### Send your GitHub

Use **[Submit a GitHub project](https://github.com/solarfren69420/GameDecompLibrary/issues/new?template=add-project.yml)**. Send the repository URL, platform, a short description and a primary source for its scope or progress. Your GitHub account is your contact, so no separate email is required. Anyone with a GitHub account can submit; SolarFren reviews additions.

Prefer a pull request? Add one JSON file in [`data/projects/`](data/projects/) using the [example](examples/project.json). The catalog checks it, and merging updates the index and website.

### Keep it current

Open a project file in [`data/projects/`](data/projects/), click GitHub's pencil, update the fields and commit. The website also has an **Edit entry** link for each project. GitHub Actions validates the records and regenerates this README's counts and the full index. See the [maintainer guide](MAINTAINING.md) for approving submissions.

### Read the numbers accurately

Decompiled progress measures a **published code target**, including its platform, version and scope. Fully linked progress is a separate metric. Neither establishes overall game, asset, port, build or test completion.

Unknown percentages are `null`, never 0%. Maintainer completion claims and function-count metrics keep their original wording. Tools, reimplementations and source releases have no comparable game decompilation percentage. The screenshot was a design reference; the library uses real upstream URLs and sourced statuses.

The original sourced list remains in [`sources/`](sources/game-decomp-github-linklist.txt). New snapshots should cite their upstream evidence and the date of the underlying report.

### Interactive library

The repository includes a searchable, responsive website based on the supplied GitHub-style layout, with platform filters, progress filters, sorting, pagination and a source inspector.

Expected Pages address: **https://solarfren69420.github.io/GameDecompLibrary/**. To activate it once, open [Settings → Pages](https://github.com/solarfren69420/GameDecompLibrary/settings/pages), select **GitHub Actions** under Source, then rerun **Build and update catalog** from [Actions](https://github.com/solarfren69420/GameDecompLibrary/actions). Until Pages is enabled, the complete library is available in [CATALOG.md](CATALOG.md).

For local preview:

```sh
python3 scripts/build.py
python3 -m http.server 8080 --directory _site
```

Open http://localhost:8080. No npm dependencies, database, hosting subscription or API key is needed.
