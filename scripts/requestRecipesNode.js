import * as dotenv from "dotenv";
import * as path from "path";
import { OpenAI } from "openai";
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

//create openai object with api key
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});
//loop to delete all previous file in openai storage to ensure we downlaod th emost recent file
const list = await openai.files.list();
for await (var file of list) {
    file = await openai.files.del(file.id);
   console.log(file);
 }

//retreive asssistant for requests
const assistant1 = await openai.beta.assistants.retrieve(process.env.ASSISTANT_ID);
console.log(assistant1);

const thread = await openai.beta.threads.create();


//include filename or filepath for files to upload
const metroFile = process.env.CSV_FILE_PATH;
const metroFileName = `${process.env.STORE_NAME}.csv`;
const dietType = process.env.DIET_TYPE;
const metroStoreName = `${process.env.STORE_NAME}`;

fs.readFile(metroFile,'utf-8',async(err,data)=>{
    if(err){
        console.error(err);
      return;
    }
    //upload file to assistant
    const file = await openai.files.create({
        file: fs.createReadStream(metroFile),
        purpose: "assistants",
    });

    
    // Update the assistant with the new file ID
    await openai.beta.assistants.update(assistant1.id, {
        file_ids: [file.id],
    });

    //create message prompt for assistant for vegetarian recipes
    const recipes = [
  {
    "name": "#",
    "description": "#",
    "ingredients": [
      {"name": "#", "amount": "#", "cost": #},
    ],
    "total_cost": #,
    "serves": #
  },
  {
    "name": "#",
    "description": "#",
    "ingredients": [
      {"name": "#", "amount": "#", "cost": #},
    ],
    "total_cost": #,
    "serves": #
  }
];

const messageContent = 
  `${metroFileName} is a csv file with the first line providing context for the file contents.`+
  `Use the food items from the csv file to create 7 ${dietType} meal recipes. Ensure that `+
  `all the ingredients used in the recipes are ${dietType}. `+
  "Include the recipe name, description, ingredient names from the csv file and their "+
  "amounts and costs, total recipe cost, and how many it serves. Assume persons have "+
  "basic essentials like butter, milk, eggs, oil, rice, and seasonings. Output everything "+
  `in JSON format to a downloadable file named '${metroStoreName}_${dietType}_recipes'`;

// Add the JSON format to message content request
messageContent += '\n' + JSON.stringify(recipes, null, 2);


    //create message 
    const messages =  await openai.beta.threads.messages.create(thread.id,{
        role: "user",
        content:messageContent
    });
    // //run assistant
    const run = await openai.beta.threads.runs.create(thread.id, {
        assistant_id: assistant1.id
    });

    setTimeout(async()=>{

        //grab list of all files in this openai account
         const list = await openai.files.list();
         console.log(list);

         //grab assistant made output file from lsit of files:
         for await (var file of list){
            if(file.purpose == 'assistants_output'){
                try{
                    const fileData = await openai.files.retrieve(file.id);

                    //ensuring file is ready for download
                    if(fileData.status == 'processed'){
                        const fileContent = await openai.files.content(file.id);

                        const fileName = fileData.filename.split('/mnt/data/')[1];
                        const storeName = getStoreName(fileName);
                        //creating folder path and file
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
//function to get date in yyyymmdd format 
function yyyymmdd() {
    var date = new Date();
    var estDate = new Date(date.toLocaleString('en-US', { timeZone: 'America/New_York' }));
    var isoDate = estDate.toISOString();
    return isoDate.slice(0,10).replace(/-/g, '');
}

