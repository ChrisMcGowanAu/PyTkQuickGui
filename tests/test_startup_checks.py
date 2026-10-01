import faulthandler
import unittest
from types import SimpleNamespace

import startup_checks


def lookup_for(version):
    """Return a metadata lookup that reports *version* for any package."""
    return lambda _package: version


def failing_lookup(_package):
    raise startup_checks.metadata.PackageNotFoundError("ttkbootstrap")


class StartupChecksTests(unittest.TestCase):
    def test_major_version_handles_common_version_shapes(self):
        self.assertEqual(startup_checks.major_version("2.0.1"), 2)
        self.assertEqual(startup_checks.major_version("1.20.2"), 1)
        self.assertEqual(startup_checks.major_version("2.0.1.dev0"), 2)
        self.assertEqual(startup_checks.major_version("2.0.1b1"), 2)
        self.assertEqual(startup_checks.major_version(None), 0)
        self.assertEqual(startup_checks.major_version("unknown"), 0)

    def test_installed_version_prefers_package_metadata(self):
        module = SimpleNamespace(__version__="1.9.9")
        self.assertEqual(
            startup_checks.installed_version(module, lookup_for("2.0.1")), "2.0.1"
        )

    def test_installed_version_falls_back_to_module_attributes(self):
        module = SimpleNamespace(VERSION="2.0.1")
        version = startup_checks.installed_version(module, failing_lookup)
        self.assertEqual(version, "2.0.1")
        self.assertEqual(
            startup_checks.installed_version(SimpleNamespace(), failing_lookup), "0.0"
        )

    def test_check_passes_for_supported_releases(self):
        for version in ("2.0.1", "2.5", "3.0.0"):
            with self.subTest(version=version):
                self.assertIsNone(
                    startup_checks.check_ttkbootstrap(None, lookup_for(version))
                )

    def test_check_explains_how_to_upgrade_for_old_releases(self):
        message = startup_checks.check_ttkbootstrap(None, lookup_for("1.20.2"))
        self.assertIsNotNone(message)
        self.assertIn("requires ttkbootstrap 2.0 or later", message)
        self.assertIn("Installed version: 1.20.2", message)
        self.assertIn(startup_checks.UPGRADE_COMMAND, message)

    def test_check_fails_closed_when_the_version_is_unknown(self):
        message = startup_checks.check_ttkbootstrap(SimpleNamespace(), failing_lookup)
        self.assertIsNotNone(message)
        self.assertIn("Installed version: 0.0", message)

    def test_check_does_not_import_tkinter(self):
        """The guard has to work before any Tk window exists."""
        self.assertNotIn("tkinter", str(startup_checks.__dict__.keys()))
        self.assertNotIn("tkinter", startup_checks.__doc__ or "")

    def test_crash_diagnostics_are_enabled(self):
        """A segfault should print the Python frame, and SIGUSR1 a traceback."""
        self.assertTrue(startup_checks.enable_crash_diagnostics())
        self.assertTrue(faulthandler.is_enabled())

    def test_crash_diagnostics_never_raise(self):
        """Diagnostics must not be able to stop the application."""
        original = startup_checks.faulthandler.enable
        startup_checks.faulthandler.enable = _raise_oserror
        try:
            self.assertFalse(startup_checks.enable_crash_diagnostics())
        finally:
            startup_checks.faulthandler.enable = original


def _raise_oserror():
    raise OSError("no stderr")


if __name__ == "__main__":
    unittest.main()
