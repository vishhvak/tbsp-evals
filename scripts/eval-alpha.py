import argparse
import json
import os
import sys

import pandas as pd
from openai import OpenAI
from tqdm import tqdm

tqdm.pandas()
# os.environ['OPENAI_API_KEY'] = "insert your key here"


def create_chat_prompt(item_description):
    example_schema = {"properties": {"foo": {"title": "Foo", "description": "a list of strings",
                                             "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
    example_object = {"foo": ["bar", "baz"]}
    incorrect_object = {"properties": {"foo": ["bar", "baz"]}}
    output_schema = {"properties": {"carbohydrates": {"title": "Carbohydrates", "description": "carbohydrates in grams", "type": "number"}, "proteins": {"title": "Proteins", "description": "proteins in grams", "type": "number"}, "fats": {
        "title": "Fats", "description": "fats in grams", "type": "number"}, "calories": {"title": "Calories", "description": "calories in kcal", "type": "number"}}, "required": ["carbohydrates", "proteins", "fats", "calories"]}

    user_prompt = f"""What is the nutrition information of 100g of {item_description}?
    The output should be formatted as a JSON instance that conforms to the JSON schema below.

    As an example, for the schema {example_schema}
    the object {example_object} is a well-formatted instance of the schema. The object {incorrect_object} is not well-formatted.

    Here is the output schema:
    {output_schema}
    """
    return [
        {"role": "user", "content": user_prompt}
    ]


def is_valid_json(json_data):
    try:
        json_object = json.loads(json_data)
    except ValueError as e:
        return False
    return True


def compare_jsons(json1, json2):
    if not is_valid_json(json1) or not is_valid_json(json2):
        return False, "Invalid JSON"
    dict1 = json.loads(json1)
    dict2 = json.loads(json2)
    if dict1.keys() != dict2.keys():
        return False, "Keys mismatch"
    for key in dict1.keys():
        if dict1[key] != dict2[key]:
            return False, "Values mismatch for key: " + key
    return True, "Match"


def get_answer(messages):
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",  # gpt-3.5-turbo-1106
        response_format={"type": "json_object"},
        temperature=0.0,
        seed=42,
        messages=messages
    )
    # TODO: Add logic to verify system_fingerprint is same across all requests
    return response.choices[0].message.content


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--sample_number", type=int, default=100)
    parser.add_argument("--dataset", type=str, default="sr28.csv")
    parser.add_argument("--output_file", type=str, default="eval_result.json")
    args = parser.parse_args()

    df = pd.read_csv(args.dataset)

    test_samples = df.sample(
        args.sample_number, random_state=1).reset_index(drop=True)
    test_samples["input"] = test_samples.apply(
        lambda x: create_chat_prompt(x['description']), axis=1)

    client = OpenAI()

    test_samples['gpt-response'] = test_samples.input.progress_apply(
        get_answer)

    # Calculate overall accuracy of match between estimated JSON and Ground Truth JSON of Nutrients
    # 1. Filter out the invalid JSONs
    # 2. Key-wise comparison of the JSONs
    # 3. Calculate the accuracy
    test_samples['correct'], test_samples['reason'] = zip(
        *test_samples.apply(lambda row: compare_jsons(row['answer'], row['gpt-response']), axis=1))

    # Export the result as a csv
    # test_samples.to_csv('eval_result.csv', index=False)

    # Export the result as a json
    test_samples['item_description'] = test_samples['description']
    test_samples['nutrients'] = test_samples['answer'].apply(
        lambda x: {k: v for k, v in sorted(json.loads(x).items(), key=lambda item: item[0])})
    test_samples['estimated_nutrients'] = test_samples['gpt-response'].apply(
        lambda x: {k: v for k, v in sorted(json.loads(x).items(), key=lambda item: item[0])})
    keys_to_export = ['item_description', 'nutrients',
                      'estimated_nutrients', 'correct', 'reason']
    json_result = test_samples[keys_to_export].to_dict(orient='records')
    with open('eval_result.json', 'w') as f:
        json.dump(json_result, f, indent=4)

    accuracy = test_samples['correct'].mean()

    # Print the accuracy
    print(f'Accuracy: {accuracy * 100}%')

    total_squared_error = {
        "calories": 0,
        "carbohydrates": 0,
        "fats": 0,
        "proteins": 0
    }

    with open(args.output_file, 'r') as f:
        data = json.load(f)

    for item in data:
        for nutrient in total_squared_error.keys():
            actual = item['nutrients'][nutrient]
            estimated = item['estimated_nutrients'][nutrient]
            total_squared_error[nutrient] += (actual - estimated) ** 2

    # Calculate mean squared error for each nutrient and print it
    for nutrient in total_squared_error.keys():
        mean_squared_error = total_squared_error[nutrient] / len(data)
        print(f'Mean Squared Error for {nutrient}: {mean_squared_error}')
