import express, { Request, Response } from "express";
import HTTPError from 'http-errors';

// ==== Type Definitions, feel free to add or modify ==========================
interface cookbookEntry {
  name: string;
  type: string;
}

interface requiredItem {
  name: string;
  quantity: number;
}

interface recipe extends cookbookEntry {
  requiredItems: requiredItem[];
}

interface ingredient extends cookbookEntry {
  cookTime: number;
}

interface summary extends cookbookEntry {
  cookTime: number;
  requiredItems: requiredItem[];
}

// =============================================================================
// ==== HTTP Endpoint Stubs ====================================================
// =============================================================================
const app = express();
app.use(express.json());

// Store your recipes here!
const cookbook: any = [];

// Task 1 helper (don't touch)
app.post("/parse", (req:Request, res:Response) => {
  const { input } = req.body;

  const parsed_string = parse_handwriting(input)
  if (parsed_string == null) {
    res.status(400).send("this string is cooked");
    return;
  } 
  res.json({ msg: parsed_string });
  return;
  
});

// [TASK 1] ====================================================================
// Takes in a recipeName and returns it in a form that 
const parse_handwriting = (recipeName: string): string | null => {
  recipeName = recipeName
    .replace(/[-_]/g, " ", )  // replaces - and _ to whitespace
    .toLowerCase()
    .replace(/[^a-z ]/g, "")  // removes all symbols
    .trim()
    .replace(/\s+/g, " ")     // remove duplicate whitespace
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.substring(1)) // capitalise first letter
    .join(' ');

  if (!recipeName.length) return null;
  return recipeName;
}

// [TASK 2] ====================================================================
// Endpoint that adds a CookbookEntry to your magical cookbook
app.post("/entry", (req:Request, res:Response) => {
  const input: recipe | ingredient = req.body;

  res.status(200).send(add_entry(input));
});

// adds new entry to cookbook
const add_entry = (input: recipe | ingredient): void => {
  if (!(input.type === "ingredient" || input.type === "recipe")) {
    throw(HTTPError(400));
  } else if (cookbook.find((entry) => entry.name === input.name)) {
    throw(HTTPError(400));
  }

  if (input.type === "recipe") {
    const itemNames = (input as recipe).requiredItems.map((i) => i.name);
    if (new Set(itemNames).size !== itemNames.length) {
      throw(HTTPError(400));
    }

    cookbook.push(input as recipe);
  } else {
    if ((input as ingredient).cookTime < 0) {
      throw (HTTPError(400));
    }

    cookbook.push(input as ingredient);
  }
}

// [TASK 3] ====================================================================
// Endpoint that returns a summary of a recipe that corresponds to a query name
app.get("/summary", (req:Request, res:Request) => {
  const input : string = req.query.name;

  res.status(200).send(get_summary(input));
});

const get_summary = (input: string): summary => {
  let recipe: summary = cookbook.find((entry) => entry.name === input);
  if (!recipe || recipe.type === "ingredient") {
    throw (HTTPError(400));
  }

  let summary: summary = {...recipe}; // copy the recipe so we don't mutate the original file

  summary.requiredItems = recursive_summary(summary.requiredItems);
  summary.cookTime = 0;

  for (const item of summary.requiredItems) {
    summary.cookTime += 
      cookbook.find((entry) => entry.name === item.name).cookTime * item.quantity
  }

  return summary;
};

const recursive_summary = (requiredItems: requiredItem[]): requiredItem[] => {
  let result: requiredItem[] = [...requiredItems];

  for (const item of requiredItems) {
    const itemReference: cookbookEntry = cookbook.find((entry) => entry.name === item.name);
    if (!itemReference) {
      throw(HTTPError(400));
    } else if (itemReference.type === "ingredient"){
      
    }
    
    const itemRequirements: requiredItem[] = recursive_summary((itemReference as recipe).requiredItems);
    mergeRequiredItems(result, itemRequirements, item.quantity);

    // remove recipe after inputting all the ingredients
    result.splice(result.findIndex((temp) => temp.name === item.name), 1);
  }

  return result;
};

const mergeRequiredItems = (arr1: requiredItem[], arr2: requiredItem[], quantity: number) => {
  for (const entry of arr2) {
    const existing: requiredItem = arr1.find((it) => it.name === entry.name);

    if (existing) {
      existing.quantity += quantity * entry.quantity;
    } else {
      arr1.push({...entry, quantity: quantity * entry.quantity})
    }
  }
}

// =============================================================================
// ==== DO NOT TOUCH ===========================================================
// =============================================================================
const port = 8080;
app.listen(port, () => {
  console.log(`Running on: http://127.0.0.1:8080`);
});
