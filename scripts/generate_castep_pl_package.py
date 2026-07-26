#!/usr/bin/env python3
"""Generate self-contained MaterialsScript PL/XSD folders for manual submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


def safe_name(value: str, max_length: int = 40) -> str:
    """Return a short ASCII name suitable for Materials Studio job paths."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._")
    if not cleaned:
        raise ValueError("calculation name is empty after sanitization")
    if len(cleaned) <= max_length:
        return cleaned
    digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:8]
    return f"{cleaned[: max_length - 9]}_{digest}"


def validate_xsd(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"XSD not found: {path}")
    size = path.stat().st_size
    if size < 256:
        raise ValueError(f"XSD is unexpectedly small ({size} bytes): {path}")
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="ignore")
    if "<XSD" not in text and "<Atom3d" not in text:
        raise ValueError(f"file does not look like a Materials Studio XSD: {path}")
    atoms = len(re.findall(r"<Atom3d\b", text))
    if atoms < 1:
        raise ValueError(f"XSD contains no Atom3d entries: {path}")
    return {
        "source_name": path.name,
        "bytes": size,
        "atom3d_entries": atoms,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def make_pl(
    args: argparse.Namespace,
    model_name: str,
    calc_name: str,
    spin: int,
    expected_atoms: int,
) -> str:
    local_guard = "" if args.allow_local else r'''
die "LOCAL EXECUTION BLOCKED: choose a remote Gateway in Run on Server.\n"
    if $^O =~ /MSWin32/i;
'''
    optimize_spin = "Yes" if args.spin_mode == "relaxed" else "No"
    return f'''#!perl
use strict;
use warnings;
use MaterialsScript qw(:all);

{local_guard}$ENV{{DSD_NumProc}} = {args.cores};

my $model = "{model_name}";
my $calc = "{calc_name}";
my $initial_spin = {spin};
my $expected_atoms = {expected_atoms};

my $source = eval {{ $Documents{{$model}} }};
die "Input document lookup failed: $model; $@" if $@;
die "Input document not found: $model" unless $source;

my $atom_count = $source->UnitCell->Atoms->Count;
die "Input document is empty: $model" unless $atom_count > 0;
die "Unexpected atom count for $model: expected $expected_atoms, got $atom_count"
    unless $atom_count == $expected_atoms;
print "Validated input: $model; atoms=$atom_count; spin=$initial_spin; cores={args.cores}\\n";

my $work = $source->SaveAs("/$calc/in.xsd");
my $settings = Settings(
    "XCFunctional" => "PBE",
    "Pseudopotentials" => "OTFG ultrasoft",
    "UseDFTD" => "Yes",
    "DFTDMethod" => "{args.dispersion_method}",
    "UseCustomEnergyCutoff" => "Yes",
    "EnergyCutoff" => {args.cutoff},
    "KPointDerivation" => "Gamma",
    "MaximumSCFCycles" => {args.max_scf_cycles},
    "EnergyTolerancesScope" => "Atom",
    "SCFConvergence" => {args.scf_convergence},
    "DensityMixingScheme" => "Pulay",
    "DensityMixingAmplitude" => {args.density_mixing_amplitude},
    "SpinMixingAmplitude" => {args.spin_mixing_amplitude},
    "DIISHistory" => {args.diis_history},
    "Smearing" => {args.smearing},
    "CellOptimization" => "None",
    "OptimizationAlgorithm" => "{args.optimization_algorithm}",
    "MaxIterations" => {args.max_geometry_iterations},
    "EnergyConvergence" => 0.00001,
    "ForceConvergence" => {args.force_convergence},
    "DisplacementConvergence" => 0.001,
    "CalculateCharge" => "Hirshfeld",
    "CalculateSpin" => "Hirshfeld",
    "SpinTreatment" => "Collinear",
    "UseFormalSpin" => "No",
    "InitialSpin" => $initial_spin,
    "OptimizeTotalSpin" => "{optimize_spin}"
);

my $results = Modules->CASTEP->GeometryOptimization->Run($work, $settings);

eval {{
    my $optimized = $results->Structure;
    $optimized->SaveAs("/$calc/opt.xsd") if $optimized;
}};
print "WARNING: optimized structure export failed: $@\\n" if $@;

eval {{
    my $report = $results->Report;
    $report->SaveAs("/$calc/report.txt") if $report;
}};
print "WARNING: report export failed: $@\\n" if $@;

my $energy = "";
my $moment = "";
eval {{ $energy = $results->TotalEnergy; }};
eval {{ $moment = $results->TotalSpin; }};
print "RESULT status=completed calculation=$calc spin=$initial_spin "
    . "atoms=$atom_count energy=$energy final_moment=$moment\\n";
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xsd", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--calculation-name", required=True)
    parser.add_argument("--spins", required=True, nargs="+", type=int)
    parser.add_argument("--cores", type=int, default=48)
    parser.add_argument("--cutoff", type=float, default=326.5)
    parser.add_argument("--max-scf-cycles", type=int, default=500)
    parser.add_argument("--max-geometry-iterations", type=int, default=150)
    parser.add_argument("--scf-convergence", type=float, default=0.000002)
    parser.add_argument("--force-convergence", type=float, default=0.03)
    parser.add_argument("--dispersion-method", default="TS")
    parser.add_argument("--spin-mode", choices=("fixed", "relaxed"), default="fixed")
    parser.add_argument("--density-mixing-amplitude", type=float, default=0.05)
    parser.add_argument("--spin-mixing-amplitude", type=float, default=0.08)
    parser.add_argument("--diis-history", type=int, default=5)
    parser.add_argument("--smearing", type=float, default=0.2)
    parser.add_argument(
        "--optimization-algorithm", choices=("BFGS", "LBFGS"), default="BFGS"
    )
    parser.add_argument("--allow-local", action="store_true")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.cores < 1:
        raise ValueError("cores must be positive")
    if any(spin < 0 for spin in args.spins):
        raise ValueError("spin values must be non-negative")
    if args.diis_history < 1:
        raise ValueError("DIIS history must be positive")
    for name in (
        "density_mixing_amplitude",
        "spin_mixing_amplitude",
        "smearing",
        "scf_convergence",
        "force_convergence",
    ):
        if getattr(args, name) <= 0:
            raise ValueError(f"{name} must be positive")


def main() -> int:
    args = parse_args()
    validate_args(args)
    metadata = validate_xsd(args.xsd)
    root = args.output_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    base_calc = safe_name(args.calculation_name)
    tasks = []

    for spin in args.spins:
        task_name = safe_name(f"{base_calc}_s{spin}_{args.cores}c", max_length=48)
        task_dir = root / task_name
        task_dir.mkdir(parents=True, exist_ok=False)
        model_name = f"{base_calc}_s{spin}.xsd"
        pl_name = f"run_{task_name}.pl"
        shutil.copy2(args.xsd, task_dir / model_name)
        (task_dir / pl_name).write_text(
            make_pl(
                args,
                model_name,
                task_name,
                spin,
                metadata["atom3d_entries"],
            ),
            encoding="utf-8",
        )
        tasks.append(
            {
                "task": task_name,
                "directory": str(task_dir),
                "xsd_document": model_name,
                "pl_document": pl_name,
                "expected_atoms": metadata["atom3d_entries"],
                "initial_spin": spin,
                "spin_mode": args.spin_mode,
                "cores": args.cores,
                "gateway": "USER_SELECTS_IN_MATERIALS_STUDIO",
                "result_documents": ["opt.xsd", "report.txt"],
            }
        )

    manifest = {
        "source": metadata,
        "calculation_type": "CASTEP GeometryOptimization",
        "automatic_submission": False,
        "gateway": "not hard-coded; user selects during Run on Server",
        "allow_local": bool(args.allow_local),
        "settings": {
            "spin_mode": args.spin_mode,
            "max_scf_cycles": args.max_scf_cycles,
            "optimization_algorithm": args.optimization_algorithm,
            "density_mixing_amplitude": args.density_mixing_amplitude,
            "spin_mixing_amplitude": args.spin_mixing_amplitude,
            "diis_history": args.diis_history,
            "smearing": args.smearing,
        },
        "tasks": tasks,
    }
    (root / "package_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    instructions = (
        "MANUAL SUBMISSION REQUIRED\n\n"
        "For each task directory, import both the XSD and PL into the same "
        "Materials Studio project folder. Open the XSD and verify the structure. "
        "Open the PL, press Ctrl+F5, select the Gateway, and confirm the requested "
        "core count. No Gateway is hard-coded and this generator submits no job.\n"
        "Successful scripts return opt.xsd and report.txt and print "
        "'RESULT status=completed' in PL output.\n"
    )
    (root / "MANUAL_SUBMISSION.txt").write_text(instructions, encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
