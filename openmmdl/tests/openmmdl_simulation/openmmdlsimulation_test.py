"""Tests for openmmdl simulation CLI with restart functionality."""

import os
import pytest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from openmmdl.openmmdl_simulation.openmmdlsimulation import (
    copy_file_if_exists,
    validate_file_format,
    main,
)


@pytest.fixture
def test_data_directory():
    """Return the path to the test data directory."""
    return Path(__file__).parent.parent / "data" / "in"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


class TestCopyFileIfExists:
    """Tests for copy_file_if_exists function."""

    def test_copy_existing_file(self, test_data_directory, temp_dir):
        """Test copying a file that exists."""
        src_file = test_data_directory / "6b73.pdb"
        result = copy_file_if_exists(str(src_file), temp_dir, "test file")
        assert result is True
        assert os.path.exists(os.path.join(temp_dir, "6b73.pdb"))

    def test_copy_nonexistent_file(self, temp_dir, capsys):
        """Test copying a file that doesn't exist."""
        result = copy_file_if_exists("/nonexistent/file.pdb", temp_dir, "test file")
        assert result is False
        captured = capsys.readouterr()
        assert "Wrong test file path" in captured.out

    def test_copy_none_file(self, temp_dir):
        """Test copying when file path is None (optional parameter)."""
        result = copy_file_if_exists(None, temp_dir, "test file")
        assert result is True


class TestValidateFileFormat:
    """Tests for validate_file_format function."""

    def test_valid_format_pdb(self):
        """Test validation of a valid PDB file."""
        result = validate_file_format("protein.pdb", [".pdb", ".prmtop"], "topology")
        assert result is True

    def test_valid_format_prmtop(self):
        """Test validation of a valid prmtop file."""
        result = validate_file_format("protein.prmtop", [".pdb", ".prmtop"], "topology")
        assert result is True

    def test_invalid_format(self, capsys):
        """Test validation of an invalid file format."""
        result = validate_file_format("protein.xyz", [".pdb", ".prmtop"], "topology")
        assert result is False
        captured = capsys.readouterr()
        assert "Wrong Format for topology" in captured.out

    def test_validate_none_file(self):
        """Test validation when file path is None (optional parameter)."""
        result = validate_file_format(None, [".pdb"], "topology")
        assert result is True

    def test_valid_checkpoint_format(self):
        """Test validation of checkpoint file format."""
        result = validate_file_format("checkpoint.chk", [".chk"], "checkpoint")
        assert result is True

    def test_valid_dcd_format(self):
        """Test validation of DCD trajectory format."""
        result = validate_file_format("trajectory.dcd", [".dcd"], "trajectory")
        assert result is True


class TestMainRestartValidation:
    """Tests for main function restart argument validation."""

    @patch("openmmdl.openmmdl_simulation.openmmdlsimulation.os.system")
    @patch("openmmdl.openmmdl_simulation.openmmdlsimulation.os.chdir")
    def test_restart_requires_checkpoint(self, mock_chdir, mock_system, capsys):
        """Test that restart mode requires checkpoint argument."""
        with patch(
            "sys.argv",
            [
                "openmmdl_simulation",
                "-f",
                "test_folder",
                "-s",
                "script.py",
                "-t",
                "topology.pdb",
                "--restart",
            ],
        ):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "--checkpoint is required" in captured.out

    @patch("openmmdl.openmmdl_simulation.openmmdlsimulation.os.system")
    @patch("openmmdl.openmmdl_simulation.openmmdlsimulation.os.chdir")
    def test_restart_requires_restart_step(self, mock_chdir, mock_system, capsys):
        """Test that restart mode requires restart-step argument."""
        with patch(
            "sys.argv",
            [
                "openmmdl_simulation",
                "-f",
                "test_folder",
                "-s",
                "script.py",
                "-t",
                "topology.pdb",
                "--restart",
                "--checkpoint",
                "checkpoint.chk",
            ],
        ):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "--restart-step is required" in captured.out


class TestRestartConfigFile:
    """Tests for restart configuration file generation."""

    @patch("openmmdl.openmmdl_simulation.openmmdlsimulation.os.system")
    def test_restart_config_file_created(self, mock_system, test_data_directory, temp_dir):
        """Test that restart config file is created with correct content."""
        script_path = temp_dir + "/test_script.py"
        topology_path = test_data_directory / "6b73.pdb"
        checkpoint_path = test_data_directory / "checkpoint.chk"
        equilibrated_path = test_data_directory / "Equilibration_6b73.pdb"
        folder_path = temp_dir + "/restart_test"

        # Create a dummy script file
        with open(script_path, "w") as f:
            f.write("# Dummy script\nprint('test')\n")

        with patch(
            "sys.argv",
            [
                "openmmdl_simulation",
                "-f",
                folder_path,
                "-s",
                script_path,
                "-t",
                str(topology_path),
                "--restart",
                "--checkpoint",
                str(checkpoint_path),
                "--equilibrated",
                str(equilibrated_path),
                "--restart-step",
                "10000",
            ],
        ):
            # We need to change cwd back after test
            original_cwd = os.getcwd()
            try:
                main()
            finally:
                os.chdir(original_cwd)

            # Check that restart config was created
            config_path = os.path.join(folder_path, "restart_config.txt")
            assert os.path.exists(config_path)

            with open(config_path, "r") as f:
                content = f.read()
                assert "restart=true" in content
                assert "checkpoint=checkpoint.chk" in content
                assert "restart_step=10000" in content
                assert "equilibrated=Equilibration_6b73.pdb" in content


class TestFolderPreservation:
    """Tests for folder handling in normal vs restart mode."""

    def test_normal_mode_recreates_folder(self, temp_dir):
        """Test that normal mode recreates the folder."""
        folder_path = os.path.join(temp_dir, "test_folder")
        os.makedirs(folder_path)
        test_file = os.path.join(folder_path, "existing_file.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        script_path = os.path.join(temp_dir, "test.py")
        with open(script_path, "w") as f:
            f.write("# test script\n")

        topology_path = os.path.join(temp_dir, "test.pdb")
        with open(topology_path, "w") as f:
            f.write("# test topology\n")

        with patch("openmmdl.openmmdl_simulation.openmmdlsimulation.os.system"):
            original_cwd = os.getcwd()
            try:
                with patch(
                    "sys.argv",
                    [
                        "openmmdl_simulation",
                        "-f",
                        folder_path,
                        "-s",
                        script_path,
                        "-t",
                        topology_path,
                    ],
                ):
                    main()
            finally:
                os.chdir(original_cwd)

            # The existing file should be removed in normal mode
            assert not os.path.exists(test_file)
