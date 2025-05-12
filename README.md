# Evaluation Backend

## Setup

1. Create and activate your micromamba environment (already done):
   ```sh
   micromamba activate evaluation
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Copy and edit environment variables:
   ```sh
   cp .env.example .env
   # Edit .env as needed
   ```

4. Run the FastAPI app:
   ```sh
   uvicorn app.main:app --reload
   ```

## Health Check
Visit [http://localhost:8000/health](http://localhost:8000/health) to verify the backend is running.