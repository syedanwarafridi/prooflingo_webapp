**Proof Lingo**

**To set up and run the project, follow these steps:**
1. Clone the project repository by executing `git clone project_path`
2. Navigate to the project directory using the command `cd project_directory`
3. Inside the project directory, access the virtual environment by navigating to `env\Scripts\` and then activate it by typing `activate`
4. Install dependencies by running `pip install -r requirements.txt`
5. Migrate migration cmd `py manage.py migrate`
6. Run server locally `py manage.py runserver`
   
These steps should properly set up the project environment and install all necessary dependencies.

**Important points to note:**

1. Whenever a new library is added to the project, ensure that the correct version of that library is included in the `requirements.txt` file.
2. When pushing code, always create a new branch and push the code changes. Then, initiate a pull request (PR) instead of merging directly. This ensures proper review and collaboration before merging changes into the main codebase.
