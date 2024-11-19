from user_input_handler import get_user_input
from gradient_generator import generate_gradient

def main():
    # Step 1: Get user inputs
    user_inputs = get_user_input()

    # Step 2: Generate the gradient with text
    generate_gradient(**user_inputs)

    print("Your image has been successfully generated!")

if __name__ == "__main__":
    main()