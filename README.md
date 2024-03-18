## Recreational Club Membership

### How to get started

1. Install Python 3.12.1

    Optional but recommended

    1.1 Create Python virtual environment 
    ```console
    python3 -m venv .venv 
    ```

    1.2 Run the virtual environment 
    
    Windows Powershell
    ```console
    source .venv/Scripts/activate
    ```
    Windows CMD
    ```console
    source .venv/Scripts/activate.bat
    ```

    Linux / Mac
    ```console
    source env/bin/activate 
    ```


2. Install required modules from requirements.txt
    ```console
    pip install -r requirements.txt
    ```

### Run the App

1. Launch the flask server
```console
python3 main.py
```



### Directories and Files

main.py -- flask server - contains all route methods 

**templates** -- all frontend HTML files - what the user sees

**data** -- all user data files in JSON format - where we store all user information, like username, password, etc

**static** -- all media, fonts, css files 
