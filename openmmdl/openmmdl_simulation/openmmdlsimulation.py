"""
mmdl_simulation.py
Perform Simulations of Protein-ligand complexes with OpenMM
"""

import argparse
import os
import shutil


logo = "\n".join(
    [
        r"     ,-----.    .-------.     .-''-.  ,---.   .--.,---.    ,---.,---.    ,---. ______       .---.      ",
        r"   .'  .-,  '.  \  _(`)_ \  .'_ _   \ |    \  |  ||    \  /    ||    \  /    ||    _ `''.   | ,_|      ",
        r"  / ,-.|  \ _ \ | (_ o._)| / ( ` )   '|  ,  \ |  ||  ,  \/  ,  ||  ,  \/  ,  || _ | ) _  \,-./  )      ",
        r" ;  \  '_ /  | :|  (_,_) /. (_ o _)  ||  |\_ \|  ||  |\_   /|  ||  |\_   /|  ||( ''_'  ) |\  '_ '`)    ",
        r" |  _`,/ \ _/  ||   '-.-' |  (_,_)___||  _( )_\  ||  _( )_/ |  ||  _( )_/ |  || . (_) `. | > (_)  )    ",
        r" : (  '\_/ \   ;|   |     '  \   .---.| (_ o _)  || (_ o _) |  || (_ o _) |  ||(_    ._) '(  .  .-'    ",
        r"  \ `_/  \  ) / |   |      \  `-'    /|  (_,_)\  ||  (_,_)  |  ||  (_,_)  |  ||  (_.\.' /  `-'`-'|___  ",
        r"   '. \_/``'.'  /   )       \       / |  |    |  ||  |      |  ||  |      |  ||       .'    |        \ ",
        r"     '-----'    `---'        `'-..-'  '--'    '--''--'      '--''--'      '--''-----'`      `--------` ",
        r"              Prepare and Perform OpenMM Protein-Ligand MD Simulations                                 ",
        r"                                     Version 1.2.0                                                     ",
    ]
)


def copy_file_if_exists(file_path, dest_folder, file_description):
    """Copy a file to destination folder if it exists.

    Args:
        file_path (str): Path to the source file.
        dest_folder (str): Destination folder path.
        file_description (str): Description of the file for error messages.

    Returns:
        bool: True if file was copied successfully, False otherwise.
    """
    if file_path is None:
        return True
    if os.path.exists(file_path):
        shutil.copy(file_path, dest_folder)
        return True
    else:
        print(f"Wrong {file_description} path, try the absolute path")
        return False


def validate_file_format(file_path, valid_extensions, file_description):
    """Validate that a file has one of the expected extensions.

    Args:
        file_path (str): Path to the file.
        valid_extensions (list): List of valid file extensions (e.g., ['.pdb', '.prmtop']).
        file_description (str): Description of the file for error messages.

    Returns:
        bool: True if file has valid extension, False otherwise.
    """
    if file_path is None:
        return True
    for ext in valid_extensions:
        if ext in file_path:
            return True
    print(f"Wrong Format for {file_description}, expected one of: {', '.join(valid_extensions)}")
    return False


def run_restart_simulation(args):
    """Run a restart simulation from checkpoint - completely separate branch from normal simulation.

    This function handles all restart logic directly from CLI without requiring
    modifications to the generated simulation script.

    Args:
        args: Parsed command line arguments containing restart parameters.

    Returns:
        int: 0 on success, 1 on failure.
    """
    print("=" * 70)
    print("RESTART MODE: Continuing simulation from checkpoint")
    print("=" * 70)

    # Validate required files exist
    if not os.path.exists(args.checkpoint):
        print(f"Error: Checkpoint file not found: {args.checkpoint}")
        return 1

    if not os.path.exists(args.script):
        print(f"Error: Simulation script not found: {args.script}")
        return 1

    if not os.path.exists(args.topology):
        print(f"Error: Topology file not found: {args.topology}")
        return 1

    # Create or use existing folder (preserve contents in restart mode)
    if not os.path.exists(args.folder):
        os.mkdir(args.folder)
        print(f"Created simulation folder: {args.folder}")
    else:
        print(f"Using existing simulation folder: {args.folder}")

    # Copy necessary files to folder
    shutil.copy(args.script, args.folder)
    shutil.copy(args.topology, args.folder)
    shutil.copy(args.checkpoint, args.folder)

    if args.ligand and os.path.exists(args.ligand):
        shutil.copy(args.ligand, args.folder)

    if args.coordinate and os.path.exists(args.coordinate):
        shutil.copy(args.coordinate, args.folder)

    if args.equilibrated and os.path.exists(args.equilibrated):
        shutil.copy(args.equilibrated, args.folder)

    if args.trajectory and os.path.exists(args.trajectory):
        shutil.copy(args.trajectory, args.folder)

    # Generate restart simulation script
    restart_script_path = os.path.join(args.folder, "restart_simulation.py")
    checkpoint_filename = os.path.basename(args.checkpoint)
    topology_filename = os.path.basename(args.topology)

    # Determine if using PDB or Amber format
    is_amber = args.topology.endswith(".prmtop")

    restart_script_content = f'''"""
OpenMMDL Restart Simulation Script
Generated automatically for restarting from checkpoint.
"""

import sys
import os
from openmm import Platform, LangevinMiddleIntegrator, MonteCarloBarostat
from openmm.app import (
    PDBFile, Simulation, DCDReporter, StateDataReporter, CheckpointReporter,
    PDBReporter, AmberPrmtopFile, AmberInpcrdFile
)
from openmm import unit

print("=" * 70)
print("OpenMMDL Restart Simulation")
print("Checkpoint: {checkpoint_filename}")
print("Restart Step: {args.restart_step}")
print("=" * 70)

# Load the original simulation script to extract parameters
# Users should ensure the original script is compatible
original_script = "{os.path.basename(args.script)}"

# Read topology
'''

    if is_amber:
        coord_filename = os.path.basename(args.coordinate) if args.coordinate else "coordinates.inpcrd"
        restart_script_content += f'''
prmtop = AmberPrmtopFile("{topology_filename}")
inpcrd = AmberInpcrdFile("{coord_filename}")
topology = prmtop.topology
positions = inpcrd.positions
'''
    else:
        restart_script_content += f'''
pdb = PDBFile("{topology_filename}")
topology = pdb.topology
positions = pdb.positions
'''

    restart_script_content += f'''
# Execute the original script to get system and simulation parameters
# This loads all the configurations from the original script
print("Loading configuration from original script...")
exec(open(original_script).read())

# Load checkpoint and continue simulation
print(f"Loading checkpoint: {checkpoint_filename}")
simulation.loadCheckpoint("{checkpoint_filename}")

# Set the current step to the restart step
simulation.currentStep = {args.restart_step}
print(f"Resuming from step: {args.restart_step}")

# Continue simulation
print("Continuing simulation...")
simulation.step(steps - {args.restart_step})

print("Restart simulation completed successfully!")
'''

    with open(restart_script_path, "w") as f:
        f.write(restart_script_content)

    print(f"Generated restart script: {restart_script_path}")
    print(f"Checkpoint file: {checkpoint_filename}")
    print(f"Restart step: {args.restart_step}")
    print("-" * 70)

    # Change to folder and run the restart script
    os.chdir(args.folder)
    print("Starting restart simulation...")
    os.system("python3 restart_simulation.py")

    return 0


def run_normal_simulation(args, input_formats):
    """Run a normal (non-restart) simulation.

    Args:
        args: Parsed command line arguments.
        input_formats: Dictionary of valid file extensions.

    Returns:
        int: 0 on success, 1 on failure.
    """
    # Normal mode: create fresh folder
    if not os.path.exists(args.folder):
        os.mkdir(args.folder)
    else:
        shutil.rmtree(args.folder)
        os.mkdir(args.folder)

    if os.path.exists(args.folder):
        # Validate and copy script
        if not validate_file_format(args.script, input_formats["script"], "script"):
            return 1
        if not copy_file_if_exists(args.script, args.folder, "python script"):
            return 1

        # Validate and copy topology
        if not validate_file_format(args.topology, input_formats["topology"], "topology"):
            return 1
        if not copy_file_if_exists(args.topology, args.folder, "topology file"):
            return 1

        # Validate and copy ligand (optional)
        if args.ligand is not None:
            if not validate_file_format(args.ligand, input_formats["ligand"], "ligand"):
                return 1
            if not copy_file_if_exists(args.ligand, args.folder, "ligand file"):
                return 1

        # Validate and copy coordinate (optional)
        if args.coordinate is not None:
            if not validate_file_format(args.coordinate, input_formats["coordinate"], "coordinate"):
                return 1
            if not copy_file_if_exists(args.coordinate, args.folder, "coordinates file"):
                return 1

        os.chdir(args.folder)
        os.system("python3 *.py")

    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="openmmdl_simulation",
        description=logo,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-f",
        dest="folder",
        type=str,
        help="Folder Name for MD Simulation",
        required=True,
    )
    parser.add_argument(
        "-s",
        dest="script",
        type=str,
        help="MD Simulation script",
        required=True,
    )
    parser.add_argument("-t", dest="topology", help="Protein Topology PDB/Amber File", required=True)
    parser.add_argument("-l", dest="ligand", help="SDF File of Ligand", default=None)
    parser.add_argument("-c", dest="coordinate", help="Amber coordinates file", default=None)

    # Restart-related arguments
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Enable restart mode to continue a simulation from a checkpoint",
    )
    parser.add_argument(
        "--checkpoint",
        dest="checkpoint",
        type=str,
        help="Path to checkpoint file (.chk) for restarting simulation",
        default=None,
    )
    parser.add_argument(
        "--equilibrated",
        dest="equilibrated",
        type=str,
        help="Path to equilibrated topology file (PDB) for restarting simulation",
        default=None,
    )
    parser.add_argument(
        "--trajectory",
        dest="trajectory",
        type=str,
        help="Path to existing trajectory file (.dcd) to append to during restart",
        default=None,
    )
    parser.add_argument(
        "--restart-step",
        dest="restart_step",
        type=int,
        help="Step number to restart simulation from",
        default=None,
    )

    input_formats = {
        "script": [".py"],
        "topology": [".pdb", ".prmtop"],
        "ligand": [".sdf", ".mol"],
        "coordinate": [".inpcrd"],
        "checkpoint": [".chk"],
        "equilibrated": [".pdb"],
        "trajectory": [".dcd"],
    }

    args = parser.parse_args()

    # RESTART BRANCH: Completely separate code path for restart mode
    if args.restart:
        # Validate restart-specific arguments
        if args.checkpoint is None:
            print("Error: --checkpoint is required when using --restart")
            return 1
        if args.restart_step is None:
            print("Error: --restart-step is required when using --restart")
            return 1

        # Validate file formats for restart
        if not validate_file_format(args.checkpoint, input_formats["checkpoint"], "checkpoint"):
            return 1
        if args.equilibrated and not validate_file_format(
            args.equilibrated, input_formats["equilibrated"], "equilibrated topology"
        ):
            return 1
        if args.trajectory and not validate_file_format(args.trajectory, input_formats["trajectory"], "trajectory"):
            return 1

        # Run the restart simulation (completely separate branch)
        return run_restart_simulation(args)

    # NORMAL BRANCH: Standard simulation workflow
    else:
        return run_normal_simulation(args, input_formats)


if __name__ == "__main__":
    main()
