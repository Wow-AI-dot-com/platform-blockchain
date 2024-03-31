db = db.getSiblingDB('wow'); // Select your database
db.createCollection('index'); // Create a collection
db.mycollection.insert({ name: 'test', value: 'test' }); // Insert some data