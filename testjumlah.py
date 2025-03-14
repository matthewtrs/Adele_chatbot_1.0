import os

def access_file(filename):
    """Reads the content of a file if it exists, otherwise returns an empty string."""
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return file.read()
    return ""  # Return empty string if file doesn't exist

a = "ayam\n"
b = access_file("rules.txt")  # Call the function to get file content
c = a + b

print(c)
