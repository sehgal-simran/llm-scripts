import OpenAI from "openai";
import { MongoClient } from "mongodb";
const openai = new OpenAI();

const labelReaderPrompt = `
Give me a diverse list of 100 english poems under public license i.e greater than 70 years old. Should be short to medium. 
Should have some famous poems, some niche poems, some limericks, some simile etc
Return an object with content_type=poem and an array poems of poems with each item having poem name, author name, year, 3 moods of the poem according to this list
of moods: Aroused,Cheeky,Free,Joyful,Curious,Inquisitive,Successful,Confident,Respected,Valued,Courageous,Creative,Loving,Thankful,Sensitive,Intimate,Hopeful,Inspired,Shocked,Dismayed,Disillusioned,Perplexed,Astonished,Awe,Eager,Energetic,Frightened,Helpless,Overwhelmed,Worried,Inadequate,Inferior,Worthless,Insignificant,Persecuted,Excluded,Nervous,Exposed,Out of Control,Unfocused,Sleepy,Indifferent,Apathetic,Pressured,Rushed,Judgmental,Embarrassed,Appalled
which i got from the feeling wheel. If a poem makes you feel Confident, Free, Joyful- in that order put the most strong feeling in mood1, then second strongest feeling in mood2 and third strongest feeling in mood3.
`
const poemInfoSchema = {
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "author": {"type": "string"},
    "moods": {
      "type": "array",
      "items": {
        "type": "string",
      }
    },
  },
  "required": ["name", "author", "moods"],
  "additionalProperties": false
}

const poemArraySchema = {
  "type": "object",
  "properties": {
    "poem_array": {
      "type": "array",
      "items": {
        "type":  "object",
        "properties": {
          "name": {"type": "string"},
          "author": {"type": "string"},
          "mood1": {"type": "string"},
          "mood2": {"type": "string"},
          "mood3": {"type": "string"},
        },
        "required": ["name", "author", "moods"],
      }
    }
  },
  "required": [ "poem_array"],
  "additionalProperties": false,
  strict:true,

}



async function main() {
  // const mongo = new MongoClient("mongodb://root:example@localhost:27017/");
  // await mongo.connect();
  // const db = mongo.db("pood");
//  const coll = db.collection("poem_info");

const response = await openai.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [
      {
          role: "user",
          content: labelReaderPrompt,
      },
  ],
  response_format: {
    "type": "json_schema",
    "json_schema": {
      "name": 'poem_info_reader',
      "schema": poemArraySchema,
      },
    }

  }, // Set to json as you're expecting a JSON structure
);


  //console.log('response', response.choices[0].message)
  // read image links from csv 
  const csvPath = '/Users/seagull/Downloads/products3.csv';
  const results = []
  fs.createReadStream(csvPath)
  .pipe(csvParser({ headers: false }))
  .on('data', (data) => {
    const filteredData = []
    Object.values(data).forEach(v => {
      if(v){
        filteredData.push(v)
      }
    })
    results.push(filteredData)
  })
  .on('end', () => {
  // extract information
  Promise.map(results, async(imageLinks) => {
    const response = await extractInformation(imageLinks);
    if(!response.message || response.message.refusal) {
      console.error("Error in extracting information for product")
    }else {
      console.log('inserting document')
      await coll.insertOne(JSON.parse(response.message.content))
  
    }
  })
  });

}
main();