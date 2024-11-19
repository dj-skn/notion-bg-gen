from user_input_handler import get_user_input
from gradient_generator import generate_gradient
from halo import Halo
from colorama import Fore, Style
import time

def main():
    # Step 1: Get user inputs
    user_inputs = get_user_input()

    # Step 2: Use a spinner while generating the gradient
    spinner = Halo(text="Generating gradient...", spinner="dots")
    spinner.start()

    try:
        # Step 3: Generate the gradient with text
        time.sleep(2)
        generate_gradient(**user_inputs)
        spinner.succeed("Your cover has been successfully generated!")
        print(Style.BRIGHT + "Cover location: " + Style.NORMAL + user_inputs["output_file"])
    except Exception as e:
        spinner.fail(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
