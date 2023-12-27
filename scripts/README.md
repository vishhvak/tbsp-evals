## Environment Setup

Set up your Python environment. You can use either venv or conda for this. Here's how you can do it with venv:

`python3 -m venv env`

After setting up the environment, activate it using the command below:

For Unix or MacOS, use:
`source env/bin/activate`

For Windows, use:
`.\env\Scripts\activate`

## Install Requirements

`pip install -r requirements.txt`

## Run the evaluation

`python eval-alpha.py --sample_num 100 --dataset sr28.csv --output_file eval_result.json`


