from flask import Flask, render_template, request
import subprocess
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    obfuscated_code = ""
    if request.method == "POST":
        original_code = request.form["code"]
        
        # Write the original code to a temporary Python file
        with open("temp_code.py", "w") as f:
            f.write(original_code)
        
        # Run pyarmor command to obfuscate the code using subprocess
        subprocess.run(["pyarmor", "obfuscate", "temp_code.py"])
        
        # Read the obfuscated code from the generated file
        obfuscated_code_path = "dist/temp_code.py"
        
        # Check if the obfuscated file exists
        if os.path.exists(obfuscated_code_path):
            with open(obfuscated_code_path, "r") as f:
                obfuscated_code = f.read()

    return render_template("index.html", obfuscated_code=obfuscated_code)

if __name__ == "__main__":
    app.run(debug=True)
