from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from typing import Dict, List
import json
import os
from pathlib import Path

# Import our custom modules
from dpa_analyzer import DPAAnalyzer
from knowledge_base import DPAKnowledgeBase

app = FastAPI(title="DPA Privacy Legal Review AI Agent", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
knowledge_base = DPAKnowledgeBase()
analyzer = DPAAnalyzer()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "DPA Privacy Legal Review AI Agent is running!"}

@app.get("/playbook")
async def get_playbook():
    """Get the DPA review playbook"""
    try:
        playbook = knowledge_base.get_playbook()
        return {"playbook": playbook}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving playbook: {str(e)}")

@app.post("/analyze-dpa")
async def analyze_dpa(file: UploadFile = File(...)):
    """
    Analyze a Data Processing Agreement document
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.txt', '.doc', '.docx')):
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload PDF, TXT, DOC, or DOCX files."
            )
        
        # Read file content
        content = await file.read()
        
        # Process and analyze the DPA
        analysis_result = await analyzer.analyze_document(content, file.filename)
        
        return {
            "filename": file.filename,
            "analysis": analysis_result,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing DPA: {str(e)}")

@app.get("/analysis-template")
async def get_analysis_template():
    """Get the template/structure for DPA analysis"""
    return analyzer.get_analysis_template()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
