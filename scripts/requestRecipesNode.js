import * as dotenv from "dotenv";
import * as path from "path";
import { OpenAI } from "openai";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
//setting .env path 
const fs = require("fs");

//create openai object with api key
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

     launchMessagePrompt();
    //we want to query assistant after about a minute, to give it enguh time to process
    setTimeout(async()=>{
        checkAndRelaunchRequest();      
    }, process.env.DELAY_TIME);

// Function to extract the store name from the filename
function getStoreName(filename) {
    // Logic to extract the store name based on the filename pattern
    // This can be customized based on the naming convention used for the files

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
//grabs today's date
function yyyymmdd() {
    var x = new Date();
    var y = x.getFullYear().toString();
    var m = (x.getMonth() + 1).toString();
    var d = x.getDate().toString();
    (d.length == 1) && (d = '0' + d);
    (m.length == 1) && (m = '0' + m);
    var yyyymmdd = y + m + d;
    return yyyymmdd;
}

//checks if assistant output file exists in openai end
async function checkIfFileExists() {
    try {
        
        // List all files from the assistant
        const fileList = await openai.files.list();
        for await (const file of fileList) {
            if(file.purpose == 'assistants_output'){
                try{
                    const fileData = await openai.files.retrieve(file.id);
                    return fileData;
                }
                catch(error) {
                    console.error('Error checking if the file exists:', error);
                    return false; // Assume file doesn't exist in case of error to avoid false positives
                }
            }
            
        }
    } catch(error) {
        console.error('Error checking if the file exists:', error);
        return false; // Assume file doesn't exist in case of error to avoid false positives
    }
    return false; // No file matching the criteria has been found
}

async function checkAndRelaunchRequest() {
    var numOfTries = 3;

    for(var count =0;count< numOfTries;count++){
        var fileExists = await checkIfFileExists();//grab assitant output file

    
    if (fileExists.purpose != 'assistants_output') {
        try{
        console.log('No processed file from assistant output was found. Attempting to relaunch the request...');
        // Implement your relaunch request logic here
        launchMessagePrompt();
        setTimeout(async()=>{
            fileExists = checkIfFileExists();//if file is assistant_output type
            if(fileExists.status == 'processed'){//if relaunch works
                const fileContent = await openai.files.content(fileExists.id);
                console.log(fileExists);
                //assitant output files aways start with this /mnt/data/
                //so we are removing this from file name for internal storage
                const fileName = fileExists.filename.split('/mnt/data/')[1];
                const storeName = getStoreName(fileName);
                //creating folder path and file
                const folderPath = `data/requestedRecipes/${storeName}`;
                const file_path1 = `data/requestedRecipes/${storeName}/recipes_${yyyymmdd()}.json`
                const bufferView = new Uint8Array(await fileContent.arrayBuffer());
                fs.writeFileSync(`${folderPath}/recipes_${yyyymmdd()}.json`, bufferView, 'utf8');
                fs.writeFileSync(`${folderPath}/recipes.json`, bufferView, 'utf8');
                console.log(`Downloaded file: ${fileName} to ${file_path1}`);
                return;
            }
        },process.env.DELAY_TIME);
    }catch(error){
        if (count == 2){
            console.log("3 attemtps have been made please check code");
        }
        console.log(error);
    }
    
    
} else {
        console.log('A processed file from the assistant output was found.');
        if(fileExists.status == 'processed'){
            const fileContent = await openai.files.content(fileExists.id);
            console.log(fileExists);
            //assitant output files aways start with this /mnt/data/
            //so we are removing this from file name for internal storage
            const fileName = fileExists.filename.split('/mnt/data/')[1];
            const storeName = getStoreName(fileName);
            //creating folder path and file
            const folderPath = `data/requestedRecipes/${storeName}`;
            const file_path1 = `data/requestedRecipes/${storeName}/recipes_${yyyymmdd()}.json`
            const bufferView = new Uint8Array(await fileContent.arrayBuffer());
            fs.writeFileSync(`${folderPath}/recipes_${yyyymmdd()}.json`, bufferView, 'utf8');
            fs.writeFileSync(`${folderPath}/recipes.json`, bufferView, 'utf8');
            console.log(`Downloaded file: ${fileName} to ${file_path1}`);
            return;
        }
        else{
            console.log(`File content is undefined for file: ${fileExists.filename}`);
        }
    }
    
    }
}

async function launchMessagePrompt(){
    //loop to delete all previous file in openai storage to ensure we downlaod th emost recent file
const list = await openai.files.list();
for await (var file of list) {
    file = await openai.files.del(file.id);
   console.log(file);
 }

 //retreive asssistant for requests
const assistant1 = await openai.beta.assistants.retrieve(process.env.ASSISTANT_ID);
console.log(assistant1);

//create thread to send messages through
const thread = await openai.beta.threads.create();
//retreive an older thread
//const thread = await openai.beta.threads.retrieve("thread_rLCdFvkULL9H70ruJaVvsxyo");
//console.log(thread);

//include filename or filepath for files to upload
const metroFile = process.env.CSV_FILE_PATH;//file to read
const metroFileName = `${process.env.STORE_NAME}_${yyyymmdd()}.csv`; //file to store/write to
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

    //create message prompt for assistant for vegetarein recipes
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
    //create message 
    const messages =  await openai.beta.threads.messages.create(thread.id,{
        role: "user",
        content:messageContent
    });
    //run assistant
    const run = await openai.beta.threads.runs.create(thread.id, {
        assistant_id: assistant1.id
    });

})};
