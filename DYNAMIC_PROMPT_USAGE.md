# Dynamic Prompt System Usage Examples

## Sample Prompt Templates

Here are some example prompt templates you can use with the dynamic prompt system:

### 1. Menu Extraction (from your reference code)
```json
{
  "name": "Menu Extraction",
  "description": "Extract structured menu data from restaurant documents",
  "prompt_template": "You are a data extraction assistant.\n\nYour task:\n- Extract structured menu data from the given text.\n- Return valid JSON in this format:\n\n{{\n  \"menu\": {{\n    \"<main_category>\": {{\n      \"<sub_category>\": [\n        {{\n          \"name\": \"<item name>\",\n          \"price\": <number>,\n          \"description\": \"<short description>\",\n          \"extra_items\": [\n            {{\n              \"name\": \"Choose Your Toppings\",\n              \"options\": [\"pepperoni\", \"sausage\", \"bacon\", \"ham\"]\n            }}\n          ]\n        }}\n      ]\n    }}\n  }}\n}}\n\nRules:\n1. Main categories = broad groups like \"food\", \"drinks\", etc.\n2. Subcategories = dish type like \"pizza\", \"pasta\", \"burgers\".\n3. Each menu item must include: name, price, description.\n4. Always return valid JSON, no explanations.\n\nText:\n{text}"
}
```

### 2. Document Summarization
```json
{
  "name": "Document Summarizer",
  "description": "Create a comprehensive summary of any document",
  "prompt_template": "Please analyze the following text and provide a comprehensive summary:\n\n1. **Main Topics**: List the main topics covered\n2. **Key Points**: Extract the most important points\n3. **Summary**: Provide a concise summary (2-3 paragraphs)\n4. **Action Items**: If applicable, list any action items or next steps\n5. **Keywords**: Extract 5-10 key terms\n\nText:\n{text}"
}
```

### 3. Invoice Data Extraction
```json
{
  "name": "Invoice Extractor",
  "description": "Extract structured data from invoices",
  "prompt_template": "Extract the following information from this invoice text and return as JSON:\n\n{{\n  \"invoice_number\": \"string\",\n  \"date\": \"YYYY-MM-DD\",\n  \"vendor\": \"string\",\n  \"customer\": \"string\",\n  \"items\": [\n    {{\n      \"description\": \"string\",\n      \"quantity\": number,\n      \"unit_price\": number,\n      \"total\": number\n    }}\n  ],\n  \"subtotal\": number,\n  \"tax\": number,\n  \"total\": number\n}}\n\nText:\n{text}"
}
```

### 4. Contract Analysis
```json
{
  "name": "Contract Analyzer",
  "description": "Analyze legal contracts and extract key information",
  "prompt_template": "Analyze this contract text and extract the following information in JSON format:\n\n{{\n  \"parties\": [\"party1\", \"party2\"],\n  \"contract_type\": \"string\",\n  \"start_date\": \"YYYY-MM-DD\",\n  \"end_date\": \"YYYY-MM-DD\",\n  \"key_terms\": [\"term1\", \"term2\"],\n  \"payment_terms\": \"string\",\n  \"termination_clauses\": [\"clause1\", \"clause2\"],\n  \"risk_factors\": [\"risk1\", \"risk2\"],\n  \"summary\": \"Brief summary of the contract\"\n}}\n\nText:\n{text}"
}
```

## API Endpoints

### Dynamic Prompt Management
- `POST /dynamic-prompts/` - Create a new prompt
- `GET /dynamic-prompts/` - Get all user prompts
- `GET /dynamic-prompts/{prompt_id}` - Get specific prompt
- `PUT /dynamic-prompts/{prompt_id}` - Update prompt
- `DELETE /dynamic-prompts/{prompt_id}` - Delete prompt

### Document Processing
- `POST /dynamic-prompts/upload-document` - Upload and process document
- `GET /dynamic-prompts/processed-documents/` - Get all processed documents
- `GET /dynamic-prompts/processed-documents/{document_id}` - Get specific processed document
- `GET /dynamic-prompts/processed-documents/{document_id}/result` - Get processing result

## Usage Flow

1. **Create a Prompt**: Use the prompt management endpoints to create custom prompts
2. **Upload Document**: Upload a document (PDF, DOCX, TXT, or image) with a specific prompt ID
3. **Process**: The system will extract text and apply your custom prompt
4. **Retrieve Results**: Get the processed results in JSON format

## Supported File Types
- PDF (including scanned PDFs with OCR)
- DOCX (Word documents)
- TXT (Plain text)
- Images: JPG, JPEG, PNG, JFIF, BMP, TIFF, TIF, WEBP, HEIC
