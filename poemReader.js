import { MongoClient } from "mongodb";
import Promise from "bluebird";
import fs from 'fs';
import { readFileSync } from "node:fs";
import OpenAI from "openai";
const openai = new OpenAI();

function returnPrompt(poemName, poemAuthor){
    let ans=`Fetch me the poem ${poemName} by ${poemAuthor}. Return only the poem and no other details`;
}

async function main(){
    const mongo = new MongoClient("mongodb://localhost:27017/");
    await mongo.connect();
    const db = mongo.db("pood");
    const coll = db.collection("poem_info");

    let poems;
    try {
        poems = (await JSON.parse(readFileSync('./poems.json', 'utf8'))).poem_array;
        for(var i=0; i<1; i++){
            console.log(poems[i])
            const prompt = returnPrompt(poems[i].poemName, poems[i].poemAuthor);
            const response = await openai.chat.completions.create({
                model: "gpt-4o-2024-08-06",
                messages: [
                  {
                    role: "user",
                    content: [
                      { type: "text", 
                        text: prompt },
                    ],
                  },
                ],
                response_format:{
                  "type": "string",
                }
            
            });
            const obj = response.choices[0];
            console.log('obj', obj)
        }
    } catch (e) {
        console.error(e)
    }

    await coll.insertMany(poems.poem_array, function(err, res) {
        if (err) throw err;
        console.log("Number of documents inserted: " + res.insertedCount);
        db.close();
      });
}

main();