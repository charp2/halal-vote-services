**Pre-reqs: 
* Have a working aws cli with admin access to the halalharam aws account
* Brew install python3.8 (if you do any other version, update the updateFunction script to reflect that)
**

This is a python service for interacting with the haram-halal-db MySql database

This library contains code for a lambda function which gets invoked by an AWS API-Gateway. lambda_function.py contains the handler for the https event that invokes the lambda.

The updateFunction script contains a series of bash commands which will update the lambda on aws. In order for this script to work, you must have installed the dependencies using Pipenv as follows:

First install Pipenv:

`brew install pipenv`

Set Pipenv to install dependencies to this directory:

`export PIPENV_VENV_IN_PROJECT="enabled"`

Install dependencies using Pipenv:

`pipenv install --python 3.8`

NOTE: You must have Python 3.8 installed for this to work. If you don't, first do so as follows:

`brew install python@3.8`

Then follow the cli output to set your PATH.

Now you can run `~/halal-vote-services$ ./updateFunction {service} {aws_password}` anytime code is updated.

Note that the updateFunction script takes two arguments- 
1) The name of the lambda you want to update (`topics`, `comment`, `users`)
2) The aws password for a user account which has permission to update the lambda

*MAKE SURE YOU GIVE THE updateFunction SCRIPT PERSMISSION TO EXECUTE BY RUNNING `chmod +x ./updateFunction`*