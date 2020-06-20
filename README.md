# Audiobook Generator
Serverless application which converts text to audio, and creates a simple video with it, for upload to Youtube. Uses a range of AWS services including SNS, S3, Lambda, ECS (Fargate variant), Polly and DynamoDB. Built in Python

## Contents
* ./Infrastructure - the definition of the infrastructure needed to run this application using AWS's CDK framework
* ./Functions - contains the actual application code, resources for running locally, and the definition for the video processing container

## Application Flow

## Technical details/Notes
### Container
#### Environment Variables
AUDIO_URL
VIDEO_S3_BUCKET
IMAGE_URL
BOOK_NAME

### Database
#### Schema
```json
{
    "id": "Randomly generated string",
    "bookName": "string",
    "imageURL": "string",
    "authorName": "string",
    "genres": ["genre 1", "genre 2"],
    "audioURLs":  ["URL for part 1", "URL for part 2"],
    "audioGenerated": true/false,
    "videoGenerated": true/false,
    "uploadedToYoutube": true/false,
    "youtubeURLs": ["URL for part 1", "URL for part 2"],
    "description": "string",
    "hidden": true/false,
    "hasShortPart": true/false,
    "addedAt": 12345678 // Date in Unix timestamp format
}
```