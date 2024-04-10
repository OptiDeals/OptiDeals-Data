// Import necessary modules
import * as dotenv from "dotenv";
import { OpenAI } from "openai";
import * as path from "path";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const fs = require('fs');

// Load environment variables
dotenv.config();

// Check if necessary environment variables are set
if (!process.env.OPENAI_API_KEY || !process.env.ASSISTANT_ID || !process.env.CSV_FILE_PATH || !process.env.STORE_NAME || !process.env.DIET_TYPE || !process.env.DELAY_TIME) {
    console.error("Error: Missing necessary environment variables.");
    process.exit(1);
}

// Check if the CSV file exists
if (!fs.existsSync(process.env.CSV_FILE_PATH)) {
    console.error(`Error: File ${process.env.CSV_FILE_PATH} does not exist.`);
    process.exit(1);
}

// Create OpenAI object with API key
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

// Loop to delete all previous files in OpenAI storage to ensure we download the most recent file
const list = await openai.files.list();
for await (var file of list) {
    file = await openai.files.del(file.id);
    console.log(file);
}

// Retrieve assistant for requests
const assistant1 = await openai.beta.assistants.retrieve(process.env.ASSISTANT_ID);
console.log(assistant1);

// Create a new thread
const thread = await openai.beta.threads.create();

// Include filename or filepath for files to upload
const metroFile = process.env.CSV_FILE_PATH;
const metroFileName = `${process.env.STORE_NAME}.csv`;
const dietType = process.env.DIET_TYPE;
const metroStoreName = `${process.env.STORE_NAME}`;

// Read the file and process it
fs.readFile(metroFile,'utf-8',async(err,data)=>{
    if(err){
        console.error(err);
        return;
    }
    // Upload file to assistant
    const file = await openai.files.create({
        file: fs.createReadStream(metroFile),
        purpose: "assistants",
    });

    // Update the assistant with the new file ID
    await openai.beta.assistants.update(assistant1.id, {
        file_ids: [file.id],
    });

    // Create the message content
    const messageContent = 
        `${metroFileName} is a csv file with the first line providing context for the file contents.`+
        `Use the food items from the csv file to create 7 ${dietType} meal recipes. Ensure that `+
        `all the ingredients used in the recipes are ${dietType}, and that there are 7 recipes. `+
        "Include the recipe name, description, ingredient names from the csv file and their "+
        "amounts and costs, total recipe cost, and how many it serves. Assume persons have "+
        "basic essentials like butter, milk, eggs, oil, rice, and seasonings. Output everything "+
        `in JSON format to a downloadable file named '${metroStoreName}_${dietType}_recipes, following this format:\n'`
        +`[`
    +`      {`
    +`          "name": "Recipe Name",`
    +`          "description": "Description of Recipe",`
    +`          "ingredients": [`
    +`              {"name": "Ingredient 1", "amount": "Amount", "cost": "Cost"},`
    +`              {"name": "Ingredient 2", "amount": "Amount", "cost": "Cost"}`
    +`          ],`
    +`          "total_cost": "Total Cost for Recipe",`
    +`          "serves": "Number of Servings for Recipe"`
    +`      },`
    +`      {`
    +`          "name": "Recipe Name",`
    +`          "description": "Description of Recipe",`
    +`          "ingredients": [`
    +`              {"name": "Ingredient 1", "amount": "Amount", "cost": "Cost"},`
    +`              {"name": "Ingredient 2", "amount": "Amount", "cost": "Cost"}`
    +`          ],`
    +`          "total_cost": "Total Cost for Recipe",`
    +`          "serves": "Number of Servings for Recipe"`
    +`      },`
    +`      ...`
    +`  ]`;

    // Create message 
    const messages =  await openai.beta.threads.messages.create(thread.id,{
        role: "user",
        content:messageContent
    });

    // Run assistant
    const run = await openai.beta.threads.runs.create(thread.id, {
        assistant_id: assistant1.id
    });

    // Set a delay before processing the files
    setTimeout(async()=>{

        // Grab list of all files in this OpenAI account
        const list = await openai.files.list();
        console.log(list);

        // Grab assistant made output file from list of files:
        for await (var file of list){
            if(file.purpose == 'assistants_output'){
                try{
                    const fileData = await openai.files.retrieve(file.id);

                    // Ensuring file is ready for download
                    if(fileData.status == 'processed'){
                        const fileContent = await openai.files.content(file.id);

                        const fileName = fileData.filename.split('/mnt/data/')[1];
                        const storeName = getStoreName(fileName);
                        // Creating folder path and file
                        const folderPath = `data/requestedRecipes/${storeName}`;
                        const file_path1 = `data/requestedRecipes/${storeName}/recipes_${yyyymmdd()}.json`
                        const bufferView = new Uint8Array(await fileContent.arrayBuffer());
                        fs.writeFileSync(`${folderPath}/recipes_${yyyymmdd()}.json`, bufferView, 'utf8');
                        fs.writeFileSync(`${folderPath}/recipes.json`, bufferView, 'utf8');
                        console.log(`Downloaded file: ${fileName} to ${file_path1}`);
                    }
                    else{
                        console.log(`File content is undefined for file: ${file.filename}`);
                    }
                } catch(error){
                    console.error(`Error retrieving file content for file: ${file.filename}`);
                    console.error(error);
                }
            }
        }
    }, process.env.DELAY_TIME);
});

// Function to extract the store name from the filename
function getStoreName(filename) {
    if (filename.includes('metro')) {
        return 'metro';
    } else if (filename.includes('foodBasics')) {
        return 'foodBasics';
    } // Add more store name extraction logic as needed
    else {
        return 'unknown_store';
    }
}

// Function to get date in yyyymmdd format 
function yyyymmdd() {
    var date = new Date();
    var estDate = new Date(date.toLocaleString('en-US', { timeZone: 'America/New_York' }));
    var isoDate = estDate.toISOString();
    return isoDate.slice(0,10).replace(/-/g, '');
}
