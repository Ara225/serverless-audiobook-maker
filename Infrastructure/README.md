# Infrastructure for Audiobook Generator
# Database
DynamoDB, part of the CloudFormation stack defined in the CDK code (.../Infrastructure/audiobook/audiobook_stack.py)
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