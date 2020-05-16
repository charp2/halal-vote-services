**Pre-reqs: 
* Have a working aws cli with admin access to the halalharam aws account
* Brew install python3.7 (if you do any other version, update the updateFunction script to reflect that)
**

This is a python service for interacting with the haram-halal-db MySql database

This library contains code for a lambda function which gets invoked by an AWS API-Gateway. lambda_function.py contains the handler for the https event that invokes the lambda.

The updateFunction script contains a series of bash commands which will update the lambda on aws. In order for this script to work, you must have installed PyMySql by following the instructions below:

`~/make-item$ python3 -m venv v-env` 

`~/make-item$ source v-env/bin/activate` 

`~/make-item$ pip3 install PyMySql`

Now you can run ~/make-item$ ./updateFunction anytime code is updated.

*MAKE SURE YOU GIVE THE updateFunction SCRIPT PERSMISSION TO EXECUTE BY RUNNING `chmod +x ./updateFunction`*