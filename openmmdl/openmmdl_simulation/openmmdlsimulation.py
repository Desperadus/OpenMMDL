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

    # Validate restart arguments
    if args.restart:
        if args.checkpoint is None:
            print("Error: --checkpoint is required when using --restart")
            return 1
        if args.restart_step is None:
            print("Error: --restart-step is required when using --restart")
            return 1

    # Create or prepare the simulation folder
    if args.restart:
        # In restart mode, don't delete existing folder - preserve existing files
        if not os.path.exists(args.folder):
            os.mkdir(args.folder)
    else:
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

        # Handle restart-specific files
        if args.restart:
            # Validate and copy checkpoint
            if not validate_file_format(args.checkpoint, input_formats["checkpoint"], "checkpoint"):
                return 1
            if not copy_file_if_exists(args.checkpoint, args.folder, "checkpoint file"):
                return 1

            # Validate and copy equilibrated topology (optional but recommended)
            if args.equilibrated is not None:
                if not validate_file_format(args.equilibrated, input_formats["equilibrated"], "equilibrated topology"):
                    return 1
                if not copy_file_if_exists(args.equilibrated, args.folder, "equilibrated topology file"):
                    return 1

            # Validate and copy existing trajectory (optional)
            if args.trajectory is not None:
                if not validate_file_format(args.trajectory, input_formats["trajectory"], "trajectory"):
                    return 1
                if not copy_file_if_exists(args.trajectory, args.folder, "trajectory file"):
                    return 1

            # Create a restart configuration file that the simulation script can read
            restart_config_path = os.path.join(args.folder, "restart_config.txt")
            with open(restart_config_path, "w") as f:
                f.write("restart=true\n")
                f.write(f"checkpoint={os.path.basename(args.checkpoint)}\n")
                f.write(f"restart_step={args.restart_step}\n")
                if args.equilibrated:
                    f.write(f"equilibrated={os.path.basename(args.equilibrated)}\n")
                if args.trajectory:
                    f.write(f"trajectory={os.path.basename(args.trajectory)}\n")
            print(f"Restart configuration written to {restart_config_path}")

        os.chdir(args.folder)
        os.system("python3 *.py")


if __name__ == "__main__":
    main()
