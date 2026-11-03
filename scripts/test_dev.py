#!/usr/bin/env python3
"""Run with: python3 -m unittest discover -s scripts -p test_dev.py -v."""

import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import patch

import dev


class DevCommandTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))
        self.enterContext(patch.object(dev.shutil, "which", return_value="/usr/bin/docker"))
        self.settings_file = self.enterContext(patch.object(dev.Path, "is_file", return_value=True))
        self.run = self.enterContext(patch.object(dev.subprocess, "run"))

    def healthy_stack(self):
        outputs = [
            "Compose version",
            "Docker version",
            "django\nredis\npostgres",
            "container-id",
            json.dumps([{"Destination": "/ion", "Source": str(dev.ROOT)}]),
        ]
        self.run.side_effect = [subprocess.CompletedProcess([], 0, stdout=output) for output in outputs]

    def test_missing_docker(self):
        with patch.object(dev.shutil, "which", return_value=None):
            self.assertEqual(dev.main(["doctor"]), 1)
        self.run.assert_not_called()

    def test_unavailable_compose_or_daemon(self):
        for stage in (0, 1):
            with self.subTest(stage=stage):
                self.run.side_effect = [subprocess.CompletedProcess([], 0, stdout="version")] * stage + [subprocess.CompletedProcess([], 1)]
                self.assertEqual(dev.main(["doctor"]), 1)

    def test_diagnostic_timeout(self):
        self.run.side_effect = subprocess.TimeoutExpired("docker", 10)
        self.assertEqual(dev.main(["doctor"]), 1)

    def test_stopped_services(self):
        self.run.side_effect = [subprocess.CompletedProcess([], 0, stdout=output) for output in ("version", "version", "redis")]
        self.assertEqual(dev.main(["test"]), 1)
        self.assertEqual(self.run.call_count, 3)

    def test_wrong_checkout(self):
        self.healthy_stack()
        results = list(self.run.side_effect)
        results[-1].stdout = json.dumps([{"Destination": "/ion", "Source": str(dev.ROOT / "another-checkout")}])
        self.run.side_effect = results
        self.assertEqual(dev.main(["test"]), 1)
        self.assertEqual(self.run.call_count, 5)

    def test_missing_settings(self):
        self.healthy_stack()
        self.settings_file.return_value = False
        self.assertEqual(dev.main(["doctor"]), 1)

    def test_healthy_doctor_only_runs_diagnostics(self):
        self.healthy_stack()
        self.assertEqual(dev.main(["doctor"]), 0)
        self.assertEqual(self.run.call_count, 5)
        for call in self.run.call_args_list:
            self.assertEqual(call.kwargs["cwd"], dev.ROOT)
            self.assertEqual(call.kwargs["timeout"], 10)
            self.assertNotIn("exec", call.args[0])

    def test_test_arguments_and_exit_status_are_preserved(self):
        self.healthy_stack()
        self.run.side_effect = list(self.run.side_effect) + [subprocess.CompletedProcess([], 7)]
        args = ["intranet.apps.polls", "-v", "2", "--keepdb"]
        self.assertEqual(dev.main(["test", *args]), 7)
        self.run.assert_called_with(
            dev.COMPOSE + ["exec", "-T", "django", "python", "./manage.py", "test", "--noinput", *args], cwd=dev.ROOT, check=False
        )


if __name__ == "__main__":
    unittest.main()
