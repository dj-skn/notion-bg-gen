from user_input_handler import get_user_input
from gradient_generator import generate_gradient
from halo import Halo
from colorama import Fore, Style
import time

def main():
    # Step 1: Get user inputs
    user_inputs_list = get_user_input()

    # Step 2: Process each cover
    for i, user_inputs in enumerate(user_inputs_list, start=1):
        print(Fore.CYAN + Style.BRIGHT + f"\nGenerating cover {i}/{len(user_inputs_list)}...")

        # Step 3: Use a spinner while generating the gradient
        spinner = Halo(text=f"Generating gradient for cover {i}...", spinner="dots")
        spinner.start()

        try:
            # Step 4: Generate the gradient with text
            generate_gradient(**user_inputs)
            spinner.succeed(Fore.GREEN + f"Cover {i} successfully generated!")
            print(Style.BRIGHT + "Cover location: " + Style.NORMAL + user_inputs["output_file"])
        except Exception as e:
            spinner.fail(Fore.RED + f"An error occurred while generating cover {i}: {e}")

    print(Fore.CYAN + Style.BRIGHT + "\nAll covers have been successfully generated!")

if __name__ == "__main__":
    main()
