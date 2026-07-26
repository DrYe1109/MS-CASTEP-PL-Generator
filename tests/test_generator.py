import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_castep_pl_package.py"
)
SPEC = importlib.util.spec_from_file_location("castep_generator", SCRIPT)
GENERATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GENERATOR)


class GeneratorTests(unittest.TestCase):
    def test_portable_windows_entrypoints_are_present(self):
        root = Path(__file__).resolve().parents[1]
        configure_bat = (root / "Configure-CASTEP-PL-Skill.bat").read_text(
            encoding="utf-8"
        )
        generate_bat = (root / "Generate-CASTEP-PL-Package.bat").read_text(
            encoding="utf-8"
        )
        self.assertIn("%~dp0", configure_bat)
        self.assertIn("%~dp0", generate_bat)
        self.assertIn("pl-skill.local.bat", generate_bat)
        self.assertIn("--spin-mode fixed", generate_bat)
        self.assertNotIn("D:\\CodexInstall", configure_bat + generate_bat)

    def test_safe_name_is_short_and_stable(self):
        value = "BLG_AB_8x8_VC_top_" + "very_long_name_" * 10
        first = GENERATOR.safe_name(value)
        self.assertLessEqual(len(first), 40)
        self.assertEqual(first, GENERATOR.safe_name(value))

    def test_generated_pl_avoids_virtual_path_file_io(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            xsd = root / "input.xsd"
            xsd.write_text(
                "<XSD>" + "<Atom3d ID='1'/>" * 4 + "</XSD>" + " " * 300,
                encoding="utf-8",
            )
            output = root / "out"
            original = list(sys.argv)
            try:
                sys.argv = [
                    str(SCRIPT),
                    "--xsd",
                    str(xsd),
                    "--output-dir",
                    str(output),
                    "--calculation-name",
                    "vacancy_reference",
                    "--spins",
                    "1",
                    "3",
                ]
                self.assertEqual(GENERATOR.main(), 0)
            finally:
                sys.argv = original

            scripts = sorted(output.glob("*/*.pl"))
            self.assertEqual(len(scripts), 2)
            manifest = (output / "package_manifest.json").read_text(encoding="utf-8")
            self.assertIn('"source_name": "input.xsd"', manifest)
            self.assertNotIn("source_path", manifest)
            text = scripts[0].read_text(encoding="utf-8")
            self.assertIn('"OptimizeTotalSpin" => "No"', text)
            self.assertIn('SaveAs("/$calc/opt.xsd")', text)
            self.assertIn('SaveAs("/$calc/report.txt")', text)
            self.assertIn("RESULT status=completed", text)
            self.assertNotIn("open(my", text)
            self.assertIn("Unexpected atom count", text)


if __name__ == "__main__":
    unittest.main()
