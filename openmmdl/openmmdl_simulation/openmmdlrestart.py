"""
openmmdl_restart.py
Restart simulations from checkpoints with OpenMM
"""

import argparse
import os


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
        r"               Restart OpenMM Protein-Ligand MD Simulations from Checkpoint                           ",
        r"                                     Version 1.2.0                                                     ",
    ]
)


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


def find_checkpoint_in_directory(directory):
    """Find the most recent checkpoint file in a directory.

    Args:
        directory (str): Path to the directory to search.

    Returns:
        str or None: Path to the most recent checkpoint file, or None if not found.
    """
    chk_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".chk"):
            filepath = os.path.join(directory, filename)
            chk_files.append((filepath, os.path.getmtime(filepath)))

    if not chk_files:
        return None

    # Return the most recently modified checkpoint file
    return max(chk_files, key=lambda x: x[1])[0]


def find_script_in_directory(directory):
    """Find a simulation script in a directory.

    Args:
        directory (str): Path to the directory to search.

    Returns:
        str or None: Path to a simulation script, or None if not found.
    """
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "restart_simulation.py":
            return os.path.join(directory, filename)
    return None


def find_topology_in_directory(directory):
    """Find a topology file in a directory.

    Args:
        directory (str): Path to the directory to search.

    Returns:
        str or None: Path to a topology file, or None if not found.
    """
    for filename in os.listdir(directory):
        if filename.endswith((".pdb", ".prmtop")):
            return os.path.join(directory, filename)
    return None


def find_coordinate_in_directory(directory):
    """Find an Amber coordinate file in a directory.

    Args:
        directory (str): Path to the directory to search.

    Returns:
        str or None: Path to a coordinate file, or None if not found.
    """
    for filename in os.listdir(directory):
        if filename.endswith(".inpcrd"):
            return os.path.join(directory, filename)
    return None


def find_trajectory_in_directory(directory):
    """Find a trajectory file in a directory.

    Args:
        directory (str): Path to the directory to search.

    Returns:
        str or None: Path to a trajectory file, or None if not found.
    """
    dcd_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".dcd"):
            filepath = os.path.join(directory, filename)
            dcd_files.append((filepath, os.path.getmtime(filepath)))

    if not dcd_files:
        return None

    # Return the most recently modified trajectory file
    return max(dcd_files, key=lambda x: x[1])[0]


def run_restart_simulation(args):
    """Run a restart simulation from checkpoint.

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

    # Resolve the simulation directory
    sim_directory = os.path.abspath(args.directory)
    if not os.path.exists(sim_directory):
        print(f"Error: Simulation directory not found: {sim_directory}")
        return 1

    print(f"Simulation directory: {sim_directory}")

    # Auto-detect files if not specified
    checkpoint = args.checkpoint
    if checkpoint is None:
        checkpoint = find_checkpoint_in_directory(sim_directory)
        if checkpoint is None:
            print("Error: No checkpoint file found in directory. Use --checkpoint to specify.")
            return 1
        print(f"Auto-detected checkpoint: {checkpoint}")
    elif not os.path.isabs(checkpoint):
        checkpoint = os.path.join(sim_directory, checkpoint)

    script = args.script
    if script is None:
        script = find_script_in_directory(sim_directory)
        if script is None:
            print("Error: No simulation script found in directory. Use --script to specify.")
            return 1
        print(f"Auto-detected script: {script}")
    elif not os.path.isabs(script):
        script = os.path.join(sim_directory, script)

    topology = args.topology
    if topology is None:
        topology = find_topology_in_directory(sim_directory)
        if topology is None:
            print("Error: No topology file found in directory. Use --topology to specify.")
            return 1
        print(f"Auto-detected topology: {topology}")
    elif not os.path.isabs(topology):
        topology = os.path.join(sim_directory, topology)

    coordinate = args.coordinate
    if coordinate is None:
        coordinate = find_coordinate_in_directory(sim_directory)
        if coordinate:
            print(f"Auto-detected coordinate file: {coordinate}")
    elif not os.path.isabs(coordinate):
        coordinate = os.path.join(sim_directory, coordinate)

    # Validate required files exist
    if not os.path.exists(checkpoint):
        print(f"Error: Checkpoint file not found: {checkpoint}")
        return 1

    if not os.path.exists(script):
        print(f"Error: Simulation script not found: {script}")
        return 1

    if not os.path.exists(topology):
        print(f"Error: Topology file not found: {topology}")
        return 1

    # Determine restart step
    restart_step = args.restart_step
    if restart_step is None:
        print("Warning: --restart-step not specified. Will attempt to infer from checkpoint.")
        print("         Specify --restart-step for precise control over the restart point.")
        # Default to 0 if not specified - the checkpoint will restore the actual step
        restart_step = 0

    # Generate restart simulation script
    restart_script_path = os.path.join(sim_directory, "restart_simulation.py")
    checkpoint_filename = os.path.basename(checkpoint)
    topology_filename = os.path.basename(topology)
    script_filename = os.path.basename(script)

    # Determine if using PDB or Amber format
    is_amber = topology.endswith(".prmtop")

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
print("Restart Step: {restart_step}")
print("=" * 70)

# Load the original simulation script to extract parameters
# Users should ensure the original script is compatible
original_script = "{script_filename}"

# Read topology
'''

    if is_amber:
        coord_filename = os.path.basename(coordinate) if coordinate else "coordinates.inpcrd"
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
simulation.currentStep = {restart_step}
print(f"Resuming from step: {restart_step}")

# Continue simulation
print("Continuing simulation...")
simulation.step(steps - {restart_step})

print("Restart simulation completed successfully!")
'''

    with open(restart_script_path, "w") as f:
        f.write(restart_script_content)

    print(f"\nGenerated restart script: {restart_script_path}")
    print(f"Checkpoint file: {checkpoint_filename}")
    print(f"Restart step: {restart_step}")
    print("-" * 70)

    # Change to folder and run the restart script
    os.chdir(sim_directory)
    print("Starting restart simulation...")
    os.system("python3 restart_simulation.py")

    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="openmmdl_restart",
        description=logo,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-d",
        "--directory",
        dest="directory",
        type=str,
        help="Directory where the simulation run has stopped (required)",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--checkpoint",
        dest="checkpoint",
        type=str,
        help="Path to checkpoint file (.chk). If not specified, the most recent .chk file in the directory will be used.",
        default=None,
    )
    parser.add_argument(
        "-s",
        "--script",
        dest="script",
        type=str,
        help="Path to the original simulation script (.py). If not specified, will be auto-detected.",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--topology",
        dest="topology",
        type=str,
        help="Path to topology file (.pdb or .prmtop). If not specified, will be auto-detected.",
        default=None,
    )
    parser.add_argument(
        "--coordinate",
        dest="coordinate",
        type=str,
        help="Path to Amber coordinate file (.inpcrd). If not specified, will be auto-detected.",
        default=None,
    )
    parser.add_argument(
        "--restart-step",
        dest="restart_step",
        type=int,
        help="Step number to restart simulation from. If not specified, will continue from checkpoint state.",
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

    input_formats = {
        "checkpoint": [".chk"],
        "script": [".py"],
        "topology": [".pdb", ".prmtop"],
        "coordinate": [".inpcrd"],
        "equilibrated": [".pdb"],
        "trajectory": [".dcd"],
    }

    args = parser.parse_args()

    # Validate file formats if provided
    if args.checkpoint and not validate_file_format(args.checkpoint, input_formats["checkpoint"], "checkpoint"):
        return 1
    if args.script and not validate_file_format(args.script, input_formats["script"], "script"):
        return 1
    if args.topology and not validate_file_format(args.topology, input_formats["topology"], "topology"):
        return 1
    if args.coordinate and not validate_file_format(args.coordinate, input_formats["coordinate"], "coordinate"):
        return 1
    if args.equilibrated and not validate_file_format(
        args.equilibrated, input_formats["equilibrated"], "equilibrated topology"
    ):
        return 1
    if args.trajectory and not validate_file_format(args.trajectory, input_formats["trajectory"], "trajectory"):
        return 1

    return run_restart_simulation(args)


if __name__ == "__main__":
    main()
