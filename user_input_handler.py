import os
import inquirer
import colorama
from colorama import Fore, Style
from inquirer.themes import GreenPassion

colorama.init(autoreset=True)

def get_next_available_filename(base_name, directory, index):
    """
    Generate the next available file name if the base name exists.

    Args:
        base_name (str): The base file name without the index.
        directory (str): The directory to check for existing files.
        index (int): The current index for naming.

    Returns:
        str: The next available file name with an appended index.
    """
    name = f"{base_name}-{index}"
    ext = ".png"
    while os.path.exists(os.path.join(directory, f"{name}{ext}")):
        index += 1
        name = f"{base_name}-{index}"
    return f"{name}{ext}"


def get_user_input():
    """
    Collects and validates user input for the gradient generator.

    Returns:
        list: A list of dictionaries containing user inputs for each cover.
    """
    print(Fore.CYAN + Style.BRIGHT + """
 _   _       _   _             
| \ | | ___ | |_(_) ___  _ __  
|  \| |/ _ \| __| |/ _ \| '_ \ 
| |\  | (_) | |_| | (_) | | | |
|_|_\_|\___/ \__|_|\___/|_| |_|
  _____                        
 / ___|_____   _____ _ __      
| |   / _ \ \ / / _ \ '__|     
| |__| (_) \ V /  __/ |        
 \____\___/ \_/ \___|_|        
  _____                    
 / ___| ___ _ __               
| |  _ / _ \ '_ \              
| |_| |  __/ | | |             
 \____|\___|_| |_|             
    """)
    print("-" * 75)
    print("\n")

    # Ask for the number of covers
    num_covers_question = [
        inquirer.Text(
            "num_covers",
            message=Style.BRIGHT + "How many covers?",
            validate=lambda _, x: x.isdigit() and int(x) > 0,
        )
    ]
    num_covers = int(inquirer.prompt(num_covers_question, theme=GreenPassion())["num_covers"])

    # Ask for background mode (dark/light)
    mode_question = [
        inquirer.List(
            "dark_mode",
            message="Background mode:",
            choices=["Dark", "Light"],
            default="Dark",
        )
    ]
    dark_mode = inquirer.prompt(mode_question, theme=GreenPassion())["dark_mode"] == "Dark"

    # Ask if the user wants custom output names
    custom_name_question = [
        inquirer.List(
            "custom_name",
            message="Custom output name?",
            choices=["Yes", "No"],
            default="No",
        )
    ]
    use_custom_name = inquirer.prompt(custom_name_question, theme=GreenPassion())["custom_name"] == "Yes"

    # Get base name if custom output name is selected
    if use_custom_name:
        base_name = input(Fore.YELLOW + "Enter base name (e.g., 'custom-cover'): ").strip() or "custom-cover"
    else:
        base_name = "page"

    # Ensure the output directory exists
    output_dir = "backgrounds"
    os.makedirs(output_dir, exist_ok=True)

    # Collect inputs for each cover
    user_inputs_list = []
    for i in range(1, num_covers + 1):
        print(Fore.CYAN + Style.BRIGHT + f"\nCover {i}/{num_covers}:")
        text = input(Fore.WHITE + Style.BRIGHT + "Enter cover text " + Style.NORMAL + Style.DIM + "(empty for none)" + Style.RESET_ALL + ": ").strip() or " "
        
        # Generate the output file name
        output_file = os.path.join(output_dir, get_next_available_filename(base_name, output_dir, i))

        user_inputs_list.append({
            "text": text,
            "dark_mode": dark_mode,
            "output_file": output_file,
        })

    return user_inputs_list
