/**
 * MongoDB Initialization Script
 * Sets up the turtle_tracking database with collections and indexes
 */

// Switch to the turtle_tracking database
db = db.getSiblingDB('turtle_tracking');

// Create turtles collection with JSON Schema validation
db.createCollection('turtles', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['turtle_id', 'name', 'species', 'status'],
      properties: {
        turtle_id: {
          bsonType: 'string',
          description: 'Unique identifier for the turtle - required'
        },
        name: {
          bsonType: 'string',
          description: 'Name given to the turtle - required'
        },
        species: {
          bsonType: 'string',
          enum: ['green', 'loggerhead', 'leatherback', 'hawksbill', 'olive_ridley', 'kemp_ridley', 'flatback'],
          description: 'Species of the sea turtle - required'
        },
        tag_date: {
          bsonType: 'date',
          description: 'Date when the turtle was tagged'
        },
        sensor_id: {
          bsonType: 'string',
          description: 'ID of the satellite sensor attached to the turtle'
        },
        status: {
          bsonType: 'string',
          enum: ['active', 'inactive', 'lost'],
          description: 'Current tracking status - required'
        },
        created_at: {
          bsonType: 'date',
          description: 'Record creation timestamp'
        },
        updated_at: {
          bsonType: 'date',
          description: 'Record last update timestamp'
        }
      }
    }
  }
});

// Create readings collection with JSON Schema validation
db.createCollection('readings', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['turtle_id', 'timestamp', 'latitude', 'longitude'],
      properties: {
        turtle_id: {
          bsonType: 'string',
          description: 'Reference to the turtle - required'
        },
        timestamp: {
          bsonType: 'date',
          description: 'Time of the reading - required'
        },
        latitude: {
          bsonType: 'double',
          minimum: -90,
          maximum: 90,
          description: 'Latitude coordinate - required'
        },
        longitude: {
          bsonType: 'double',
          minimum: -180,
          maximum: 180,
          description: 'Longitude coordinate - required'
        },
        temperature: {
          bsonType: 'double',
          description: 'Water temperature in Celsius'
        },
        pressure: {
          bsonType: 'double',
          description: 'Pressure in bar'
        },
        depth: {
          bsonType: 'double',
          description: 'Depth in meters (calculated from pressure)'
        },
        created_at: {
          bsonType: 'date',
          description: 'Record creation timestamp'
        }
      }
    }
  }
});

// Create indexes for turtles collection
db.turtles.createIndex({ turtle_id: 1 }, { unique: true });
db.turtles.createIndex({ species: 1 });
db.turtles.createIndex({ status: 1 });
db.turtles.createIndex({ tag_date: 1 });

// Create indexes for readings collection
db.readings.createIndex({ turtle_id: 1 });
db.readings.createIndex({ timestamp: -1 });
db.readings.createIndex({ turtle_id: 1, timestamp: -1 });
db.readings.createIndex({
  latitude: 1,
  longitude: 1
}, { name: 'location_index' });

// Create a 2dsphere index for geospatial queries
db.readings.createIndex({
  location: '2dsphere'
}, { sparse: true });

print('Database initialization completed successfully!');
print('Collections created: turtles, readings');
print('Indexes created for optimal query performance');
