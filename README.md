# 🚀 AI-Powered Roadmap Generator  

An AI-powered roadmap generator that creates structured learning paths for various topics using **Mistral AI** or **OpenAI**. This project allows users to generate, store, and retrieve detailed course roadmaps formatted in **Markdown**.  The frontend for this project is available here:  [Roadmap Generator Frontend](https://github.com/madhvi-n/roadmap-generator-frontend)

## ✨ Features  

- Generate structured course roadmaps with AI  
- Supports **Mistral AI** and **OpenAI** for content generation  
- Stores roadmaps in a **SQL database**  
- Provides a **REST API** for fetching roadmaps  
- **React + TypeScript + Vite** frontend with **Tailwind CSS** for styling  
- Uses **React Markdown** for rendering formatted content

## 🔧 Tech Stack  

- **Backend:** FastAPI, SQLAlchemy, SQLite/PostgreSQL  
- **AI Models:** OpenAI, Mistral AI  
- **Frontend:** React 19 (Vite), TypeScript, Tailwind CSS  

## 🚀 Setup & Installation  

1. Clone the repository

    ```sh
    git clone https://github.com/madhvi-n/ai-roadmap-generator.git
    cd ai-roadmap-generator
    ```

2. Create a virtual environment & install dependencies

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use 'venv\Scripts\activate'
    pip install -r requirements.txt
    ```

3. Set up environment variables. Update .env with your OpenAI or Mistral AI API keys

    ```sh
    cp .env.example .env
    ```

4. Run the server

    ```sh
    uvicorn app.main:app --reload
    ```

    Server will be live at: `http://127.0.0.1:8000`

## 📖 **API Documentation**

FastAPI automatically generates interactive API documentation using **Swagger UI** and **ReDoc**.

- **Swagger UI:**  
  📍 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  

- **ReDoc UI:**  
  📍 [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)  
