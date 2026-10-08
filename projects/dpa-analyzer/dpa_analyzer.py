"""
DPA Analyzer - AI-powered analysis of Data Processing Agreements using open source LLMs
"""

import json
import asyncio
import aiohttp
import PyPDF2
import docx
from io import BytesIO
from typing import Dict, List, Any
from knowledge_base import DPAKnowledgeBase

class DPAAnalyzer:
    def __init__(self):
        self.knowledge_base = DPAKnowledgeBase()
        self.ollama_url = "http://localhost:11434"  # Default Ollama URL
        self.model_name = "llama3.2:1b"  # Using smaller, faster model
        
    async def analyze_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Analyze a DPA document and return structured analysis
        """
        try:
            # Extract text from document
            text_content = await self._extract_text(file_content, filename)
            
            # Perform AI analysis
            analysis_result = await self._perform_ai_analysis(text_content)
            
            # Structure the results
            structured_analysis = self._structure_analysis(analysis_result, text_content)
            
            return structured_analysis
            
        except Exception as e:
            raise Exception(f"Document analysis failed: {str(e)}")
    
    async def _extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from various file formats"""
        try:
            if filename.lower().endswith('.pdf'):
                return self._extract_from_pdf(file_content)
            elif filename.lower().endswith('.docx'):
                return self._extract_from_docx(file_content)
            elif filename.lower().endswith('.txt'):
                return file_content.decode('utf-8')
            else:
                raise Exception(f"Unsupported file format: {filename}")
        except Exception as e:
            raise Exception(f"Text extraction failed: {str(e)}")
    
    def _extract_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def _extract_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc_file = BytesIO(file_content)
            doc = docx.Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")
    
    async def _perform_ai_analysis(self, text_content: str) -> Dict[str, Any]:
        """
        Perform AI analysis using Ollama LLM
        """
        try:
            # Get playbook for context
            playbook = self.knowledge_base.get_playbook()
            key_clauses = self.knowledge_base.get_key_clauses()
            risk_indicators = self.knowledge_base.get_risk_indicators()
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(text_content, playbook, key_clauses, risk_indicators)
            
            # Call Ollama API
            analysis_result = await self._call_ollama_api(prompt)
            
            return analysis_result
            
        except Exception as e:
            # Fallback to rule-based analysis if LLM fails
            print(f"LLM analysis failed, falling back to rule-based analysis: {str(e)}")
            return await self._fallback_analysis(text_content)
    
    def _create_analysis_prompt(self, text_content: str, playbook: Dict, key_clauses: List, risk_indicators: Dict) -> str:
        """Create a simpler, more focused prompt for DPA analysis"""
        
        # Limit text content for smaller model
        limited_text = text_content[:2000]  # Much smaller for 1B model
        
        prompt = f"""You are a privacy lawyer reviewing a Data Processing Agreement (DPA).

Analyze this DPA text for GDPR compliance and respond ONLY with valid JSON:

DOCUMENT:
{limited_text}

REQUIRED JSON RESPONSE:
{{
    "overall_assessment": {{
        "compliance_score": 75,
        "risk_level": "medium",
        "executive_summary": "Brief summary of main findings"
    }},
    "section_analysis": [
        {{
            "section": "Key Provisions",
            "status": "compliant",
            "score": 80,
            "findings": ["Found data controller definitions", "Security measures present"],
            "recommendations": ["Add retention periods", "Clarify breach notification"],
            "red_flags": ["Missing audit rights"]
        }}
    ],
    "missing_clauses": ["retention period", "audit rights"],
    "strengths": ["Clear roles", "Security measures"],
    "critical_issues": ["No breach notification clause"],
    "recommendations": ["Add missing clauses", "Define retention periods"]
}}

Respond with ONLY the JSON object, no other text."""
        return prompt
    
    async def _call_ollama_api(self, prompt: str) -> Dict[str, Any]:
        """Call Ollama API for LLM analysis"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent legal analysis
                        "top_p": 0.9
                    }
                }
                
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        # Try to parse JSON response with better error handling
                        try:
                            # Clean up the response text
                            cleaned_response = response_text.strip()
                            
                            # Try direct JSON parsing first
                            try:
                                return json.loads(cleaned_response)
                            except json.JSONDecodeError:
                                # Extract JSON from response (might have additional text)
                                json_start = cleaned_response.find('{')
                                json_end = cleaned_response.rfind('}') + 1
                                if json_start != -1 and json_end != -1:
                                    json_content = cleaned_response[json_start:json_end]
                                    # Fix common JSON issues
                                    json_content = json_content.replace('\n', ' ').replace('  ', ' ')
                                    return json.loads(json_content)
                                else:
                                    raise Exception("No valid JSON found in response")
                        except (json.JSONDecodeError, Exception) as e:
                            print(f"JSON parsing failed: {e}")
                            print(f"Raw response (first 500 chars): {response_text[:500]}")
                            # Return a basic structure if JSON parsing fails
                            return {
                                "overall_assessment": {
                                    "compliance_score": 70,
                                    "risk_level": "medium", 
                                    "executive_summary": "AI analysis encountered formatting issues, using fallback assessment"
                                },
                                "section_analysis": [
                                    {
                                        "section": "AI Analysis",
                                        "status": "unclear",
                                        "score": 70,
                                        "findings": ["AI generated response but with formatting issues"],
                                        "recommendations": ["Manual review recommended"],
                                        "red_flags": ["AI response parsing failed"]
                                    }
                                ],
                                "missing_clauses": [],
                                "strengths": ["Document processed by AI"],
                                "critical_issues": ["Response formatting needs improvement"],
                                "recommendations": ["Consider upgrading to larger AI model", "Manual legal review advised"]
                            }
                    else:
                        raise Exception(f"Ollama API call failed with status {response.status}")
                        
        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")
    
    async def _fallback_analysis(self, text_content: str) -> Dict[str, Any]:
        """
        Fallback rule-based analysis when LLM is not available
        """
        text_lower = text_content.lower()
        
        # Simple keyword-based analysis
        findings = []
        missing_clauses = []
        risk_level = "medium"
        score = 70
        
        # Check for key terms
        key_terms = {
            "data controller": ["data controller", "controller"],
            "data processor": ["data processor", "processor"], 
            "personal data": ["personal data", "personally identifiable"],
            "gdpr": ["gdpr", "general data protection regulation"],
            "security measures": ["security measures", "technical safeguards", "encryption"],
            "data breach": ["data breach", "breach notification", "security incident"],
            "data subject rights": ["data subject rights", "right to access", "right to erasure"],
            "retention": ["retention period", "data retention", "deletion"],
            "subprocessor": ["subprocessor", "sub-processor", "third party"]
        }
        
        for clause, keywords in key_terms.items():
            found = any(keyword in text_lower for keyword in keywords)
            if found:
                findings.append(f"✓ {clause.title()} provisions identified")
                score += 5
            else:
                missing_clauses.append(clause)
                score -= 10
        
        # Risk assessment based on findings
        if score >= 80:
            risk_level = "low"
        elif score >= 60:
            risk_level = "medium"
        else:
            risk_level = "high"
            
        return {
            "overall_assessment": {
                "compliance_score": max(0, min(100, score)),
                "risk_level": risk_level,
                "executive_summary": f"Rule-based analysis completed. {len(findings)} key provisions identified, {len(missing_clauses)} clauses may be missing."
            },
            "section_analysis": [
                {
                    "section": "Automated Analysis",
                    "status": "partial_review",
                    "score": score,
                    "findings": findings,
                    "recommendations": ["Complete LLM setup for detailed analysis", "Manual legal review recommended"],
                    "red_flags": ["LLM analysis unavailable - limited assessment performed"]
                }
            ],
            "missing_clauses": missing_clauses,
            "strengths": findings,
            "critical_issues": ["LLM service unavailable", "Manual review required"],
            "recommendations": [
                "Set up Ollama with Llama model for detailed analysis",
                "Conduct manual legal review",
                "Verify all GDPR Article 28 requirements"
            ]
        }
    
    def _structure_analysis(self, analysis_result: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """Structure and enhance the analysis results"""
        
        # Add metadata
        analysis_result["metadata"] = {
            "document_length": len(original_text),
            "analysis_timestamp": asyncio.get_event_loop().time(),
            "analyzer_version": "1.0.0",
            "model_used": self.model_name
        }
        
        # Add playbook reference
        analysis_result["playbook_reference"] = {
            "sections_reviewed": len(self.knowledge_base.get_playbook()["review_sections"]),
            "playbook_version": "1.0.0"
        }
        
        return analysis_result
    
    def get_analysis_template(self) -> Dict[str, Any]:
        """Return the expected structure of analysis results"""
        return {
            "overall_assessment": {
                "compliance_score": "integer (0-100)",
                "risk_level": "string (low|medium|high)",
                "executive_summary": "string"
            },
            "section_analysis": [
                {
                    "section": "string",
                    "status": "string (compliant|non_compliant|unclear)",
                    "score": "integer (0-100)",
                    "findings": ["array of strings"],
                    "recommendations": ["array of strings"],
                    "red_flags": ["array of strings"]
                }
            ],
            "missing_clauses": ["array of strings"],
            "strengths": ["array of strings"],
            "critical_issues": ["array of strings"],
            "recommendations": ["array of strings"],
            "metadata": {
                "document_length": "integer",
                "analysis_timestamp": "timestamp",
                "analyzer_version": "string",
                "model_used": "string"
            }
        }
