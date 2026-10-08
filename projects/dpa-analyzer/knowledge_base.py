"""
DPA Knowledge Base - Contains playbook and best practices for reviewing Data Processing Agreements
"""

class DPAKnowledgeBase:
    def __init__(self):
        self.playbook = self._create_playbook()
        self.key_clauses = self._get_key_clauses()
        self.risk_indicators = self._get_risk_indicators()
    
    def _create_playbook(self):
        """Create comprehensive DPA review playbook"""
        return {
            "overview": {
                "title": "Data Processing Agreement (DPA) Review Playbook",
                "purpose": "This playbook provides guidance for reviewing Data Processing Agreements to ensure GDPR compliance and adequate privacy protections.",
                "scope": "Applicable to all third-party data processing arrangements where personal data is shared."
            },
            "review_sections": [
                {
                    "section": "1. Parties and Roles",
                    "description": "Verify clear identification of data controller and processor roles",
                    "key_points": [
                        "Controller and processor clearly identified",
                        "Roles and responsibilities explicitly defined",
                        "No ambiguity about who controls processing purposes and means"
                    ],
                    "red_flags": [
                        "Joint controller arrangements without clear allocation of responsibilities",
                        "Processor attempting to determine purposes of processing",
                        "Unclear chain of responsibility in multi-party arrangements"
                    ]
                },
                {
                    "section": "2. Purpose and Scope of Processing",
                    "description": "Ensure processing is limited to specified, explicit and legitimate purposes",
                    "key_points": [
                        "Clear description of processing purposes",
                        "Specific categories of personal data identified",
                        "Data subjects clearly defined",
                        "Processing activities explicitly listed"
                    ],
                    "red_flags": [
                        "Vague or broad purpose descriptions",
                        "Open-ended categories of personal data",
                        "Unlimited scope for future processing activities",
                        "Secondary use rights without explicit consent"
                    ]
                },
                {
                    "section": "3. Data Subject Rights",
                    "description": "Verify adequate provisions for data subject rights fulfillment",
                    "key_points": [
                        "Processor assists with data subject requests",
                        "Response timeframes clearly defined",
                        "Technical and organizational measures for rights fulfillment",
                        "Procedures for handling rectification, erasure, and portability"
                    ],
                    "red_flags": [
                        "No mention of data subject rights assistance",
                        "Unreasonable response timeframes",
                        "Processor claiming inability to assist with certain rights",
                        "Excessive fees for rights fulfillment assistance"
                    ]
                },
                {
                    "section": "4. Security Measures",
                    "description": "Assess adequacy of technical and organizational security measures",
                    "key_points": [
                        "Appropriate technical safeguards (encryption, access controls)",
                        "Organizational measures (staff training, security policies)",
                        "Regular security assessments and updates",
                        "Incident detection and response procedures"
                    ],
                    "red_flags": [
                        "Generic or insufficient security measures",
                        "No mention of encryption for sensitive data",
                        "Lack of access controls or monitoring",
                        "No incident response procedures"
                    ]
                },
                {
                    "section": "5. International Transfers",
                    "description": "Ensure adequate safeguards for international data transfers",
                    "key_points": [
                        "Clear identification of transfer destinations",
                        "Appropriate transfer mechanisms (adequacy decisions, SCCs, BCRs)",
                        "Additional safeguards where required",
                        "Notification requirements for new transfer destinations"
                    ],
                    "red_flags": [
                        "Transfers to countries without adequacy decisions",
                        "No transfer mechanisms in place",
                        "Blanket permissions for worldwide transfers",
                        "Insufficient additional safeguards for high-risk transfers"
                    ]
                },
                {
                    "section": "6. Subprocessing",
                    "description": "Review subprocessor arrangements and approval mechanisms",
                    "key_points": [
                        "Clear subprocessor approval process",
                        "Written agreements with equivalent protection levels",
                        "Notification requirements for new subprocessors",
                        "Right to object to subprocessor appointments"
                    ],
                    "red_flags": [
                        "General authorization without approval rights",
                        "No equivalent protection requirements for subprocessors",
                        "Insufficient notification periods",
                        "No objection rights or unreasonable objection criteria"
                    ]
                },
                {
                    "section": "7. Data Retention and Deletion",
                    "description": "Verify appropriate data retention and deletion provisions",
                    "key_points": [
                        "Clear retention periods aligned with purposes",
                        "Secure deletion procedures and timelines",
                        "Certification of deletion where required",
                        "Return of data options"
                    ],
                    "red_flags": [
                        "Indefinite retention periods",
                        "No secure deletion procedures",
                        "Unreasonable delays in data return/deletion",
                        "Processor claiming right to retain copies"
                    ]
                },
                {
                    "section": "8. Breach Notification",
                    "description": "Ensure adequate breach notification procedures",
                    "key_points": [
                        "Prompt notification requirements (24-72 hours)",
                        "Detailed information requirements for breach notifications",
                        "Assistance with regulatory reporting",
                        "Cooperation in breach investigation and mitigation"
                    ],
                    "red_flags": [
                        "No specific notification timeframes",
                        "Limited information sharing about breaches",
                        "No assistance with regulatory obligations",
                        "Disclaimer of liability for breach-related costs"
                    ]
                },
                {
                    "section": "9. Auditing and Compliance",
                    "description": "Review audit rights and compliance monitoring provisions",
                    "key_points": [
                        "Reasonable audit rights and access",
                        "Regular compliance assessments",
                        "Documentation and record-keeping requirements",
                        "Third-party certification acceptance"
                    ],
                    "red_flags": [
                        "Severely restricted audit rights",
                        "Excessive fees for audit activities",
                        "No documentation or transparency requirements",
                        "Refusal to accept reasonable certification standards"
                    ]
                },
                {
                    "section": "10. Liability and Indemnification",
                    "description": "Assess liability allocation and indemnification provisions",
                    "key_points": [
                        "Appropriate liability allocation between parties",
                        "Adequate insurance or financial guarantees",
                        "Indemnification for processor-caused violations",
                        "No unreasonable liability caps for data protection violations"
                    ],
                    "red_flags": [
                        "Complete liability exclusions for the processor",
                        "Unreasonably low liability caps",
                        "No indemnification for processor negligence",
                        "Attempts to shift controller liability to processor"
                    ]
                }
            ],
            "risk_assessment": {
                "high_risk_indicators": [
                    "Processing of special category data without adequate safeguards",
                    "Large-scale systematic monitoring",
                    "Cross-border transfers to high-risk jurisdictions",
                    "Innovative technologies with privacy implications",
                    "Processing affecting vulnerable populations"
                ],
                "compliance_checklist": [
                    "Article 28 GDPR requirements fully addressed",
                    "Data Protection Impact Assessment completed if required",
                    "Legal basis for processing clearly established",
                    "Transparency requirements met",
                    "Data minimization principles applied"
                ]
            }
        }
    
    def _get_key_clauses(self):
        """Define key clauses that must be present in a DPA"""
        return [
            "purpose_limitation",
            "data_categories",
            "retention_period",
            "security_measures",
            "subprocessor_management",
            "data_subject_rights",
            "breach_notification",
            "international_transfers",
            "audit_rights",
            "termination_procedures"
        ]
    
    def _get_risk_indicators(self):
        """Define risk indicators for DPA analysis"""
        return {
            "high_risk": [
                "unlimited data retention",
                "broad processing purposes",
                "weak security measures",
                "unrestricted subprocessing",
                "no breach notification",
                "limited audit rights",
                "liability exclusions",
                "no data subject rights support"
            ],
            "medium_risk": [
                "vague purpose descriptions",
                "standard security measures",
                "general subprocessor approval",
                "limited international transfer safeguards",
                "basic breach notification",
                "restricted audit access"
            ],
            "low_risk": [
                "specific limited purposes",
                "strong security measures",
                "explicit subprocessor approval",
                "robust transfer safeguards",
                "comprehensive breach procedures",
                "full audit rights",
                "adequate liability provisions"
            ]
        }
    
    def get_playbook(self):
        """Return the complete DPA review playbook"""
        return self.playbook
    
    def get_key_clauses(self):
        """Return list of key clauses that should be present"""
        return self.key_clauses
    
    def get_risk_indicators(self):
        """Return risk indicators for analysis"""
        return self.risk_indicators
    
    def get_section_guidance(self, section_name: str):
        """Get specific guidance for a review section"""
        for section in self.playbook["review_sections"]:
            if section_name.lower() in section["section"].lower():
                return section
        return None
