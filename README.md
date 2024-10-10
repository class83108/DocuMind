# DocuMind

DocuMind is a project where users can upload PDFs to the server, input keywords, and retrieve related parts of the articles.

## Features

- Upload PDF documents to the server.
- Search for keywords within the uploaded documents.
- Retrieve and display parts of the articles related to the input keywords.

## Technologies Used

- Django: Full-stack framework
- Django Admin: Used as a direct operation platform for users
- Django Celery: Handles long-running tasks, such as converting plain text to vector data and interacting with AI models
- PostgreSQL: Used for persistent data storage in the project
- Redis: Besides serving as Django's cache storage, it's mainly used to store Celery queue information
- ChromaDB: Lightweight vector database
