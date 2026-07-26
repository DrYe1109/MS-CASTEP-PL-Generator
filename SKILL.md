---
name: ms-castep-pl-generator
description: Generate self-contained Materials Studio MaterialsScript PL/XSD packages for CASTEP geometry optimizations and spin screens. Each package binds to one copied XSD, validates it at runtime, uses short result names, and leaves remote Gateway selection to the user.
---

# MS CASTEP PL Generator

Generate PL/XSD task folders only. Never submit a job unless the user separately
asks for submission.

## Workflow

1. Obtain the exact source XSD path, calculation name, spin value(s), core count,
   and any CASTEP overrides.
2. Verify that the source exists, is non-empty, contains XSD structure content,
   and contains at least one `Atom3d` entry.
3. Run `scripts/generate_castep_pl_package.py`.
4. Inspect `package_manifest.json` and every generated PL. Confirm that each PL:
   - names its unique copied XSD;
   - checks the runtime atom count;
   - calls `GeometryOptimization->Run`;
   - saves `opt.xsd` and `report.txt`;
   - does not use ordinary Perl file I/O with a Materials Studio virtual path.
5. Give the generated folders to the user with the instructions in
   `references/manual-submission.md`.
6. Do not select a Gateway or submit a remote job during package generation.

## Generate a package

For Windows users, the easiest setup is:

```text
Configure-CASTEP-PL-Skill.bat
Generate-CASTEP-PL-Package.bat
```

The first BAT validates Python 3.7+, optionally validates the Materials Studio
MaterialsScript runtime, and creates an ignored machine-local configuration.
The second BAT prompts for XSD, calculation name, spins, cores, and output
location, then calls the bundled generator.

The equivalent direct command is:

```powershell
python scripts/generate_castep_pl_package.py `
  --xsd "D:\path\BLG_Co_C3.xsd" `
  --output-dir "D:\path\prepared" `
  --calculation-name "Co_C3" `
  --spins 1 3 5 `
  --cores 48
```

The default is a fixed-spin calculation (`OptimizeTotalSpin = No`). Use
`--spin-mode relaxed` only when total spin should be allowed to change.

The robust defaults reflect the convergence repair used for metallic,
spin-polarized graphene-defect systems:

- fixed spin;
- BFGS geometry optimization;
- 500 maximum SCF cycles;
- Pulay charge/spin mixing amplitudes of 0.05/0.08;
- DIIS history 5;
- Gaussian smearing 0.2 eV;
- 150 maximum geometry iterations.

Optional arguments include `--cutoff`, `--max-scf-cycles`,
`--max-geometry-iterations`, `--scf-convergence`, `--force-convergence`,
`--dispersion-method`, `--spin-mode`, `--density-mixing-amplitude`,
`--spin-mixing-amplitude`, `--diis-history`, `--smearing`,
`--optimization-algorithm`, and `--allow-local`.

See `references/environment-setup.zh-CN.md` for prerequisites, Gateway
requirements, and the BAT workflow.

Default behavior blocks execution on Windows. This guards against accidentally
running locally when the user intended to choose a remote Gateway. Use
`--allow-local` only when local execution is explicitly requested.

## Binding and result rules

Each PL binds to the copied project document by exact name:

```perl
my $source = eval { $Documents{$model} };
die "Input document not found" unless $source;
my $atom_count = $source->UnitCell->Atoms->Count;
die "Unexpected atom count" unless $atom_count == $expected_atoms;
```

Never assume an unnamed current document and never fall back to another XSD.
Import the generated XSD and PL into the same Materials Studio project folder.

Materials Studio paths such as `/$calc/opt.xsd` are virtual document paths.
Use MaterialsScript `SaveAs` for them. Do not pass those paths to ordinary Perl
`open()`: doing so can mark an otherwise successful CASTEP job as failed during
PL post-processing.

The generated PL reports completion through standard output:

```text
RESULT status=completed calculation=... spin=... atoms=...
```

and returns:

- `opt.xsd`;
- `report.txt`;
- the normal CASTEP job artifacts managed by Materials Studio.

## Deliverables

Return links to:

- every task folder;
- its copied XSD;
- its generated PL;
- `package_manifest.json`;
- `MANUAL_SUBMISSION.txt`.

State explicitly that no Gateway was selected and no task was submitted.
