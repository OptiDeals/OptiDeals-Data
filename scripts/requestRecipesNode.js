import * as dotenv from "dotenv";
import { OpenAI } from "openai";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const fs = require("fs");
dotenv.config();
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});
const list = await openai.files.list();
for await (var file of list) {
    file = await openai.files.del(file.id);
   console.log(file);
 }
const assistant1 = await openai.beta.assistants.retrieve("asst_x4VQbYi72W6pgafutM97jqrT");
console.log(assistant1);
const thread = await openai.beta.threads.create();
const metroFile = process.env.CSV_FILE_PATH;
const metroFileName = `${process.env.STORE_NAME}_${yyyymmdd()}.csv`;
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
    await openai.beta.assistants.update(assistant1.id, {
        file_ids: [file.id],
    });
    const messageContent = 
    `${metroFileName} is a csv file with the first line providing context for the file contents.`+
    `Use the food items from the csv file to create 7 ${dietType} meal recipes. Ensure that `+
    `all the ingredients used in the recipes are ${dietType}. `+
    "Include the recipe name, description, ingredient names from the csv file and their "+
    "amounts and costs, total recipe cost, and how many it serves. Assume persons have "+
    "basic essentials like butter, milk, eggs, oil, rice, and seasonings. Output everything "+
    `in JSON format to a downloadable file named '${metroStoreName}_${dietType}_recipes'`
    const messages =  await openai.beta.threads.messages.create(thread.id,{
        role: "user",
        content:messageContent
    });
    const run = await openai.beta.threads.runs.create(thread.id, {
        assistant_id: assistant1.id
    });
    setTimeout(async()=>{
        const message = await openai.beta.threads.messages.list(thread.id);
        message.body.data.forEach((m) => {
            console.log(m.content);
         });
         const list = await openai.files.list();
         console.log(list);
         for await (var file of list){
            if(file.purpose == 'assistants_output'){
                try{
                    const fileData = await openai.files.retrieve(file.id);

                    if(fileData.status == 'processed'){
                        const fileContent = await openai.files.content(file.id);
                        const fileName = fileData.filename.split('/mnt/data/')[1];
                        const storeName = getStoreName(fileName);
                        const folderPath = `../data/requestedRecipes/${storeName}/`;

                        const file_path1 = `../data/requestedRecipes/metro/recipes_${yyyymmdd()}.json`
                        const file_path2 = '../data/requestedRecipes/metro/recipes.json'
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
    }, 90000);
});
// Function to extract the store name from the filename
function getStoreName(filename) {
    // Logic to extract the store name based on the filename pattern
    // This can be customized based on the naming convention used for the files

    // If the filename includes 'metro', return 'metro'
    if (filename.includes('metro')) {
        return 'metro';
    } 
    // If the filename includes 'foodBasics', return 'foodBasics'
    else if (filename.includes('foodBasics')) {
        return 'foodBasics';
    } 
    // If the filename doesn't match any of the above patterns, return 'unknown_store'
    else {
        return 'unknown_store';
    }
}

// Function to get the current date in the format 'yyyymmdd'
function yyyymmdd() {
    // Get the current date
    var x = new Date();

    // Extract the year, month, and day
    var y = x.getFullYear().toString();
    var m = (x.getMonth() + 1).toString();
    var d = x.getDate().toString();

    // If the day is a single digit, prepend it with '0'
    (d.length == 1) && (d = '0' + d);

    // If the month is a single digit, prepend it with '0'
    (m.length == 1) && (m = '0' + m);

    // Concatenate the year, month, and day to get the date in the format 'yyyymmdd'
    var yyyymmdd = y + m + d;

    // Return the date
    return yyyymmdd;
}
