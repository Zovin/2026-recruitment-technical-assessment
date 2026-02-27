from dataclasses import dataclass
from typing import List, Dict, Any
from flask import Flask, request, jsonify, abort
import re
from dataclasses import is_dataclass, asdict
import copy

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str
	type: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int

@dataclass
class Summary(CookbookEntry):
	required_items: List[RequiredItem]
	cook_time: int

# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook: Dict[str, CookbookEntry] = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> str | None:
	recipeName = recipeName.lower()
	recipeName = re.sub(r'[-_]', ' ', recipeName)	# replaces - and _ to whitespace
	recipeName = re.sub(r'[^a-z ]', '', recipeName)	# removes all symbols
	recipeName = re.sub(r'\s+', ' ', recipeName)	# remove duplicate whitespace		
	recipeName = recipeName.title()
	recipeName = recipeName.strip()

	return recipeName if recipeName else None

# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()
	add_entry(class_to_snake_case(data))
	return jsonify({}), 200

# converts a camelCase string to snake_case
def to_snake_case(name: str) -> str:
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)	# inserts _ when there's a lowercase and uppercase letter next to each other
    return name.lower()	# changes every character to lowercase

# converst an obj from camelCase to snake_case
def class_to_snake_case(obj: Any) -> Any:
	if is_dataclass(obj):
		obj = asdict(obj)
	if isinstance(obj, dict):
		return {to_snake_case(k): class_to_snake_case(v) for k, v in obj.items()}
	if isinstance(obj, list):
		return [class_to_snake_case(v) for v in obj]
	return obj

# adds a new entry to cookbook
# have to use .get() or [''] for input since input doesn't have a type and is a generic dict
def add_entry(input: dict):
	if input.get('type') not in ('recipe', 'ingredient'):
		abort(400)
	elif input.get('name') in cookbook:
		abort(400)
	
	if input.get('type') == 'recipe':
		required_items = input.get('required_items', [])

		names = [item['name'] for item in required_items]
		if len(names) != len(set(names)):
			abort(400)

		required_items = [RequiredItem(**item) for item in required_items]	# convert from dict to list to match the dataclass

		cookbook[input['name']] = Recipe(
			name=input['name'],
			type='recipe',
			required_items=required_items
		)
	else:
		if input['cook_time'] < 0:
			abort(400)
		
		cookbook[input['name']] = Ingredient(**input)
	

# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	name = request.args.get('name')
	summary = create_summary(name)
	return jsonify(class_to_camel_case(summary)), 200

# converts a snake_case string to camelCase
def to_camel_case(snake_str: str) -> str:
    parts = snake_str.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])

# converts a snake_case obj to camelCase
def class_to_camel_case(obj: Any) -> Any:
	if is_dataclass(obj):
		obj = asdict(obj)
	if isinstance(obj, dict):
		return {to_camel_case(k): class_to_camel_case(v) for k, v in obj.items()}
	if isinstance(obj, list):
		return [class_to_camel_case(v) for v in obj]
	return obj

# Takes in a recipe namee and returns the summary of the recipe
def create_summary(name: str) -> Summary:
	recipe: CookbookEntry | None = cookbook.get(name)

	if recipe == None or recipe.type == "ingredient":
		abort(400)

	summary: Summary = copy.deepcopy(recipe)
	summary.required_items = recursive_summary(summary.required_items)
	summary.cook_time = 0

	# sums up the cookTime of the recipe
	for item in summary.required_items:
		# can assume every item will be ingredient
		ingredient :Ingredient = cookbook.get(item.name)
		summary.cook_time += item.quantity * ingredient.cook_time

	return summary

# recursively gets the list of all required items for the recipe
def recursive_summary(required_items: List[RequiredItem]) -> List[RequiredItem]:
	result: List[RequiredItem] = copy.deepcopy(required_items)

	for item in result:
		cookbook_entry = cookbook.get(item.name)
		if cookbook_entry == None:
			abort(400)
		elif cookbook_entry.type != "recipe":
			continue
	
		itemRequirements: List[RequiredItem] = recursive_summary(cookbook_entry.required_items)
		merge_required_items(result, itemRequirements, item.quantity)

		# remove recipe from result array
		result = [x for x in result if x.name != item.name]

	return result

# merges the required items of 2 different recipes.
def merge_required_items(arr1: List[RequiredItem], arr2: List[RequiredItem], quantity: int):
	lookup = {item.name: item for item in arr1}

	for entry in arr2:
		if entry.name in lookup:
			lookup[entry.name].quantity += entry.quantity * quantity
		else:
			new_item = copy.deepcopy(entry)
			new_item.quantity *= quantity
			arr1.append(new_item)
	
# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
