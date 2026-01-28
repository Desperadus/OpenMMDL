"""Tests for openmmdl restart CLI command."""

import os
import pytest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from openmmdl.openmmdl_simulation.openmmdlrestart import (
    validate_file_format,
    find_checkpoint_in_directory,
    find_script_in_directory,
    find_topology_in_directory,
    find_coordinate_in_directory,
    find_trajectory_in_directory,
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


class TestFileDetection:
    """Tests for auto-detection of files in a directory."""

    def test_find_checkpoint_in_directory(self, temp_dir):
        """Test finding checkpoint file in directory."""
        chk_path = os.path.join(temp_dir, "checkpoint.chk")
        with open(chk_path, "w") as f:
            f.write("test checkpoint")

        result = find_checkpoint_in_directory(temp_dir)
        assert result == chk_path

    def test_find_checkpoint_returns_none_when_missing(self, temp_dir):
        """Test that None is returned when no checkpoint exists."""
        result = find_checkpoint_in_directory(temp_dir)
        assert result is None

    def test_find_script_in_directory(self, temp_dir):
        """Test finding script file in directory."""
        script_path = os.path.join(temp_dir, "simulation.py")
        with open(script_path, "w") as f:
            f.write("# simulation script")

        result = find_script_in_directory(temp_dir)
        assert result == script_path

    def test_find_script_ignores_restart_script(self, temp_dir):
        """Test that restart_simulation.py is ignored."""
        restart_path = os.path.join(temp_dir, "restart_simulation.py")
        with open(restart_path, "w") as f:
            f.write("# restart script")

        result = find_script_in_directory(temp_dir)
        assert result is None

    def test_find_topology_pdb(self, temp_dir):
        """Test finding PDB topology file."""
        pdb_path = os.path.join(temp_dir, "protein.pdb")
        with open(pdb_path, "w") as f:
            f.write("ATOM...")

        result = find_topology_in_directory(temp_dir)
        assert result == pdb_path

    def test_find_topology_prmtop(self, temp_dir):
        """Test finding prmtop topology file."""
        prmtop_path = os.path.join(temp_dir, "protein.prmtop")
        with open(prmtop_path, "w") as f:
            f.write("ATOM...")

        result = find_topology_in_directory(temp_dir)
        assert result == prmtop_path

    def test_find_coordinate_in_directory(self, temp_dir):
        """Test finding Amber coordinate file."""
        inpcrd_path = os.path.join(temp_dir, "coords.inpcrd")
        with open(inpcrd_path, "w") as f:
            f.write("coordinates")

        result = find_coordinate_in_directory(temp_dir)
        assert result == inpcrd_path

    def test_find_trajectory_in_directory(self, temp_dir):
        """Test finding trajectory file."""
        dcd_path = os.path.join(temp_dir, "trajectory.dcd")
        with open(dcd_path, "w") as f:
            f.write("trajectory")

        result = find_trajectory_in_directory(temp_dir)
        assert result == dcd_path


class TestMainRestartValidation:
    """Tests for main function with restart command."""

    def test_restart_requires_directory(self, capsys):
        """Test that restart command requires directory argument."""
        with patch("sys.argv", ["openmmdl_restart"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2  # argparse error code

    def test_restart_with_nonexistent_directory(self, capsys):
        """Test that restart fails with nonexistent directory."""
        with patch("sys.argv", ["openmmdl_restart", "-d", "/nonexistent/directory"]):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "Simulation directory not found" in captured.out

    @patch("openmmdl.openmmdl_simulation.openmmdlrestart.os.system")
    def test_restart_auto_detects_files(self, mock_system, test_data_directory, temp_dir, capsys):
        """Test that restart command auto-detects files in directory."""
        # Set up a simulation directory with the required files
        script_path = os.path.join(temp_dir, "simulation.py")
        with open(script_path, "w") as f:
            f.write("# simulation script\nsteps = 1000\n")

        # Copy test files
        shutil.copy(test_data_directory / "6b73.pdb", temp_dir)
        shutil.copy(test_data_directory / "checkpoint.chk", temp_dir)

        original_cwd = os.getcwd()
        try:
            with patch(
                "sys.argv",
                [
                    "openmmdl_restart",
                    "-d",
                    temp_dir,
                    "--restart-step",
                    "5000",
                ],
            ):
                result = main()
        finally:
            os.chdir(original_cwd)

        assert result == 0
        captured = capsys.readouterr()
        assert "Auto-detected checkpoint" in captured.out
        assert "Auto-detected script" in captured.out
        assert "Auto-detected topology" in captured.out


class TestRestartScriptGeneration:
    """Tests for restart simulation script generation."""

    @patch("openmmdl.openmmdl_simulation.openmmdlrestart.os.system")
    def test_restart_script_created(self, mock_system, test_data_directory, temp_dir):
        """Test that restart simulation script is created with correct content."""
        script_path = os.path.join(temp_dir, "test_script.py")
        with open(script_path, "w") as f:
            f.write("# Dummy script\nprint('test')\nsteps = 10000\n")

        # Copy test files to temp directory
        shutil.copy(test_data_directory / "6b73.pdb", temp_dir)
        shutil.copy(test_data_directory / "checkpoint.chk", temp_dir)

        original_cwd = os.getcwd()
        try:
            with patch(
                "sys.argv",
                [
                    "openmmdl_restart",
                    "-d",
                    temp_dir,
                    "-s",
                    "test_script.py",
                    "-t",
                    "6b73.pdb",
                    "-c",
                    "checkpoint.chk",
                    "--restart-step",
                    "10000",
                ],
            ):
                main()
        finally:
            os.chdir(original_cwd)

        # Check that restart simulation script was created
        restart_script_path = os.path.join(temp_dir, "restart_simulation.py")
        assert os.path.exists(restart_script_path)

        with open(restart_script_path, "r") as f:
            content = f.read()
            assert "OpenMMDL Restart Simulation" in content
            assert "checkpoint.chk" in content
            assert "10000" in content
            assert "loadCheckpoint" in content

    @patch("openmmdl.openmmdl_simulation.openmmdlrestart.os.system")
    def test_restart_with_amber_topology(self, mock_system, temp_dir):
        """Test restart with Amber topology format."""
        script_path = os.path.join(temp_dir, "test_script.py")
        with open(script_path, "w") as f:
            f.write("# Dummy script\nsteps = 10000\n")

        prmtop_path = os.path.join(temp_dir, "protein.prmtop")
        with open(prmtop_path, "w") as f:
            f.write("# Amber topology\n")

        inpcrd_path = os.path.join(temp_dir, "coords.inpcrd")
        with open(inpcrd_path, "w") as f:
            f.write("# Amber coordinates\n")

        chk_path = os.path.join(temp_dir, "checkpoint.chk")
        with open(chk_path, "w") as f:
            f.write("# checkpoint\n")

        original_cwd = os.getcwd()
        try:
            with patch(
                "sys.argv",
                [
                    "openmmdl_restart",
                    "-d",
                    temp_dir,
                    "-s",
                    "test_script.py",
                    "-t",
                    "protein.prmtop",
                    "-c",
                    "checkpoint.chk",
                    "--coordinate",
                    "coords.inpcrd",
                    "--restart-step",
                    "5000",
                ],
            ):
                main()
        finally:
            os.chdir(original_cwd)

        restart_script_path = os.path.join(temp_dir, "restart_simulation.py")
        assert os.path.exists(restart_script_path)

        with open(restart_script_path, "r") as f:
            content = f.read()
            assert "AmberPrmtopFile" in content
            assert "AmberInpcrdFile" in content


class TestInvalidFormats:
    """Tests for invalid file format handling."""

    def test_invalid_checkpoint_format(self, temp_dir, capsys):
        """Test rejection of invalid checkpoint format."""
        with patch(
            "sys.argv",
            [
                "openmmdl_restart",
                "-d",
                temp_dir,
                "-c",
                "checkpoint.xyz",
            ],
        ):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "Wrong Format for checkpoint" in captured.out

    def test_invalid_topology_format(self, temp_dir, capsys):
        """Test rejection of invalid topology format."""
        with patch(
            "sys.argv",
            [
                "openmmdl_restart",
                "-d",
                temp_dir,
                "-t",
                "topology.xyz",
            ],
        ):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "Wrong Format for topology" in captured.out
