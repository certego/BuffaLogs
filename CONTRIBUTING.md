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
## Discussions
If you would like help in troubleshooting on a PR you are working on, or have a new idea to share, join us in [discussions](https://github.com/certego/BuffaLogs/discussions).
To start a new discussion, the categories to choose from are: 
*   General: chat about important news affecting the project
*   Ideas: share ideas for new features to implement
*   Polls: take a vote from the community
*   Q&A: ask the community for help or doubts
*   Show and tell: show off to the community something you have made

## Issues
You can create or solve an issue. 
###    Create an issue
If you spot a problem, search if an issue already exists ([here](https://github.com/certego/BuffaLogs/issues)). If a related issue doesn't exist, you can open a new issue.

###    Solve an issue
Scan through our existing issues to find one that interests you. You can narrow down the search using `labels` as filters. Before starting to work on an issue, you need to get the approval of one of the maintainers. Therefore please ask to be assigned to an issue. If you do not that but you still raise a PR for that issue, your PR can be rejected. This is a form of respect for both the maintainers and the other contributors who could have already started to work on the same problem.

## Pull Request
You should usually open a pull request in the following situations:
*   Submit trivial fixes (for example, a typo, a broken link or an obvious error)
*   Start working on a contribution that was already asked for, or that you have already discussed, in an issue.

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
    *   Flake8
    ```bash
        flake8 . --show-source --config ../.github/configurations/.flake8
    ```
    *   Black
    ```bash
    black --config ../.github/configurations/.black .
    ```
    *   Isort
    ```bash
    isort --sp ../.github/configurations/.isort.cfg --profile black .
    ```

3.  **IF** your changes include differences in the template view, **include sceenshots of the before and after**.
4.  **Test your changes**: Run any existing tests with the command below and create new tests if needed. Whether tests exist or not, make sure your changes don’t break the project.
    ```bash
    ./manage.py test impossible_travel
    ```
**Working on your first Pull Request?** You can learn how from this *free* series [How to Contribute to an Open Source Project on GitHub](https://kcd.im/pull-request) 
