// Import necessary modules
const dotenv = require("dotenv");
const OpenAI = require("openai");
const fs = require('fs');

(async () => {
    // Load environment variables
    dotenv.config();

    // Define required environment variables
    const requiredEnvVars = ['OPENAI_API_KEY', 'ASSISTANT_ID', 'CSV_FILE_PATH', 'STORE_NAME', 'DIET_TYPE', 'DELAY_TIME'];

    // Check if all required environment variables are set
    for (const varName of requiredEnvVars) {
        if (!process.env[varName]) {
            console.error(`Error: Missing necessary environment variable ${varName}.`);
            process.exit(1);
        }
    }

    // Check if the CSV file exists
    if (!fs.existsSync(process.env.CSV_FILE_PATH)) {
        console.error(`Error: File ${process.env.CSV_FILE_PATH} does not exist.`);
        process.exit(1);
    }

    // Create OpenAI object with API key
    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

    // Delete all previous files in OpenAI storage
    const list = await openai.files.list();
    for await (const file of list) {
        await openai.files.del(file.id);
    }

    // Retrieve assistant for requests
    const assistant = await openai.beta.assistants.retrieve(process.env.ASSISTANT_ID);

    // Create a new thread
    const thread = await openai.beta.threads.create();

    // Read the file and process it
    fs.readFile(process.env.CSV_FILE_PATH, 'utf-8', async (err, data) => {
        if (err) {
            console.error(err);
            return;
        }

        // Upload file to assistant
        const file = await openai.files.create({
            file: fs.createReadStream(process.env.CSV_FILE_PATH),
            purpose: "assistants",
        });

        // Update the assistant with the new file ID
        await openai.beta.assistants.update(assistant.id, { file_ids: [file.id] });

        // Create message 
        const messageContent = 
        `${process.env.STORE_NAME}.csv is a csv file with the first line providing context for the file contents.`+
        `Use the food items from the csv file to create 7 ${process.env.DIET_TYPE} meal recipes. Ensure that `+
        `all the ingredients used in the recipes are ${process.env.DIET_TYPE}, and that there are 7 recipes. `+
        "Include the recipe name, description, ingredient names from the csv file and their "+
        "amounts and costs, total recipe cost, and how many it serves. Assume persons have "+
        "basic essentials like butter, milk, eggs, oil, rice, and seasonings. Output everything "+
        `in JSON format following this format:\n'`
        +`[`
    +`      {`
    +`          "name": "Recipe Name",`
    +`          "description": "Description of Recipe",`
    +`          "ingredients": [`
    +`              {"name": "Ingredient 1", "amount": "Amount", "cost": "Cost"},`
    +`              {"name": "Ingredient ...", "amount": "Amount", "cost": "Cost"}`
    +`          ],`
    +`          "total_cost": "Total Cost for Recipe",`
    +`          "serves": "Number of Servings for Recipe"`
    +`      },`
    +`      {`
    +`          "name": "Recipe Name",`
    +`          "description": "Description of Recipe",`
    +`          "ingredients": [`
    +`              {"name": "Ingredient 1", "amount": "Amount", "cost": "Cost"},`
    +`              {"name": "Ingredient ...", "amount": "Amount", "cost": "Cost"}`
    +`          ],`
    +`          "total_cost": "Total Cost for Recipe ",`
    +`          "serves": "Number of Servings for Recipe "`
    +`      },`
    +`      ...`
    +`  ]`;
        const messages = await openai.beta.threads.messages.create(thread.id, { role: "user", content: messageContent });

        // Run assistant
        const run = await openai.beta.threads.runs.create(thread.id, { assistant_id: assistant.id });

        // Set a delay before processing the files
        setTimeout(async () => {

            // Grab list of all files in this OpenAI account
            const list = await openai.files.list();

            // Grab assistant made output file from list of files:
            for await (const file of list) {
                if (file.purpose == 'assistants_output') {
                    const fileData = await openai.files.retrieve(file.id);

                    // Ensuring file is ready for download
                    if (fileData.status == 'processed') {
                        const fileContent = await openai.files.content(file.id);
                        const fileName = fileData.filename.split('/mnt/data/')[1];
                        // Creating folder path and file
                        const folderPath = `data/requestedRecipes/${process.env.STORE_NAME}`;
                        const file_path = `${folderPath}/recipes_${process.env.CURRENT_DATE}.json`
                        const bufferView = new Uint8Array(await fileContent.arrayBuffer());
                        fs.writeFileSync(file_path, bufferView, 'utf8');
                        fs.writeFileSync(`${folderPath}/recipes.json`, bufferView, 'utf8');
                        console.log(`Downloaded file: ${fileName} to ${file_path}`);
                    } else {
                        console.log(`File content is undefined for file: ${file.filename}`);
                    }
                }
            }
        }, process.env.DELAY_TIME);
    });
})();
