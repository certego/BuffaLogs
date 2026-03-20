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

## Contributor License Agreement

Before being allowed to contribute to Buffalogs, you will be asked to sign a Contributor License Agreement (CLA). This agreement ensures that the project remains legally secure and that Certego can continue to distribute it as free and open-source software indefinitely.

### 1. Individual CLA (ICLA)

If you are contributing as an **individual** (using your personal time and resources), the process is fully automated via **CLA Assistant**.

#### How to proceed:

1.  Open a **Pull Request** with your proposed changes.
2.  The **CLA Assistant** bot will automatically check if you have already signed the agreement.
3.  If this is your first time, the bot will post a comment on your Pull Request with a dedicated link.
4.  Click the link, log in with your GitHub account, and accept the terms (which include coverage for past contributions, our Open Source commitment, and the jurisdiction of Modena, Italy).
5.  Once accepted, your Pull Request will be cleared for technical review.

*Note: You only need to sign the ICLA once for all Certego repositories.*

### 2. Corporate CLA (CCLA)

If you are contributing on behalf of your **employer** or an **organization** (e.g., during work hours or using corporate assets), a **Corporate CLA** must be signed by your organization. 

In this case, an individual signature is not sufficient, as the economic rights to the software legally belong to your employer (under Art. 12-bis of the Italian Copyright Law or similar international statutes).

#### How to proceed:

1.  **Do not** sign via the GitHub bot as an individual.
2.  Send an email to [compliance@certego.net](mailto:compliance@certego.net) stating your company name and the GitHub usernames of the employees who intend to contribute.
3.  Our legal department will send you the CCLA form to be signed by an authorized representative of your company.
4.  Once we receive the signed document, we will add your GitHub account to an **Allow List**, and your Pull Requests will be automatically cleared moving forward.

### 3. Contribution Requirements

Before submitting a Pull Request, please ensure that:

* The code is original or you have the legal right to share it.
* Commit messages are clear and descriptive.
* The code follows the project's style guidelines (if applicable).

### 4. Minor Contributions (Threshold of Originality)

For minor changes that do not constitute original intellectual property (such as fixing a single typo or reformatting whitespace), a CLA signature may not be strictly required by law; however, we encourage you to complete the process to streamline project management.

### Questions?

If you have any doubts regarding the legal procedure or which type of CLA is appropriate for your situation, please feel free to contact us at [compliance@certego.net](mailto:compliance@certego.net).

Thank you for supporting Certego!

#  Contribution Process

## Bug fixes

For **bug fixes**, you may open a pull request **directly, without a prior issue**.
The PR description must clearly include:

* a detailed explanation of the problem

* steps to reproduce the issue

* screenshots or other evidence of the error

* a description of how the issue was fixed

## Issues (for features or refactors)

* Create an issue using the appropriate template and fill in all required sections.

* Before starting any work, the issue must be **reviewed, approved, and assigned** by a maintainer.

* Pull requests opened without a prior assignment may be rejected, to avoid duplicated work and ensure coordination with maintainers and other contributors.

## Pull Request

* Pull requests are accepted only for the **develop** branch.

* Add or update documentation under the `docs/` folder if needed

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
    Installing them:
    ```bash
        pip install ../.github/configurations/python_linters/requirements-linters.txt
    ```
    Running them (**flake8, black and isort are mandatory** because used also in the CI)
    *   Autoflake - tool to remove unused imports and unused variables
    ```bash
        autoflake -r -cd . --remove-all-unused-imports --remove-unused-variables --ignore-init-module-imports --ignore-pass-statements
    ```
    *   Flake8 - linter for code syntax and cleaning
    ```bash
        flake8 . --show-source --config .github/configurations/python_linters/.flake8
    ```
    *   Black - an uncompromising Python code formatter
    ```bash
        black --config .github/configurations/python_linters/.black .
    ```
    *   Isort - utility to sort imports alphabetically, and automatically separated into sections and by type
    ```bash
        isort --sp .github/configurations/python_linters/.isort.cfg --profile black .
    ```
    *   Pylint - a static code analyser for Python
    ```bash
    pylint --load-plugins=pylint_django --django-settings-module=buffalogs.settings --recursive=y --rcfile=.github/configurations/python_linters/.pylintrc .
    ```
    *   Bandit - a tool designed to find common security issues in Python code
    ```bash
    bandit -c .github/configurations/python_linters/.bandit.yaml .
    ```
    *   FawltyDeps - dependency checker for Python that finds undeclared and/or unused 3rd-party dependencies
    ```bash
    fawltydeps --detailed
    ```

3.  **IF** your changes include differences in the template view, **include sceenshots of the before and after**.
4.  **Test your changes**: Run any existing tests with the command below and create new tests if needed. Whether tests exist or not, make sure your changes don’t break the project.
    ```bash
    ./manage.py test impossible_travel
    ```
5.  **Doc your code**: please, document your new code if needed, under the `docs/` folder

**Working on your first Pull Request?** You can learn how from this *free* series [How to Contribute to an Open Source Project on GitHub](https://kcd.im/pull-request)
