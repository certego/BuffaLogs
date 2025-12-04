#   Guidance on how to contribute
Thank you for your interest in contributing to BuffaLogs, all contributions are welcome! 
BuffaLogs was developed to allow contributions from people with any level of experience, but in order to create a friendly and respectful community, please follow these guidelines.

In this guide you will get an overview of the contribution workflow from opening an issue, creating a Pull Request, reviewing and merging the PR. 

##  Before Starting

To get a general outlook  of the project, read the [README](README.md) file.
Before contributing, you are invited to install the project on your local machine and test its functioning to have a detailed view of how the project works. 

##  Code of Conduct
In the interest of fostering an open and welcoming environment, we pledge to make participation in our project and our community a harassment-free experience for everyone. For this reason, it is strongly requested to use an inclusive language, be respectful of different points of view, make criticisms in a constructive way, show empathy towards other community members.
Please follow the code of conduct in all your interactions with the project.

#  Contribution Process
## Issues
You can create an issue choosing the template that suits you and completing the required sections:

![image](https://github.com/user-attachments/assets/82ed3a87-545a-47aa-8bbe-e2196cda739c)

In any case, if you want to work on an existing issue or you have created a new one, before starting to work on it, you need to get the approval of one of the maintainers. 
If you do not receive the assignment but you still raise a PR for that issue, your PR can be rejected. This is a form of respect for both the maintainers and the other contributors who could have already started to work on the same problem.

## Pull Request
You can submit a PR only for an assigned issue. If you open a PR without prior discussion or approval, it may be directly rejected.
Once you have started working on an issue and you have some work to share and discuss with us, please raise a draft PR early with incomplete changes. In this way you can continue working on the same and we can track your progress and actively review and help.
Pull requests are allowed only for the `develop` branch. That code will be pushed to master only on a new release. Before submitting the PR, remember to pull the most recent changes available in the develop branch.

How to create and submit a PR:
1.  [Fork the repository](https://docs.github.com/en/get-started/quickstart/contributing-to-projects) and clone it locally. Connect your local to the `develop` branch and pull in changes from it so that you stay up to date. 
2.  [Create a new branch](https://docs.github.com/en/get-started/quickstart/github-flow) starting from the `develop` branch with a name that refers to the issue you are working on.
    ```bash
    git checkout -b myfeature develop
    ```
    Now, we strongly suggest configuring pre-commit to force linters on every commit you perform:
    ```bash
    # create virtualenv to host pre-commit installation
    python3 -m venv venv
    source venv/bin/activate
    # from the project base directory
    pip install pre-commit
    ```
    If you didn't install pre-commit, it is necessary to run linters manually:
    *   Autoflake
    ```bash
        autoflake -r -cd . --remove-all-unused-imports --remove-unused-variables --ignore-init-module-imports --ignore-pass-statements
    ```
    *   Flake8
    ```bash
        flake8 . --show-source --config ../.github/configurations/python_linters/.flake8
    ```
    *   Black
    ```bash
    black --config .github/configurations/python_linters/.black .
    ```
    *   Isort
    ```bash
    isort --sp .github/configurations/python_linters/.isort.cfg --profile black .
    ```
    *   Pylint
    ```bash
    pylint --load-plugins=pylint_django --django-settings-module=buffalogs.settings --recursive=y --rcfile=.github/configurations/python_linters/.pylintrc .
    ```
    *   Bandit
    ```bash
    bandit -c .github/configurations/python_linters/.bandit.yaml .
    ```

3.  **IF** your changes include differences in the template view, **include sceenshots of the before and after**.
4.  **Test your changes**: Run any existing tests with the command below and create new tests if needed. Whether tests exist or not, make sure your changes don’t break the project.
    ```bash
    ./manage.py test impossible_travel
    ```
5.  **Doc your code**: please, document your new code if needed, under the `docs/` folder

**Working on your first Pull Request?** You can learn how from this *free* series [How to Contribute to an Open Source Project on GitHub](https://kcd.im/pull-request)
