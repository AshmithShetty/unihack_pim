# UniHack PIM (Product Information Management)

UniHack PIM is a highly automated, AI-driven Product Information Management system designed to ingest, clean, scrape, enrich, and validate arbitrary supplier product data. The platform normalizes chaotic CSV datasets into a structured "Golden Record" format using an intelligent multi-stage pipeline, making it ready for downstream e-commerce and catalog applications.

## Features

### 1. Universal CSV Ingestion & AI Schema Mapping
- **Agnostic Input**: Upload any supplier CSV file. The system does not rely on hardcoded column names.
- **Intelligent Mapping**: Uses a Large Language Model (LLM) to analyze the input dataset and automatically propose mappings to the target Golden Record schema. Users can review, adjust, and confirm the mappings before processing begins.

### 2. Multi-Stage AI Enrichment Pipeline
The core of the application is a highly concurrent, asynchronous 5-stage pipeline:
- **Stage 1 (Cleaner)**: Sanitizes raw inputs, strips dummy data, and utilizes LLMs to confidently resolve Canonical Manufacturer Names and Brand Names.
- **Stage 2 (Scraper)**: Dynamically generates search queries based on the product row. Bypasses distributor domains to identify the official manufacturer product page and dedicated specification PDFs. Extracts text natively using PyMuPDF and Crawl4AI.
- **Stage 3 (Enricher)**: A generative AI agent that synthesizes short descriptions, long descriptions, invoice metadata, and extracts over 50 specific attribute-value-UOM tuples directly from the scraped web and PDF context.
- **Stage 4 (Validator)**: Standardizes unit conversions (e.g., decimal to imperial fractions where applicable) and computes a final confidence score based on the quality and source of the extracted data.
- **Stage 5 (Persister)**: Safely flattens the enriched product and logs every modified field into an Audit Log with source tracking.

### 3. Human Review Queue
- **Confidence Scoring**: Any row that falls below a 60% confidence threshold or triggers validation warnings is automatically flagged.
- **Queue Interface**: A dedicated UI where data stewards can manually review flagged rows, edit specific attributes, and approve them to clear the queue.

### 4. Dynamic Dashboard & Command Center
- **Command Center**: A fast, virtualized list displaying the status of every row. View comprehensive product identities, synthesized descriptions, and extracted specifications.
- **Dashboard**: Generates real-time, dynamic charts summarizing the completion rate, confidence distribution, and category distribution based strictly on the processed dataset.

### 5. NLP Database Chatbot
- **Conversational Analytics**: Embedded within each project is a LangChain SQL Agent. Users can ask natural language questions (e.g., "What is the average list price of the dishwashers?", "Show me products with confidence below 80%") and the AI will autonomously query the SQLite database to provide accurate answers.

## Tech Stack

### Frontend
- **Framework**: React 19 + Vite
- **Styling**: TailwindCSS
- **Routing**: React Router DOM
- **State Management**: Zustand
- **Charts/Visualization**: Recharts
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite3
- **AI / LLMs**: Groq (Llama-3.1-8b-instant / OpenAI OSS equivalents)
- **AI Orchestration**: LangChain (SQL Agent)
- **Web Scraping**: Crawl4AI
- **PDF Extraction**: PyMuPDF (fitz)
- **Data Processing**: Pandas

## Local Development Setup

Follow these instructions to clone the repository and run the application locally.

### Prerequisites
- Node.js (v18 or higher recommended)
- Python (3.9 or higher recommended)
- Git

### 1. Clone the Repository
Open your terminal and run:

```bash
git clone https://github.com/AshmithShetty/unihack_pim.git
cd unihack_pim
```

### 2. Environment Variables
You must configure the backend environment variables before starting.

1. Navigate to the root directory.
2. Copy the example configuration file:
   ```bash
   cp .env.example .env
   ```
3. Open the `.env` file and insert your Groq API key:
   ```env
   GROQ_API_KEY="your_groq_api_key_here"
   GROQ_MODEL="llama-3.1-8b-instant"
   ```

### 3. Backend Setup
The backend requires Python dependencies to be installed in a virtual environment.

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the required Python packages
pip install -r backend/requirements.txt

# Start the FastAPI server
python run_server.py
```
The backend server will start on `http://127.0.0.1:8000`. It will automatically initialize the SQLite database (`enrichment.db`) on the first run.

### 4. Frontend Setup
Open a new terminal window (keep the backend terminal running).

```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```
The frontend will start on `http://localhost:5173`. The Vite configuration automatically proxies all `/api` requests to your local backend.

## Deployment Notes
This application natively supports dual-mode execution (Local vs Online). If you choose to deploy online (e.g., Vercel for Frontend and Render for Backend):
- **Frontend**: Set `VITE_API_URL` in your Vercel environment variables to point to your Render backend URL.
- **Backend**: Set `FRONTEND_URL` in your Render environment variables to point to your Vercel URL. The FastAPI CORS middleware will dynamically authorize it.
